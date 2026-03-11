# -*- coding: utf-8 -*-
"""限售解禁风险监控 Processor 入口"""

import asyncio

from .restricted_release_processor import main

if __name__ == "__main__":
    asyncio.run(main())
