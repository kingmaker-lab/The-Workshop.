require "json"
begin
  frame = JSON.parse(STDIN.read)
  valid = frame.is_a?(Hash) &&
    frame["protocol"] == "orion-ipc/1" &&
    frame["type"] == "message" &&
    frame["payload"].is_a?(Hash) &&
    frame["payload"]["message"].is_a?(String)
  puts(valid ? "ACCEPT" : "REJECT")
rescue JSON::ParserError
  puts "REJECT"
end
