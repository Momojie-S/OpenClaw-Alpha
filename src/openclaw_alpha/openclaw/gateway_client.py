# -*- coding: utf-8 -*-
"""
OpenClaw Gateway HTTP 客户端

提供与 OpenClaw Gateway 的 HTTP API 通信。

关联文档：
- docs/openclaw/gateway.md
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# 默认 Gateway 地址
DEFAULT_GATEWAY_URL = "http://127.0.0.1:18789"

# 默认超时配置
DEFAULT_REQUEST_TIMEOUT = 30.0


@dataclass
class GatewayConfig:
    """Gateway 配置"""

    url: str = DEFAULT_GATEWAY_URL
    token: str = ""
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT

    @classmethod
    def from_openclaw_config(cls) -> "GatewayConfig":
        """从 OpenClaw 配置文件加载"""
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        if not config_path.exists():
            logger.warning(f"OpenClaw 配置文件不存在: {config_path}")
            return cls()

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            gateway_config = config.get("gateway", {})
            auth_config = gateway_config.get("auth", {})

            # 支持 token 和 password 两种认证模式
            token = auth_config.get("token", "")
            password = auth_config.get("password", "")

            return cls(
                url=f"http://127.0.0.1:{gateway_config.get('port', 18789)}",
                token=token or password,
            )
        except Exception as e:
            logger.error(f"加载 OpenClaw 配置失败: {e}")
            return cls()


@dataclass
class GatewayClient:
    """
    OpenClaw Gateway HTTP 客户端

    Features:
    - 使用 HTTP API 调用 Gateway 工具
    - 支持 Bearer token 认证
    - 连接复用

    Usage:
        client = GatewayClient(GatewayConfig.from_openclaw_config())

        # 调用工具
        result = await client.call_tool("cron", {"action": "list"})
        print(result)

        # 关闭连接
        await client.close()
    """

    config: GatewayConfig
    _client: httpx.AsyncClient | None = field(default=None, repr=False)

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            headers = {}
            if self.config.token:
                headers["Authorization"] = f"Bearer {self.config.token}"

            self._client = httpx.AsyncClient(
                base_url=self.config.url,
                headers=headers,
                timeout=self.config.request_timeout,
            )
        return self._client

    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Gateway HTTP 客户端已关闭")

    async def call_tool(
        self,
        tool: str,
        args: dict[str, Any] | None = None,
        *,
        action: str | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        调用 Gateway 工具

        Args:
            tool: 工具名（如 "cron"）
            args: 工具参数
            action: 操作类型（如 "list", "add"）
            timeout: 超时时间（秒）

        Returns:
            Gateway 响应数据
        """
        client = await self._get_client()

        body: dict[str, Any] = {"tool": tool}
        if args:
            body["args"] = args
        if action:
            body["action"] = action

        try:
            response = await client.post(
                "/tools/invoke",
                json=body,
                timeout=timeout or self.config.request_timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "ok": False,
                "error": {
                    "type": "http_error",
                    "message": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                },
            }
        except httpx.TimeoutException:
            return {"ok": False, "error": {"type": "timeout", "message": "请求超时"}}
        except Exception as e:
            return {"ok": False, "error": {"type": "error", "message": str(e)}}

    @property
    def is_connected(self) -> bool:
        """是否已连接（HTTP 客户端始终可用）"""
        return True


# 全局客户端实例
_gateway_client: GatewayClient | None = None


async def get_gateway_client() -> GatewayClient:
    """
    获取全局 Gateway 客户端实例

    Returns:
        GatewayClient 实例
    """
    global _gateway_client

    if _gateway_client is None:
        config = GatewayConfig.from_openclaw_config()
        _gateway_client = GatewayClient(config)

    return _gateway_client


async def close_gateway_client() -> None:
    """关闭全局 Gateway 客户端"""
    global _gateway_client

    if _gateway_client:
        await _gateway_client.close()
        _gateway_client = None
