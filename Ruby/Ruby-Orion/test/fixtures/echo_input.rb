# frozen_string_literal: true
require 'json'
input = $stdin.read
puts JSON.generate({ length: input.bytesize, rubyopt: ENV['RUBYOPT'], env_test: ENV['ORION_SECRET_TEST'] })
