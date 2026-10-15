#!/usr/bin/env ruby
require 'json'
require_relative 'source/lessons'
lessons = Wolfpack::Lessons.all.map do |lesson|
  {
    id: lesson.id, act: lesson.act, title: lesson.title, scene: lesson.scene,
    theory: lesson.theory, example: lesson.example, task: lesson.task,
    hint: lesson.hint, solution: lesson.solution,
    requirements: lesson.requirements.map { |regexp, msg| { pattern: regexp.source, message: msg } },
    cases: lesson.cases.map { |input, output| { input: input, output: output } }
  }
end
File.write(File.join(__dir__, 'data', 'lessons.json'), JSON.pretty_generate(lessons))
