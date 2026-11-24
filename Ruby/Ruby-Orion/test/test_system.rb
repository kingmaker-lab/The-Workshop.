# frozen_string_literal: true
require 'minitest/autorun'
require 'json'
require_relative '../lib/orion'

class OrionSystemTest < Minitest::Test
  def fixture(name)
    path = File.expand_path("fixtures/#{name}.rb", __dir__)
    Orion::Tasks::Task.new(id: "test-#{name}", name: name, kind: 'test', script: path)
  end

  def test_process_success
    result = Orion::System::Supervisor.new.run(id: '002', kind: 'process', timeout: 3)
    assert result.success?
    assert_equal 0, result.exit_code
    assert_includes result.stdout, 'task completed'
    assert_equal false, result.timed_out
  end

  def test_process_nonzero_exit
    result = Orion::System::Runner.new.run(task: fixture('exit_nonzero'), timeout: 3)
    assert_equal 'failed', result.status
    assert_equal 7, result.exit_code
    assert_includes result.stderr, 'intentional failure'
  end

  def test_process_timeout_and_cleanup
    result = Orion::System::Runner.new.run(task: fixture('slow'), timeout: 0.1)
    assert_equal 'timed_out', result.status
    assert_equal true, result.timed_out
    assert_operator result.duration_ms, :<, 3000
  end

  def test_timeout_escalates_to_sigkill_when_child_ignores_term
    skip 'POSIX-only signal test' if RbConfig::CONFIG.fetch('host_os').match?(/mswin|mingw|cygwin/i)
    result = Orion::System::Runner.new.run(task: fixture('ignore_term'), timeout: 0.2)
    assert_equal 'timed_out', result.status
    assert_operator result.duration_ms, :<, 3000
  end

  def test_output_bounded_and_drained
    result = Orion::System::Runner.new.run(task: fixture('large_output'), timeout: 3, max_output_bytes: 1024)
    assert result.success?
    assert_equal 1024, result.stdout.bytesize
    assert_equal 1024, result.stderr.bytesize
    assert_equal true, result.stdout_truncated
    assert_equal true, result.stderr_truncated
  end

  def test_environment_isolated_and_stdin
    previous = ENV['ORION_SECRET_TEST']
    ENV['ORION_SECRET_TEST'] = 'should-not-inherit'
    result = Orion::System::Runner.new.run(task: fixture('echo_input'), timeout: 3, input: 'safe')
    assert result.success?
    response = JSON.parse(result.stdout)
    assert_equal 4, response.fetch('length')
    assert_nil response.fetch('env_test')
    assert_nil response.fetch('rubyopt')
  ensure
    ENV['ORION_SECRET_TEST'] = previous
  end

  def test_input_limit
    assert_raises(Orion::System::Runner::InvalidInput) do
      Orion::System::Runner.new.run(task: fixture('echo_input'), input: 'x' * (8 * 1024 + 1))
    end
  end

  def test_timeout_argument_rejected
    assert_raises(Orion::System::Runner::InvalidInput) do
      Orion::System::Runner.new.run(task: fixture('echo_input'), timeout: 31)
    end
  end

  def test_unknown_task_rejected
    assert_raises(ArgumentError) { Orion::System::Supervisor.new.run(id: '../slow', kind: 'process') }
    assert_raises(ArgumentError) { Orion::System::Supervisor.new.run(id: '003', kind: 'process') }
  end
end
