# frozen_string_literal: true
module ProtocoloRuby
  module BinaryInspector
    module_function
    def inspect(bytes)
      bytes = bytes.b
      return pe(bytes) if bytes.start_with?('MZ')
      return elf(bytes) if bytes.start_with?("\x7fELF".b)
      {type: 'unknown', valid_header: false}
    end
    def pe(data)
      out = {type: 'PE', valid_header: false}
      return out.merge(reason: 'truncated DOS header') if data.bytesize < 64
      offset = data.byteslice(0x3c, 4).unpack1('V')
      return out.merge(reason: 'PE header offset out of range') if offset > data.bytesize - 24
      return out.merge(reason: 'missing PE signature') unless data.byteslice(offset, 4) == "PE\x00\x00".b
      machine, sections, timestamp = data.byteslice(offset + 4, 8).unpack('vvV')
      opt_size = data.byteslice(offset + 20, 2).unpack1('v')
      opt_off = offset + 24
      return out.merge(reason: 'truncated optional header') if opt_size > data.bytesize - opt_off
      magic = opt_size >= 2 ? data.byteslice(opt_off, 2).unpack1('v') : nil
      out.merge(valid_header: true, machine: format('0x%04X', machine), sections_declared: sections,
                timestamp_unix: timestamp, optional_header: {0x10b => 'PE32', 0x20b => 'PE32+'}.fetch(magic, 'unknown'))
    end
    def elf(data)
      out = {type: 'ELF', valid_header: false}
      return out.merge(reason: 'truncated ELF ident') if data.bytesize < 20
      bits = {1 => '32-bit', 2 => '64-bit'}[data.getbyte(4)]
      endian = {1 => 'little', 2 => 'big'}[data.getbyte(5)]
      return out.merge(reason: 'invalid ELF class or endianness') unless bits && endian
      return out.merge(reason: 'truncated ELF header') if data.bytesize < (bits == '64-bit' ? 64 : 52)
      fmt = endian == 'little' ? 'v' : 'n'
      out.merge(valid_header: true, bits: bits, endianness: endian,
                elf_type: data.byteslice(16, 2).unpack1(fmt),
                machine: data.byteslice(18, 2).unpack1(fmt))
    end
    def hex_preview(bytes, length: 128)
      bytes.byteslice(0, [[length, 1].max, 256].min).unpack1('H*').scan(/.{1,32}/).first(16)
    end
  end
end
