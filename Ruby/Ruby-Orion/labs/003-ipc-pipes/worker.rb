#!/usr/bin/env ruby
# frozen_string_literal: true
require_relative '../../lib/orion/ipc/channel'

channel = Orion::IPC::Channel.new(input: $stdin, output: $stdout)
begin
  frame = channel.read
  raise Orion::IPC::ProtocolError, 'solicitação ausente' unless frame && frame.fetch('type') == 'request'
  data = frame.fetch('payload')
  values = data.fetch('values')
  unless values.is_a?(Array) && values.length.between?(1, 32) && values.all? { |x| x.is_a?(Integer) && x.between?(-1_000_000, 1_000_000) }
    raise Orion::IPC::ProtocolError, 'values deve conter até 32 inteiros válidos'
  end
  channel.write(type: 'response', payload: { sum: values.sum, count: values.length })
rescue Orion::IPC::ProtocolError, KeyError => e
  warn "orion-ipc: #{e.message}"
  exit 2
end
