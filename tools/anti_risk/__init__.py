# -*- coding: utf-8 -*-
"""
反风控策略库 - 统一入口

使用示例：
    from tools.anti_risk import RiskDetector, RetryStrategy, RiskLevel
    
    # 检测风控信号
    detector = RiskDetector()
    event = detector.detect("xhs", status_code=429, response_text="访问频繁")
    
    if event.level == RiskLevel.HIGH:
        print(f"高风险：{event.signal.value}")
    
    # 带重试执行
    strategy = RetryStrategy()
    result = await strategy.execute("xhs", fetch_data, url)
"""

from .detector import (
    RiskDetector,
    RiskEvent,
    RiskLevel,
    RiskSignal,
    PlatformRiskRules,
    get_detector,
)

from .strategy import (
    RetryStrategy,
    RetryConfig,
    RetryPolicy,
    CircuitBreaker,
    with_retry,
)

from .platform_rules import (
    get_platform_rules,
    register_platform_rules,
    PLATFORM_RULES,
    XiaoHongShuRules,
    DouYinRules,
    BilibiliRules,
    WeiboRules,
)

__all__ = [
    # 检测器
    'RiskDetector',
    'RiskEvent',
    'RiskLevel',
    'RiskSignal',
    'PlatformRiskRules',
    'get_detector',
    
    # 策略
    'RetryStrategy',
    'RetryConfig',
    'RetryPolicy',
    'CircuitBreaker',
    'with_retry',
    
    # 平台规则
    'get_platform_rules',
    'register_platform_rules',
    'PLATFORM_RULES',
    'XiaoHongShuRules',
    'DouYinRules',
    'BilibiliRules',
    'WeiboRules',
]
