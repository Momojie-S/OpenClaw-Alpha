# -*- coding: utf-8 -*-
"""事件回顾调度测试"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from openclaw_alpha.backend.quick_news.event_review_config import (
    EventReviewConfig,
    load_event_review_config,
)


class TestEventReviewConfig:
    def test_defaults(self):
        config = EventReviewConfig()
        assert config.enabled is True
        assert config.schedule_time == "08:00"
        assert config.concurrency == 1

    def test_load_from_file(self, tmp_path):
        config_file = tmp_path / "event-review.yaml"
        config_file.write_text(
            "enabled: false\nschedule_time: '09:30'\nconcurrency: 3\n",
            encoding="utf-8",
        )
        config = load_event_review_config(config_file)
        assert config.enabled is False
        assert config.schedule_time == "09:30"
        assert config.concurrency == 3

    def test_load_missing_file(self, tmp_path):
        config = load_event_review_config(tmp_path / "nonexistent.yaml")
        assert config == EventReviewConfig()


class TestReviewScheduler:
    """测试 Scheduler 的 add_daily_job 方法"""

    @pytest.mark.asyncio
    async def test_add_daily_job(self):
        from openclaw_alpha.backend.scheduler import Scheduler, SchedulerConfig

        sched = Scheduler(SchedulerConfig())
        sched.start()

        sched.add_daily_job(
            lambda: None,
            job_id="test-daily",
            time_str="08:00",
        )

        jobs = sched.scheduler.get_jobs()
        job_ids = [j.id for j in jobs]
        assert "test-daily" in job_ids

        sched.shutdown()
