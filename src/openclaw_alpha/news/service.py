# -*- coding: utf-8 -*-
"""News CLI 业务逻辑层。"""

import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from openclaw_alpha.core.embedding import get_embedder
from openclaw_alpha.core.milvus import get_client
from openclaw_alpha.core.path_utils import get_runtime_dir
from openclaw_alpha.news.fetcher import fetch as fetcher_fetch, NewsItem
from openclaw_alpha.news.store import ensure_collection

_DEFAULT_DATA_DIR = get_runtime_dir() / "data"


def _news_dir(news_id: str, data_dir: Path | None = None) -> Path:
    d = (data_dir or _DEFAULT_DATA_DIR) / "news" / news_id
    return d


def _event_dir(event_id: str, data_dir: Path | None = None) -> Path:
    return (data_dir or _DEFAULT_DATA_DIR) / "events" / event_id


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_news_json(news_id: str, data_dir: Path | None = None) -> dict | None:
    return _read_json(_news_dir(news_id, data_dir) / "news.json")


def write_news_json(news_id: str, data: dict, data_dir: Path | None = None) -> None:
    _write_json(_news_dir(news_id, data_dir) / "news.json", data)


def read_content(news_id: str, data_dir: Path | None = None) -> str | None:
    p = _news_dir(news_id, data_dir) / "content.md"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def read_summary_vector(news_id: str, data_dir: Path | None = None) -> list[float] | None:
    d = _read_json(_news_dir(news_id, data_dir) / "summary_vector.json")
    if d is None:
        return None
    return d.get("vector")


def _save_news_item(item: NewsItem, data_dir: Path | None = None) -> bool:
    """保存单条新闻到本地。已存在则跳过。返回 True 表示新创建。"""
    nd = _news_dir(item.news_id, data_dir)
    news_json_path = nd / "news.json"
    if news_json_path.exists():
        return False

    nd.mkdir(parents=True, exist_ok=True)

    news_data = {
        "news_id": item.news_id,
        "title": item.title,
        "source": item.source,
        "link": item.url or "",
        "published": f"{item.date}T{item.time or '00:00:00'}" if item.date else "",
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
        "analysis_status": "pending",  # 新增：标记为待分析
    }
    _write_json(news_json_path, news_data)

    if item.content:
        (nd / "content.md").write_text(item.content, encoding="utf-8")

    return True


def _sync_to_milvus(news_id: str, data_dir: Path | None = None) -> None:
    """统一 Milvus 同步：读 news.json + summary_vector.json，有向量时 upsert。"""
    news = read_news_json(news_id, data_dir)
    if news is None:
        return
    vector = read_summary_vector(news_id, data_dir)
    if vector is None:
        return

    client = get_client()
    ensure_collection(client)
    entities = news.get("entities", "")
    # 确保 entities 是 string（兼容 list 格式）
    if isinstance(entities, list):
        entities = " ".join(entities)

    client.upsert(
        collection_name="news_items",
        data=[{
            "news_id": news_id,
            "summary_vector": vector,
            "event_id": news.get("event_id", ""),
            "entities": entities,
            "created_at": news.get("created_at", 0),
        }],
    )


def _build_entities(analysis: dict) -> str:
    """从 analysis 拼接 entities 字符串。"""
    parts = list(analysis.get("related_sectors", []))
    for company in analysis.get("related_companies", []):
        name = company.get("name", "")
        if name:
            parts.append(name)
    return " ".join(parts)


# ── 公开接口 ──


async def fetch_and_save(
    source: str = "cls_global",
    symbol: str | None = None,
    keyword: str | None = None,
    date: str | None = None,
    limit: int = 20,
    data_dir: Path | None = None,
) -> dict:
    """拉取新闻并落盘。"""
    result = await fetcher_fetch(
        source=source, symbol=symbol, keyword=keyword, date=date, limit=limit
    )

    saved_list: list[str] = []
    skipped_list: list[str] = []
    news_output: list[dict] = []

    for item in result.news:
        created = _save_news_item(item, data_dir)
        if created:
            saved_list.append(item.news_id)
            nd = _news_dir(item.news_id, data_dir)
            content = read_content(item.news_id, data_dir) or ""
            news_output.append({
                "news_id": item.news_id,
                "news_dir": str(nd.resolve()),
                "title": item.title,
                "link": item.url or "",
                "content": content,
                "analysis_status": "pending",  # 新增：标记为待分析
                "saved": True,
                "skipped": False,
            })
        else:
            skipped_list.append(item.news_id)
            news_output.append({
                "news_id": item.news_id,
                "saved": False,
                "skipped": True,
            })

    return {
        "source": result.source,
        "total": result.total,
        "saved": len(saved_list),
        "skipped": len(skipped_list),
        "news": news_output,
    }


def update_news(
    news_id: str,
    summary: str | None = None,
    analysis: dict | None = None,
    event_id: str | None = None,
    data_dir: Path | None = None,
) -> dict:
    """更新新闻字段，统一 sync 一次。"""
    news = read_news_json(news_id, data_dir)
    if news is None:
        return {"error": f"news_id {news_id} not found"}

    # --summary: 生成 embedding
    if summary is not None:
        embedder = get_embedder()
        vector = embedder.embed(summary)
        _write_json(
            _news_dir(news_id, data_dir) / "summary_vector.json",
            {"vector": vector},
        )
        news["summary"] = summary

    # --analysis: 更新 analysis + entities
    if analysis is not None:
        news["analysis"] = analysis
        news["entities"] = _build_entities(analysis)

    # --event-id: 双向关联
    if event_id is not None:
        event_path = _event_dir(event_id, data_dir) / "event.json"
        event = _read_json(event_path)
        if event is None:
            return {"error": f"event_id {event_id} not found"}

        news["event_id"] = event_id

        # 追加 news_id 到 event.json.news_ids（幂等）
        now = _now_iso()
        existing_ids = {n["news_id"] for n in event.get("news_ids", [])}
        if news_id not in existing_ids:
            event.setdefault("news_ids", []).append(
                {"news_id": news_id, "timestamp": now}
            )
            event["updated_at"] = now
            _write_json(event_path, event)

    news["updated_at"] = int(time.time())
    write_news_json(news_id, news, data_dir)

    # 统一 sync 一次
    _sync_to_milvus(news_id, data_dir)

    return {"news_id": news_id, "updated": True}


def search_similar(
    news_id: str, top: int = 10, data_dir: Path | None = None
) -> dict:
    """向量搜索相似新闻。"""
    news = read_news_json(news_id, data_dir)
    if news is None:
        return {"error": f"news_id {news_id} not found"}

    vector = read_summary_vector(news_id, data_dir)
    if vector is None:
        return {"error": f"news_id {news_id} has no summary_vector yet"}

    client = get_client()
    ensure_collection(client)

    results = client.search(
        collection_name="news_items",
        data=[vector],
        anns_field="summary_vector",
        limit=top + 1,  # 多取一个排除自己
        output_fields=["news_id", "event_id"],
    )

    out = []
    for hit in results[0]:
        hit_id = hit["entity"]["news_id"]
        if hit_id == news_id:
            continue
        news_data = read_news_json(hit_id, data_dir)
        out.append({
            "news_id": hit_id,
            "event_id": hit["entity"].get("event_id", ""),
            "score": hit["distance"],
            "summary": news_data.get("summary", "") if news_data else "",
        })
        if len(out) >= top:
            break

    return {"results": out}


def search_keyword(
    keyword: str, top: int = 10, data_dir: Path | None = None
) -> dict:
    """BM25 关键词搜索。"""
    client = get_client()
    ensure_collection(client)

    results = client.search(
        collection_name="news_items",
        data=[keyword],
        anns_field="entities_vector",
        limit=top,
        output_fields=["news_id", "entities"],
    )

    out = []
    for hit in results[0]:
        hit_id = hit["entity"]["news_id"]
        news_data = read_news_json(hit_id, data_dir)
        if news_data is None:
            continue
        out.append({
            "news_id": hit_id,
            "summary": news_data.get("summary", ""),
            "entities": hit["entity"].get("entities", ""),
            "score": hit["distance"],
        })

    return {"results": out}


def get_news(
    news_id: str,
    fields: list[str] | None = None,
    data_dir: Path | None = None,
) -> dict:
    """获取新闻字段。"""
    news = read_news_json(news_id, data_dir)
    if news is None:
        return {"error": f"news_id {news_id} not found"}

    nd = str(_news_dir(news_id, data_dir).resolve())

    if fields is None:
        news["news_dir"] = nd
        return news

    result = {}
    for f in fields:
        if f == "content":
            content = read_content(news_id, data_dir)
            result["content"] = content or ""
        elif f in news:
            result[f] = news[f]
    return result


def _now_iso() -> str:
    """当前时间 ISO 8601 字符串（东八区）。"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat()


def _gen_event_id() -> str:
    """生成 event_id: evt_{timestamp}_{random4}。"""
    ts = int(time.time())
    rand = hashlib.md5(str(ts).encode()).hexdigest()[:4]
    return f"evt_{ts}_{rand}"


def create_event(
    title: str,
    news_id: str,
    data_dir: Path | None = None,
) -> dict:
    """创建事件并双向关联首条新闻。"""
    # 校验 news_id 存在
    news = read_news_json(news_id, data_dir)
    if news is None:
        return {"error": f"news_id {news_id} not found"}

    now = _now_iso()
    event_id = _gen_event_id()
    event = {
        "event_id": event_id,
        "title": title,
        "status": "ongoing",
        "news_ids": [{"news_id": news_id, "timestamp": now}],
        "created_at": now,
        "updated_at": now,
    }
    _write_json(_event_dir(event_id, data_dir) / "event.json", event)

    # 双向：更新 news.json 的 event_id
    news["event_id"] = event_id
    write_news_json(news_id, news, data_dir)

    return event


def close_event(
    event_id: str, data_dir: Path | None = None
) -> dict:
    """关闭事件。"""
    event_path = _event_dir(event_id, data_dir) / "event.json"
    event = _read_json(event_path)
    if event is None:
        return {"error": f"event_id {event_id} not found"}
    if event.get("status") == "closed":
        return {"error": f"event {event_id} already closed"}

    event["status"] = "closed"
    event["updated_at"] = _now_iso()
    _write_json(event_path, event)
    return event


def list_events(
    status: str | None = None,
    limit: int = 50,
    data_dir: Path | None = None,
) -> dict:
    """列出事件，按 updated_at 降序。"""
    events_dir = (data_dir or _DEFAULT_DATA_DIR) / "events"
    if not events_dir.exists():
        return {"events": []}

    events = []
    for d in events_dir.iterdir():
        if not d.is_dir():
            continue
        event = _read_json(d / "event.json")
        if event is None:
            continue
        if status and event.get("status") != status:
            continue
        events.append(event)

    # 按 updated_at 降序
    events.sort(key=lambda e: e.get("updated_at", ""), reverse=True)
    events = events[:limit]
    return {"events": events}


def get_event(
    event_id: str, data_dir: Path | None = None
) -> dict:
    """获取事件信息。"""
    event = _read_json(_event_dir(event_id, data_dir) / "event.json")
    if event is None:
        return {"error": f"event_id {event_id} not found"}
    return event
