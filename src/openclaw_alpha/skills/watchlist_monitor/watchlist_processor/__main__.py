# -*- coding: utf-8 -*-
"""自选股监控 Processor 入口"""

import asyncio

from .watchlist_processor import main

if __name__ == "__main__":
    asyncio.run(main())
