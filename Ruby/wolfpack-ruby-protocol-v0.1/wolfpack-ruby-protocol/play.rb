#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'lib/wolfpack/game'

Wolfpack::Game.new.run if $PROGRAM_NAME == __FILE__
