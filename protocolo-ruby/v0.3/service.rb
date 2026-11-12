# frozen_string_literal: true
require 'rack'
require 'json'
require 'securerandom'
require 'openssl'
require 'redis'
require 'sidekiq'
require_relative 'worker'

class ProtocolRubyAPI
  MAX_SIZE = 20 * 1024 * 1024
  def initialize
    @redis = Redis.new(url: ENV.fetch('REDIS_URL', 'redis://127.0.0.1:6379/0'))
    @token = ENV.fetch('RUBY_API_TOKEN') { raise 'Set RUBY_API_TOKEN' }
    raise 'API token too short' if @token.bytesize < 32
  end

  def call(env)
    request = Rack::Request.new(env)
    return respond(200, {status: 'ok', service: 'protocolo-ruby-v0.3'}) if request.get? && request.path == '/health'
    supplied = env['HTTP_AUTHORIZATION'].to_s.delete_prefix('Bearer ')
    return respond(401, {error: 'unauthorized'}) unless secure_match(supplied, @token)
    if request.post? && request.path == '/v1/analyses'
      length = env['CONTENT_LENGTH'].to_i
      return respond(413, {error: 'sample exceeds 20 MiB'}) if length > MAX_SIZE
      return respond(400, {error: 'application/octet-stream required'}) unless request.media_type == 'application/octet-stream'
      bytes = request.body.read(MAX_SIZE + 1)
      return respond(400, {error: 'empty sample'}) if bytes.empty?
      return respond(413, {error: 'sample exceeds 20 MiB'}) if bytes.bytesize > MAX_SIZE
      id = SecureRandom.uuid
      # Redis stores the temporary binary payload with a short TTL. No persistence allowed.
      @redis.set("pr:sample:#{id}", bytes, ex: 300, nx: true)
      @redis.set("pr:status:#{id}", JSON.generate(state: 'queued'), ex: 3600)
      AnalysisJob.perform_async(id)
      return respond(202, {id: id, state: 'queued'})
    end
    if request.get? && (match = request.path.match(%r{\A/v1/analyses/([0-9a-f-]{36})\z}))
      value = @redis.get("pr:status:#{match[1]}")
      return respond(404, {error: 'unknown or expired analysis'}) unless value
      return [200, headers, [value]]
    end
    respond(404, {error: 'not found'})
  rescue Redis::BaseError
    respond(503, {error: 'queue unavailable'})
  end

  private

  def secure_match(a, b)
    a.bytesize == b.bytesize && Rack::Utils.secure_compare(a, b)
  end

  def headers
    {'content-type' => 'application/json; charset=utf-8', 'cache-control' => 'no-store',
     'x-content-type-options' => 'nosniff'}
  end

  def respond(code, body)
    [code, headers, [JSON.generate(body)]]
  end
end
