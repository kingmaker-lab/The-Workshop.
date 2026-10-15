# frozen_string_literal: true

require 'minitest/autorun'
require 'tmpdir'
require_relative '../lib/vulpes77'

class Vulpes77Test < Minitest::Test
  def setup
    @tmp = Dir.mktmpdir('vulpes77-test')
    @save = File.join(@tmp, 'save.json')
    @game = Vulpes77::Game.new(save_path: @save, fresh: true)
  end

  def teardown
    FileUtils.remove_entry(@tmp)
  end

  def run_cmd(cmd)
    @game.perform(cmd)
  end

  def test_first_mission_flow
    assert_match(/ECO FANTASMA/, @game.intro)
    assert_match(/8080\/tcp/, run_cmd('scan 10.77.0.12').text)
    assert_match(/Conectado/, run_cmd('connect 10.77.0.12:8080').text)
    assert_match(/TklHSFRKQVI=/, run_cmd('cat traffic.log').text)
    assert_equal 'Resultado: NIGHTJAR', run_cmd('decode b64 TklHSFRKQVI=').text
    assert_equal :success, run_cmd('submit NIGHTJAR').kind
    assert_equal 1, @game.mission_index
    assert_equal 100, @game.score
  end

  def test_complete_campaign
    run_cmd('submit NIGHTJAR')
    run_cmd('scan 10.77.0.23')
    run_cmd('connect 10.77.0.23:9200')
    assert_match(/svc-bridge/, run_cmd('grep E-441 auth.log').text)
    run_cmd('submit svc-bridge')
    assert_equal 2, @game.mission_index
    assert_equal :error, run_cmd('contain 10.77.0.1').kind
    run_cmd('scan 10.77.0.44')
    run_cmd('connect 10.77.0.44:8443')
    assert_equal :error, run_cmd('submit IR-2607').kind
    assert_equal :error, run_cmd('contain 10.77.0.23').kind
    assert_equal :success, run_cmd('contain 10.77.0.12').kind
    assert_equal :win, run_cmd('submit IR-2607').kind
    assert @game.complete?
    assert_equal 300, @game.score
  end

  def test_locked_hosts_and_scanning_required
    assert_equal :error, run_cmd('scan 10.77.0.44').kind
    assert_equal :error, run_cmd('connect 10.77.0.12:8080').kind
    assert_equal :error, run_cmd('scan 8.8.8.8').kind
    assert_equal :error, run_cmd('connect 8.8.8.8:53').kind
  end

  def test_hint_penalizes_once_and_wrong_answer
    run_cmd('hint')
    run_cmd('hint')
    run_cmd('submit wrong')
    run_cmd('submit NIGHTJAR')
    assert_equal 80, @game.score
  end

  def test_invalid_encodings_are_safe
    assert_equal :error, run_cmd('decode b64 !!!').kind
    assert_equal :error, run_cmd('decode hex ZZZ').kind
    assert_equal :success, run_cmd('decode hex 464f58').kind
    assert_equal 'Resultado: FOX', run_cmd('decode hex 464f58').text
  end

  def test_sha256
    assert_match(/ba7816bf8f01cfea/, run_cmd('hash sha256 abc').text)
  end

  def test_save_and_restore
    run_cmd('scan 10.77.0.12')
    run_cmd('connect 10.77.0.12:8080')
    restored = Vulpes77::Game.new(save_path: @save)
    assert_match(/WEB-01:8080/, restored.prompt)
    assert_match(/traffic.log/, restored.perform('ls').text)
    restored.perform('submit NIGHTJAR')
    resumed = Vulpes77::Game.new(save_path: @save)
    assert_equal 1, resumed.mission_index
  end

  def test_corrupt_save_starts_fresh
    File.write(@save, '{ broken')
    game = Vulpes77::Game.new(save_path: @save)
    assert_equal 0, game.mission_index
  end

  def test_no_shell_execution
    assert_equal :error, run_cmd('$(touch /tmp/vulpes77-pwned)').kind
    assert_equal :error, run_cmd('scan localhost').kind
  end

  def test_restart
    run_cmd('submit NIGHTJAR')
    assert_equal 1, @game.mission_index
    run_cmd('novo')
    assert_equal 0, @game.mission_index
    assert_equal 0, @game.score
  end
  def test_migrates_old_progress_without_deleting_source
    run_cmd('submit NIGHTJAR')
    legacy = File.join(@tmp, 'old', 'save.json')
    FileUtils.mkdir_p(File.dirname(legacy))
    FileUtils.mv(@save, legacy)
    migrated = Vulpes77::Game.new(save_path: @save, legacy_save_path: legacy)
    assert_equal 1, migrated.mission_index
    assert_equal 100, migrated.score
    assert File.file?(@save)
    assert File.file?(legacy)
    resumed = Vulpes77::Game.new(save_path: @save, legacy_save_path: legacy)
    assert_equal 1, resumed.mission_index
  end

  def test_new_campaign_does_not_migrate
    run_cmd('submit NIGHTJAR')
    legacy = File.join(@tmp, 'old', 'save.json')
    FileUtils.mkdir_p(File.dirname(legacy))
    FileUtils.mv(@save, legacy)
    new_game = Vulpes77::Game.new(save_path: @save, fresh: true, legacy_save_path: legacy)
    assert_equal 0, new_game.mission_index
    refute File.file?(@save)
  end

end
