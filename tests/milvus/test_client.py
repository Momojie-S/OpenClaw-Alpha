"""Milvus 连接管理测试。"""

import os
from unittest.mock import MagicMock, patch

import pytest

from openclaw_alpha.milvus.client import close, get_client


def _make_mock_client():
    return MagicMock()


@pytest.fixture(autouse=True)
def _reset_client():
    """每个测试前后重置单例。"""
    close()
    yield
    close()


class TestGetClientSingleton:
    """get_client() 单例测试。"""

    def test_returns_same_instance(self, monkeypatch):
        monkeypatch.setenv("MILVUS_URI", "http://localhost:19530")
        monkeypatch.setenv("MILVUS_TOKEN", "root:Milvus")

        mock = _make_mock_client()
        with patch("openclaw_alpha.milvus.client.MilvusClient", return_value=mock):
            client1 = get_client()
            client2 = get_client()
            assert client1 is mock
            assert client2 is mock


class TestEnvVarValidation:
    """环境变量缺失测试。"""

    def test_missing_uri(self, monkeypatch):
        monkeypatch.delenv("MILVUS_URI", raising=False)
        monkeypatch.delenv("MILVUS_TOKEN", raising=False)

        with pytest.raises(ValueError, match="MILVUS_URI"):
            get_client()

    def test_missing_token(self, monkeypatch):
        monkeypatch.setenv("MILVUS_URI", "http://localhost:19530")
        monkeypatch.delenv("MILVUS_TOKEN", raising=False)

        with pytest.raises(ValueError, match="MILVUS_TOKEN"):
            get_client()


class TestClose:
    def test_close_then_get_new_instance(self, monkeypatch):
        monkeypatch.setenv("MILVUS_URI", "http://localhost:19530")
        monkeypatch.setenv("MILVUS_TOKEN", "root:Milvus")

        mock1 = _make_mock_client()
        mock2 = _make_mock_client()
        with patch("openclaw_alpha.milvus.client.MilvusClient", side_effect=[mock1, mock2]):
            client1 = get_client()
            assert client1 is mock1
            close()
            client2 = get_client()
            assert client2 is mock2
            assert client1 is not client2

    def test_close_when_no_client(self):
        # 未初始化时 close 不报错
        close()


@pytest.mark.skipif(
    not os.environ.get("MILVUS_URI") or not os.environ.get("MILVUS_TOKEN"),
    reason="需要 .env 中配置 MILVUS_URI 和 MILVUS_TOKEN",
)
class TestRealConnection:
    """真实连接测试（需要 .env 配置，通过 uv run --env-file .env 运行）。"""

    def test_list_collections(self):
        client = get_client()
        result = client.list_collections()
        assert isinstance(result, list)
