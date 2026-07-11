"""core 层统一放置项目级基础能力，例如配置、日志、常量等。"""

from app.core.config import Settings, get_settings

# 统一导出，外部可以直接从 `app.core` 导入配置相关对象。
__all__ = ["Settings", "get_settings"]
