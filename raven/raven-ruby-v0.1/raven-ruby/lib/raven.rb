# frozen_string_literal: true

require 'json'
require 'net/http'
require 'openssl'
require 'optparse'
require 'time'
require 'uri'

module Raven
  VERSION = '0.1.0'
  HEADER_NAMES = %w[
    strict-transport-security content-security-policy x-content-type-options
    referrer-policy permissions-policy x-frame-options
    cross-origin-opener-policy cross-origin-embedder-policy
    cross-origin-resource-policy access-control-allow-origin
    access-control-allow-credentials
  ].freeze

  class Error < StandardError; end

  module_function

  def inspect_url(url, timeout: 8)
    uri = URI.parse(url)
    unless %w[http https].include?(uri.scheme) && uri.host && !uri.host.empty?
      raise Error, 'Informe uma URL HTTP(S) absoluta.'
    end
    raise Error, 'Credenciais e query strings na URL não são permitidas.' if uri.userinfo || uri.query
    raise Error, 'O timeout precisa ser positivo.' unless timeout.positive?

    # Apenas UMA solicitação HEAD; redirecionamentos não são seguidos.
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = uri.scheme == 'https'
    http.verify_mode = OpenSSL::SSL::VERIFY_PEER if http.use_ssl?
    http.open_timeout = timeout
    http.read_timeout = timeout
    http.write_timeout = timeout
    http.max_retries = 0

    response = nil
    certificate = nil
    http.start do |client|
      response = client.request(Net::HTTP::Head.new(uri.request_uri))
      certificate = client.peer_cert if client.use_ssl?
    end

    headers = HEADER_NAMES.each_with_object({}) do |header, result|
      values = response.get_fields(header)
      result[header] = values.join(', ') if values && !values.empty?
    end

    cookies = Array(response.get_fields('set-cookie')).filter_map do |line|
      parse_cookie(line)
    end.sort_by { |cookie| [cookie['name'], cookie['domain'].to_s, cookie['path'].to_s] }

    tls = certificate && {
      'subject_cn' => certificate.subject.to_a.find { |part| part[0] == 'CN' }&.at(1),
      'issuer_cn' => certificate.issuer.to_a.find { |part| part[0] == 'CN' }&.at(1),
      'valid_from' => certificate.not_before.utc.iso8601,
      'expires_at' => certificate.not_after.utc.iso8601,
      'days_until_expiry' => ((certificate.not_after - Time.now) / 86_400).floor
    }

    snapshot = {
      'schema_version' => 1,
      'tool' => "RAVEN #{VERSION}",
      'target' => "#{uri.scheme}://#{uri.host}:#{uri.port}#{uri.path.empty? ? '/' : uri.path}",
      'observed_at' => Time.now.utc.iso8601,
      'request_method' => 'HEAD',
      'status' => response.code.to_i,
      'redirect_location' => response['location'],
      'headers' => headers,
      'cookies' => cookies,
      'tls' => tls
    }
    snapshot['observations'] = observations(snapshot)
    snapshot
  rescue URI::InvalidURIError
    raise Error, 'URL inválida.'
  rescue SocketError, IOError, SystemCallError, Timeout::Error, OpenSSL::SSL::SSLError => e
    raise Error, "Falha de conexão ou TLS: #{e.class}: #{e.message}"
  end

  def parse_cookie(header)
    segments = header.split(';').map(&:strip)
    name, = segments.shift.to_s.split('=', 2)
    return nil unless name && name.match?(/\A[A-Za-z0-9!#$%&'*+.^_`|~-]+\z/)

    flags = segments.map(&:downcase)
    same_site_attr = segments.find { |s| s.match?(/\Asamesite\s*=/i) }
    {
      'name' => name,
      'domain' => attribute(segments, 'domain'),
      'path' => attribute(segments, 'path'),
      'secure' => flags.include?('secure'),
      'http_only' => flags.include?('httponly'),
      'same_site' => same_site_attr&.split('=', 2)&.last&.strip&.downcase
    }
  end

  def attribute(segments, key)
    value = segments.find { |s| s.match?(/\A#{Regexp.escape(key)}\s*=/i) }
    value&.split('=', 2)&.last&.strip
  end

  def observations(snap)
    h = snap.fetch('headers')
    result = []
    if [405, 501].include?(snap['status'])
      return [{ 'severity' => 'info', 'code' => 'head_unsupported', 'message' => 'Servidor não aceita HEAD; não é possível inferir sua postura de segurança nesta execução.' }]
    end
    append = ->(severity, code, message) { result << { 'severity' => severity, 'code' => code, 'message' => message } }

    if snap['target'].start_with?('http://')
      append.call('medium', 'unencrypted_transport', 'O alvo utiliza HTTP sem TLS.')
    elsif !h.key?('strict-transport-security')
      append.call('low', 'missing_hsts', 'HSTS não observado na resposta HTTPS.')
    end
    append.call('info', 'missing_csp', 'CSP não observada; verificar o contexto antes de classificar o risco.') unless h.key?('content-security-policy')
    append.call('low', 'missing_nosniff', 'X-Content-Type-Options não observado.') unless h['x-content-type-options']&.downcase == 'nosniff'
    append.call('info', 'missing_referrer_policy', 'Referrer-Policy não observada.') unless h.key?('referrer-policy')
    unless h.key?('x-frame-options') || h.fetch('content-security-policy', '').match?(/(?:\A|;)\s*frame-ancestors\b/i)
      append.call('info', 'no_frame_restriction', 'Não foi observada uma restrição explícita de embedding.')
    end

    snap['cookies'].each do |cookie|
      if snap['target'].start_with?('https://') && !cookie['secure']
        append.call('medium', 'cookie_without_secure', "Cookie #{cookie['name']} sem Secure na resposta HTTPS.")
      end
      unless cookie['http_only']
        append.call('info', 'cookie_without_http_only', "Cookie #{cookie['name']} sem HttpOnly; avaliar se precisa ser acessível por JavaScript.")
      end
      if cookie['same_site'].nil?
        append.call('info', 'cookie_without_samesite', "Cookie #{cookie['name']} sem SameSite explícito.")
      end
    end

    if snap['tls'] && snap['tls']['days_until_expiry'] <= 30
      append.call('medium', 'tls_expiring', 'O certificado TLS vence em até 30 dias.')
    end
    if (300..399).cover?(snap['status'])
      append.call('info', 'redirect_not_followed', 'Redirecionamento registrado, mas não seguido por segurança de escopo.')
    end
    result
  end

  def read_snapshot(path)
    data = JSON.parse(File.read(path))
    unless data.is_a?(Hash) && data['schema_version'] == 1 && data['target'].is_a?(String) &&
           data['headers'].is_a?(Hash) && data['cookies'].is_a?(Array)
      raise Error, "Snapshot incompatível ou inválido: #{path}"
    end
    data
  rescue JSON::ParserError
    raise Error, "JSON inválido: #{path}"
  rescue Errno::ENOENT, Errno::EACCES => e
    raise Error, "Não foi possível abrir #{path}: #{e.message}"
  end

  def comparable_cookie(cookie)
    cookie.slice('name', 'domain', 'path', 'secure', 'http_only', 'same_site')
  end

  def normalized_header(key, value)
    return value unless key == 'content-security-policy' && value.is_a?(String)
    # Nonces são aleatórios por resposta e não devem gerar falsos alertas.
    value.gsub(/'nonce-[A-Za-z0-9+\/_=-]+'/, "'nonce-<rotating>'")
  end

  def posture(snapshot)
    headers = snapshot.fetch('headers').to_h do |key, value|
      normalized_key = key.downcase
      [normalized_key, normalized_header(normalized_key, value)]
    end
    cookies = snapshot.fetch('cookies').map { |cookie| comparable_cookie(cookie) }
    cookies.sort_by! { |cookie| [cookie['name'].to_s, cookie['domain'].to_s, cookie['path'].to_s] }
    tls = snapshot['tls']
    {
      'status' => snapshot['status'],
      'headers' => headers,
      'cookies' => cookies,
      'tls' => tls&.slice('subject_cn', 'issuer_cn', 'valid_from', 'expires_at')
    }
  end

  def diff(before, after)
    raise Error, 'Os snapshots devem ter o mesmo alvo.' unless before['target'] == after['target']
    old_state = posture(before)
    new_state = posture(after)
    changes = []
    compare_tree(old_state, new_state, '', changes)
    { 'target' => before['target'], 'changes_count' => changes.size, 'changes' => changes }
  end

  def compare_tree(before, after, path, changes)
    if before.is_a?(Hash) && after.is_a?(Hash)
      (before.keys | after.keys).sort.each do |key|
        compare_tree(before[key], after[key], "#{path}/#{key}", changes)
      end
    elsif before != after
      changes << { 'path' => path, 'before' => before, 'after' => after }
    end
  end

  def save_json(path, obj)
    File.write(path, JSON.pretty_generate(obj) + "\n")
  rescue Errno::ENOENT, Errno::EACCES => e
    raise Error, "Não foi possível gravar #{path}: #{e.message}"
  end

  def run(args)
    cmd = args.shift
    case cmd
    when 'snapshot'
      options = { timeout: 8, output: nil }
      parser = OptionParser.new do |o|
        o.banner = 'Uso: ruby bin/raven snapshot URL --output relatorio.json [--timeout 8]'
        o.on('--output FILE', 'Salvar evidências em JSON') { |v| options[:output] = v }
        o.on('--timeout N', Integer, 'Timeout em segundos (padrão 8)') { |v| options[:timeout] = v }
      end
      parser.parse!(args)
      raise Error, parser.banner unless args.size == 1 && options[:output]
      snapshot = inspect_url(args.first, timeout: options[:timeout])
      save_json(options[:output], snapshot)
      puts "[RAVEN] HTTP #{snapshot['status']} | #{snapshot['target']}"
      puts "[RAVEN] #{snapshot['observations'].size} observações | #{options[:output]}"
      snapshot['observations'].each { |item| puts "  [#{item['severity'].upcase}] #{item['code']}: #{item['message']}" }
      0
    when 'diff'
      diff_options = { output: nil }
      parser = OptionParser.new do |o|
        o.banner = 'Uso: ruby bin/raven diff baseline.json atual.json [--output drift.json]'
        o.on('--output FILE') { |v| diff_options[:output] = v }
      end
      parser.parse!(args)
      raise Error, parser.banner unless args.size == 2
      report = diff(read_snapshot(args[0]), read_snapshot(args[1]))
      save_json(diff_options[:output], report) if diff_options[:output]
      puts "[RAVEN] #{report['changes_count']} alteração(ões) de postura em #{report['target']}"
      report['changes'].each { |c| puts "  #{c['path']}: #{c['before'].inspect} -> #{c['after'].inspect}" }
      report['changes_count'].positive? ? 3 : 0
    else
      warn 'Uso: ruby bin/raven snapshot URL --output baseline.json | ruby bin/raven diff baseline.json atual.json'
      1
    end
  rescue Error, OptionParser::ParseError => e
    warn "[RAVEN] ERRO: #{e.message}"
    2
  end
end
