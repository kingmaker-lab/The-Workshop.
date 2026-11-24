# frozen_string_literal: true
require_relative "lib/orion/version"
Gem::Specification.new do |spec|
  spec.name = "ruby-orion"
  spec.version = Orion::VERSION
  spec.summary = "Engineering toolkit and laboratories for Ruby"
  spec.description = "The Workshop Ruby Orion initiative: inspect, hash, explore and learn Ruby."
  spec.authors = ["The Workshop"]
  spec.license = "MIT"
  spec.homepage = "https://github.com/kingmaker-lab/The-Workshop./tree/main/Ruby/Ruby-Orion"
  spec.required_ruby_version = ">= 3.1"
  spec.files = Dir["lib/**/*.rb", "README.md", "LICENSE", "docs/**/*", "labs/**/*"]
  spec.bindir = "bin"
  spec.executables = ["orion"]
  spec.require_paths = ["lib"]
end
