# frozen_string_literal: true

require 'base64'
require 'digest'
require 'fileutils'
require 'json'
require 'shellwords'
require 'set'

module Vulpes77
  VERSION = '0.1.0'
  NETWORK = {
    '10.77.0.1' => { name: 'GATEWAY', ports: { 443 => 'edge-dashboard', 53 => 'dns-snapshot' } },
    '10.77.0.12' => { name: 'WEB-01', ports: { 80 => 'public-site', 8080 => 'telemetry-console' } },
    '10.77.0.23' => { name: 'LOG-01', ports: { 9200 => 'log-archive' } },
    '10.77.0.44' => { name: 'SEC-CTRL', ports: { 8443 => 'response-console' } }
  }.freeze

  FILES = {
    '10.77.0.1:443' => {
      'welcome.txt' => "[EDGE] Gateway de treinamento. Nenhuma conexão externa é realizada.\nAtivos: WEB-01, LOG-01, SEC-CTRL.\n"
    },
    '10.77.0.1:53' => {
      'zones.txt' => "web-01.lab 10.77.0.12\nlog-01.lab 10.77.0.23\nsec-ctrl.lab 10.77.0.44\n"
    },
    '10.77.0.12:80' => {
      'index.html' => "<h1>NEXUS LAB</h1>\n<!-- O servidor de telemetria responde em :8080 -->\n"
    },
    '10.77.0.12:8080' => {
      'readme.txt' => "WEB-01 / telemetria\nO identificador de uma transmissão suspeita está codificado em Base64.\nUse 'cat traffic.log' e 'decode b64 <valor>'.\n",
      'traffic.log' => "02:13:52 GET /health code=200\n02:14:07 POST /telemetry destination=203.0.113.7 beacon_id_b64=TklHSFRKQVI= code=202\n02:14:09 GET /health code=200\n",
      'notes.txt' => "203.0.113.0/24 é um bloco reservado para documentação.\nEsta telemetria, assim como os hosts, é completamente fictícia.\n"
    },
    '10.77.0.23:9200' => {
      'readme.txt' => "[IR] Alerta: WEB-01 apresentou egress suspeito às 02:14:07.\nCorrelacione o event_id de egress.log com auth.log.\nEnvie o nome da conta responsável, não o ID.\n",
      'auth.log' => "02:13:43 user=ana src=10.77.0.81 event_id=E-105 result=ok\n02:13:59 user=svc-bridge src=10.77.0.99 event_id=E-441 result=ok\n02:14:01 user=svc-backup src=10.77.0.71 event_id=E-883 result=ok\n",
      'egress.log' => "02:14:07 host=WEB-01 destination=203.0.113.7 event_id=E-441 verdict=alert\n02:17:22 host=GATEWAY destination=198.51.100.3 event_id=E-883 verdict=allow\n"
    },
    '10.77.0.44:8443' => {
      'runbook.txt' => "RUNBOOK DE RESPOSTA - NEXUS LAB\n1. Identifique o host impactado em incident.json.\n2. Isole apenas o host comprometido: contain <IP>.\n3. Registre o ticket: submit <ticket>.\nA quarentena é somente uma mudança no estado deste jogo.\n",
      'incident.json' => JSON.pretty_generate({ ticket: 'IR-2607', severity: 'high', host: '10.77.0.12', actor: 'svc-bridge', required_action: 'isolate_host' }),
      'dashboard.txt' => "SEGMENTO NEXUS\nWEB-01: incidente aberto\nLOG-01: preservado para análise\nGATEWAY: operação normal\n"
    }
  }.freeze

  MISSIONS = [
    {
      title: '01 / O ECO FANTASMA',
      lead: 'Uma transmissão inesperada saiu do servidor WEB-01.\nEncontre o identificador secreto do beacon sem sair da rede simulada.',
      target: 'Localizar e decodificar o beacon_id; enviar o codinome.',
      hint: 'scan 10.77.0.12 -> connect 10.77.0.12:8080 -> cat traffic.log -> decode b64 <token>',
      answer: 'NIGHTJAR',
      unlock: %w[10.77.0.1 10.77.0.12],
      outro: 'Beacon identificado! Agora precisamos atribuir a atividade a uma identidade.'
    },
    {
      title: '02 / SOMBRAS NOS LOGS',
      lead: 'A equipe SOC recuperou dois arquivos de eventos.\nCorrelacione a transmissão suspeita com a autenticação que a precedeu.',
      target: 'Encontrar a conta relacionada ao evento suspeito e enviar o nome da conta.',
      hint: 'scan 10.77.0.23 -> connect 10.77.0.23:9200 -> cat egress.log -> grep E-441 auth.log',
      answer: 'svc-bridge',
      unlock: %w[10.77.0.1 10.77.0.12 10.77.0.23],
      outro: 'A identidade foi correlacionada. Um último passo: contenção responsável.'
    },
    {
      title: '03 / SILÊNCIO OPERACIONAL',
      lead: 'O atacante ainda pode estar ativo no host comprometido.\nLeia o runbook e isole somente a máquina afetada.\nDepois registre o ticket de incidente.',
      target: 'Conter o host correto e submeter o ID do ticket.',
      hint: 'scan 10.77.0.44 -> connect 10.77.0.44:8443 -> cat incident.json -> contain 10.77.0.12 -> submit IR-2607',
      answer: 'IR-2607',
      unlock: %w[10.77.0.1 10.77.0.12 10.77.0.23 10.77.0.44],
      outro: 'INCIDENTE CONTIDO. A rede NEXUS está novamente sob controle.'
    }
  ].freeze

  Output = Struct.new(:text, :kind, keyword_init: true)

  class Game
    attr_reader :mission_index, :score, :save_path

    def initialize(save_path: File.join(Dir.home, '.vulpes77', 'save.json'), fresh: false, legacy_save_path: nil)
      @save_path = File.expand_path(save_path)
      reset_state
      return if fresh

      if File.file?(@save_path)
        load_state
      else
        default_save = File.join(Dir.home, '.vulpes77', 'save.json')
        previous_save = legacy_save_path || (save_path == default_save ? File.join(Dir.home, '.ghostwire', 'save.json') : nil)
        # Importa o progresso antigo uma vez, sem alterar nem apagar o arquivo original.
        persist if previous_save && File.file?(previous_save) && load_state(previous_save)
      end
    end

    def complete?
      @mission_index >= MISSIONS.length
    end

    def mission
      MISSIONS[@mission_index]
    end

    def intro
      if complete?
        "Operação NEXUS concluída. Pontuação: #{@score}/300. Digite 'status', 'novo' ou 'sair'."
      else
        "#{mission[:title]}\n#{mission[:lead].gsub('\\n', "\n")}\n\nOBJETIVO: #{mission[:target]}\nDigite 'help' para conhecer os comandos."
      end
    end

    def prompt
      context = @session ? "#{NETWORK[@session[:host]][:name]}:#{@session[:port]}" : 'nexus'
      "vulpes77@#{context}$ "
    end

    def perform(line)
      args = Shellwords.split(line.to_s.strip)
      return output('Digite help para ver os comandos.', :info) if args.empty?

      command = args.shift.downcase
      return restart if command == 'novo'
      return output('Fim de transmissão. O estado foi salvo.', :quit) if %w[sair exit quit].include?(command)
      return output('Comando indisponível após a conclusão. Use status, journal ou novo.', :info) if complete? && !%w[help ajuda status journal diario save salvar].include?(command)

      result = case command
               when 'help', 'ajuda' then help
               when 'map', 'mapa' then map
               when 'scan' then scan(args)
               when 'connect' then connect(args)
               when 'disconnect', 'dc' then disconnect
               when 'ls', 'dir' then list_files
               when 'cat' then cat(args)
               when 'grep' then grep(args)
               when 'decode' then decode(args)
               when 'hash' then hash_text(args)
               when 'contain' then contain(args)
               when 'submit' then submit(args)
               when 'hint', 'dica' then hint
               when 'status' then status
               when 'journal', 'diario' then journal
               when 'save', 'salvar' then output('Progresso registrado em disco.', :success)
               else output("Comando desconhecido: #{command}. Digite help.", :error)
               end
      persist
      result
    rescue ArgumentError => e
      output("Entrada inválida: #{e.message}", :error)
    end

    private

    def output(text, kind = :info)
      Output.new(text: text, kind: kind)
    end

    def reset_state
      @mission_index = 0
      @score = 0
      @penalty = 0
      @hint_used = false
      @contained = false
      @scanned = Set.new
      @session = nil
      @journal = []
    end

    def restart
      reset_state
      persist
      output("Nova operação iniciada.\n\n#{intro}", :success)
    end

    def help
      output(<<~HELP)
        COMANDOS DO TERMINAL (todos simulados)
          help                       Mostra esta referência
          map                        Mapa dos hosts do laboratório
          scan <IP>                  Descobre serviços de um host fictício
          connect <IP>:<porta>       Abre console do serviço
          disconnect                 Encerra sessão atual
          ls                         Lista arquivos do serviço
          cat <arquivo>              Lê um arquivo
          grep <texto> <arquivo>     Filtra linhas de um arquivo
          decode b64 <texto>         Decodifica Base64
          decode hex <texto>         Decodifica hexadecimal
          hash sha256 <texto>        Calcula hash local
          contain <IP>               Isola host virtual (na missão 03)
          submit <resposta>          Entrega a solução da missão
          hint                       Dica (-15 pontos na primeira vez)
          status                     Mostra andamento/pontuação
          journal                    Histórico recente de evidências
          save                       Salva progresso
          novo                       Reinicia toda a campanha
          sair                       Salva e encerra
        DICA: espaços em argumentos? Use aspas, como grep "event_id=E-441" auth.log.
      HELP
    end

    def map
      rows = NETWORK.map do |ip, node|
        lock = mission[:unlock].include?(ip) ? 'ONLINE' : 'BLOQUEADO'
        "#{ip.ljust(13)} #{node[:name].ljust(10)} [#{lock}]"
      end
      output("NEXUS / SEGMENTO DE TREINAMENTO\n#{rows.join("\n")}\nNenhum endereço corresponde a um alvo real.")
    end

    def scan(args)
      return output('Uso: scan <IP> (veja map)', :error) unless args.length == 1
      ip = args[0]
      node = NETWORK[ip]
      return output('Host não existe na topologia virtual.', :error) unless node
      return output('Acesso ao segmento ainda bloqueado nesta missão.', :error) unless mission[:unlock].include?(ip)

      @scanned.add(ip)
      ports = node[:ports].map { |port, label| "#{port}/tcp open #{label}" }
      add_journal("SCAN #{node[:name]} #{ip}")
      output("#{node[:name]} (#{ip})\n#{ports.join("\n")}", :success)
    end

    def connect(args)
      return output('Uso: connect <IP>:<porta>', :error) unless args.length == 1
      match = /\A(\d+\.\d+\.\d+\.\d+):(\d{1,5})\z/.match(args[0])
      return output('Destino inválido. Ex.: connect 10.77.0.12:8080', :error) unless match

      ip, port = match[1], match[2].to_i
      return output('Host bloqueado ou desconhecido.', :error) unless mission[:unlock].include?(ip)
      return output('Primeiro faça scan no host.', :error) unless @scanned.include?(ip)
      node = NETWORK[ip]
      return output('Porta não disponível nesse host virtual.', :error) unless node && node[:ports].key?(port)

      @session = { host: ip, port: port }
      add_journal("CONNECT #{node[:name]}:#{port}")
      output("Conectado a #{node[:name]} / #{node[:ports][port]}. Use ls ou cat.", :success)
    end

    def disconnect
      @session = nil
      output('Sessão encerrada.')
    end

    def service_files
      return nil unless @session
      FILES["#{@session[:host]}:#{@session[:port]}"]
    end

    def list_files
      files = service_files
      return output('Não há sessão ativa. Use connect.', :error) unless files
      output("ARQUIVOS DISPONÍVEIS\n#{files.keys.sort.join("\n")}")
    end

    def file_content(filename)
      files = service_files
      return nil unless files
      files[filename]
    end

    def cat(args)
      return output('Uso: cat <arquivo>', :error) unless args.length == 1
      return output('Conecte-se a um serviço antes.', :error) unless @session
      text = file_content(args[0])
      return output('Arquivo não encontrado no serviço atual.', :error) unless text

      add_journal("READ #{@session[:host]}:#{@session[:port]}/#{args[0]}")
      output(text)
    end

    def grep(args)
      return output('Uso: grep <texto> <arquivo>', :error) unless args.length == 2
      return output('Conecte-se a um serviço antes.', :error) unless @session
      content = file_content(args[1])
      return output('Arquivo não encontrado.', :error) unless content

      lines = content.lines.select { |line| line.downcase.include?(args[0].downcase) }
      add_journal("GREP '#{args[0][0, 40]}' #{args[1]}")
      output(lines.empty? ? 'Nenhuma correspondência.' : lines.join)
    end

    def decode(args)
      return output('Uso: decode b64|hex <texto>', :error) unless args.length >= 2
      kind, token = args.shift.downcase, args.join(' ')
      bytes = case kind
              when 'b64', 'base64' then Base64.strict_decode64(token)
              when 'hex' then decode_hex(token)
              else return output('Formato aceito: b64 ou hex.', :error)
              end
      return output('Entrada excede o limite de 4096 bytes.', :error) if bytes.bytesize > 4096

      as_text = bytes.dup.force_encoding('UTF-8')
      readable = as_text.valid_encoding? && as_text.each_codepoint.all? { |c| c == 10 || c == 13 || (c >= 32 && c != 127) }
      result = readable ? as_text : bytes.unpack1('H*')
      add_journal("DECODE #{kind}")
      output("Resultado: #{result}", :success)
    rescue ArgumentError
      output('Codificação inválida.', :error)
    end

    def decode_hex(value)
      sanitized = value.delete(' ')
      raise ArgumentError, 'hex inválido' unless sanitized.match?(/\A(?:[0-9a-fA-F]{2})*\z/)
      [sanitized].pack('H*')
    end

    def hash_text(args)
      return output('Uso: hash sha256 <texto>', :error) unless args.length >= 2 && args[0].downcase == 'sha256'
      text = args.drop(1).join(' ')
      return output('Texto longo demais (máximo 4096 bytes).', :error) if text.bytesize > 4096

      output("SHA-256: #{Digest::SHA256.hexdigest(text)}")
    end

    def contain(args)
      return output('Uso: contain <IP>', :error) unless args.length == 1
      return output('Comando disponível apenas na missão 03.', :error) unless @mission_index == 2
      return output('Acesse primeiro o console SEC-CTRL:8443.', :error) unless @session == { host: '10.77.0.44', port: 8443 }
      return output('Este host não está autorizado no runbook. Nenhuma ação executada.', :error) unless args[0] == '10.77.0.12'
      return output('WEB-01 já está isolado.', :info) if @contained

      @contained = true
      add_journal('CONTAIN WEB-01 (somente simulação)')
      output('WEB-01 ISOLADO. Segmentação aplicada ao cenário fictício. Agora registre o ticket.', :success)
    end

    def submit(args)
      return output('Uso: submit <resposta>', :error) if args.empty?
      answer = args.join(' ').strip
      if answer.casecmp?(mission[:answer])
        return output('Antes de registrar o ticket, isole WEB-01 pelo console SEC-CTRL.', :error) if @mission_index == 2 && !@contained

        achieved = [100 - @penalty, 0].max
        @score += achieved
        name = mission[:title]
        outro = mission[:outro]
        add_journal("COMPLETE #{name} +#{achieved}")
        @mission_index += 1
        @penalty = 0
        @hint_used = false
        @contained = false
        @scanned = Set.new
        @session = nil
        if complete?
          output("✓ #{outro}\nMISSÃO FINALIZADA: #{name}\n+#{achieved} pontos | TOTAL #{@score}/300\n\n#{ending}", :win)
        else
          output("✓ #{outro}\n+#{achieved} pontos | TOTAL #{@score}/300\n\n#{intro}", :success)
        end
      else
        @penalty = [@penalty + 5, 100].min
        add_journal('SUBMIT incorreto (-5 pts)')
        output('Resposta não confere com as evidências. -5 pontos nesta missão.', :error)
      end
    end

    def hint
      unless @hint_used
        @penalty = [@penalty + 15, 100].min
        @hint_used = true
      end
      output("DICA: #{mission[:hint]}\n(Penalidade total nesta missão: -#{@penalty})")
    end

    def status
      if complete?
        output("CAMPANHA CONCLUÍDA\nPontuação: #{@score}/300 | Rank: #{rank}\nUse novo para jogar novamente.", :success)
      else
        output("#{mission[:title]}\nOBJETIVO: #{mission[:target]}\nPontos acumulados: #{@score}\nPontos possíveis nesta missão: #{[100 - @penalty, 0].max}\nHost em sessão: #{@session ? @session[:host] : 'nenhum'}\nIsolamento WEB-01: #{@contained ? 'sim' : 'não'}")
      end
    end

    def journal
      entries = @journal.last(15)
      output(entries.empty? ? 'Diário ainda vazio.' : "DIÁRIO DE OPERAÇÕES\n#{entries.map.with_index(1) { |e, i| "#{i.to_s.rjust(2)}. #{e}" }.join("\n")}")
    end

    def ending
      <<~TEXT
        ╔══════════════════════════════════════════════════╗
        ║           OPERAÇÃO NEXUS: CONCLUÍDA             ║
        ╚══════════════════════════════════════════════════╝
        PONTUAÇÃO: #{@score}/300 | PATENTE: #{rank}
        A ameaça foi descoberta, atribuída e contida.
        O melhor ataque? Às vezes, é uma boa investigação.
        Digite status para conferir ou novo para recomeçar.
      TEXT
    end

    def rank
      case @score
      when 270..300 then 'VULPES OPERATOR'
      when 210..269 then 'SENIOR ANALYST'
      when 150..209 then 'THREAT HUNTER'
      else 'SOC RECRUIT'
      end
    end

    def add_journal(event)
      @journal << "M#{@mission_index + 1}: #{event}"
      @journal = @journal.last(40)
    end

    def persist
      state = {
        version: VERSION, mission_index: @mission_index, score: @score,
        penalty: @penalty, hint_used: @hint_used, contained: @contained,
        scanned: @scanned.to_a, session: @session, journal: @journal
      }
      FileUtils.mkdir_p(File.dirname(@save_path))
      tmp = "#{@save_path}.tmp-#{Process.pid}"
      File.write(tmp, JSON.pretty_generate(state), mode: 'w', perm: 0o600)
      File.rename(tmp, @save_path)
    rescue SystemCallError => e
      warn "[Vulpes77] Não foi possível salvar: #{e.message}"
    end

    def load_state(source = @save_path)
      return false unless File.file?(source)
      data = JSON.parse(File.read(source))
      raise ArgumentError, 'save inválido' unless data.is_a?(Hash) && data['version'] == VERSION
      idx = Integer(data.fetch('mission_index'))
      raise ArgumentError, 'missão inválida' unless idx.between?(0, MISSIONS.length)
      @mission_index = idx
      @score = Integer(data.fetch('score', 0)).clamp(0, 300)
      @penalty = Integer(data.fetch('penalty', 0)).clamp(0, 100)
      @hint_used = data['hint_used'] == true
      @contained = data['contained'] == true && idx == 2
      unlocked = idx < MISSIONS.length ? MISSIONS[idx][:unlock] : []
      @scanned = Set.new(Array(data['scanned']) & unlocked)
      session = data['session']
      if session.is_a?(Hash) && @scanned.include?(session['host'])
        ip, port = session['host'], Integer(session['port']) rescue nil
        @session = { host: ip, port: port } if NETWORK[ip]&.dig(:ports)&.key?(port)
      end
      @journal = Array(data['journal']).select { |entry| entry.is_a?(String) }.last(40)
      true
    rescue JSON::ParserError, ArgumentError, TypeError, Errno::ENOENT => e
      warn "[Vulpes77] Save corrompido ou incompatível (#{e.message}); iniciando do zero."
      reset_state
      false
    end
  end
end
