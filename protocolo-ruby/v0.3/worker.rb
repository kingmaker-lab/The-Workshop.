# frozen_string_literal: true
require 'json'
require 'redis'
require 'sidekiq'
require_relative '../lib/protocolo_ruby/analyzer'

Sidekiq.configure_client { |c| c.redis = {url: ENV.fetch('REDIS_URL', 'redis://127.0.0.1:6379/0')} }
Sidekiq.configure_server { |c| c.redis = {url: ENV.fetch('REDIS_URL', 'redis://127.0.0.1:6379/0')} }

class AnalysisJob
  include Sidekiq::Job
  sidekiq_options retry: false, queue: 'analysis'

  def perform(id)
    redis = Redis.new(url: ENV.fetch('REDIS_URL', 'redis://127.0.0.1:6379/0'))
    key = "pr:sample:#{id}"
    bytes = redis.getdel(key)
    unless bytes
      redis.set("pr:status:#{id}", JSON.generate(state: 'expired'), ex: 3600)
      return
    end
    report = ProtocoloRuby::Analyzer.new.analyze(bytes)
    redis.set("pr:status:#{id}", JSON.generate(state: 'completed', report: report), ex: 3600)
  rescue StandardError
    redis&.set("pr:status:#{id}", JSON.generate(state: 'failed'), ex: 3600)
    raise
  end
end
