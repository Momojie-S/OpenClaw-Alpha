# -*- coding: utf-8 -*-
"""配置管理 API 测试"""

import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient


class TestIterationLoopConfigAPI:
    """Iteration Loop 配置 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from openclaw_alpha.backend.main import app

        return TestClient(app)

    def test_get_config_default(self, client):
        """测试获取默认配置"""
        with patch(
            "openclaw_alpha.backend.iteration_loop.config.get_config_path"
        ) as mock_path:
            mock_path.return_value = Path("/nonexistent/config.yaml")

            response = client.get("/api/config/iteration-loop")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["interval_minutes"] == 30
            assert data["dev_tasks"]["enabled"] is True

    def test_update_config_dev_tasks_disabled(self, client):
        """测试禁用开发任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            with patch(
                "openclaw_alpha.backend.config_api.get_iteration_config_path",
                return_value=config_path,
            ):
                # 更新配置：禁用 dev_tasks
                response = client.put(
                    "/api/config/iteration-loop",
                    json={"dev_tasks": {"enabled": False}},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["dev_tasks"]["enabled"] is False
                assert data["enabled"] is True  # 主开关不受影响

                # 验证文件已写入
                assert config_path.exists()
                with open(config_path) as f:
                    saved = yaml.safe_load(f)
                assert saved["dev_tasks"]["enabled"] is False

    def test_update_config_main_switch(self, client):
        """测试主开关"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            with patch(
                "openclaw_alpha.backend.config_api.get_iteration_config_path",
                return_value=config_path,
            ):
                # 禁用主开关
                response = client.put(
                    "/api/config/iteration-loop",
                    json={"enabled": False},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["enabled"] is False

    def test_update_config_interval(self, client):
        """测试更新间隔"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            
            with patch(
                "openclaw_alpha.backend.config_api.get_iteration_config_path",
                return_value=config_path,
            ):
                # 更新间隔
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
        """创建测试客户端"""
        from openclaw_alpha.backend.main import app

        return TestClient(app)

    def test_get_config_default(self, client):
        """测试获取默认配置"""
        with patch(
            "openclaw_alpha.backend.feedback.config.get_feedback_config_path"
        ) as mock_path:
            mock_path.return_value = Path("/nonexistent/config.yaml")

            response = client.get("/api/config/feedback")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["interval_minutes"] == 30

    def test_update_config_enabled(self, client):
        """测试禁用反馈"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "feedback_config.yaml"

            with patch(
                "openclaw_alpha.backend.config_api.get_feedback_config_path",
                return_value=config_path,
            ):
                response = client.put(
                    "/api/config/feedback",
                    json={"enabled": False},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["enabled"] is False
