from pathlib import Path

def test_project_structure():
    root = Path(__file__).resolve().parent.parent
    assert (root / "requirements.txt").exists()
    assert (root / ".env.example").exists()
    assert (root / "sources" / "__init__.py").exists()
    assert (root / "sources" / "openrouter" / "__init__.py").exists()
    assert (root / "data" / "openrouter" / "models").is_dir()
    assert (root / "data" / "openrouter" / "rankings_daily").is_dir()
    assert (root / "data" / "openrouter" / "apps").is_dir()
    assert (root / "data" / "openrouter" / "task_spend").is_dir()
    assert (root / "data" / "openrouter" / "session_cost").is_dir()
    assert (root / "data" / "openrouter" / "benchmarks").is_dir()
    assert (root / "data" / "openrouter" / "performance").is_dir()
