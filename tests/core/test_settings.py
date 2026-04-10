# -*- coding: utf-8 -*-
"""Settings 统一配置管理测试"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from openclaw_alpha.core.settings import Settings


@pytest.fixture
def config_dir(tmp_path):
    """创建临时配置目录"""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    config = {
        "tushare": {"credit_limit": 200},
        "quick_news": {"enabled": True, "interval_minutes": 30},
        "feedback": {"enabled": True, "interval_minutes": 30},
        "event_review": {"enabled": True, "schedule_time": "08:00"},
    }
    (runtime / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


@pytest.fixture
def env_vars():
    """设置测试环境变量"""
    env = {
        "TUSHARE_TOKEN": "test_token",
        "TUSHARE_CREDIT": "100",
        "DASHSCOPE_API_KEY": "test_dashscope",
        "MILVUS_URI": "http://localhost:19530",
        "MILVUS_TOKEN": "test_milvus",
    }
    with patch.dict(os.environ, env, clear=False):
        yield env


class TestSettings:
    def test_load_config(self, config_dir, env_vars):
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}):
            s = Settings()
            assert s.quick_news["enabled"] is True
            assert s.event_review["schedule_time"] == "08:00"

    def test_credentials_from_env(self, config_dir, env_vars):
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}):
            s = Settings()
            assert s.tushare_token == "test_token"
            assert s.tushare_credit == 100
            assert s.dashscope_api_key == "test_dashscope"
            assert s.milvus_uri == "http://localhost:19530"
            assert s.milvus_token == "test_milvus"

    def test_missing_credential_raises(self, config_dir):
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}, clear=False):
            s = Settings()
            # 清除环境变量
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="TUSHARE_TOKEN"):
                    _ = Settings().tushare_token

    def test_default_credit(self, config_dir):
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}, clear=False):
            s = Settings()
            with patch.dict(os.environ, {}, clear=True):
                assert Settings().tushare_credit == 0

    def test_missing_config_file(self, tmp_path):
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(tmp_path)}):
            s = Settings()
            with pytest.raises(FileNotFoundError):
                _ = s.quick_news

    def test_project_root_from_env(self, tmp_path):
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(tmp_path)}):
            s = Settings()
            assert s.project_root == tmp_path

    def test_defaults_inheritance(self, config_dir, env_vars):
        """模块缺省字段从 defaults 继承"""
        config = {
            "defaults": {"agent_id": "main", "model": "test-model"},
            "quick_news": {"enabled": True},
        }
        runtime = config_dir / "runtime"
        (runtime / "config.json").write_text(json.dumps(config), encoding="utf-8")
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}):
            s = Settings()
            assert s.quick_news["agent_id"] == "main"
            assert s.quick_news["model"] == "test-model"

    def test_defaults_module_override(self, config_dir, env_vars):
        """模块自身值优先于 defaults"""
        config = {
            "defaults": {"agent_id": "main", "model": "default-model"},
            "feedback": {"agent_id": "alpha", "enabled": True},
        }
        runtime = config_dir / "runtime"
        (runtime / "config.json").write_text(json.dumps(config), encoding="utf-8")
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}):
            s = Settings()
            assert s.feedback["agent_id"] == "alpha"
            assert s.feedback["model"] == "default-model"  # 继承

    def test_no_defaults(self, config_dir, env_vars):
        """无 defaults 时配置保持原样"""
        config = {"quick_news": {"enabled": True, "agent_id": "custom"}}
        runtime = config_dir / "runtime"
        (runtime / "config.json").write_text(json.dumps(config), encoding="utf-8")
        with patch.dict(os.environ, {"OPENCLAW_ALPHA_ROOT": str(config_dir)}):
            s = Settings()
            assert s.quick_news["agent_id"] == "custom"
            assert "model" not in s.quick_news

    def test_project_root_inferred(self):
        with patch.dict(os.environ, {}, clear=True):
            s = Settings()
            # 应该推断到项目根目录
            assert (s.project_root / "src").exists()
