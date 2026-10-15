#!/usr/bin/env ruby
# frozen_string_literal: true

require 'digest'
require 'ipaddr'
require 'json'
require 'net/http'
require 'openssl'
require 'optparse'
require 'resolv'
require 'time'
require 'uri'

module RavenHTTP
  VERSION = '0.1.0'

  class Error < StandardError; end
  class ScopeError < Error; end
  class LimitError < Error; end

  # Restrict network destinations unless the operator explicitly opts into
  # private/loopback networks for local authorized testing.
  class Scope
    EXCLUDED_RANGES = %w[
      0.0.0.0/8 10.0.0.0/8 100.64.0.0/10 127.0.0.0/8
      169.254.0.0/16 172.16.0.0/12 192.0.0.0/24
      192.0.2.0/24 192.168.0.0/16 198.18.0.0/15
      198.51.100.0/24 203.0.113.0/24 224.0.0.0/4 240.0.0.0/4
      ::/128 ::1/128 ::ffff:0:0/96 fc00::/7 fe80::/10 ff00::/8
      2001:db8::/32
    ].map { |cidr| IPAddr.new(cidr) }.freeze

    def initialize(allow_private: false)
      @allow_private = allow_private
    end

    def validate_url(value)
      uri = URI.parse(value)
      unless %w[http https].include?(uri.scheme) && uri.host && !uri.host.empty?
        raise ScopeError, 'Informe uma URL absoluta HTTP ou HTTPS válida.'
      end
      raise ScopeError, 'Credenciais na URL não são permitidas.' if uri.userinfo
      raise ScopeError, 'Fragmentos na URL não são aceitos.' if uri.fragment
      uri
    rescue URI::InvalidURIError => e
      raise ScopeError, "URL inválida: #{e.message}"
    end

    def resolve_allowed_ip(uri)
      addresses = Resolv.getaddresses(uri.host).uniq
      raise ScopeError, "Falha ao resolver o host: #{uri.host}" if addresses.empty?

      selected = addresses.find { |address| @allow_private || globally_routable?(address) }
      raise ScopeError, 'Destino privado, reservado ou local bloqueado. Use --allow-private somente com autorização.' unless selected
      selected
    rescue Resolv::ResolvError => e
      raise ScopeError, "Erro de DNS: #{e.message}"
    end

    def same_origin?(a, b)
      a.scheme.casecmp?(b.scheme) && a.host.casecmp?(b.host) && a.port == b.port
    end

    private

    def globally_routable?(address)
      ip = IPAddr.new(address)
      EXCLUDED_RANGES.none? { |range| range.include?(ip) }
    rescue IPAddr::InvalidAddressError
      false
    end
  end

  class Auditor
    DEFAULTS = { timeout: 6, max_redirects: 3, max_bytes: 262_144, allow_private: false }.freeze

    def initialize(url, **options)
      @options = DEFAULTS.merge(options)
      @scope = Scope.new(allow_private: @options.fetch(:allow_private))
      @original = @scope.validate_url(url)
      @findings = []
    end

    def run
      current = @original
      hops = []
      final_response = nil
      final_cert = nil
      final_body = +''
      final_url = nil

      0.upto(@options.fetch(:max_redirects)) do |index|
        raise ScopeError, 'Redirecionamento fora da origem permitida.' unless @scope.same_origin?(@original, current)
        ip = @scope.resolve_allowed_ip(current)
        response, body, certificate = fetch(current, ip)
        hops << { url: redact_url(current), status: response.code.to_i }

        location = response['location']
        if response.is_a?(Net::HTTPRedirection) && location && !location.empty?
          next_uri = @scope.validate_url(URI.join(current.to_s, location).to_s)
          unless @scope.same_origin?(@original, next_uri)
            finding('medium', 'redirect_out_of_scope', 'Redirecionamento externo bloqueado',
                    "HTTP #{response.code}; Location aponta para outra origem")
            final_response, final_cert, final_body, final_url = response, certificate, body, current
            break
          end
          if index == @options.fetch(:max_redirects)
            finding('low', 'redirect_limit', 'Limite de redirecionamentos atingido', "Máximo: #{index}")
            final_response, final_cert, final_body, final_url = response, certificate, body, current
            break
          end
          current = next_uri
          next
        end

        final_response, final_cert, final_body, final_url = response, certificate, body, current
        break
      end

      analyze(final_response, final_url, final_cert)
      {
        tool: 'RAVEN HTTP', version: VERSION, timestamp_utc: Time.now.utc.iso8601,
        authorized_use_only: true,
        target: redact_url(@original), final_url: redact_url(final_url),
        requests_made: hops.length, redirects: hops,
        response: {
          status: final_response.code.to_i,
          content_type: final_response['content-type'],
          body_size_bytes: final_body.bytesize,
          body_sha256: Digest::SHA256.hexdigest(final_body),
          security_headers: relevant_headers(final_response),
          cookies: cookie_metadata(final_response),
          tls: certificate_metadata(final_cert)
        },
        findings: @findings,
        summary: @findings.group_by { |item| item.fetch(:severity) }
                          .transform_values(&:size)
      }
    end

    private

    def fetch(uri, pinned_ip)
      http = Net::HTTP.new(uri.host, uri.port, nil)
      http.ipaddr = pinned_ip # DNS is checked and pinned for this TCP connection.
      http.use_ssl = uri.scheme == 'https'
      http.verify_mode = OpenSSL::SSL::VERIFY_PEER if http.use_ssl?
      http.open_timeout = @options.fetch(:timeout)
      http.read_timeout = @options.fetch(:timeout)
      http.write_timeout = @options.fetch(:timeout)

      path = uri.request_uri
      request = Net::HTTP::Get.new(path)
      request['User-Agent'] = "RAVEN-HTTP/#{VERSION} (authorized passive audit)"
      request['Accept'] = '*/*'
      body = +''
      response = nil
      certificate = nil

      http.start do |connection|
        certificate = connection.peer_cert if connection.use_ssl?
        connection.request(request) do |res|
          response = res
          res.read_body do |chunk|
            if body.bytesize + chunk.bytesize > @options.fetch(:max_bytes)
              raise LimitError, "Resposta excedeu #{@options.fetch(:max_bytes)} bytes."
            end
            body << chunk
          end
        end
      end
      [response, body, certificate]
    rescue OpenSSL::SSL::SSLError => e
      raise Error, "Falha na validação TLS: #{e.message}"
    rescue Timeout::Error, SocketError, SystemCallError, IOError => e
      raise Error, "Erro de conexão: #{e.class}: #{e.message}"
    end

    def analyze(response, uri, cert)
      return unless response

      headers = relevant_headers(response)
      html = (response['content-type'] || '').downcase.include?('text/html')
      csp = response['content-security-policy'].to_s

      if html && csp.empty?
        finding('medium', 'missing_csp', 'CSP ausente', 'Página HTML sem Content-Security-Policy; verificar exposição a injeção de conteúdo.')
      end
      if html && response['x-frame-options'].nil? && !csp.downcase.include?('frame-ancestors')
        finding('low', 'missing_frame_protection', 'Proteção de enquadramento ausente',
                'Sem X-Frame-Options ou diretiva CSP frame-ancestors.')
      end
      unless response['x-content-type-options'].to_s.downcase == 'nosniff'
        finding('low', 'missing_nosniff', 'X-Content-Type-Options não define nosniff',
                'Configuração de proteção de tipo MIME ausente ou diferente de nosniff.')
      end
      unless response['referrer-policy']
        finding('info', 'missing_referrer_policy', 'Referrer-Policy ausente',
                'Vale avaliar a política adequada à aplicação.')
      end
      if uri.scheme == 'https' && response['strict-transport-security'].nil?
        finding('low', 'missing_hsts', 'HSTS ausente', 'Resposta HTTPS sem Strict-Transport-Security.')
      end

      origin = response['access-control-allow-origin']
      credentials = response['access-control-allow-credentials']
      if origin == '*'
        finding('info', 'cors_wildcard', 'CORS permite qualquer origem',
                credentials.to_s.casecmp?('true') ? 'ACAO=* e ACAC=true: combinação incompatível com credenciais em navegadores.' : 'Verifique se o recurso foi projetado para acesso público.')
      elsif origin && !origin.empty?
        finding('info', 'cors_origin_declared', 'Origem CORS explicitada',
                'Política observada: Access-Control-Allow-Origin definido. Não comprova exploração.')
      end

      cookie_metadata(response).each do |cookie|
        name = cookie[:name]
        if uri.scheme == 'https' && !cookie[:secure]
          finding('medium', 'cookie_without_secure', "Cookie #{name} sem Secure", 'Atributo Secure ausente em resposta HTTPS.')
        end
        unless cookie[:http_only]
          finding('low', 'cookie_without_httponly', "Cookie #{name} sem HttpOnly", 'Pode ser intencional; confirme se é cookie de sessão.')
        end
        unless cookie[:same_site]
          finding('low', 'cookie_without_samesite', "Cookie #{name} sem SameSite", 'Confira a política cross-site necessária.')
        end
      end

      if cert && cert.not_after <= Time.now.utc + 30 * 86_400
        finding('medium', 'tls_certificate_expiring', 'Certificado TLS perto de expirar', cert.not_after.utc.iso8601)
      end
      headers # Header snapshots are included in evidence, not fully classified as vulnerabilities.
    end

    def cookie_metadata(response)
      (response.get_fields('set-cookie') || []).filter_map do |header|
        segments = header.split(';').map(&:strip)
        name = segments.first.to_s.split('=', 2).first.to_s.strip
        next if name.empty?
        attrs = segments.drop(1).map { |s| s.split('=', 2).first.to_s.downcase }
        samesite_segment = segments.drop(1).find { |s| s.downcase.start_with?('samesite=') }
        {
          name: name, secure: attrs.include?('secure'), http_only: attrs.include?('httponly'),
          same_site: samesite_segment&.split('=', 2)&.last
        }
      end
    end

    def relevant_headers(response)
      names = %w[
        content-security-policy strict-transport-security x-frame-options
        x-content-type-options referrer-policy permissions-policy
        access-control-allow-origin access-control-allow-credentials
        cache-control
      ]
      names.each_with_object({}) { |header, map| map[header] = response[header] if response[header] }
    end

    def certificate_metadata(cert)
      return nil unless cert
      {
        subject: cert.subject.to_s,
        issuer: cert.issuer.to_s,
        valid_from: cert.not_before.utc.iso8601,
        valid_until: cert.not_after.utc.iso8601
      }
    end

    def redact_url(uri)
      safe = uri.dup
      if safe.query
        parts = URI.decode_www_form(safe.query)
        safe.query = URI.encode_www_form(parts.map { |key, _value| [key, 'REDACTED'] })
      end
      safe.to_s
    rescue ArgumentError
      # Preserve only origin/path if malformed query cannot be parsed safely.
      "#{uri.scheme}://#{uri.host}:#{uri.port}#{uri.path}"
    end

    def finding(severity, id, title, evidence)
      @findings << { severity: severity, id: id, title: title, evidence: evidence,
                     interpretation: 'Sinal de configuração; não é prova isolada de vulnerabilidade.' }
    end
  end

  def self.cli(argv)
    options = Auditor::DEFAULTS.dup
    report_file = nil
    parser = OptionParser.new do |opts|
      opts.banner = 'Uso: ruby raven.rb URL [opções]'
      opts.on('--json ARQUIVO', 'Salvar evidências em JSON') { |value| report_file = value }
      opts.on('--max-redirects N', Integer, 'Máximo de redirecionamentos (0–10)') { |value| options[:max_redirects] = value }
      opts.on('--max-bytes N', Integer, 'Máximo de bytes por resposta (1024–2097152)') { |value| options[:max_bytes] = value }
      opts.on('--timeout SEG', Integer, 'Timeout por conexão/leitura (1–30)') { |value| options[:timeout] = value }
      opts.on('--allow-private', 'Permitir destino local/privado autorizado') { options[:allow_private] = true }
      opts.on('-h', '--help', 'Mostrar ajuda') { puts opts; return 0 }
    end

    parser.parse!(argv)
    raise Error, 'Informe uma única URL. Execute com --help para instruções.' unless argv.length == 1
    raise Error, 'max-redirects fora do intervalo 0–10' unless (0..10).cover?(options[:max_redirects])
    raise Error, 'max-bytes fora do intervalo 1024–2097152' unless (1024..2_097_152).cover?(options[:max_bytes])
    raise Error, 'timeout fora do intervalo 1–30' unless (1..30).cover?(options[:timeout])

    report = Auditor.new(argv.first, **options).run
    puts "RAVEN HTTP v#{VERSION} | HTTP #{report.dig(:response, :status)} | #{report[:requests_made]} requisição(ões)"
    report.fetch(:findings).each do |item|
      puts "[#{item[:severity].upcase.ljust(6)}] #{item[:title]} — #{item[:evidence]}"
    end
    puts "Total: #{report.fetch(:findings).length} observação(ões)."
    if report_file
      require 'fileutils'
      FileUtils.mkdir_p(File.dirname(report_file))
      File.write(report_file, JSON.pretty_generate(report) + "\n")
      puts "Relatório: #{report_file}"
    end
    0
  rescue OptionParser::ParseError, Error => e
    warn "Erro: #{e.message}"
    2
  end
end

exit(RavenHTTP.cli(ARGV)) if $PROGRAM_NAME == __FILE__
