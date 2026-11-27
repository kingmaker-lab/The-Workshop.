require "json"
stats = Hash.new(0)
STDIN.each_line do |line|
  next if line.strip.empty?
  begin
    event = JSON.parse(line)
    severity = event.is_a?(Hash) ? event["severity"] : nil
    stats[severity] += 1 if ["high", "critical"].include?(severity)
  rescue JSON::ParserError
    stats["invalid"] += 1
  end
end
puts "high=#{stats['high']};critical=#{stats['critical']};invalid=#{stats['invalid']}"
