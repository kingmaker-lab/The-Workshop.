# frozen_string_literal: true
require "minitest/autorun"
require "stringio"
require "json"
require "tempfile"
require_relative "../lib/orion"

class OrionCliTest < Minitest::Test
  def execute(*args)
    out, err = StringIO.new, StringIO.new
    status = Orion::CLI.new(out: out, err: err).run(args)
    [status, out.string, err.string]
  end

  def test_help
    status, out, = execute("help")
    assert_equal 0, status
    assert_includes out, "RUBY ORION"
  end

  def test_version
    status, out, = execute("--version")
    assert_equal 0, status
    assert_equal "Ruby Orion 0.2.0\n", out
  end

  def test_info_json
    status, out, = execute("info", "--json")
    assert_equal 0, status
    assert_equal "Ruby Orion", JSON.parse(out).fetch("project")
  end

  def test_labs_distinguishes_planned_and_available
    status, out, = execute("labs", "--json")
    assert_equal 0, status
    labs = JSON.parse(out)
    assert_equal "available", labs.first.fetch("status")
    assert_equal "planned", labs.last.fetch("status")
  end

  def test_inspect_file_json
    Tempfile.create("orion") do |f|
      f.binmode
      f.write("%PDF-1.4\n")
      f.flush
      status, out, = execute("inspect", f.path, "--json")
      assert_equal 0, status
      assert_equal "PDF", JSON.parse(out).fetch("signature")
    end
  end

  def test_hash_verify_success_and_failure
    Tempfile.create("orion") do |f|
      f.write("ruby orion")
      f.flush
      good = Digest::SHA256.hexdigest("ruby orion")
      status, out, = execute("hash", f.path, "--verify", good, "--json")
      assert_equal 0, status
      assert_equal true, JSON.parse(out).fetch("verified")
      status, out, = execute("hash", f.path, "--verify", "0" * 64, "--json")
      assert_equal 1, status
      assert_equal false, JSON.parse(out).fetch("verified")
    end
  end

  def test_invalid_algorithm
    Tempfile.create("orion") do |f|
      status, _, err = execute("hash", f.path, "--algorithm", "md5")
      assert_equal 2, status
      assert_match(/invalid argument|inválido/i, err)
    end
  end

  def test_inspect_without_path
    status, _, err = execute("inspect")
    assert_equal 2, status
    assert_includes err, "informe exatamente um arquivo"
  end
end
