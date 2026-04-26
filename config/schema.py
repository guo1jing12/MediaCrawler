# -*- coding: utf-8 -*-
"""
配置校验 Schema
使用 dataclass 定义配置结构，支持类型校验和默认值
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class PlatformEnum(str, Enum):
    """支持的平台"""
    XHS = "xhs"
    DOUYIN = "dy"
    KUAISHOU = "ks"
    BILIBILI = "bili"
    WEIBO = "wb"
    TIEBA = "tieba"
    ZHIHU = "zhihu"


class LoginTypeEnum(str, Enum):
    """登录类型"""
    QRCODE = "qrcode"
    PHONE = "phone"
    COOKIE = "cookie"


class CrawlerTypeEnum(str, Enum):
    """爬取类型"""
    SEARCH = "search"
    DETAIL = "detail"
    CREATOR = "creator"


class SaveDataOptionEnum(str, Enum):
    """数据保存选项"""
    CSV = "csv"
    DB = "db"
    JSON = "json"
    JSONL = "jsonl"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    EXCEL = "excel"
    POSTGRES = "postgres"


@dataclass
class AccountConfig:
    """账号配置"""
    name: str
    platform: str = "xhs"
    cookies: str = ""
    proxy: str = ""
    user_agent: str = ""
    enabled: bool = True


@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    pool_count: int = 2
    provider_name: str = "kuaidaili"


@dataclass
class CDPConfig:
    """CDP 配置"""
    enabled: bool = True
    debug_port: int = 9222
    headless: bool = False
    connect_existing: bool = True
    custom_browser_path: str = ""
    launch_timeout: int = 60
    auto_close: bool = True


@dataclass
class CheckpointConfig:
    """断点续爬配置"""
    enabled: bool = False
    checkpoint_dir: str = "data/checkpoints"
    checkpoint_file: str = ""


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_concurrency: int = 1
    max_notes_count: int = 15
    max_sleep_sec: int = 2
    start_page: int = 1


@dataclass
class FeatureConfig:
    """功能配置"""
    get_comments: bool = True
    get_sub_comments: bool = False
    get_medias: bool = False
    get_wordcloud: bool = False


@dataclass
class CrawlerConfigSchema:
    """完整的爬虫配置 Schema"""
    
    # 基础配置
    platform: PlatformEnum = PlatformEnum.XHS
    keywords: str = ""
    login_type: LoginTypeEnum = LoginTypeEnum.QRCODE
    cookies: str = ""
    crawler_type: CrawlerTypeEnum = CrawlerTypeEnum.SEARCH
    
    # 性能
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # 功能
    features: FeatureConfig = field(default_factory=FeatureConfig)
    
    # 多账号
    enable_multi_account: bool = False
    account_config_path: str = "config/accounts.json"
    accounts: List[AccountConfig] = field(default_factory=list)
    
    # 断点续爬
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    
    # 运行时
    disable_playwright: bool = False
    headless: bool = False
    save_data_option: SaveDataOptionEnum = SaveDataOptionEnum.JSONL
    save_data_path: str = ""
    save_login_state: bool = True
    
    # CDP
    cdp: CDPConfig = field(default_factory=CDPConfig)
    
    # 代理
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    
    # 小红书特有
    xhs_international: bool = False
    
    # 安全
    disable_ssl_verify: bool = False
    
    def validate(self) -> List[str]:
        """完整校验"""
        errors = []
        
        # 基础校验
        if not self.keywords and self.crawler_type == CrawlerTypeEnum.SEARCH:
            errors.append("keywords is required for search mode")
        
        if self.disable_playwright and self.login_type != LoginTypeEnum.COOKIE and not self.enable_multi_account:
            errors.append("API-only mode requires cookie login or multi-account")
        
        # 性能校验
        if self.performance.max_concurrency < 1:
            errors.append("max_concurrency must be >= 1")
        
        if self.performance.max_notes_count < 1:
            errors.append("max_notes_count must be >= 1")
        
        # 路径校验
        if self.account_config_path and not self.account_config_path.endswith('.json'):
            errors.append("account_config_path must be a JSON file")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)
