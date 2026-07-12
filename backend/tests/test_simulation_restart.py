import json

from app.api.simulation import _check_simulation_prepared
from app.config import Config


def test_paused_simulation_with_complete_artifacts_can_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "OASIS_SIMULATION_DATA_DIR", str(tmp_path))
    simulation_dir = tmp_path / "sim_paused"
    simulation_dir.mkdir()
    (simulation_dir / "state.json").write_text(
        json.dumps({
            "status": "paused",
            "config_generated": True,
            "enable_twitter": True,
            "enable_reddit": False,
        }),
        encoding="utf-8",
    )
    (simulation_dir / "simulation_config.json").write_text("{}", encoding="utf-8")
    (simulation_dir / "twitter_profiles.csv").write_text("user_id,name\n", encoding="utf-8")

    prepared, info = _check_simulation_prepared("sim_paused")

    assert prepared is True
    assert info["status"] == "paused"
