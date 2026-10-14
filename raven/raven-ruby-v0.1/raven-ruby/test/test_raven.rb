# frozen_string_literal: true
require 'minitest/autorun'
require 'socket'
require 'tempfile'
require 'webrick'
require_relative '../lib/raven'

class RavenTest < Minitest::Test
  def setup
    @server = WEBrick::HTTPServer.new(Port: 0, BindAddress: '127.0.0.1', Logger: WEBrick::Log.new(File::NULL), AccessLog: [])
    @server.mount_proc('/') do |_req, res|
      res.status = 200
      res['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'"
      res['X-Content-Type-Options'] = 'nosniff'
      res['Set-Cookie'] = 'session=secret-value; Path=/; HttpOnly; SameSite=Lax'
      res.body = 'Hello'
    end
    @thread = Thread.new { @server.start }
    sleep 0.01 until @server.status == :Running
    @url = "http://127.0.0.1:#{@server.listeners.first.addr[1]}/"
  end

  def teardown
    @server.shutdown
    @thread.join
  end

  def test_snapshot_redacts_cookie_values
    snapshot = Raven.inspect_url(@url)
    assert_equal 200, snapshot['status']
    assert_equal 'HEAD', snapshot['request_method']
    assert_equal 'session', snapshot.dig('cookies', 0, 'name')
    refute_includes JSON.generate(snapshot), 'secret-value'
  end

  def test_no_automatic_redirect
    @server.mount_proc('/redirect') { |_req, res| res.status = 302; res['Location'] = 'https://example.org/' }
    snapshot = Raven.inspect_url(@url + 'redirect')
    assert_equal 302, snapshot['status']
    assert_equal 'https://example.org/', snapshot['redirect_location']
  end

  def test_unchanged_snapshot_ignores_observed_timestamp
    a = Raven.inspect_url(@url)
    b = Marshal.load(Marshal.dump(a))
    b['observed_at'] = '2099-01-01T00:00:00Z'
    assert_equal 0, Raven.diff(a, b)['changes_count']
  end

  def test_drift_detects_removed_header
    a = Raven.inspect_url(@url)
    b = Marshal.load(Marshal.dump(a))
    b['headers'].delete('content-security-policy')
    assert_includes Raven.diff(a, b)['changes'].map { |c| c['path'] }, '/headers/content-security-policy'
  end

  def test_dynamic_csp_nonce_does_not_create_drift
    a = Raven.inspect_url(@url)
    b = Marshal.load(Marshal.dump(a))
    a['headers']['content-security-policy'] = "script-src 'nonce-AAAabcd123='"
    b['headers']['content-security-policy'] = "script-src 'nonce-BBBabcd123='"
    assert_equal 0, Raven.diff(a, b)['changes_count']
  end

  def test_different_target_is_rejected
    a = Raven.inspect_url(@url)
    b = Marshal.load(Marshal.dump(a))
    b['target'] = 'https://other.example:443/'
    assert_raises(Raven::Error) { Raven.diff(a, b) }
  end

  def test_malformed_url_is_rejected
    assert_raises(Raven::Error) { Raven.inspect_url('file:///etc/passwd') }
    assert_raises(Raven::Error) { Raven.inspect_url('http://example.test/?access_token=secret') }
  end

  def test_cookie_attributes_parser
    c = Raven.parse_cookie('uid=secret; Path=/; Secure; HttpOnly; SameSite=Strict')
    assert_equal 'uid', c['name']
    assert_equal 'strict', c['same_site']
    assert c['secure']
    assert c['http_only']
    refute c.to_s.include?('secret')
  end

  def test_json_round_trip
    snap = Raven.inspect_url(@url)
    Tempfile.create(['raven-', '.json']) do |file|
      Raven.save_json(file.path, snap)
      assert_equal snap, Raven.read_snapshot(file.path)
    end
  end
end
