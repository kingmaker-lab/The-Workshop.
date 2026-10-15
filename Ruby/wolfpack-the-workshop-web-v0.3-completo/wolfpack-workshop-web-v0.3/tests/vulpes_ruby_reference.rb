# frozen_string_literal: true
# Executa sequências no motor Ruby original para validar paridade da adaptação web.
require 'json'
require 'tmpdir'
require_relative '../source/vulpes77/lib/vulpes77'
cmds = JSON.parse(STDIN.read)
Dir.mktmpdir('vulpes77-parity-') do |dir|
  game = Vulpes77::Game.new(save_path: File.join(dir, 'save.json'), fresh: true)
  result = cmds.map do |cmd|
    output = game.perform(cmd)
    { cmd: cmd, text: output.text, kind: output.kind.to_s, score: game.score, mission_index: game.mission_index }
  end
  STDOUT.write(JSON.generate(result))
end
