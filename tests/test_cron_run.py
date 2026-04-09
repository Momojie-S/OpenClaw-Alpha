# -*- coding: utf-8 -*-
"""测试 cron.run 的 await vs fire-and-forget 行为差异"""

import asyncio
import time
import sys
import logging

sys.path.insert(0, "src")

from openclaw_alpha.openclaw.gateway_client import get_gateway_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def test_await_vs_fire_and_forget():
    client = await get_gateway_client()

    # ========== Test 1: await 模式（旧版行为）==========
    logger.info("===== Test 1: await 模式 =====")

    # 创建一个简单任务
    job1 = await client.call_tool("cron", {
        "action": "add",
        "name": "test-await",
        "agentId": "main",
        "sessionTarget": "isolated",
        "schedule": {"kind": "at", "at": "2099-01-01T00:00:00Z"},  # 远期，不会自动触发
        "payload": {"kind": "agentTurn", "message": "回复 OK 两个字即可", "thinking": "low", "timeoutSeconds": 60},
        "delivery": {"mode": "none"},
        "enabled": True,
    })
    job1_id = job1.get("result", {}).get("details", {}).get("id", "")
    logger.info(f"Test1 任务创建: {job1_id}")

    # await 同步触发
    t0 = time.monotonic()
    run1 = await client.call_tool("cron", {"action": "run", "jobId": job1_id}, timeout=120.0)
    elapsed1 = time.monotonic() - t0
    logger.info(f"Test1 await run 完成: elapsed={elapsed1:.1f}s, ok={run1.get('ok')}")
    logger.info(f"Test1 run response keys: {list(run1.get('result', {}).keys())}")
    logger.info(f"Test1 sessionId: {run1.get('result', {}).get('sessionId')}")
    logger.info(f"Test1 sessionKey: {run1.get('result', {}).get('sessionKey')}")

    # 清理
    await client.call_tool("cron", {"action": "remove", "jobId": job1_id}, timeout=10.0)
    logger.info(f"Test1 任务已删除")

    # 等 2 秒
    await asyncio.sleep(2)

    # ========== Test 2: fire-and-forget 模式（新版行为）==========
    logger.info("===== Test 2: fire-and-forget 模式 =====")

    job2 = await client.call_tool("cron", {
        "action": "add",
        "name": "test-fire-forget",
        "agentId": "main",
        "sessionTarget": "isolated",
        "schedule": {"kind": "at", "at": "2099-01-01T00:00:00Z"},
        "payload": {"kind": "agentTurn", "message": "回复 OK 两个字即可", "thinking": "low", "timeoutSeconds": 60},
        "delivery": {"mode": "none"},
        "enabled": True,
    })
    job2_id = job2.get("result", {}).get("details", {}).get("id", "")
    logger.info(f"Test2 任务创建: {job2_id}")

    # fire-and-forget
    fire_result = {"done": False, "response": None}

    async def _fire():
        try:
            resp = await client.call_tool("cron", {"action": "run", "jobId": job2_id}, timeout=120.0)
            fire_result["done"] = True
            fire_result["response"] = resp
            logger.info(f"Test2 后台 run 完成: ok={resp.get('ok')}, sessionId={resp.get('result', {}).get('sessionId')}")
        except Exception as e:
            fire_result["done"] = True
            fire_result["error"] = str(e)
            logger.error(f"Test2 后台 run 异常: {e}")

    task = asyncio.create_task(_fire())
    logger.info(f"Test2 fire-and-forget 已发出，不等结果")

    # 轮询 cron.runs 看任务是否被执行
    logger.info("Test2 开始轮询 cron.runs...")
    for i in range(30):
        await asyncio.sleep(2)
        runs = await client.call_tool("cron", {"action": "runs", "jobId": job2_id}, timeout=10.0)
        entries = runs.get("result", {}).get("details", {}).get("entries", [])
        if entries:
            latest = entries[0]
            logger.info(f"Test2 第{i+1}次轮询: status={latest.get('status')}, durationMs={latest.get('durationMs')}")
            if latest.get("status") in ("ok", "error"):
                break
        else:
            logger.info(f"Test2 第{i+1}次轮询: 无 entries")

    logger.info(f"Test2 fire-and-forget task 状态: done={fire_result['done']}")

    # 清理
    await client.call_tool("cron", {"action": "remove", "jobId": job2_id}, timeout=10.0)
    logger.info("Test2 任务已删除")

    # ========== 对比总结 ==========
    logger.info("===== 对比总结 =====")
    logger.info(f"await 模式: 直接返回 sessionId 和 sessionKey，耗时 {elapsed1:.1f}s")
    logger.info(f"fire-and-forget 模式: 需要轮询 runs 来获取结果")


if __name__ == "__main__":
    asyncio.run(test_await_vs_fire_and_forget())
