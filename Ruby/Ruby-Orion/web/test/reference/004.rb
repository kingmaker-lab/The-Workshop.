require "json"
headers = JSON.parse(STDIN.read)
keys = headers.keys.map(&:downcase)
missing = []
missing << "CSP" unless keys.include?("content-security-policy")
missing << "HSTS" unless keys.include?("strict-transport-security")
puts missing.empty? ? "OK" : "MISSING: #{missing.join(',')}"
