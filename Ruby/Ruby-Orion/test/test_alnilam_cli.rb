# frozen_string_literal: true
require 'minitest/autorun'
require 'stringio'
require 'json'
require_relative '../lib/orion'

class OrionAlnilamCliTest < Minitest::Test
  def execute(*args)
    out, err = StringIO.new, StringIO.new
    status = Orion::CLI.new(out: out, err: err).run(args)
    [status, out.string, err.string]
  end

  def test_process_run
    status, out, = execute('process', 'run', '002', '--timeout', '3', '--json')
    assert_equal 0, status
    assert_equal 'completed', JSON.parse(out).fetch('status')
  end

  def test_process_list
    status, out, = execute('process', 'list', '--json')
    assert_equal 0, status
    assert_equal '002', JSON.parse(out).first.fetch('id')
  end

  def test_ipc_demo
    status, out, = execute('ipc', 'demo', '--json')
    assert_equal 0, status
    assert_equal 42, JSON.parse(out).fetch('response').fetch('sum')
  end

  def test_unknown_task_does_not_execute
    status, _out, err = execute('process', 'run', '../../../etc/passwd')
    assert_equal 2, status
    assert_includes err, 'tarefa não cadastrada'
  end

  def test_timeout_bounds_rejected
    status, _out, err = execute('process', 'run', '002', '--timeout', '100')
    assert_equal 2, status
    assert_includes err, 'timeout'
  end

  def test_legacy_lab_still_available
    _status, out, = execute('labs', '--json')
    labs = JSON.parse(out)
    assert_equal '001', labs.first.fetch('id')
    assert_equal 'available', labs.find { |x| x.fetch('id') == '002' }.fetch('status')
  end
end
