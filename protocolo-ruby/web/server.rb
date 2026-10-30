# frozen_string_literal: true
require 'webrick'
require 'json'
require_relative '../lib/protocolo_ruby/analyzer'

ROOT = File.expand_path(__dir__)
PORT = Integer(ENV.fetch('PORT', '9292'))
server = WEBrick::HTTPServer.new(Port: PORT, BindAddress: ENV.fetch('BIND', '127.0.0.1'), RequestTimeout: 10, MaxClients: 8)
server.mount_proc('/') do |req, res|
  res['Cache-Control'] = 'no-store'
  res['X-Content-Type-Options'] = 'nosniff'
  res['X-Frame-Options'] = 'DENY'
  res['Content-Security-Policy'] = "default-src 'none'; style-src 'self'; script-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'none'"
  case [req.request_method, req.path]
  when ['GET', '/']
    res['Content-Type'] = 'text/html; charset=utf-8'
    res.body = File.binread(File.join(ROOT, 'index.html'))
  when ['GET', '/app.js']
    res['Content-Type'] = 'text/javascript; charset=utf-8'
    res.body = File.binread(File.join(ROOT, 'app.js'))
  when ['GET', '/style.css']
    res['Content-Type'] = 'text/css; charset=utf-8'
    res.body = File.binread(File.join(ROOT, 'style.css'))
  when ['POST', '/api/analyze']
    begin
      length = req.content_length.to_i
      raise ArgumentError, 'Content-Length required' if length.zero?
      raise ArgumentError, 'File exceeds 20 MiB limit' if length > ProtocoloRuby::Analyzer::MAX_BYTES
      raise ArgumentError, 'Use application/octet-stream' unless req['content-type'] == 'application/octet-stream'
      result = ProtocoloRuby::Analyzer.new.analyze(req.body, filename: req['x-filename'] || 'sample.bin')
      res['Content-Type'] = 'application/json; charset=utf-8'
      res.body = JSON.generate(result)
    rescue ArgumentError => e
      res.status = 400
      res['Content-Type'] = 'application/json; charset=utf-8'
      res.body = JSON.generate(error: e.message)
    end
  else
    res.status = 404
    res.body = 'Not found'
  end
end
trap('INT') { server.shutdown }
trap('TERM') { server.shutdown }
server.start
