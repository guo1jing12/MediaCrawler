# -*- coding: utf-8 -*-
"""
反风控策略库 - 平台规则配置

各平台特有的风控特征和应对策略
"""

from typing import Dict, List
from dataclasses import dataclass, field

from .detector import PlatformRiskRules, RiskSignal


@dataclass
class XiaoHongShuRules(PlatformRiskRules):
    """小红书风控规则"""
    
    def __post_init__(self):
        super().__post_init__()
        self.platform = "xhs"
        
        # 小红书特有状态码
        self.status_code_rules.update({
            461: RiskSignal.CAPTCHA,  # 滑块验证
            471: RiskSignal.CAPTCHA,  # 验证码
            300012: RiskSignal.IP_BAN,  # 网络连接错误（IP被封）
        })
        
        # 小红书特有响应关键词
        self.content_keywords.update({
            "请通过验证": RiskSignal.CAPTCHA,
            "访问频繁": RiskSignal.RATE_LIMIT,
            "操作频繁": RiskSignal.RATE_LIMIT,
            "账号异常": RiskSignal.ACCOUNT_BAN,
            "登录过期": RiskSignal.ACCOUNT_BAN,
            "网络连接错误": RiskSignal.IP_BAN,
            "请稍后重试": RiskSignal.RATE_LIMIT,
        })
        
        # 小红书响应较慢
        self.slow_threshold = 3.0
        
        # 小红书风控较严格，降低连续错误阈值
        self.consecutive_errors_threshold = 2


@dataclass
class DouYinRules(PlatformRiskRules):
    """抖音风控规则"""
    
    def __post_init__(self):
        super().__post_init__()
        self.platform = "dy"
        
        # 抖音特有响应关键词
        self.content_keywords.update({
            "访问太频繁": RiskSignal.RATE_LIMIT,
            "操作太频繁": RiskSignal.RATE_LIMIT,
            "账号被封禁": RiskSignal.ACCOUNT_BAN,
            "设备被封禁": RiskSignal.IP_BAN,
            "验证码": RiskSignal.CAPTCHA,
            "滑动验证": RiskSignal.CAPTCHA,
        })
        
        self.slow_threshold = 4.0
        self.consecutive_errors_threshold = 3


@dataclass
class BilibiliRules(PlatformRiskRules):
    """B站风控规则"""
    
    def __post_init__(self):
        super().__post_init__()
        self.platform = "bili"
        
        # B站风控相对宽松
        self.content_keywords.update({
            "请求过于频繁": RiskSignal.RATE_LIMIT,
            "账号被封停": RiskSignal.ACCOUNT_BAN,
            "IP被封禁": RiskSignal.IP_BAN,
        })
        
        self.slow_threshold = 5.0
        self.consecutive_errors_threshold = 5


@dataclass
class WeiboRules(PlatformRiskRules):
    """微博风控规则"""
    
    def __post_init__(self):
        super().__post_init__()
        self.platform = "wb"
        
        self.content_keywords.update({
            "访问频次过高": RiskSignal.RATE_LIMIT,
            "操作频次过高": RiskSignal.RATE_LIMIT,
            "账号异常": RiskSignal.ACCOUNT_BAN,
            "登录状态失效": RiskSignal.ACCOUNT_BAN,
        })
        
        self.slow_threshold = 3.0
        self.consecutive_errors_threshold = 3


# 平台规则注册表
PLATFORM_RULES = {
    "xhs": XiaoHongShuRules("xhs"),
    "dy": DouYinRules("dy"),
    "ks": PlatformRiskRules("ks"),  # 快手使用默认规则
    "bili": BilibiliRules("bili"),
    "wb": WeiboRules("wb"),
    "tieba": PlatformRiskRules("tieba"),  # 贴吧使用默认规则
    "zhihu": PlatformRiskRules("zhihu"),  # 知乎使用默认规则
}


def get_platform_rules(platform: str) -> PlatformRiskRules:
    """获取平台规则"""
    return PLATFORM_RULES.get(platform, PlatformRiskRules(platform))


def register_platform_rules(platform: str, rules: PlatformRiskRules) -> None:
    """注册平台规则"""
    PLATFORM_RULES[platform] = rules
