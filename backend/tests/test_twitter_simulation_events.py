import json
from pathlib import Path
import sqlite3
import pytest

from app.services.simulation_runner import RunnerStatus, SimulationRunState, SimulationRunner
from scripts.run_twitter_simulation import (
    TwitterSimulationRunner,
    normalize_posts_to_english,
)


def test_normalize_posts_to_english_translates_cjk_fields(tmp_path):
    db_path = tmp_path / "twitter_simulation.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE post (post_id INTEGER PRIMARY KEY, content TEXT, quote_content TEXT)"
    )
    connection.execute(
        "INSERT INTO post VALUES (1, ?, ?)",
        ("通胀仍然居高不下。", "Policy remains data-dependent."),
    )
    connection.commit()
    connection.close()

    translated = normalize_posts_to_english(
        str(db_path), lambda text: "Inflation remains elevated."
    )

    connection = sqlite3.connect(db_path)
    row = connection.execute(
        "SELECT content, quote_content FROM post WHERE post_id = 1"
    ).fetchone()
    connection.close()
    assert translated == 1
    assert row == ("Inflation remains elevated.", "Policy remains data-dependent.")


def test_normalize_posts_to_english_rejects_cjk_translation(tmp_path):
    db_path = tmp_path / "twitter_simulation.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE post (post_id INTEGER PRIMARY KEY, content TEXT, quote_content TEXT)"
    )
    connection.execute("INSERT INTO post VALUES (1, ?, NULL)", ("通胀。",))
    connection.commit()
    connection.close()

    try:
        normalize_posts_to_english(str(db_path), lambda text: "仍然是中文。")
    except ValueError as error:
        assert "English" in str(error)
    else:
        raise AssertionError("CJK translation should be rejected")


@pytest.mark.parametrize("source", ["こんにちは", "안녕하세요"])
def test_normalize_posts_to_english_translates_all_cjk_scripts(tmp_path, source):
    db_path = tmp_path / "twitter_simulation.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE post (post_id INTEGER PRIMARY KEY, content TEXT, quote_content TEXT)"
    )
    connection.execute("INSERT INTO post VALUES (1, ?, NULL)", (source,))
    connection.commit()
    connection.close()

    translated = normalize_posts_to_english(str(db_path), lambda text: "Hello.")

    connection = sqlite3.connect(db_path)
    content = connection.execute("SELECT content FROM post WHERE post_id = 1").fetchone()[0]
    connection.close()
    assert translated == 1
    assert content == "Hello."


def test_normalize_posts_to_english_rejects_non_latin_translation(tmp_path):
    db_path = tmp_path / "twitter_simulation.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE post (post_id INTEGER PRIMARY KEY, content TEXT, quote_content TEXT)"
    )
    connection.execute("INSERT INTO post VALUES (1, ?, NULL)", ("通胀。",))
    connection.commit()
    connection.close()

    with pytest.raises(ValueError, match="English"):
        normalize_posts_to_english(str(db_path), lambda text: "Русский текст")


def test_twitter_runner_counts_persisted_actions(tmp_path):
    config_path = tmp_path / "simulation_config.json"
    config_path.write_text(json.dumps({"simulation_id": "sim_test"}), encoding="utf-8")
    runner = TwitterSimulationRunner(str(config_path), wait_for_commands=True)
    connection = sqlite3.connect(tmp_path / "twitter_simulation.db")
    connection.execute("CREATE TABLE trace (id INTEGER PRIMARY KEY)")
    connection.executemany("INSERT INTO trace DEFAULT VALUES", [(), (), ()])
    connection.commit()
    connection.close()

    assert runner._get_total_action_count() == 3


def test_twitter_runner_emits_completion_event_consumable_by_monitor(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationRunner, "RUN_STATE_DIR", str(tmp_path))
    simulation_dir = tmp_path / "sim_test"
    simulation_dir.mkdir()
    config_path = simulation_dir / "simulation_config.json"
    config_path.write_text(json.dumps({"simulation_id": "sim_test"}), encoding="utf-8")
    runner = TwitterSimulationRunner(str(config_path), wait_for_commands=True)

    runner._append_action_event(
        {
            "event_type": "simulation_end",
            "total_rounds": 3,
            "total_actions": 7,
        }
    )

    log_path = simulation_dir / "twitter" / "actions.jsonl"
    state = SimulationRunState(
        simulation_id="sim_test",
        runner_status=RunnerStatus.RUNNING,
        total_rounds=3,
        twitter_running=True,
    )
    SimulationRunner._read_action_log(str(log_path), 0, state, "twitter")

    assert state.twitter_completed is True
    assert state.twitter_running is False
    assert state.twitter_actions_count == 7
    assert state.runner_status is RunnerStatus.COMPLETED


def test_twitter_runner_round_event_advances_progress_even_without_actions(tmp_path):
    config_path = tmp_path / "simulation_config.json"
    config_path.write_text(json.dumps({"simulation_id": "sim_test"}), encoding="utf-8")
    runner = TwitterSimulationRunner(str(config_path), wait_for_commands=True)

    runner._append_action_event(
        {
            "event_type": "round_end",
            "round": 1,
            "simulated_hours": 1,
            "actions_count": 0,
        }
    )

    log_path = tmp_path / "twitter" / "actions.jsonl"
    state = SimulationRunState(
        simulation_id="sim_test",
        runner_status=RunnerStatus.RUNNING,
        total_rounds=3,
        twitter_running=True,
    )
    SimulationRunner._read_action_log(str(log_path), 0, state, "twitter")

    assert state.current_round == 1
    assert state.twitter_current_round == 1
    assert state.twitter_simulated_hours == 1
