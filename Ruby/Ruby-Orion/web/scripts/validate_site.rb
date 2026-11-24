#!/usr/bin/env ruby
# frozen_string_literal: true
require "json"
require "ripper"
require "open3"
require "rbconfig"
require "minitest/autorun"

class OrionStudioTest < Minitest::Test
  ROOT = File.expand_path("..", __dir__)
  EXPECTED_IDS = %w[001 002 003].freeze

  def test_registry_is_versioned_and_unique
    registry = JSON.parse(File.read(File.join(ROOT, "data/labs.json")))
    assert_equal 1, registry.fetch("schema_version")
    labs = registry.fetch("labs")
    assert_equal EXPECTED_IDS, labs.map { |lab| lab.fetch("id") }
    assert_equal labs.length, labs.map { |lab| lab.fetch("slug") }.uniq.length
  end

  def test_each_laboratory_is_real_ruby_and_matches_expected_output
    JSON.parse(File.read(File.join(ROOT, "data/labs.json"))).fetch("labs").each do |lab|
      code = lab.fetch("code")
      assert Ripper.sexp(code), "Ruby syntax invalid in #{lab.fetch("id")}"
      stdout, stderr, status = Open3.capture3(RbConfig.ruby, "-e", code)
      assert status.success?, "Lab #{lab.fetch("id")} failed: #{stderr}"
      assert_equal lab.fetch("expected"), stdout, "Lab #{lab.fetch("id")} output mismatch"
    end
  end

  def test_html_has_every_interactive_environment
    html = File.read(File.join(ROOT, "index.html"))
    %w[panel-playground panel-labs panel-inspector source stdout ruby-runtime].each do |key|
      # Last key is a deliberate check for actual supported runtime text.
      assert html.include?(key == "ruby-runtime" ? "runtime-selftest" : key), "Missing #{key}"
    end
    assert_includes html, '/assets/favicon.svg'
    refute_match(/<script[^>]+src="https:/, html)
  end

  def test_runtime_is_in_web_worker_not_backend
    worker = File.read(File.join(ROOT, "assets/ruby-worker.js"))
    app = File.read(File.join(ROOT, "assets/studio.js"))
    assert_includes worker, "DefaultRubyVM"
    assert_includes worker, "WebAssembly.compile"
    assert_includes app, 'new Worker("/assets/ruby-worker.js"'
    assert_includes app, "worker.terminate()"
    refute_includes app, "innerHTML"
    refute_includes app, "eval("
  end

  def test_static_worker_builder_includes_csp_and_strict_methods
    script = File.read(File.join(ROOT, "scripts/build-worker.rb"))
    assert_includes script, "wasm-unsafe-eval"
    assert_includes script, "frame-ancestors 'none'"
    assert_includes script, '"HEAD"'
    assert_includes script, '"GET"'
  end
end
