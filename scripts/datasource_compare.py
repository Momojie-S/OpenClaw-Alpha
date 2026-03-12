# -*- coding: utf-8 -*-
"""数据源对比工具 - 直接调用 AKShare 和 Tushare API 对比数据质量"""

import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Optional

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

try:
    import tushare as ts
    HAS_TUSHARE = True
except ImportError:
    HAS_TUSHARE = False


def fetch_akshare(date: str) -> dict:
    """
    使用 AKShare 获取涨停数据
    
    Args:
        date: 交易日期 (YYYYMMDD)
    
    Returns:
        数据结果
    """
    if not HAS_AKSHARE:
        return {"success": False, "error": "AKShare 未安装"}
    
    try:
        df = ak.stock_zt_pool_em(date=date)
        
        if df.empty:
            return {"success": True, "total": 0, "items": []}
        
        items = []
        for _, row in df.iterrows():
            items.append({
                "code": str(row.get("代码", "")),
                "name": str(row.get("名称", "")),
                "continuous": int(row.get("连板数", 1)),
                "limit_time": str(row.get("首次封板时间", "")),
                "industry": str(row.get("所属行业", "")),
            })
        
        return {
            "success": True,
            "total": len(items),
            "items": items,
            "has_limit_time": any(item["limit_time"] for item in items),
            "limit_time_count": sum(1 for item in items if item["limit_time"]),
            "codes": set(item["code"] for item in items),
            "continuous_stats": _calc_continuous_stats(items),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_tushare(date: str, token: Optional[str] = None) -> dict:
    """
    使用 Tushare 获取涨停数据
    
    Args:
        date: 交易日期 (YYYYMMDD)
        token: Tushare token
    
    Returns:
        数据结果
    """
    if not HAS_TUSHARE:
        return {"success": False, "error": "Tushare 未安装"}
    
    try:
        if token:
            ts.set_token(token)
        pro = ts.pro_api()
        
        df = pro.limit_list_d(trade_date=date, limit='U')
        
        if df is None or df.empty:
            return {"success": True, "total": 0, "items": []}
        
        items = []
        for _, row in df.iterrows():
            # 解析连板数
            up_stat = str(row.get("up_stat", ""))
            continuous = 1
            if up_stat:
                parts = up_stat.split("/")
                if parts:
                    try:
                        continuous = int(parts[0])
                    except ValueError:
                        continuous = 1
            
            items.append({
                "code": str(row.get("ts_code", ""))[:6],
                "name": str(row.get("name", "")),
                "continuous": continuous,
                "limit_time": "",  # Tushare 不提供
                "industry": str(row.get("industry", "")),
            })
        
        return {
            "success": True,
            "total": len(items),
            "items": items,
            "has_limit_time": any(item["limit_time"] for item in items),
            "limit_time_count": sum(1 for item in items if item["limit_time"]),
            "codes": set(item["code"] for item in items),
            "continuous_stats": _calc_continuous_stats(items),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _calc_continuous_stats(items: list) -> dict:
    """计算连板统计"""
    stats = {}
    for item in items:
        c = item["continuous"]
        key = c if c < 4 else 4
        stats[key] = stats.get(key, 0) + 1
    return stats


def compare_datasources(date: str, tushare_token: Optional[str] = None) -> dict:
    """
    对比两个数据源的数据
    
    Args:
        date: 交易日期 (YYYY-MM-DD)
        tushare_token: Tushare token
    
    Returns:
        对比结果
    """
    date_fmt = date.replace("-", "")
    
    results = {
        "date": date,
        "akshare": fetch_akshare(date_fmt),
        "tushare": fetch_tushare(date_fmt, tushare_token),
        "comparison": None,
    }
    
    # 对比结果
    ak = results["akshare"]
    ts = results["tushare"]
    
    if ak["success"] and ts["success"]:
        ak_codes = ak["codes"]
        ts_codes = ts["codes"]
        
        results["comparison"] = {
            "akshare_total": ak["total"],
            "tushare_total": ts["total"],
            "diff_count": abs(ak["total"] - ts["total"]),
            "same_codes": len(ak_codes & ts_codes),
            "akshare_only": len(ak_codes - ts_codes),
            "tushare_only": len(ts_codes - ak_codes),
            "akshare_has_limit_time": ak["has_limit_time"],
            "tushare_has_limit_time": ts["has_limit_time"],
        }
    
    return results


def format_output(results: dict) -> str:
    """格式化输出"""
    lines = []
    date = results["date"]
    
    lines.append(f"数据源对比报告 ({date})")
    lines.append("=" * 60)
    
    # AKShare 结果
    lines.append("\n【AKShare 数据源】")
    ak = results["akshare"]
    if ak["success"]:
        lines.append(f"  涨停数: {ak['total']}")
        lines.append(f"  有封板时间: {'是' if ak['has_limit_time'] else '否'} ({ak['limit_time_count']}/{ak['total']})")
        lines.append(f"  连板统计: {ak['continuous_stats']}")
        lines.append(f"  Top 5 龙头:")
        sorted_items = sorted(ak["items"], key=lambda x: x["continuous"], reverse=True)
        for item in sorted_items[:5]:
            limit_time = item["limit_time"] if item["limit_time"] else "无"
            lines.append(f"    {item['code']} {item['name']} {item['continuous']}板 封板时间: {limit_time}")
    else:
        lines.append(f"  ❌ 获取失败: {ak['error']}")
    
    # Tushare 结果
    lines.append("\n【Tushare 数据源】")
    ts = results["tushare"]
    if ts["success"]:
        lines.append(f"  涨停数: {ts['total']}")
        lines.append(f"  有封板时间: {'是' if ts['has_limit_time'] else '否'} ({ts['limit_time_count']}/{ts['total']})")
        lines.append(f"  连板统计: {ts['continuous_stats']}")
        lines.append(f"  Top 5 龙头:")
        sorted_items = sorted(ts["items"], key=lambda x: x["continuous"], reverse=True)
        for item in sorted_items[:5]:
            limit_time = item["limit_time"] if item["limit_time"] else "无"
            lines.append(f"    {item['code']} {item['name']} {item['continuous']}板 封板时间: {limit_time}")
    else:
        lines.append(f"  ❌ 获取失败: {ts['error']}")
    
    # 对比结果
    comp = results["comparison"]
    if comp:
        lines.append("\n【对比结果】")
        lines.append(f"  涨停数差异: {comp['diff_count']} (AKShare: {comp['akshare_total']}, Tushare: {comp['tushare_total']})")
        lines.append(f"  相同股票: {comp['same_codes']}")
        lines.append(f"  仅 AKShare: {comp['akshare_only']}")
        lines.append(f"  仅 Tushare: {comp['tushare_only']}")
        lines.append(f"  封板时间: AKShare {'✓' if comp['akshare_has_limit_time'] else '✗'}, Tushare {'✓' if comp['tushare_has_limit_time'] else '✗'}")
        
        # 推荐建议
        lines.append("\n【推荐建议】")
        if comp['akshare_has_limit_time'] and not comp['tushare_has_limit_time']:
            lines.append("  ✓ 推荐 AKShare：提供封板时间数据，适合龙头分析")
        elif not comp['akshare_has_limit_time'] and comp['tushare_has_limit_time']:
            lines.append("  ✓ 推荐 Tushare：提供封板时间数据")
        else:
            lines.append("  ✓ 两者数据质量相当，可按需选择")
        
        if comp['diff_count'] > 5:
            lines.append(f"  ⚠️  数据差异较大 ({comp['diff_count']} 只)，建议交叉验证")
    else:
        lines.append("\n【对比结果】")
        lines.append("  无法对比（至少一个数据源获取失败）")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="数据源对比工具")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="交易日期")
    parser.add_argument("--days", type=int, default=1, help="对比天数")
    parser.add_argument("--tushare-token", help="Tushare token")
    args = parser.parse_args()
    
    dates = []
    if args.days > 1:
        base_date = datetime.strptime(args.date, "%Y-%m-%d")
        for i in range(args.days):
            d = base_date - timedelta(days=i)
            dates.append(d.strftime("%Y-%m-%d"))
    else:
        dates = [args.date]
    
    for date in dates:
        results = compare_datasources(date, args.tushare_token)
        print(format_output(results))
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
