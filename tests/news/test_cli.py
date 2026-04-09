# -*- coding: utf-8 -*-
"""News CLI 测试。"""

import json
import subprocess
import sys


CLI = [sys.executable, "-m", "openclaw_alpha.news.cli"]


def _run(*args, env=None):
    import os
    _env = os.environ.copy()
    _env.setdefault("MILVUS_URI", "https://localhost:19530")
    _env.setdefault("MILVUS_TOKEN", "test")
    if env:
        _env.update(env)
    return subprocess.run(
        CLI + list(args),
        capture_output=True,
        text=True,
        env=_env,
        timeout=30,
    )


class TestCLIBasic:
    def test_no_command_exits(self):
        r = _run()
        assert r.returncode != 0

    def test_get_news_not_found(self, tmp_path):
        r = _run("get-news", "nonexistent", "--data-dir", str(tmp_path))
        assert r.returncode == 1
        data = json.loads(r.stdout)
        assert "error" in data
        assert "not found" in data["error"]

    def test_get_event_not_found(self, tmp_path):
        r = _run("get-event", "nonexistent", "--data-dir", str(tmp_path))
        assert r.returncode == 1
        data = json.loads(r.stdout)
        assert "error" in data

    def test_search_similar_not_found(self, tmp_path):
        r = _run("search-similar", "nonexistent", "--data-dir", str(tmp_path))
        assert r.returncode == 1
        data = json.loads(r.stdout)
        assert "error" in data

    def test_create_event_stub(self, tmp_path):
        # 先创建新闻
        news_dir = tmp_path / "news" / "any_id"
        news_dir.mkdir(parents=True, exist_ok=True)
        (news_dir / "news.json").write_text(
            json.dumps({
                "news_id": "any_id",
                "title": "测试新闻",
                "source": "test",
                "link": "",
                "published": "",
                "created_at": 1234567890,
                "updated_at": 1234567890
            }),
            encoding="utf-8"
        )

        r = _run("create-event", "any_id", "--title", "测试事件", "--data-dir", str(tmp_path))
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "event_id" in data
