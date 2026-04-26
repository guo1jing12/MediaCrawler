# -*- coding: utf-8 -*-
"""
反风控策略库 - 限流/封禁信号检测

支持多平台风控特征识别：
- HTTP 状态码：429(限流), 461/471(验证码), 403(封禁)
- 响应内容关键词："请通过验证", "访问频繁", "账号异常"
- 响应时间异常：突然变慢可能预示风控
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import re


class RiskLevel(Enum):
    """风险等级"""
    NONE = "none"         # 无风险
    LOW = "low"           # 低风险（轻微限流）
    MEDIUM = "medium"     # 中风险（明显限流）
    HIGH = "high"         # 高风险（封禁/验证码）
    CRITICAL = "critical"  # 严重（账号/IP封禁）


class RiskSignal(Enum):
    """风险信号类型"""
    RATE_LIMIT = "rate_limit"       # 限流
    CAPTCHA = "captcha"             # 验证码
    IP_BAN = "ip_ban"              # IP封禁
    ACCOUNT_BAN = "account_ban"    # 账号封禁
    SLOW_DOWN = "slow_down"        # 响应变慢
    UNKNOWN = "unknown"            # 未知异常


@dataclass
class RiskEvent:
    """风险事件"""
    signal: RiskSignal
    level: RiskLevel
    platform: str
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformRiskRules:
    """平台风控规则配置"""
    platform: str
    
    # HTTP 状态码映射
    status_code_rules: Dict[int, RiskSignal] = field(default_factory=dict)
    
    # 响应内容关键词
    content_keywords: Dict[str, RiskSignal] = field(default_factory=dict)
    
    # 响应时间阈值（秒）
    slow_threshold: float = 5.0
    
    # 连续错误阈值
    consecutive_errors_threshold: int = 3
    
    def __post_init__(self):
        # 默认规则
        if not self.status_code_rules:
            self.status_code_rules = {
                429: RiskSignal.RATE_LIMIT,
                461: RiskSignal.CAPTCHA,
                471: RiskSignal.CAPTCHA,
                403: RiskSignal.IP_BAN,
                401: RiskSignal.ACCOUNT_BAN,
            }
        
        if not self.content_keywords:
            self.content_keywords = {
                "请通过验证": RiskSignal.CAPTCHA,
                "访问频繁": RiskSignal.RATE_LIMIT,
                "操作频繁": RiskSignal.RATE_LIMIT,
                "账号异常": RiskSignal.ACCOUNT_BAN,
                "IP被封": RiskSignal.IP_BAN,
                "网络连接错误": RiskSignal.UNKNOWN,
            }


class RiskDetector:
    """风控信号检测器"""
    
    def __init__(self):
        self._rules: Dict[str, PlatformRiskRules] = {}
        self._history: List[RiskEvent] = []
        self._consecutive_errors: Dict[str, int] = {}  # 平台 -> 连续错误数
        self._callbacks: List[Callable[[RiskEvent], None]] = []
        
        # 初始化默认规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化各平台默认规则"""
        platforms = ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"]
        for platform in platforms:
            self._rules[platform] = PlatformRiskRules(platform)
    
    def add_rule(self, platform: str, rule: PlatformRiskRules) -> None:
        """添加/覆盖平台规则"""
        self._rules[platform] = rule
    
    def add_callback(self, callback: Callable[[RiskEvent], None]) -> None:
        """添加风险事件回调"""
        self._callbacks.append(callback)
    
    def detect(
        self,
        platform: str,
        status_code: int,
        response_text: str = "",
        response_time: float = 0.0,
        error: Optional[Exception] = None,
    ) -> RiskEvent:
        """
        检测风控信号
        
        Args:
            platform: 平台标识
            status_code: HTTP 状态码
            response_text: 响应文本
            response_time: 响应时间（秒）
            error: 异常对象
        
        Returns:
            RiskEvent: 风险事件
        """
        rule = self._rules.get(platform, PlatformRiskRules(platform))
        
        # 1. 检查状态码
        signal = self._check_status_code(status_code, rule)
        if signal:
            level = self._signal_to_level(signal)
            event = RiskEvent(
                signal=signal,
                level=level,
                platform=platform,
                message=f"Status {status_code} detected",
                metadata={"status_code": status_code},
            )
            self._record_event(event)
            return event
        
        # 2. 检查响应内容
        signal = self._check_content(response_text, rule)
        if signal:
            level = self._signal_to_level(signal)
            event = RiskEvent(
                signal=signal,
                level=level,
                platform=platform,
                message=f"Content keyword matched: {response_text[:100]}",
                metadata={"matched_text": response_text[:200]},
            )
            self._record_event(event)
            return event
        
        # 3. 检查响应时间
        if response_time > rule.slow_threshold:
            event = RiskEvent(
                signal=RiskSignal.SLOW_DOWN,
                level=RiskLevel.LOW,
                platform=platform,
                message=f"Slow response: {response_time:.2f}s",
                metadata={"response_time": response_time},
            )
            self._record_event(event)
            return event
        
        # 4. 检查连续错误
        if error:
            signal = self._check_consecutive_errors(platform, rule)
            if signal:
                level = self._signal_to_level(signal)
                event = RiskEvent(
                    signal=signal,
                    level=level,
                    platform=platform,
                    message=f"Consecutive errors: {error}",
                    metadata={"error": str(error)},
                )
                self._record_event(event)
                return event
        
        # 无风险
        return RiskEvent(
            signal=RiskSignal.UNKNOWN,
            level=RiskLevel.NONE,
            platform=platform,
            message="No risk detected",
        )
    
    def _check_status_code(self, status_code: int, rule: PlatformRiskRules) -> Optional[RiskSignal]:
        """检查状态码"""
        return rule.status_code_rules.get(status_code)
    
    def _check_content(self, response_text: str, rule: PlatformRiskRules) -> Optional[RiskSignal]:
        """检查响应内容关键词"""
        for keyword, signal in rule.content_keywords.items():
            if keyword in response_text:
                return signal
        return None
    
    def _check_consecutive_errors(self, platform: str, rule: PlatformRiskRules) -> Optional[RiskSignal]:
        """检查连续错误"""
        count = self._consecutive_errors.get(platform, 0) + 1
        self._consecutive_errors[platform] = count
        
        if count >= rule.consecutive_errors_threshold:
            self._consecutive_errors[platform] = 0  # 重置
            return RiskSignal.RATE_LIMIT
        return None
    
    def _signal_to_level(self, signal: RiskSignal) -> RiskLevel:
        """信号转风险等级"""
        mapping = {
            RiskSignal.SLOW_DOWN: RiskLevel.LOW,
            RiskSignal.RATE_LIMIT: RiskLevel.MEDIUM,
            RiskSignal.CAPTCHA: RiskLevel.HIGH,
            RiskSignal.IP_BAN: RiskLevel.CRITICAL,
            RiskSignal.ACCOUNT_BAN: RiskLevel.CRITICAL,
            RiskSignal.UNKNOWN: RiskLevel.LOW,
        }
        return mapping.get(signal, RiskLevel.LOW)
    
    def _record_event(self, event: RiskEvent) -> None:
        """记录风险事件"""
        # 只记录有风险的事件
        if event.level == RiskLevel.NONE:
            return
            
        self._history.append(event)
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[RiskDetector] Callback error: {e}")
    
    def reset_consecutive_errors(self, platform: str) -> None:
        """重置连续错误计数"""
        self._consecutive_errors[platform] = 0
    
    def get_history(self, platform: Optional[str] = None, limit: int = 100) -> List[RiskEvent]:
        """获取风险历史"""
        events = self._history
        if platform:
            events = [e for e in events if e.platform == platform]
        return events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_events": len(self._history),
            "by_signal": {},
            "by_level": {},
            "by_platform": {},
        }
        
        for event in self._history:
            signal_name = event.signal.value
            level_name = event.level.value
            platform = event.platform
            
            stats["by_signal"][signal_name] = stats["by_signal"].get(signal_name, 0) + 1
            stats["by_level"][level_name] = stats["by_level"].get(level_name, 0) + 1
            stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
        
        return stats


# 全局检测器实例
_default_detector: Optional[RiskDetector] = None


def get_detector() -> RiskDetector:
    """获取默认检测器"""
    global _default_detector
    if _default_detector is None:
        _default_detector = RiskDetector()
    return _default_detector
