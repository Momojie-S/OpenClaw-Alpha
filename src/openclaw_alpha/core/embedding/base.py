"""Embedder 抽象基类。"""

from abc import ABC, abstractmethod


class Embedder(ABC):
    """向量生成器抽象接口。"""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """将文本转换为向量。

        Args:
            text: 输入文本

        Returns:
            浮点数向量
        """
        ...
