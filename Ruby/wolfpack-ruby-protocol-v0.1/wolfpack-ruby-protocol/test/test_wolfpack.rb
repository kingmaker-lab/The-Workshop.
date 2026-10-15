# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'
require 'tmpdir'
require_relative '../lib/wolfpack/game'

class WolfpackTest < Minitest::Test
  def setup
    @runner = Wolfpack::Runner.new(timeout: 2.0)
    @validator = Wolfpack::Validator.new(runner: @runner)
  end

  def test_all_twelve_reference_solutions_pass
    assert_equal 12, Wolfpack::Lessons.all.size
    Wolfpack::Lessons.all.each do |lesson|
      result = @validator.check(lesson, lesson.solution)
      assert result.success, "Missão #{lesson.id}: #{result.feedback}"
    end
  end

  def test_every_example_is_valid_ruby
    Wolfpack::Lessons.all.each do |lesson|
      result = @runner.run(lesson.example, stdin_data: "Raven\n")
      assert_equal 0, result.status, "Exemplo #{lesson.id}: #{result.error}"
    end
  end

  def test_invalid_logic_rejected
    lesson = Wolfpack::Lessons.all.fetch(4)
    bad_solution = "energia = gets.to_i\nif energia >= 99\n puts 'PORTAO ABERTO'\nelse\n puts 'RECUAR'\nend"
    result = @validator.check(lesson, bad_solution)
    refute result.success
    assert_equal 2, result.case_number
  end

  def test_missing_required_syntax_rejected
    result = @validator.check(Wolfpack::Lessons.all.first, 'print "A matilha despertou!"')
    refute result.success
    assert_match(/puts/, result.feedback)
  end

  def test_syntax_errors_are_reported
    result = @validator.check(Wolfpack::Lessons.all.first, 'puts "hello" +')
    refute result.success
    assert_match(/erro/i, result.feedback)
  end

  def test_infinite_loop_is_interrupted
    result = @runner.run('loop { }')
    assert result.timed_out
  end

  def test_saved_progress_survives_reload
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'progress.json')
      progress = Wolfpack::Progress.new(path: path)
      progress.codename = 'Kingmaker'
      assert progress.complete!(1)
      refute progress.complete!(1)
      reopened = Wolfpack::Progress.new(path: path)
      assert_equal 'Kingmaker', reopened.codename
      assert_equal [1], reopened.completed
      assert_equal 100, reopened.xp
    end
  end

  def test_cli_first_mission_then_continue
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'progress.json')
      input = StringIO.new("Kingmaker\n1\n\nputs \"A matilha despertou!\"\nFIM\n0\n")
      output = StringIO.new
      progress = Wolfpack::Progress.new(path: path)
      Wolfpack::Game.new(input: input, output: output, progress: progress, validator: @validator).run
      assert_match(/1 teste\(s\) passaram/, output.string)
      assert_equal [1], Wolfpack::Progress.new(path: path).completed
    end
  end

  def test_entire_campaign_through_terminal
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'progress.json')
      commands = ["Kingmaker\n"]
      Wolfpack::Lessons.all.each do |lesson|
        commands << "1\n\n#{lesson.solution}\nFIM\n"
      end
      commands << "0\n"
      output = StringIO.new
      Wolfpack::Game.new(
        input: StringIO.new(commands.join),
        output: output,
        progress: Wolfpack::Progress.new(path: path),
        validator: @validator
      ).run
      saved = Wolfpack::Progress.new(path: path)
      assert_equal (1..12).to_a, saved.completed
      assert_equal 1200, saved.xp
      assert_match(/PROTOCOLO RUBY RESTAURADO/, output.string)
    end
  end

end
