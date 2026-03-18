# -*- coding: utf-8 -*-
"""
提交用户反馈脚本

由智能体调用，收集用户反馈并保存到 feedback/ 目录。

关联文档：
- 设计文档：docs/design/feedback/skill-design.md
"""

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_feedback_id(content: str) -> str:
    """
    生成反馈 ID（content hash）

    Args:
        content: 反馈内容

    Returns:
        64位 SHA256 hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_current_time_iso() -> str:
    """获取当前时间（ISO 8601，Asia/Shanghai）"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat()


def construct_feedback_json(
    content: str,
    source_user: str,
    source_channel: str,
    source_session: str,
) -> dict:
    """
    构造反馈 JSON

    Args:
        content: 反馈内容
        source_user: 提交用户
        source_channel: 提交渠道
        source_session: 来源 session key

    Returns:
        反馈 JSON 字典
    """
    feedback_id = generate_feedback_id(content)
    submitted_at = get_current_time_iso()

    return {
        "id": feedback_id,
        "source_user": source_user,
        "source_channel": source_channel,
        "source_session": source_session,
        "submitted_at": submitted_at,
        "content": content,
        "status": "pending",
    }


def save_feedback_file(feedback: dict, feedback_dir: Path) -> Path:
    """
    保存反馈文件（原子写入）

    Args:
        feedback: 反馈 JSON 字典
        feedback_dir: 反馈目录

    Returns:
        保存的文件路径
    """
    # 生成文件名
    feedback_id = feedback["id"]
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{feedback_id[:12]}.json"
    file_path = feedback_dir / filename

    # 原子写入
    temp_file = file_path.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)

    # 原子重命名
    temp_file.replace(file_path)

    return file_path


def submit_feedback(
    content: str,
    source_user: str,
    source_channel: str,
    source_session: str,
    project_root: Path | None = None,
) -> dict:
    """
    提交用户反馈

    Args:
        content: 反馈内容
        source_user: 提交用户
        source_channel: 提交渠道
        source_session: 来源 session key
        project_root: 项目根目录（None 则自动检测）

    Returns:
        {"success": bool, "feedback_id": str, "file_path": str, "error": str | None}
    """
    try:
        # 检测项目根目录
        if project_root is None:
            # 从当前文件路径向上查找
            project_root = Path(__file__).parent.parent.parent.parent.parent

        # 确定反馈目录
        feedback_dir = project_root / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        # 构造反馈 JSON
        feedback = construct_feedback_json(
            content, source_user, source_channel, source_session
        )

        # 保存文件
        file_path = save_feedback_file(feedback, feedback_dir)

        logger.info(
            f"反馈已保存: {feedback['id']}, 路径: {file_path}, "
            f"用户: {source_user}, 渠道: {source_channel}"
        )

        return {
            "success": True,
            "feedback_id": feedback["id"],
            "file_path": str(file_path),
            "error": None,
        }

    except Exception as e:
        error_msg = f"保存反馈失败: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "feedback_id": "",
            "file_path": "",
            "error": error_msg,
        }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="提交用户反馈")
    parser.add_argument("--content", required=True, help="反馈内容")
    parser.add_argument("--source-user", required=True, help="提交用户")
    parser.add_argument("--source-channel", required=True, help="提交渠道")
    parser.add_argument("--source-session", required=True, help="来源 session key")

    args = parser.parse_args()

    # 提交反馈
    result = submit_feedback(
        content=args.content,
        source_user=args.source_user,
        source_channel=args.source_channel,
        source_session=args.source_session,
    )

    if result["success"]:
        print("✅ 反馈已保存")
        print(f"  ID: {result['feedback_id']}")
        print(f"  路径: {result['file_path']}")
    else:
        print(f"❌ 反馈保存失败")
        print(f"  错误: {result['error']}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    main()
