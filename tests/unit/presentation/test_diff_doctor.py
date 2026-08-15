from pathlib import Path
import json
from typer.testing import CliRunner
from devclean.presentation.cli.main import app
from devclean.presentation.formatters.json_encoder import DevCleanJSONEncoder

runner = CliRunner()

def test_doctor_command(snapshot):
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    # The output contains python versions and paths which are dynamic, so we just check for keywords
    assert "DevClean Diagnostics" in result.stdout
    assert "Environment" in result.stdout
    assert "Permissions" in result.stdout
    assert "Plugins" in result.stdout
    assert "Built-in Loaded" in result.stdout

def test_diff_command(tmp_path):
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    
    before_data = {
        "schema_version": "1.0",
        "items": [
            {"id": "00000000-0000-0000-0000-000000000001", "size_bytes": 1000, "category": "python-cache"},
            {"id": "00000000-0000-0000-0000-000000000002", "size_bytes": 2000, "category": "docker-image"}
        ]
    }
    
    after_data = {
        "schema_version": "1.0",
        "items": [
            {"id": "00000000-0000-0000-0000-000000000001", "size_bytes": 1500, "category": "python-cache"},
            {"id": "00000000-0000-0000-0000-000000000003", "size_bytes": 500, "category": "node-modules"}
        ]
    }
    
    before_path.write_text(json.dumps(before_data, cls=DevCleanJSONEncoder))
    after_path.write_text(json.dumps(after_data, cls=DevCleanJSONEncoder))
    
    result = runner.invoke(app, ["diff", str(before_path), str(after_path)])
    assert result.exit_code == 0
    assert "Report Diff Summary" in result.stdout
    assert "Removed Findings" in result.stdout
    assert "New Findings" in result.stdout
