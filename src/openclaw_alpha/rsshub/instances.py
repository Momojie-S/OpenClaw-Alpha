# -*- coding: utf-8 -*-
"""RSSHub 实例配置"""

# RSSHub 公共实例列表（按优先级排序）
RSSHUB_INSTANCES = [
    "https://rsshub.liumingye.cn",
    # "https://rsshub.app",  # 官方实例已限制访问
]

# 投资相关 RSS 路由（按优先级排序）
INVESTMENT_ROUTES = [
    "/cls/telegraph",      # 财联社电报快讯 ⭐⭐⭐
    "/jin10",              # 金十数据快讯 ⭐⭐⭐
    "/wallstreetcn/news",  # 华尔街见闻资讯 ⭐⭐⭐
    "/yicai/brief",        # 第一财经简报 ⭐⭐
]
