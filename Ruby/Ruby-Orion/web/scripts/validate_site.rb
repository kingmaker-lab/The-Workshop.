#!/usr/bin/env ruby
# frozen_string_literal: true

# Deterministic contract tests for Orion Studio and the intermediate challenge track.
require "json"
require "ripper"
require "open3"
require "rbconfig"
require "timeout"
require "minitest/autorun"

class OrionStudioTest < Minitest::Test
  ROOT = File.expand_path("..", __dir__)
  EXPECTED_IDS = %w[001 002 003 004 005 006 007 008].freeze

  def labs
    @labs ||= JSON.parse(File.read(File.join(ROOT, "data/labs.json"))).fetch("labs")
  end

  def test_registry_is_versioned_unique_and_bounded
    registry = JSON.parse(File.read(File.join(ROOT, "data/labs.json")))
    assert_equal 2, registry.fetch("schema_version")
    assert_equal "0.3.0", registry.fetch("studio_version")
    assert_equal EXPECTED_IDS, labs.map { |lab| lab.fetch("id") }
    assert_equal labs.length, labs.map { |lab| lab.fetch("slug") }.uniq.length

    labs.each do |lab|
      assert_match(/\A[0-9]{3}\z/, lab.fetch("id"))
      %w[title level pillar summary code expected hint].each do |field|
        assert_kind_of String, lab.fetch(field), "Missing #{field} on #{lab.fetch('id')}"
      end
      assert_operator lab.fetch("code").length, :<=, 8000
      if lab.key?("tests")
        tests = lab.fetch("tests")
        assert_operator tests.size, :>=, 3
        assert_operator tests.size, :<=, 5
        tests.each do |test|
          %w[name input expected].each { |k| assert_kind_of String, test.fetch(k) }
          assert_operator test.fetch("input").length, :<=, 4000
          assert_operator test.fetch("expected").length, :<=, 2000
        end
      end
    end
  end

  def execute_ruby(code_path: nil, code: nil, input: "")
    arguments = [RbConfig.ruby]
    arguments.concat(code_path ? [code_path] : ["-e", code])
    Timeout.timeout(5) { Open3.capture3(*arguments, stdin_data: input) }
  end

  def test_labs_have_valid_ruby_reference_solutions
    labs.each do |lab|
      id = lab.fetch("id")
      starter = lab.fetch("code")
      assert Ripper.sexp(starter), "Ruby syntax invalid in EXP-#{id}"
      if lab.key?("tests")
        path = File.join(ROOT, "test/reference/#{id}.rb")
        assert File.file?(path), "Missing reference #{path}"
        assert Ripper.sexp(File.read(path)), "Reference syntax invalid in EXP-#{id}"
        lab.fetch("tests").each do |test|
          stdout, stderr, status = execute_ruby(code_path: path, input: test.fetch("input"))
          assert status.success?, "EXP-#{id} / #{test.fetch('name')}: #{stderr}"
          assert_equal test.fetch("expected"), stdout, "EXP-#{id} / #{test.fetch('name')}"
        end
      else
        stdout, stderr, status = execute_ruby(code: starter)
        assert status.success?, "EXP-#{id} failed: #{stderr}"
        assert_equal lab.fetch("expected"), stdout, "EXP-#{id} output mismatch"
      end
    end
  end

  def test_html_exposes_all_four_interactive_environments
    html = File.read(File.join(ROOT, "index.html"))
    %w[panel-playground panel-labs panel-inspector panel-bench source stdout
       runtime-selftest bench-selftest bench-run save-draft].each do |id|
      assert_includes html, %Q(id="#{id}"), "Missing #{id}"
    end
    assert_includes html, "/assets/favicon.svg"
    assert_includes html, "/assets/bench.js"
    refute_match(/<script[^>]+src="https:/, html)
  end

  def test_runtime_is_browser_only_and_workloads_are_bounded
    worker = File.read(File.join(ROOT, "assets/ruby-worker.js"))
    app = File.read(File.join(ROOT, "assets/studio.js"))
    bench = File.read(File.join(ROOT, "assets/bench.js"))
    assert_includes worker, "DefaultRubyVM"
    assert_includes worker, "WebAssembly.compile"
    assert_includes worker, 'type: "suite-case"'
    assert_includes worker, "cases.length > 6"
    assert_includes app, 'new Worker("/assets/ruby-worker.js"'
    assert_includes bench, 'new Worker("/assets/ruby-worker.js"'
    assert_includes app, "worker.terminate()"
    assert_includes bench, "worker.terminate()"
    assert_includes bench, "localStorage"
    assert_includes bench, "URL.createObjectURL"
    [app, bench].each do |script|
      refute_includes script, "innerHTML"
      refute_includes script, "eval("
    end
  end

  def test_builder_has_assets_security_headers_and_method_guards
    builder = File.read(File.join(ROOT, "scripts/build-worker.rb"))
    assert_includes builder, "/assets/bench.js"
    assert_includes builder, "wasm-unsafe-eval"
    assert_includes builder, "frame-ancestors 'none'"
    assert_includes builder, '"HEAD"'
    assert_includes builder, '"GET"'
    refute_includes builder, "unsafe-inline"
  end
end
