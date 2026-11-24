#!/usr/bin/env ruby
# frozen_string_literal: true
require "json"
require "uri"
require "set"

file = File.expand_path("../data/projects.json", __dir__)
data = JSON.parse(File.read(file, encoding: "UTF-8"))
abort "schema_version must be 1" unless data["schema_version"] == 1
projects = data.fetch("projects")
abort "projects must be a non-empty array" unless projects.is_a?(Array) && !projects.empty?
ids = Set.new
allowed_status = %w[development experimental stable planned]
allowed_hosts = %w[github.com wolfpack.wolfpackworkshop.workers.dev protocolo-ruby.wolfpackworkshop.workers.dev orion.wolfpackworkshop.workers.dev]
projects.each do |p|
  abort "project must be an object" unless p.is_a?(Hash)
  %w[id name category status kind description].each do |key|
    abort "missing or empty #{key}" unless p[key].is_a?(String) && !p[key].strip.empty?
  end
  abort "invalid id #{p['id']}" unless p["id"].match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)
  abort "duplicate id #{p['id']}" unless ids.add?(p["id"])
  abort "unsupported status" unless allowed_status.include?(p["status"])
  abort "stack must be non-empty strings" unless p["stack"].is_a?(Array) && !p["stack"].empty? && p["stack"].all? { |x| x.is_a?(String) && !x.strip.empty? }
  abort "Ruby must be in stack: #{p['id']}" unless p["stack"].include?("Ruby")
  %w[repo site].each do |key|
    next if p[key].nil?
    begin
      uri = URI.parse(p[key])
      abort "invalid URL for #{p['id']}:#{key}" unless uri.is_a?(URI::HTTPS) && allowed_hosts.include?(uri.host) && uri.userinfo.nil? && uri.query.nil?
    rescue URI::InvalidURIError
      abort "invalid URL for #{p['id']}:#{key}"
    end
  end
end
puts "Ruby Hub registry OK: #{projects.length} projects, #{projects.map { |p| p['category'] }.uniq.length} categories"
