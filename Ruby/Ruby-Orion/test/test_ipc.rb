# frozen_string_literal: true
require 'minitest/autorun'
require 'stringio'
require_relative '../lib/orion'

class OrionIpcTest < Minitest::Test
  def test_round_trip
    text = Orion::IPC::Protocol.encode(type: 'request', payload: { values: [8, 13] })
    assert_equal 'request', Orion::IPC::Protocol.decode(text).fetch('type')
    assert_equal [8, 13], Orion::IPC::Protocol.decode(text).fetch('payload').fetch('values')
  end

  def test_channel_uses_json_line
    io = StringIO.new
    Orion::IPC::Channel.new(input: StringIO.new, output: io).write(type: 'response', payload: { sum: 21 })
    out = Orion::IPC::Channel.new(input: StringIO.new(io.string), output: StringIO.new).read
    assert_equal 21, out.fetch('payload').fetch('sum')
  end

  def test_unsupported_version
    frame = Orion::IPC::Protocol.encode(type: 'request', payload: {})
    assert_raises(Orion::IPC::ProtocolError) { Orion::IPC::Protocol.decode(frame.sub('"version":1', '"version":2')) }
  end

  def test_invalid_json
    assert_raises(Orion::IPC::ProtocolError) { Orion::IPC::Protocol.decode('{invalid}\n'.gsub('\\n', "\n")) }
  end

  def test_no_newline
    assert_raises(Orion::IPC::ProtocolError) { Orion::IPC::Protocol.decode('{}') }
  end

  def test_oversize_frame
    assert_raises(Orion::IPC::ProtocolError) { Orion::IPC::Protocol.encode(type: 'request', payload: { text: 'X' * 5000 }) }
  end

  def test_invalid_payload
    assert_raises(Orion::IPC::ProtocolError) { Orion::IPC::Protocol.encode(type: 'request', payload: []) }
  end

  def test_extra_top_level_property
    frame = Orion::IPC::Protocol.encode(type: 'request', payload: {})
    assert_raises(Orion::IPC::ProtocolError) do
      Orion::IPC::Protocol.decode(frame.sub('"protocol":"orion-ipc",', '"protocol":"orion-ipc","extra":"value",'))
    end
  end

  def test_invalid_utf8
    assert_raises(Orion::IPC::ProtocolError) { Orion::IPC::Protocol.decode("\xff\n".b) }
  end

  def test_channel_rejects_overlong_line
    overlong = ('x' * (Orion::IPC::Protocol::MAX_FRAME_BYTES + 3)) + "\n"
    assert_raises(Orion::IPC::ProtocolError) do
      Orion::IPC::Channel.new(input: StringIO.new(overlong), output: StringIO.new).read
    end
  end

  def test_ipc_real_child_round_trip
    input = Orion::IPC::Protocol.encode(type: 'request', payload: { values: [8, 13, 21] })
    result = Orion::System::Supervisor.new.run(id: '003', kind: 'ipc', timeout: 3, input: input)
    assert result.success?, result.stderr
    response = Orion::IPC::Protocol.decode(result.stdout)
    assert_equal 42, response.fetch('payload').fetch('sum')
    assert_equal 'response', response.fetch('type')
  end

  def test_ipc_child_rejects_invalid_value
    input = Orion::IPC::Protocol.encode(type: 'request', payload: { values: ['bad'] })
    result = Orion::System::Supervisor.new.run(id: '003', kind: 'ipc', timeout: 3, input: input)
    assert_equal 'failed', result.status
    assert_equal 2, result.exit_code
    assert_includes result.stderr, 'values'
  end
end
