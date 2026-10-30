# frozen_string_literal: true
require 'webrick'
require 'json'
require_relative '../lib/protocolo_ruby/analyzer'

port = Integer(ENV.fetch('PORT', '10000'))
server = WEBrick::HTTPServer.new(
  Port: port, BindAddress: '0.0.0.0',
  RequestTimeout: 8, MaxClients: 8,
  AccessLog: [], Logger: WEBrick::Log.new($stderr, WEBrick::Log::WARN)
)

def response_json(res, code, data)
  res.status = code
  res['Content-Type'] = 'application/json; charset=utf-8'
  res['Cache-Control'] = 'no-store'
  res['X-Content-Type-Options'] = 'nosniff'
  res['X-Frame-Options'] = 'DENY'
  res['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
  res['Access-Control-Allow-Origin'] = 'null'
  res.body = JSON.generate(data)
end

server.mount_proc('/') do |req, res|
  if req.request_method != 'GET'
    response_json(res, 405, {error: 'method_not_allowed', sample_uploads: 'disabled'})
    next
  end
  case req.path
  when '/health'
    response_json(res, 200, {status: 'ok', app: 'protocolo-ruby', runtime: 'ruby', mode: 'staging'})
  when '/v1/capabilities'
    response_json(res, 200, {
      version: '0.3-staging',
      static_analysis: 'demo_only',
      real_file_uploads: 'disabled',
      yara_x: 'offline_adapter_only',
      background_jobs: 'not_deployed',
      sandbox: 'not_deployed'
    })
  when '/v1/demo'
    # Fixed harmless text fixture. This API does not ingest caller-supplied bytes.
    report = ProtocoloRuby::Analyzer.new.analyze("Protocol Ruby harmless fixture https://example.org 192.0.2.1", filename: 'synthetic.txt')
    response_json(res, 200, {demo: true, report: report})
  else
    response_json(res, 404, {error: 'not_found'})
  end
end
trap('INT') { server.shutdown }
trap('TERM') { server.shutdown }
server.start
