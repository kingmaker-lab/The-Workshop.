words = STDIN.read.split
counts = words.tally
result = counts.sort_by { |word, count| [-count, word] }.map { |word, count| "#{word}:#{count}" }.join("\n")
puts result
