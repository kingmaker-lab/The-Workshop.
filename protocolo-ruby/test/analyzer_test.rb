require 'minitest/autorun'
require_relative '../lib/protocolo_ruby/analyzer'
class AnalyzerTest < Minitest::Test
  def setup = @analyzer = ProtocoloRuby::Analyzer.new
  def test_hashes
    report = @analyzer.analyze('abc', filename: '../hello.txt')
    assert_equal 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', report[:hashes][:sha256]
    assert_equal 'hello.txt', report[:filename]
  end
  def test_elf
    assert_equal 'ELF', @analyzer.analyze("\x7fELFanything".b)[:format]
  end
  def test_entropy
    assert_equal 0.0, @analyzer.analyze('AAAA')[:entropy]
    assert_equal 1.0, @analyzer.analyze('ABAB')[:entropy]
  end
  def test_iocs
    report = @analyzer.analyze('Visit https://example.org/a and 192.168.1.12 now!')
    assert_includes report[:indicators][:urls], 'https://example.org/a'
    assert_includes report[:indicators][:ipv4], '192.168.1.12'
  end
  def test_limits
    assert_raises(ArgumentError) { @analyzer.analyze('') }
    assert_raises(ArgumentError) { @analyzer.analyze('A' * (ProtocoloRuby::Analyzer::MAX_BYTES + 1)) }
  end
end
