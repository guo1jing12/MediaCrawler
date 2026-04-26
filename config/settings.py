# -*- coding: utf-8 -*-
"""
统一配置中心
支持：环境变量 > 命令行 > accounts.json > base_config.py > 默认值
"""

import os
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import config


@dataclass
class CrawlerSettings:
    """爬虫统一配置"""
    
    # 基础配置
    platform: str = "xhs"
    keywords: str = ""
    login_type: str = "qrcode"
    cookies: str = ""
    crawler_type: str = "search"
    
    # 性能配置
    max_concurrency_num: int = 1
    crawler_max_notes_count: int = 15
    crawler_max_sleep_sec: int = 2
    start_page: int = 1
    
    # 功能开关
    enable_get_comments: bool = True
    enable_get_sub_comments: bool = False
    enable_get_medias: bool = False
    enable_ip_proxy: bool = False
    enable_get_wordcloud: bool = False
    
    # 多账号
    enable_multi_account: bool = False
    account_config_path: str = "config/accounts.json"
    account_name: str = "default"
    account_user_agent: str = ""
    account_proxy: str = ""
    
    # 断点续爬
    enable_resume_crawl: bool = False
    resume_checkpoint_dir: str = "data/checkpoints"
    resume_checkpoint_file: str = ""
    
    # 运行时
    disable_playwright: bool = False
    headless: bool = False
    save_data_option: str = "jsonl"
    save_data_path: str = ""
    save_login_state: bool = True
    
    # CDP
    enable_cdp_mode: bool = True
    cdp_debug_port: int = 9222
    cdp_headless: bool = False
    cdp_connect_existing: bool = True
    custom_browser_path: str = ""
    browser_launch_timeout: int = 60
    auto_close_browser: bool = True
    
    # 代理
    ip_proxy_pool_count: int = 2
    ip_proxy_provider_name: str = "kuaidaili"
    
    # 小红书特有
    xhs_international: bool = False
    
    # 其他
    disable_ssl_verify: bool = False
    
    @classmethod
    def from_defaults(cls) -> "CrawlerSettings":
        """从默认值创建"""
        return cls()
    
    @classmethod
    def from_base_config(cls) -> "CrawlerSettings":
        """从 base_config.py 加载"""
        settings = cls()
        
        # 映射 base_config.py 中的变量
        mappings = {
            'platform': 'PLATFORM',
            'keywords': 'KEYWORDS',
            'login_type': 'LOGIN_TYPE',
            'cookies': 'COOKIES',
            'crawler_type': 'CRAWLER_TYPE',
            'max_concurrency_num': 'MAX_CONCURRENCY_NUM',
            'crawler_max_notes_count': 'CRAWLER_MAX_NOTES_COUNT',
            'crawler_max_sleep_sec': 'CRAWLER_MAX_SLEEP_SEC',
            'start_page': 'START_PAGE',
            'enable_get_comments': 'ENABLE_GET_COMMENTS',
            'enable_get_sub_comments': 'ENABLE_GET_SUB_COMMENTS',
            'enable_get_medias': 'ENABLE_GET_MEIDAS',
            'enable_ip_proxy': 'ENABLE_IP_PROXY',
            'enable_get_wordcloud': 'ENABLE_GET_WORDCLOUD',
            'enable_multi_account': 'ENABLE_MULTI_ACCOUNT',
            'account_config_path': 'ACCOUNT_CONFIG_PATH',
            'account_name': 'ACCOUNT_NAME',
            'account_user_agent': 'ACCOUNT_USER_AGENT',
            'account_proxy': 'ACCOUNT_PROXY',
            'enable_resume_crawl': 'ENABLE_RESUME_CRAWL',
            'resume_checkpoint_dir': 'RESUME_CHECKPOINT_DIR',
            'resume_checkpoint_file': 'RESUME_CHECKPOINT_FILE',
            'disable_playwright': 'DISABLE_PLAYWRIGHT',
            'headless': 'HEADLESS',
            'save_data_option': 'SAVE_DATA_OPTION',
            'save_data_path': 'SAVE_DATA_PATH',
            'save_login_state': 'SAVE_LOGIN_STATE',
            'enable_cdp_mode': 'ENABLE_CDP_MODE',
            'cdp_debug_port': 'CDP_DEBUG_PORT',
            'cdp_headless': 'CDP_HEADLESS',
            'cdp_connect_existing': 'CDP_CONNECT_EXISTING',
            'custom_browser_path': 'CUSTOM_BROWSER_PATH',
            'browser_launch_timeout': 'BROWSER_LAUNCH_TIMEOUT',
            'auto_close_browser': 'AUTO_CLOSE_BROWSER',
            'ip_proxy_pool_count': 'IP_PROXY_POOL_COUNT',
            'ip_proxy_provider_name': 'IP_PROXY_PROVIDER_NAME',
            'xhs_international': 'XHS_INTERNATIONAL',
            'disable_ssl_verify': 'DISABLE_SSL_VERIFY',
        }
        
        for attr_name, config_name in mappings.items():
            if hasattr(config, config_name):
                value = getattr(config, config_name)
                setattr(settings, attr_name, value)
        
        return settings
    
    @classmethod
    def from_env(cls) -> "CrawlerSettings":
        """从环境变量加载（MC_ 前缀）"""
        settings = cls()
        
        for key, value in os.environ.items():
            if key.startswith("MC_"):
                attr_name = key[3:].lower()
                # 处理带下划线的属性名
                attr_name = attr_name.replace('_', '_')
                if hasattr(settings, attr_name):
                    current_value = getattr(settings, attr_name)
                    converted = _convert_type(value, current_value)
                    setattr(settings, attr_name, converted)
        
        return settings
    
    @classmethod
    def from_json_file(cls, path: str) -> "CrawlerSettings":
        """从 JSON 文件加载"""
        settings = cls()
        
        if not os.path.exists(path):
            return settings
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 支持两种格式：直接配置对象或 accounts 数组
        if isinstance(data, dict):
            if "accounts" in data:
                # accounts.json 格式，取第一个启用的账号
                accounts = data.get("accounts", [])
                enabled = [a for a in accounts if a.get("enabled", True)]
                if enabled:
                    account = enabled[0]
                    _apply_account_to_settings(settings, account)
            else:
                # 直接配置对象
                for key, value in data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
        
        return settings
    
    def validate(self) -> List[str]:
        """配置校验，返回错误列表"""
        errors = []
        
        valid_platforms = ("xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu")
        if self.platform not in valid_platforms:
            errors.append(f"platform must be one of {valid_platforms}, got: {self.platform}")
        
        valid_login_types = ("qrcode", "phone", "cookie")
        if self.login_type not in valid_login_types:
            errors.append(f"login_type must be one of {valid_login_types}, got: {self.login_type}")
        
        valid_crawler_types = ("search", "detail", "creator")
        if self.crawler_type not in valid_crawler_types:
            errors.append(f"crawler_type must be one of {valid_crawler_types}, got: {self.crawler_type}")
        
        if self.max_concurrency_num < 1:
            errors.append(f"max_concurrency_num must be >= 1, got: {self.max_concurrency_num}")
        
        if self.crawler_max_notes_count < 1:
            errors.append(f"crawler_max_notes_count must be >= 1, got: {self.crawler_max_notes_count}")
        
        if self.crawler_max_sleep_sec < 0:
            errors.append(f"crawler_max_sleep_sec must be >= 0, got: {self.crawler_max_sleep_sec}")
        
        valid_save_options = ("csv", "db", "json", "jsonl", "sqlite", "excel", "postgres", "mongodb")
        if self.save_data_option not in valid_save_options:
            errors.append(f"save_data_option must be one of {valid_save_options}, got: {self.save_data_option}")
        
        # API-only 模式校验
        if self.disable_playwright and self.login_type != "cookie" and not self.enable_multi_account:
            errors.append("disable_playwright requires cookie login or multi-account mode")
        
        return errors
    
    def apply_to_config(self) -> None:
        """将设置应用回 config 模块（向后兼容）"""
        mappings = {
            'PLATFORM': 'platform',
            'KEYWORDS': 'keywords',
            'LOGIN_TYPE': 'login_type',
            'COOKIES': 'cookies',
            'CRAWLER_TYPE': 'crawler_type',
            'MAX_CONCURRENCY_NUM': 'max_concurrency_num',
            'CRAWLER_MAX_NOTES_COUNT': 'crawler_max_notes_count',
            'CRAWLER_MAX_SLEEP_SEC': 'crawler_max_sleep_sec',
            'START_PAGE': 'start_page',
            'ENABLE_GET_COMMENTS': 'enable_get_comments',
            'ENABLE_GET_SUB_COMMENTS': 'enable_get_sub_comments',
            'ENABLE_GET_MEIDAS': 'enable_get_medias',
            'ENABLE_IP_PROXY': 'enable_ip_proxy',
            'ENABLE_GET_WORDCLOUD': 'enable_get_wordcloud',
            'ENABLE_MULTI_ACCOUNT': 'enable_multi_account',
            'ACCOUNT_CONFIG_PATH': 'account_config_path',
            'ACCOUNT_NAME': 'account_name',
            'ACCOUNT_USER_AGENT': 'account_user_agent',
            'ACCOUNT_PROXY': 'account_proxy',
            'ENABLE_RESUME_CRAWL': 'enable_resume_crawl',
            'RESUME_CHECKPOINT_DIR': 'resume_checkpoint_dir',
            'RESUME_CHECKPOINT_FILE': 'resume_checkpoint_file',
            'DISABLE_PLAYWRIGHT': 'disable_playwright',
            'HEADLESS': 'headless',
            'SAVE_DATA_OPTION': 'save_data_option',
            'SAVE_DATA_PATH': 'save_data_path',
            'SAVE_LOGIN_STATE': 'save_login_state',
            'ENABLE_CDP_MODE': 'enable_cdp_mode',
            'CDP_DEBUG_PORT': 'cdp_debug_port',
            'CDP_HEADLESS': 'cdp_headless',
            'CDP_CONNECT_EXISTING': 'cdp_connect_existing',
            'CUSTOM_BROWSER_PATH': 'custom_browser_path',
            'BROWSER_LAUNCH_TIMEOUT': 'browser_launch_timeout',
            'AUTO_CLOSE_BROWSER': 'auto_close_browser',
            'IP_PROXY_POOL_COUNT': 'ip_proxy_pool_count',
            'IP_PROXY_PROVIDER_NAME': 'ip_proxy_provider_name',
            'XHS_INTERNATIONAL': 'xhs_international',
            'DISABLE_SSL_VERIFY': 'disable_ssl_verify',
        }
        
        for config_name, attr_name in mappings.items():
            if hasattr(self, attr_name):
                setattr(config, config_name, getattr(self, attr_name))
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return asdict(self)
    
    def __repr__(self) -> str:
        return f"CrawlerSettings(platform={self.platform}, keywords={self.keywords}, login_type={self.login_type})"


def _convert_type(value: str, current_value: Any) -> Any:
    """根据当前值类型转换字符串值"""
    if isinstance(current_value, bool):
        return value.lower() in ("true", "1", "yes", "y", "t")
    elif isinstance(current_value, int):
        try:
            return int(value)
        except ValueError:
            return current_value
    elif isinstance(current_value, float):
        try:
            return float(value)
        except ValueError:
            return current_value
    return value


def _apply_account_to_settings(settings: CrawlerSettings, account: Dict[str, Any]) -> None:
    """将账号配置应用到设置"""
    settings.account_name = account.get("name", settings.account_name)
    settings.platform = account.get("platform", settings.platform)
    settings.cookies = account.get("cookies", account.get("cookie", settings.cookies))
    settings.account_proxy = account.get("proxy", settings.account_proxy)
    settings.account_user_agent = account.get("user_agent", settings.account_user_agent)
    
    if settings.cookies:
        settings.login_type = "cookie"


def load_settings(
    env_prefix: str = "MC_",
    account_path: Optional[str] = None,
    cmd_args: Optional[Dict[str, Any]] = None,
) -> CrawlerSettings:
    """
    统一配置加载入口
    优先级：命令行 > 环境变量 > accounts.json > base_config.py > 默认值
    """
    # 1. 默认值
    settings = CrawlerSettings.from_defaults()
    
    # 2. base_config.py
    base_settings = CrawlerSettings.from_base_config()
    _merge_settings(settings, base_settings)
    
    # 3. accounts.json
    if account_path and os.path.exists(account_path):
        json_settings = CrawlerSettings.from_json_file(account_path)
        _merge_settings(settings, json_settings)
    
    # 4. 环境变量
    env_settings = CrawlerSettings.from_env()
    _merge_settings(settings, env_settings)
    
    # 5. 命令行参数（最高优先级）
    if cmd_args:
        for key, value in cmd_args.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)
    
    return settings


def _merge_settings(target: CrawlerSettings, source: CrawlerSettings) -> None:
    """合并设置，source 的非默认值覆盖 target"""
    defaults = CrawlerSettings.from_defaults()
    
    for key in target.__dict__:
        source_value = getattr(source, key)
        default_value = getattr(defaults, key)
        
        # 如果 source 不是默认值，则覆盖
        if source_value != default_value:
            setattr(target, key, source_value)


# 向后兼容：导出统一配置实例
settings = load_settings()
