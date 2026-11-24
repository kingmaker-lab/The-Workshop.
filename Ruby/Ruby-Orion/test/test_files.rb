# frozen_string_literal: true
require "minitest/autorun"
require "tmpdir"
require "digest"
require_relative "../lib/orion"

class OrionFilesTest < Minitest::Test
  def test_elf_and_empty_file_entropy
    Dir.mktmpdir do |dir|
      elf = File.join(dir, "sample.elf")
      empty = File.join(dir, "empty.bin")
      File.binwrite(elf, "\x7fELF".b + "\x00".b * 200)
      File.binwrite(empty, "".b)
      assert_equal "ELF", Orion::Files.inspect(elf)[:signature]
      assert_equal 0.0, Orion::Files.inspect(empty)[:entropy_sample]
    end
  end

  def test_sha512
    Dir.mktmpdir do |dir|
      file = File.join(dir, "x.bin")
      File.binwrite(file, "abc")
      assert_equal Digest::SHA512.hexdigest("abc"), Orion::Files.hash(file, algorithm: "sha512")[:digest]
    end
  end

  def test_refuse_symlinks_and_directories
    Dir.mktmpdir do |dir|
      file = File.join(dir, "real")
      File.write(file, "data")
      symlink = File.join(dir, "link")
      File.symlink(file, symlink)
      assert_raises(Orion::Files::InvalidFile) { Orion::Files.inspect(symlink) }
      assert_raises(Orion::Files::InvalidFile) { Orion::Files.hash(dir) }
    end
  end

  def test_pe_signature_requires_valid_pointer
    bytes = "MZ".b.ljust(0x3c, "\x00".b) + [0x80].pack("V")
    assert_equal "MZ (possível PE)", Orion::Files.signature(bytes)
    bytes = bytes.ljust(0x80, "\x00".b) + "PE\x00\x00".b
    assert_equal "PE", Orion::Files.signature(bytes)
  end

  def test_sample_size_is_bounded
    Dir.mktmpdir do |dir|
      path = File.join(dir, "sample")
      File.binwrite(path, "A" * 9000)
      assert_equal 4096, Orion::Files.inspect(path)[:sampled_bytes]
      assert_equal 0.0, Orion::Files.inspect(path)[:entropy_sample]
    end
  end
end
