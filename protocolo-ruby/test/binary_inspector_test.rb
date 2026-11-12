require 'minitest/autorun'
require_relative '../lib/protocolo_ruby/analyzer'

class BinaryInspectorTest < Minitest::Test
  def test_pe_64bit_header
    data = "\x00".b * 256
    data[0, 2] = 'MZ'
    data[0x3c, 4] = [0x80].pack('V')
    data[0x80, 4] = "PE\x00\x00".b
    data[0x84, 2] = [0x8664].pack('v')
    data[0x86, 2] = [3].pack('v')
    data[0x94, 2] = [2].pack('v')
    data[0x98, 2] = [0x20b].pack('v')
    result = ProtocoloRuby::Analyzer.new.analyze(data)
    assert_equal true, result[:binary_header][:valid_header]
    assert_equal 'PE32+', result[:binary_header][:optional_header]
    assert_equal 3, result[:binary_header][:sections_declared]
    assert_equal 8, result[:hex_preview].length
  end

  def test_elf_header
    data = ("\x7fELF".b + [2, 1, 1, 0].pack('C*') + "\x00".b * 56)
    data[16, 2] = [2].pack('v')
    data[18, 2] = [62].pack('v')
    header = ProtocoloRuby::BinaryInspector.inspect(data)
    assert_equal true, header[:valid_header]
    assert_equal '64-bit', header[:bits]
    assert_equal 'little', header[:endianness]
  end

  def test_truncated_executable
    report = ProtocoloRuby::Analyzer.new.analyze('MZ')
    assert_equal false, report[:binary_header][:valid_header]
    assert_equal 'INVALID_EXECUTABLE_HEADER', report[:findings].first[:code]
  end

  def test_zero_entropy
    assert_equal 0.0, ProtocoloRuby::Analyzer.new.analyze('AAAA')[:entropy]
  end
end
