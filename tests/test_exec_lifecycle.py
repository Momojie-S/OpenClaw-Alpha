# -*- coding: utf-8 -*-
"""
测试：验证 exec 进程在轮询期间是否会被杀掉

模拟 news debug-quick-news 的行为：
1. exec 启动进程（yieldMs=30s, timeout=900s）
2. 进程做短暂的初始化工作（~5s）
3. 进程进入长时间轮询循环（每10秒一次，持续5分钟）
4. 不对进程做任何 process poll/log 操作
5. 等待 5 分钟后检查进程是否存活、是否正常完成
"""

import asyncio
import json
import time
import sys
import logging

sys.path.insert(0, "src")

from openclaw_alpha.openclaw.gateway_client import get_gateway_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("tests/test_exec_lifecycle.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    client = await get_gateway_client()
    log_file = "tests/test_exec_lifecycle_result.json"

    # 创建 cron 任务（用远期 schedule 防止自动触发）
    trigger_time = int((time.time() + 600) * 1000)
    add_params = {
        "action": "add",
        "name": "test-exec-lifecycle",
        "agentId": "main",
        "sessionTarget": "isolated",
        "sessionKey": "agent:main:cron:test-exec-lifecycle",
        "schedule": {"kind": "at", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(trigger_time / 1000))},
        "payload": {
            "kind": "agentTurn",
            "message": "回复OK两个字即可",
            "thinking": "low",
            "timeoutSeconds": 60,
            "model": "zai/glm-5.1",
        },
        "enabled": True,
        "delivery": {"mode": "none"},
    }

    r = await client.call_tool("cron", add_params, timeout=30.0)
    job_id = r.get("result", {}).get("details", {}).get("id", "")
    logger.info(f"任务创建: {job_id}")

    if not job_id:
        logger.error(f"创建失败: {json.dumps(r, ensure_ascii=False)[:500]}")
        return

    # 触发任务
    run_r = await client.call_tool("cron", {"action": "run", "jobId": job_id}, timeout=30.0)
    logger.info(f"任务已触发: enqueued={run_r.get('result',{}).get('details',{}).get('enqueued')}")

    # 轮询（和 task_executor.py 的 _poll_job_completion 一样的逻辑）
    poll_start = time.monotonic()
    max_duration = 300  # 最多等 5 分钟
    poll_interval = 10
    poll_count = 0
    completed = False
    last_error = None

    logger.info(f"开始轮询（最长 {max_duration}s，间隔 {poll_interval}s）")

    while (time.monotonic() - poll_start) < max_duration:
        poll_count += 1
        try:
            runs = await client.call_tool(
                "cron", {"action": "runs", "jobId": job_id}, timeout=10.0
            )
            entries = runs.get("result", {}).get("details", {}).get("entries", [])
            elapsed = time.monotonic() - poll_start

            if entries:
                status = entries[0].get("status")
                logger.info(f"轮询 #{poll_count} ({elapsed:.0f}s): status={status}")
                if status in ("ok", "error"):
                    completed = True
                    break
            else:
                logger.info(f"轮询 #{poll_count} ({elapsed:.0f}s): 无 entries")

        except Exception as e:
            elapsed = time.monotonic() - poll_start
            last_error = str(e)
            logger.error(f"轮询 #{poll_count} ({elapsed:.0f}s) 异常: {e}")

        await asyncio.sleep(poll_interval)

    total_elapsed = time.monotonic() - poll_start

    # 清理
    await client.call_tool("cron", {"action": "remove", "jobId": job_id}, timeout=10.0)

    # 写结果
    result = {
        "job_id": job_id,
        "completed": completed,
        "poll_count": poll_count,
        "total_elapsed_seconds": round(total_elapsed, 1),
        "last_error": last_error,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(log_file, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"===== 结果 =====")
    logger.info(f"完成: {completed}")
    logger.info(f"轮询次数: {poll_count}")
    logger.info(f"总耗时: {total_elapsed:.1f}s")
    logger.info(f"最后错误: {last_error}")
    logger.info(f"结果已写入: {log_file}")

    if completed:
        logger.info("✅ 进程在整个轮询期间存活，exec 未杀进程")
    else:
        logger.error("❌ 轮询未完成（超时或异常），可能 exec 杀了进程或 HTTP 连接断了")


if __name__ == "__main__":
    asyncio.run(main())
