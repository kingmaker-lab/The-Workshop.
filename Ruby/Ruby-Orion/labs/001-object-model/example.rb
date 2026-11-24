# frozen_string_literal: true
# Alnitak / Learn: observe the Ruby object model without external dependencies.
class Star
  attr_reader :name

  def initialize(name)
    @name = name
  end

  def describe
    "#{name}: #{self.class} -> #{self.class.superclass}"
  end
end

star = Star.new("Alnitak")
puts star.describe
puts "Métodos próprios: #{Star.instance_methods(false).sort.join(', ')}"
puts "Classe de Star: #{Star.class}"
