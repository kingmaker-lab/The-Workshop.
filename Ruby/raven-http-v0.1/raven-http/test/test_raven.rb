# frozen_string_literal: true

require 'minitest/autorun'
require 'webrick'
require 'json'
require_relative '../raven'

class RavenTest < Minitest::Test
  def setup
    @server = WEBrick::HTTPServer.new(Port: 0, BindAddress: '127.0.0.1', Logger: WEBrick::Log.new(File::NULL), AccessLog: [])
    @server.mount_proc('/basic') do |_req, res|
      res['Content-Type'] = 'text/html'
      res.body = '<html><body>ok</body></html>'
    end
    @server.mount_proc('/hardened') do |_req, res|
      res['Content-Type'] = 'text/html'
      res['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'"
      res['X-Content-Type-Options'] = 'nosniff'
      res['Referrer-Policy'] = 'no-referrer'
      res.body = 'ok'
    end
    @server.mount_proc('/cookie') do |_req, res|
      res['Set-Cookie'] = 'session_id=very-secret-value; Path=/'
      res['Content-Type'] = 'text/plain'
      res.body = 'ok'
    end
    @server.mount_proc('/cors') do |_req, res|
      res['Access-Control-Allow-Origin'] = '*'
      res['Access-Control-Allow-Credentials'] = 'true'
      res.body = 'ok'
    end
    @server.mount_proc('/redirect') do |_req, res|
      res.status = 302
      res['Location'] = '/basic'
      res.body = ''
    end
    @server.mount_proc('/external') do |_req, res|
      res.status = 302
      res['Location'] = 'https://example.com/other'
      res.body = ''
    end
    @server.mount_proc('/huge') do |_req, res|
      res.body = 'x' * 8_000
    end
    @thread = Thread.new { @server.start }
    sleep 0.01 until @server.status == :Running
    @url = "http://127.0.0.1:#{@server.config[:Port]}"
  end

  def teardown
    @server.shutdown
    @thread.join
  end

  def audit(path, **options)
    RavenHTTP::Auditor.new(@url + path, allow_private: true, **options).run
  end

  def test_rejects_private_ip_by_default
    assert_raises(RavenHTTP::ScopeError) { RavenHTTP::Auditor.new(@url + '/basic').run }
  end

  def test_missing_headers_classified_as_observation
    report = audit('/basic')
    ids = report[:findings].map { |f| f[:id] }
    assert_includes ids, 'missing_csp'
    assert_includes ids, 'missing_frame_protection'
    assert_equal 200, report[:response][:status]
  end

  def test_csp_frame_ancestors_can_replace_x_frame_options
    ids = audit('/hardened')[:findings].map { |f| f[:id] }
    refute_includes ids, 'missing_csp'
    refute_includes ids, 'missing_frame_protection'
    refute_includes ids, 'missing_nosniff'
  end

  def test_cookie_value_not_exposed_in_json
    report = audit('/cookie?token=secret')
    serialized = JSON.generate(report)
    assert_includes serialized, 'session_id'
    refute_includes serialized, 'very-secret-value'
    refute_includes serialized, 'token=secret'
    assert_includes serialized, 'token=REDACTED'
  end

  def test_cors_wildcard_is_not_labeled_exploitable
    report = audit('/cors')
    f = report[:findings].find { |entry| entry[:id] == 'cors_wildcard' }
    assert_equal 'info', f[:severity]
    assert_match(/incompatível/, f[:evidence])
  end

  def test_follows_same_origin_redirect_only
    report = audit('/redirect')
    assert_equal 2, report[:requests_made]
    assert_equal 200, report[:response][:status]
  end

  def test_blocks_external_redirect
    report = audit('/external')
    assert_equal 1, report[:requests_made]
    assert_includes report[:findings].map { |f| f[:id] }, 'redirect_out_of_scope'
  end

  def test_respects_redirect_budget
    report = audit('/redirect', max_redirects: 0)
    assert_equal 1, report[:requests_made]
    assert_includes report[:findings].map { |f| f[:id] }, 'redirect_limit'
  end

  def test_body_limit
    assert_raises(RavenHTTP::LimitError) { audit('/huge', max_bytes: 1_024) }
  end

  def test_invalid_url_rejected
    assert_raises(RavenHTTP::ScopeError) { RavenHTTP::Auditor.new('file:///etc/passwd') }
    assert_raises(RavenHTTP::ScopeError) { RavenHTTP::Auditor.new('http://user:pass@example.com/') }
  end
end
