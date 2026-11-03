require 'minitest/autorun'
require 'tempfile'
require_relative '../lib/protocolo_ruby/yara_x'
class YaraXTest < Minitest::Test
  def test_missing_rules
    assert_raises(Errno::ENOENT) { ProtocoloRuby::YaraX.new(rules_path: '/nonexistent/rules.yar') }
  end
  def test_invalid_sample_without_cli
    Tempfile.create(['rules', '.yar']) do |rules|
      scanner = ProtocoloRuby::YaraX.new(rules_path: rules.path)
      assert_raises(ArgumentError) { scanner.scan('') }
    end
  end
end
