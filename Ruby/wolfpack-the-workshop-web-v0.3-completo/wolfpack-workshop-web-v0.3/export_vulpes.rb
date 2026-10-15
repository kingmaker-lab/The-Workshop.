# frozen_string_literal: true
# Gera dados de referência do jogo web diretamente a partir do motor Ruby oficial.
require 'json'
require_relative './source/vulpes77/lib/vulpes77'
root = File.expand_path(__dir__)
source = {
  version: Vulpes77::VERSION,
  network: Vulpes77::NETWORK,
  port_order: Vulpes77::NETWORK.transform_values { |host| host[:ports].keys },
  files: Vulpes77::FILES,
  missions: Vulpes77::MISSIONS
}
json = JSON.pretty_generate(source)
File.write(File.join(root, 'data', 'vulpes77.json'), json + "\n")
File.write(File.join(root, 'js', 'vulpes-data.js'), "// Gerado de source/vulpes77/lib/vulpes77.rb por export_vulpes.rb\nexport const DATA = #{json};\n")
puts 'VULPES-77: dados exportados do Ruby original.'
