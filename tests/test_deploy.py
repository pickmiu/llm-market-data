from pathlib import Path

def test_deploy_configs_exist():
    root = Path(__file__).resolve().parent.parent
    wrangler_file = root / "deploy" / "cloudflare" / "wrangler.toml"
    worker_file = root / "deploy" / "cloudflare" / "worker.js"
    workflow_file = root / ".github" / "workflows" / "collector.yml"

    assert wrangler_file.exists()
    assert worker_file.exists()
    assert workflow_file.exists()

    wrangler_text = wrangler_file.read_text()
    assert 'crons = ["30 0 * * *"]' in wrangler_text

    worker_text = worker_file.read_text()
    assert "workflow_dispatch" in worker_text or "dispatches" in worker_text
    assert "GITHUB_PAT" in worker_text
    assert "async fetch(" in worker_text
    assert "async scheduled(" in worker_text
    assert "isMonday" in worker_text
    assert "generate_report" in worker_text

    workflow_text = workflow_file.read_text()
    assert "workflow_dispatch:" in workflow_text
    assert "python cli.py sync" in workflow_text
    assert "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}" in workflow_text
    assert "generate_weekly_top5_report.py" in workflow_text
    assert "git add data/ report/" in workflow_text
