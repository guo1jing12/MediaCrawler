# -*- coding: utf-8 -*-
"""
反风控策略库 - 重试策略

支持多种重试策略：
- 固定间隔重试
- 指数退避
- 自适应延迟（根据风控信号调整）
- 熔断器模式
"""

import asyncio
import random
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum
import time

from .detector import RiskDetector, RiskEvent, RiskLevel, RiskSignal, get_detector


class RetryPolicy(Enum):
    """重试策略类型"""
    FIXED = "fixed"           # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    ADAPTIVE = "adaptive"     # 自适应（根据风控信号）
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔断器


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0      # 基础延迟（秒）
    max_delay: float = 60.0      # 最大延迟（秒）
    exponential_base: float = 2.0  # 指数基数
    jitter: bool = True          # 是否添加随机抖动
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL  # 重试策略
    
    # 熔断器配置
    circuit_breaker_threshold: int = 5    # 熔断阈值
    circuit_breaker_timeout: float = 300.0  # 熔断恢复时间（秒）
    
    # 自适应配置
    adaptive_multiplier: float = 1.5  # 自适应乘数


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, threshold: int = 5, timeout: float = 300.0):
        self.threshold = threshold
        self.timeout = timeout
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open
    
    def record_success(self) -> None:
        """记录成功"""
        self._failures = 0
        self._state = "closed"
    
    def record_failure(self) -> None:
        """记录失败"""
        self._failures += 1
        self._last_failure_time = time.time()
        
        if self._failures >= self.threshold:
            self._state = "open"
    
    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self._state == "closed":
            return True
        
        if self._state == "open":
            if self._last_failure_time and (time.time() - self._last_failure_time) > self.timeout:
                self._state = "half-open"
                return True
            return False
        
        # half-open
        return True
    
    @property
    def state(self) -> str:
        return self._state


class RetryStrategy:
    """重试策略执行器"""
    
    def __init__(self, config: Optional[RetryConfig] = None, detector: Optional[RiskDetector] = None):
        self.config = config or RetryConfig()
        self.detector = detector or get_detector()
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._retry_counts: Dict[str, int] = {}  # 平台 -> 重试次数
    
    def _get_circuit_breaker(self, platform: str) -> CircuitBreaker:
        """获取熔断器"""
        if platform not in self._circuit_breakers:
            self._circuit_breakers[platform] = CircuitBreaker(
                threshold=self.config.circuit_breaker_threshold,
                timeout=self.config.circuit_breaker_timeout,
            )
        return self._circuit_breakers[platform]
    
    def _calculate_delay(self, attempt: int, risk_event: Optional[RiskEvent] = None) -> float:
        """计算延迟时间"""
        if self.config.retry_policy == RetryPolicy.FIXED:
            delay = self.config.base_delay
        
        elif self.config.retry_policy == RetryPolicy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        elif self.config.retry_policy == RetryPolicy.ADAPTIVE:
            # 根据风险等级调整
            base = self.config.base_delay * (self.config.exponential_base ** attempt)
            
            if risk_event:
                multiplier = {
                    RiskLevel.LOW: 1.0,
                    RiskLevel.MEDIUM: self.config.adaptive_multiplier,
                    RiskLevel.HIGH: self.config.adaptive_multiplier * 2,
                    RiskLevel.CRITICAL: self.config.adaptive_multiplier * 4,
                }.get(risk_event.level, 1.0)
                delay = base * multiplier
            else:
                delay = base
        
        else:
            delay = self.config.base_delay
        
        # 限制最大延迟
        delay = min(delay, self.config.max_delay)
        
        # 添加抖动
        if self.config.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    async def execute(
        self,
        platform: str,
        operation: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        执行带重试的操作
        
        Args:
            platform: 平台标识
            operation: 异步操作函数
            *args, **kwargs: 操作参数
        
        Returns:
            操作结果
        
        Raises:
            Exception: 重试耗尽后抛出最后一次异常
        """
        # 检查熔断器
        breaker = self._get_circuit_breaker(platform)
        if not breaker.can_execute():
            raise Exception(f"Circuit breaker is OPEN for platform {platform}")
        
        last_exception = None
        risk_event = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)
                
                # 成功，重置计数
                breaker.record_success()
                self._retry_counts[platform] = 0
                
                return result
            
            except Exception as e:
                last_exception = e
                
                # 检测风控信号
                # 从异常中提取状态码和响应文本
                status_code = getattr(e, 'status_code', 0)
                response_text = getattr(e, 'response_text', str(e))
                
                risk_event = self.detector.detect(
                    platform=platform,
                    status_code=status_code,
                    response_text=response_text,
                    error=e,
                )
                
                # 记录失败
                breaker.record_failure()
                self._retry_counts[platform] = self._retry_counts.get(platform, 0) + 1
                
                # 判断是否继续重试
                if attempt >= self.config.max_retries:
                    break
                
                # 严重风险直接放弃
                if risk_event.level == RiskLevel.CRITICAL:
                    break
                
                # 计算延迟
                delay = self._calculate_delay(attempt, risk_event)
                
                print(f"[RetryStrategy] {platform} attempt {attempt + 1}/{self.config.max_retries} failed, "
                      f"signal={risk_event.signal.value}, level={risk_event.level.value}, "
                      f"retrying in {delay:.1f}s...")
                
                await asyncio.sleep(delay)
        
        # 重试耗尽
        raise last_exception or Exception(f"Max retries exceeded for {platform}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "retry_counts": self._retry_counts.copy(),
            "circuit_breakers": {
                platform: {
                    "state": cb.state,
                    "failures": cb._failures,
                }
                for platform, cb in self._circuit_breakers.items()
            },
        }


# 便捷函数
async def with_retry(
    platform: str,
    operation: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs,
) -> Any:
    """便捷重试包装"""
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    strategy = RetryStrategy(config)
    return await strategy.execute(platform, operation, *args, **kwargs)
