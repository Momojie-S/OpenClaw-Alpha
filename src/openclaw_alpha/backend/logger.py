# -*- coding: utf-8 -*-
"""统一日志模块"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


# 默认日志目录
DEFAULT_LOG_DIR = Path.home() / ".openclaw_alpha" / "logs"


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
) -> None:
    """
    初始化日志系统

    Args:
        log_level: 日志级别（DEBUG / INFO / WARNING / ERROR）
        log_dir: 日志目录（None 则使用默认目录 ~/.openclaw_alpha/logs/）
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 移除已有的处理器
    root_logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（按天轮转）
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "alpha-service.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称（通常用 __name__）
        log_file: 日志文件名（None 则使用默认文件）

    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)

    # 如果需要独立日志文件
    if log_file:
        log_dir = DEFAULT_LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = TimedRotatingFileHandler(
            filename=log_dir / log_file,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
