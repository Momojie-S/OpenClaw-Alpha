# -*- coding: utf-8 -*-
"""配置管理 API 测试"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def fake_config(tmp_path):
    """创建临时 config.json 并 patch settings 指向它"""
    config_path = tmp_path / "runtime" / "config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "iteration_loop": {
                    "enabled": True,
                    "interval_minutes": 30,
                    "dev_tasks": {"enabled": True},
                },
                "feedback": {
                    "enabled": True,
                    "interval_minutes": 30,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with patch.dict("os.environ", {"OPENCLAW_ALPHA_ROOT": str(tmp_path)}):
        # 清除 settings 缓存使其重新加载
        import openclaw_alpha.core.settings as s

        old_root = s.settings._root
        old_config = s.settings._config
        s.settings._root = tmp_path
        s.settings._config = None
        yield
        s.settings._root = old_root
        s.settings._config = old_config


class TestIterationLoopConfigAPI:
    """Iteration Loop 配置 API 测试"""

    @pytest.fixture
    def client(self):
        from openclaw_alpha.backend.main import app

        return TestClient(app)

    def test_get_config_default(self, client, fake_config):
        response = client.get("/api/config/iteration-loop")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["interval_minutes"] == 30
        assert data["dev_tasks"]["enabled"] is True

    def test_update_config_dev_tasks_disabled(self, client, fake_config):
        response = client.put(
            "/api/config/iteration-loop",
            json={"dev_tasks": {"enabled": False}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dev_tasks"]["enabled"] is False
        assert data["enabled"] is True

    def test_update_config_main_switch(self, client, fake_config):
        response = client.put(
            "/api/config/iteration-loop",
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    def test_update_config_interval(self, client, fake_config):
        response = client.put(
            "/api/config/iteration-loop",
            json={"interval_minutes": 60},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["interval_minutes"] == 60


class TestFeedbackConfigAPI:
    """Feedback 配置 API 测试"""

    @pytest.fixture
    def client(self):
        from openclaw_alpha.backend.main import app

        return TestClient(app)

    def test_get_config_default(self, client, fake_config):
        response = client.get("/api/config/feedback")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["interval_minutes"] == 30

    def test_update_config_enabled(self, client, fake_config):
        response = client.put(
            "/api/config/feedback",
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
