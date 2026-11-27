require "digest"
puts Digest::SHA256.hexdigest(STDIN.read.strip)
