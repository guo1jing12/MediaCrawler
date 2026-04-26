# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/config/__init__.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


# -*- coding: utf-8 -*-
"""
配置模块统一入口
向后兼容：保留原有 base_config.py 的导入方式
新增：支持统一配置中心
"""

# 保留原有导入（向后兼容）
from .base_config import *

# 新增统一配置中心
from .settings import CrawlerSettings, load_settings
from .schema import CrawlerConfigSchema, PlatformEnum, LoginTypeEnum, CrawlerTypeEnum
from .reloader import enable_hot_reload, disable_hot_reload, ConfigReloader

# 导出统一配置实例（懒加载）
_settings_instance = None

def get_settings() -> CrawlerSettings:
    """获取统一配置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = load_settings()
    return _settings_instance

def reload_settings() -> CrawlerSettings:
    """重新加载配置"""
    global _settings_instance
    _settings_instance = load_settings()
    return _settings_instance

__all__ = [
    # 原有导出（向后兼容）
    'PLATFORM', 'KEYWORDS', 'LOGIN_TYPE', 'COOKIES', 'CRAWLER_TYPE',
    'MAX_CONCURRENCY_NUM', 'CRAWLER_MAX_NOTES_COUNT', 'CRAWLER_MAX_SLEEP_SEC',
    'ENABLE_GET_COMMENTS', 'ENABLE_GET_SUB_COMMENTS', 'ENABLE_GET_MEIDAS',
    'ENABLE_IP_PROXY', 'ENABLE_MULTI_ACCOUNT', 'ACCOUNT_CONFIG_PATH',
    'ENABLE_RESUME_CRAWL', 'RESUME_CHECKPOINT_DIR', 'DISABLE_PLAYWRIGHT',
    'HEADLESS', 'SAVE_DATA_OPTION', 'SAVE_DATA_PATH',
    'ENABLE_CDP_MODE', 'CDP_DEBUG_PORT', 'CDP_HEADLESS',
    
    # 新增导出
    'CrawlerSettings', 'load_settings', 'get_settings', 'reload_settings',
    'CrawlerConfigSchema', 'PlatformEnum', 'LoginTypeEnum', 'CrawlerTypeEnum',
    'enable_hot_reload', 'disable_hot_reload', 'ConfigReloader',
]
from .db_config import *
