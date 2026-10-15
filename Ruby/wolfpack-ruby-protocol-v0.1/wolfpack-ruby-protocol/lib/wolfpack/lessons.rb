# frozen_string_literal: true

module Wolfpack
  Lesson = Struct.new(
    :id, :act, :title, :scene, :theory, :example, :task,
    :hint, :solution, :requirements, :cases, keyword_init: true
  )

  module Lessons
    module_function

    def all
      @all ||= [
        Lesson.new(
          id: 1, act: 'ATO I — O DESPERTAR', title: 'O primeiro uivo | puts',
          scene: 'O terminal de Kingmaker está apagado. Uma mensagem precisa acender a tela.',
          theory: 'Ruby executa instruções de cima para baixo. puts exibe texto no terminal e termina com uma quebra de linha. Strings ficam entre aspas.',
          example: 'puts "A matilha está online"',
          task: 'Mostre exatamente: A matilha despertou!',
          hint: 'Use puts seguido de uma String entre aspas.',
          solution: 'puts "A matilha despertou!"',
          requirements: [[/\bputs\b/, 'Use puts para escrever no terminal.']],
          cases: [['', "A matilha despertou!\n"]]
        ),
        Lesson.new(
          id: 2, act: 'ATO I — O DESPERTAR', title: 'Identidade | variáveis e interpolação',
          scene: 'O sistema exige o codinome de quem lidera a incursão.',
          theory: 'Uma variável guarda um valor: codinome = "Kingmaker". Em uma String com aspas duplas, #{...} insere o resultado de uma expressão. A variável não precisa de tipo declarado.',
          example: "nome = \"Raven\"\nputs \"Lobo: #{'#{nome}'}\"",
          task: 'Crie a variável codinome com o valor "Kingmaker" e exiba: Lobo: Kingmaker. Use interpolação.',
          hint: 'Duas linhas: atribua codinome; depois use puts "Lobo: #{codinome}".',
          solution: "codinome = \"Kingmaker\"\nputs \"Lobo: #{'#{codinome}'}\"",
          requirements: [[/\bcodinome\b/, 'Crie/use a variável codinome.'], [/\#\{/, 'Use interpolação #{...}.']],
          cases: [['', "Lobo: Kingmaker\n"]]
        ),
        Lesson.new(
          id: 3, act: 'ATO I — O DESPERTAR', title: 'Energia | números e operações',
          scene: 'ARES precisa calcular a energia restante do gerador.',
          theory: 'Inteiros (Integer) permitem operações como +, -, * e /. O operador = atribui; puts pode imprimir um número diretamente.',
          example: "energia = 10\ncusto = 3\nputs energia - custo  # 7",
          task: 'Defina energia = 20 e custo = 7. Exiba a energia restante (13) realizando a subtração.',
          hint: 'Defina duas variáveis e use puts energia - custo.',
          solution: "energia = 20\ncusto = 7\nputs energia - custo",
          requirements: [[/\benergia\b/, 'Use a variável energia.'], [/\bcusto\b/, 'Use a variável custo.'], [/-/, 'Faça a operação de subtração.']],
          cases: [['', "13\n"]]
        ),
        Lesson.new(
          id: 4, act: 'ATO I — O DESPERTAR', title: 'Portaria | entrada de dados',
          scene: 'ARGUS recebe o próximo integrante. O terminal deve responder a qualquer nome.',
          theory: 'gets lê uma linha de STDIN. chomp remove a quebra de linha; uma String pode ser interpolada para compor uma resposta. Cada teste envia um nome diferente.',
          example: "nome = gets.chomp\nputs \"Olá, #{'#{nome}'}!\"",
          task: 'Leia um nome e imprima: Bem-vindo, NOME! (substituindo NOME pelo valor recebido).',
          hint: 'nome = gets.chomp; depois puts com interpolação.',
          solution: "nome = gets.chomp\nputs \"Bem-vindo, #{'#{nome}'}!\"",
          requirements: [[/\bgets\b/, 'Leia a entrada com gets.'], [/\.chomp\b/, 'Remova a quebra de linha com chomp.']],
          cases: [["Argus\n", "Bem-vindo, Argus!\n"], ["Raven\n", "Bem-vindo, Raven!\n"]]
        ),
        Lesson.new(
          id: 5, act: 'ATO II — A TRAVESSIA', title: 'O portão | if e else',
          scene: 'O portão só abre se a energia for de pelo menos 10 unidades.',
          theory: 'if executa um bloco quando a condição é verdadeira. else cobre o caso contrário; end fecha o bloco. gets.to_i transforma a entrada em número inteiro. >= significa maior ou igual.',
          example: "vida = gets.to_i\nif vida >= 5\n  puts \"SEGUIR\"\nelse\n  puts \"PARAR\"\nend",
          task: 'Leia energia. Se for >= 10, imprima PORTAO ABERTO; senão, RECUAR.',
          hint: 'energia = gets.to_i; if energia >= 10 ... else ... end.',
          solution: "energia = gets.to_i\nif energia >= 10\n  puts \"PORTAO ABERTO\"\nelse\n  puts \"RECUAR\"\nend",
          requirements: [[/\bif\b/, 'Use if para verificar a condição.'], [/\belse\b/, 'Inclua o caso contrário com else.'], [/\bgets\b/, 'Leia a energia informada.']],
          cases: [["9\n", "RECUAR\n"], ["10\n", "PORTAO ABERTO\n"], ["20\n", "PORTAO ABERTO\n"]]
        ),
        Lesson.new(
          id: 6, act: 'ATO II — A TRAVESSIA', title: 'Marcha | repetição com times',
          scene: 'Três passos coordenados abrem caminho até a torre.',
          theory: '3.times executa um bloco três vezes. do |indice| recebe o contador, começando em zero. end encerra o bloco. A interpolação pode mostrar cada passo.',
          example: "2.times do |i|\n  puts \"Passo #{'#{i + 1}'}\"\nend",
          task: 'Use 3.times para imprimir três linhas: Passo 1, Passo 2 e Passo 3.',
          hint: '3.times do |i|; puts "Passo #{i + 1}"; end.',
          solution: "3.times do |i|\n  puts \"Passo #{'#{i + 1}'}\"\nend",
          requirements: [[/\.times\b/, 'Repita usando .times.'], [/\bdo\b/, 'Abra o bloco com do.']],
          cases: [['', "Passo 1\nPasso 2\nPasso 3\n"]]
        ),
        Lesson.new(
          id: 7, act: 'ATO II — A TRAVESSIA', title: 'Esquadrão | arrays',
          scene: 'A unidade ARGUS está na segunda posição da formação.',
          theory: 'Array é uma lista ordenada: ["ARES", "ARGUS", "RAVEN"]. O índice começa em 0; logo [1] acessa o segundo elemento.',
          example: "equipe = [\"Lobo\", \"Raposa\"]\nputs equipe[0]  # Lobo",
          task: 'Crie a lista ["ARES", "ARGUS", "RAVEN"] e imprima ARGUS acessando a posição [1].',
          hint: 'lobos = ["ARES", "ARGUS", "RAVEN"]; puts lobos[1].',
          solution: "lobos = [\"ARES\", \"ARGUS\", \"RAVEN\"]\nputs lobos[1]",
          requirements: [[/\[[\s\S]*?\]/, 'Crie/use um Array.'], [/\[1\]/, 'Use o índice [1].']],
          cases: [['', "ARGUS\n"]]
        ),
        Lesson.new(
          id: 8, act: 'ATO II — A TRAVESSIA', title: 'Telemetria | hashes e símbolos',
          scene: 'CERBERUS registrou um pacote com nome e estado da unidade.',
          theory: 'Hash associa chaves a valores. Em { nome: "ARGUS" }, nome: é uma chave do tipo Symbol. Para buscar seu valor, usamos hash[:nome].',
          example: "sensor = { nome: \"RAVEN\", status: \"OK\" }\nputs sensor[:nome]  # RAVEN",
          task: 'Crie o Hash sensor = { nome: "ARGUS", status: "ATIVO" } e imprima o valor de :status.',
          hint: 'puts sensor[:status] acessa o valor do Hash.',
          solution: "sensor = { nome: \"ARGUS\", status: \"ATIVO\" }\nputs sensor[:status]",
          requirements: [[/\bstatus\s*:/, 'Crie a chave status:.'], [/\[:status\]/, 'Acesse o Hash pela chave :status.']],
          cases: [['', "ATIVO\n"]]
        ),
        Lesson.new(
          id: 9, act: 'ATO III — O CÓDIGO DA MATILHA', title: 'Patrulha | each e blocos',
          scene: 'O sistema precisa conferir cada unidade sem repetir código.',
          theory: '.each percorre os elementos de uma coleção. O bloco do |lobo| ... end recebe um elemento de cada vez. A variável lobo existe dentro do bloco.',
          example: "[\"A\", \"B\"].each do |item|\n  puts \"ID: #{'#{item}'}\"\nend",
          task: 'Percorra ["ARES", "ARGUS", "RAVEN"] com .each e imprima OK: ARES, OK: ARGUS, OK: RAVEN (uma por linha).',
          hint: 'lobos.each do |lobo|; puts "OK: #{lobo}"; end.',
          solution: "lobos = [\"ARES\", \"ARGUS\", \"RAVEN\"]\nlobos.each do |lobo|\n  puts \"OK: #{'#{lobo}'}\"\nend",
          requirements: [[/\.each\b/, 'Use .each para percorrer a lista.'], [/\bdo\b/, 'Use um bloco do ... end.']],
          cases: [['', "OK: ARES\nOK: ARGUS\nOK: RAVEN\n"]]
        ),
        Lesson.new(
          id: 10, act: 'ATO III — O CÓDIGO DA MATILHA', title: 'Selo | métodos',
          scene: 'Kingmaker exige uma rotina reutilizável para autenticar os codinomes.',
          theory: 'def nome(parametro) define um método. A última expressão é retornada automaticamente. .upcase cria uma versão da String em maiúsculas. end encerra o método.',
          example: "def grito(nome)\n  \"AUUU, #{'#{nome.upcase}'}\"\nend\nputs grito(\"raven\")",
          task: 'Crie def selo(nome) que retorna "Selo: NOME_EM_MAIÚSCULAS". Leia nome com gets.chomp e imprima o retorno do método.',
          hint: 'def selo(nome); "Selo: #{nome.upcase}"; end. Depois: puts selo(gets.chomp).',
          solution: "def selo(nome)\n  \"Selo: #{'#{nome.upcase}'}\"\nend\nputs selo(gets.chomp)",
          requirements: [[/\bdef\s+selo\b/, 'Declare o método selo com def.'], [/\.upcase\b/, 'Use upcase para converter o nome.'], [/\bgets\b/, 'Leia o nome enviado.']],
          cases: [["raven\n", "Selo: RAVEN\n"], ["Kingmaker\n", "Selo: KINGMAKER\n"]]
        ),
        Lesson.new(
          id: 11, act: 'ATO III — O CÓDIGO DA MATILHA', title: 'O lobo | classes e objetos',
          scene: 'A matilha ganha uma representação própria no sistema.',
          theory: 'class define um modelo de objeto. initialize é chamado ao criar um objeto com .new. @nome é uma variável de instância, acessível pelos métodos do objeto.',
          example: "class Lobo\n  def initialize(nome)\n    @nome = nome\n  end\n  def chamar\n    \"Oi, #{'#{@nome}'}\"\n  end\nend\nputs Lobo.new(\"ARES\").chamar",
          task: 'Crie a classe Lobo: initialize(nome) armazena @nome; apresentar retorna "Eu sou NOME". Leia nome e imprima Lobo.new(nome).apresentar.',
          hint: 'class Lobo; def initialize(nome); @nome = nome; end; def apresentar; "Eu sou #{@nome}"; end; end.',
          solution: "class Lobo\n  def initialize(nome)\n    @nome = nome\n  end\n\n  def apresentar\n    \"Eu sou #{'#{@nome}'}\"\n  end\nend\n\nnome = gets.chomp\nputs Lobo.new(nome).apresentar",
          requirements: [[/\bclass\s+Lobo\b/, 'Declare class Lobo.'], [/\bdef\s+initialize\b/, 'Use initialize no construtor.'], [/@nome\b/, 'Armazene o estado em @nome.'], [/\.new\b/, 'Instancie o objeto com .new.']],
          cases: [["Raven\n", "Eu sou Raven\n"], ["Argus\n", "Eu sou Argus\n"]]
        ),
        Lesson.new(
          id: 12, act: 'ATO FINAL — KINGMAKER', title: 'Protocolo WolfPack | missão integrada',
          scene: 'A torre caiu. Para reconstruir o canal, una entrada, métodos, condição e coleções.',
          theory: 'Um programa Ruby pode combinar os conceitos aprendidos. Aqui você lê duas entradas, classifica um valor com if, monta uma lista e imprime um relatório com .join.',
          example: "modulos = [\"ARES\", \"ARGUS\"]\nputs modulos.join(\", \")  # ARES, ARGUS",
          task: 'Leia duas linhas: codinome e energia. Defina um método avaliar(energia) usando if/else: >=10 retorna PRONTO, caso contrário RECARREGAR. Crie um Array ["ARES", "ARGUS", "RAVEN"] e imprima três linhas: LOBO: NOME | UNIDADES: ARES, ARGUS, RAVEN | STATUS: RESULTADO (cada | representa uma quebra de linha).',
          hint: 'Use gets.chomp para nome, gets.to_i para energia; modulos.join(", "); e puts "STATUS: #{avaliar(energia)}".',
          solution: "def avaliar(energia)\n  if energia >= 10\n    \"PRONTO\"\n  else\n    \"RECARREGAR\"\n  end\nend\n\nnome = gets.chomp\nenergia = gets.to_i\nmodulos = [\"ARES\", \"ARGUS\", \"RAVEN\"]\nputs \"LOBO: #{'#{nome}'}\"\nputs \"UNIDADES: #{'#{modulos.join(", ")}'}\"\nputs \"STATUS: #{'#{avaliar(energia)}'}\"",
          requirements: [[/\bdef\s+avaliar\b/, 'Defina o método avaliar.'], [/\bif\b/, 'Use if para checar energia.'], [/\belse\b/, 'Use else para o outro caso.'], [/\.join\b/, 'Use join para formatar a lista.'], [/\bgets\b/, 'Leia os dados de entrada.']],
          cases: [["Raven\n15\n", "LOBO: Raven\nUNIDADES: ARES, ARGUS, RAVEN\nSTATUS: PRONTO\n"], ["Wolf\n5\n", "LOBO: Wolf\nUNIDADES: ARES, ARGUS, RAVEN\nSTATUS: RECARREGAR\n"], ["Kingmaker\n10\n", "LOBO: Kingmaker\nUNIDADES: ARES, ARGUS, RAVEN\nSTATUS: PRONTO\n"]]
        )
      ].freeze
    end
  end
end
