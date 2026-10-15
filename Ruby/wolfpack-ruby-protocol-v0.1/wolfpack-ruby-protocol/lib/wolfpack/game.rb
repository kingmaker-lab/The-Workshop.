# frozen_string_literal: true

require_relative 'lessons'
require_relative 'runner'
require_relative 'progress'

module Wolfpack
  class Game
    def initialize(input: $stdin, output: $stdout, progress: Progress.new, validator: Validator.new)
      @input, @out, @progress, @validator = input, output, progress, validator
      @color = @out.tty? && ENV['NO_COLOR'].nil?
    end

    def run
      banner
      if @progress.codename.nil? || @progress.codename.empty?
        @out.print 'Escolha seu codinome de lobo: '
        name = read_line
        return farewell if name.nil?

        @progress.codename = name.strip.empty? ? 'Lobo Sem Nome' : name
      end
      @out.puts "Bem-vindo à base, #{@progress.codename}."

      loop do
        @out.puts "\n#{paint('== CENTRAL WOLFPACK ==', 36)}"
        @out.puts '1) Continuar campanha Ruby'
        @out.puts '2) Ver mapa e progresso'
        @out.puts '3) Manual de comandos'
        @out.puts '4) Reiniciar campanha'
        @out.puts '0) Sair'
        @out.print '> '
        case read_line
        when '1' then campaign
        when '2' then map
        when '3' then manual
        when '4' then reset_campaign
        when '0', nil then break
        else @out.puts 'Comando não reconhecido.'
        end
      end
      farewell
    rescue Interrupt
      @out.puts "\nSessão encerrada. O progresso concluído continua salvo."
    end

    private

    def read_line
      @input.gets&.chomp
    end

    def banner
      @out.puts paint(<<~BANNER, 35)
               /\_/\\
              ( o.o )       WOLFPACK // RUBY PROTOCOL
               > ^ <        THE WORKSHOP — KINGMAKER
      BANNER
      @out.puts 'Aprenda Ruby enfrentando 12 missões. Seus códigos são executados no Ruby local.'
      @out.puts 'SEGURANÇA: não cole código desconhecido. Este jogo NÃO é uma sandbox isolada.'
    end

    def campaign
      lesson = Lessons.all.find { |mission| !@progress.done?(mission.id) }
      unless lesson
        @out.puts paint("\n👑 MISSÃO CONCLUÍDA. #{@progress.codename} dominou o protocolo Ruby!", 32)
        return
      end

      show_lesson(lesson)
      loop do
        @out.puts "\nDigite ENTER para escrever Ruby, :dica, :solucao, :exemplo ou :voltar."
        @out.print 'comando> '
        command = read_line
        case command
        when nil, ':voltar' then return
        when ':dica' then @out.puts "DICA: #{lesson.hint}"
        when ':solucao' then @out.puts "SOLUÇÃO COMENTADA PELO DESAFIO:\n#{lesson.solution}"
        when ':exemplo' then @out.puts "EXEMPLO DE AULA:\n#{lesson.example}"
        when ''
          source = collect_code
          return if source.nil?
          result = @validator.check(lesson, source)
          if result.success
            @out.puts paint("\n✅ #{result.feedback} +100 XP", 32)
            @progress.complete!(lesson.id)
            @out.puts "Progresso: #{@progress.completed.length}/12 | #{@progress.xp} XP"
            if lesson.id == 12
              @out.puts paint('👑 KINGMAKER — PROTOCOLO RUBY RESTAURADO. A MATILHA PREVALECEU.', 33)
            else
              @out.puts 'Nova missão desbloqueada. Volte à central ou continue.'
            end
            return
          end
          @out.puts paint("\n❌ Teste #{result.case_number || '-'}: #{result.feedback}", 31)
          @out.puts 'Tente novamente; use :dica se precisar. Nenhum XP foi perdido.'
        else @out.puts 'Comando inválido. Use ENTER para abrir o editor.'
        end
      end
    end

    def show_lesson(lesson)
      @out.puts "\n#{paint(lesson.act, 35)}"
      @out.puts "[#{lesson.id}/12] #{paint(lesson.title, 36)}"
      @out.puts "\n🐺 #{lesson.scene}"
      @out.puts "\nO QUE VOCÊ APRENDE: #{lesson.theory}"
      @out.puts "\nEXEMPLO:\n#{lesson.example}"
      @out.puts "\nDESAFIO: #{lesson.task}"
      @out.puts "Testes automáticos: #{lesson.cases.length}. A resposta deve usar os conceitos da missão."
    end

    def collect_code
      @out.puts "\n[EDITOR RUBY] Digite seu código. Uma linha contendo somente FIM testa o programa."
      @out.puts 'Para cancelar sem testar, digite CANCELAR como primeira linha.'
      lines = []
      loop do
        @out.print format('%02d | ', lines.length + 1)
        line = read_line
        return nil if line.nil? || (lines.empty? && line == 'CANCELAR')
        break if line == 'FIM'

        lines << line
        if lines.length >= 100
          @out.puts 'Limite de 100 linhas atingido: verificando sua solução.'
          break
        end
      end
      lines.join("\n") + "\n"
    end

    def map
      @out.puts "\nMAPA DA MATILHA — #{@progress.codename} | #{@progress.xp} XP"
      Lessons.all.each do |lesson|
        marker = @progress.done?(lesson.id) ? '✔ CONCLUÍDA' : '○ PENDENTE'
        @out.puts format('%02d %-12s %s', lesson.id, marker, lesson.title)
      end
      @out.puts "MISSÕES: #{@progress.completed.length}/12"
    end

    def manual
      @out.puts <<~HELP

        MANUAL RÁPIDO
        - Escolha 1 para ver a próxima aula, sua história e o desafio.
        - ENTER abre o editor de código Ruby do próprio jogo.
        - Digite as linhas de Ruby; escreva FIM sozinho numa linha para testar.
        - :dica revela uma pista sem encerrar o nível.
        - :exemplo repete o exemplo de aula.
        - :solucao mostra uma solução possível, para estudar e testar.
        - :voltar retorna ao menu principal.
        - Os testes usam o interpretador Ruby local e comparam a saída gerada.
        - Ao completar uma missão, ganhe 100 XP; o jogo salva automaticamente.
        - Código digitado é executado em sua máquina. Não é sandbox de segurança.
      HELP
    end

    def reset_campaign
      @out.print 'Apagar o progresso e começar do zero? Digite REINICIAR: '
      if read_line == 'REINICIAR'
        current_codename = @progress.codename
        @progress.reset!
        @progress.codename = current_codename
        @out.puts 'Campanha reiniciada. O mapa está limpo.'
      else
        @out.puts 'Reinício cancelado.'
      end
    end

    def farewell
      @out.puts "\nAté a próxima missão, lobo. A matilha não esquece. 🐺"
    end

    def paint(text, code)
      @color ? "\e[#{code}m#{text}\e[0m" : text
    end
  end
end
