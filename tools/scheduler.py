# -*- coding: utf-8 -*-
"""
智能调度策略库

功能：
1. 账号权重评分（成功率、速度、封禁次数、最后活跃时间）
2. 动态调度算法（加权轮询、最少连接、自适应）
3. 调度日志和统计
"""

import time
import random
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ScheduleAlgorithm(Enum):
    """调度算法"""
    ROUND_ROBIN = "round_robin"       # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    ADAPTIVE = "adaptive"             # 自适应（根据权重动态调整）
    RANDOM = "random"                 # 随机


@dataclass
class AccountScore:
    """账号评分"""
    success_rate: float = 1.0        # 成功率 (0-1)
    avg_response_time: float = 0.0   # 平均响应时间（秒）
    ban_count: int = 0               # 封禁次数
    last_active: float = 0.0         # 最后活跃时间戳
    total_requests: int = 0          # 总请求数
    success_requests: int = 0        # 成功请求数
    
    @property
    def weight(self) -> float:
        """计算权重分 (0-100)"""
        # 成功率权重 40%
        success_weight = self.success_rate * 40
        
        # 响应时间权重 30%（越快越好）
        if self.avg_response_time > 0:
            speed_weight = max(0, 30 - self.avg_response_time * 5)
        else:
            speed_weight = 30
        
        # 封禁惩罚 20%（每次封禁扣10分）
        ban_penalty = max(0, 20 - self.ban_count * 10)
        
        # 活跃度权重 10%（最近活跃加分）
        if self.last_active > 0:
            time_since_active = time.time() - self.last_active
            if time_since_active < 3600:  # 1小时内
                active_weight = 10
            elif time_since_active < 86400:  # 24小时内
                active_weight = 5
            else:
                active_weight = 0
        else:
            active_weight = 0
        
        return success_weight + speed_weight + ban_penalty + active_weight


@dataclass
class AccountState:
    """账号状态"""
    name: str
    platform: str
    enabled: bool = True
    is_active: bool = True          # 是否可用
    current_connections: int = 0      # 当前连接数
    score: AccountScore = field(default_factory=AccountScore)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleLog:
    """调度日志"""
    timestamp: float
    account_name: str
    platform: str
    action: str                    # select / ban / unban / fail
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AccountScheduler:
    """账号调度器"""
    
    def __init__(self, algorithm: ScheduleAlgorithm = ScheduleAlgorithm.ADAPTIVE):
        self.algorithm = algorithm
        self._accounts: Dict[str, AccountState] = {}
        self._logs: List[ScheduleLog] = []
        self._callbacks: List[Callable[[ScheduleLog], None]] = []
        
        # 轮询计数器
        self._round_robin_index: Dict[str, int] = defaultdict(int)
    
    def register_account(self, name: str, platform: str, **metadata) -> AccountState:
        """注册账号"""
        account = AccountState(name=name, platform=platform, metadata=metadata)
        self._accounts[name] = account
        return account
    
    def unregister_account(self, name: str) -> None:
        """注销账号"""
        if name in self._accounts:
            del self._accounts[name]
    
    def get_account(self, name: str) -> Optional[AccountState]:
        """获取账号状态"""
        return self._accounts.get(name)
    
    def select_account(self, platform: Optional[str] = None) -> Optional[AccountState]:
        """
        选择账号
        
        Args:
            platform: 指定平台，None表示不限
        
        Returns:
            AccountState: 选中的账号，None表示无可用账号
        """
        # 筛选可用账号
        candidates = [
            acc for acc in self._accounts.values()
            if acc.enabled and acc.is_active
            and (platform is None or acc.platform == platform)
        ]
        
        if not candidates:
            return None
        
        # 根据算法选择
        if self.algorithm == ScheduleAlgorithm.ROUND_ROBIN:
            selected = self._round_robin_select(candidates, platform)
        elif self.algorithm == ScheduleAlgorithm.LEAST_CONNECTIONS:
            selected = self._least_connections_select(candidates)
        elif self.algorithm == ScheduleAlgorithm.ADAPTIVE:
            selected = self._adaptive_select(candidates)
        elif self.algorithm == ScheduleAlgorithm.RANDOM:
            selected = random.choice(candidates)
        else:
            selected = candidates[0]
        
        # 增加连接数
        selected.current_connections += 1
        
        # 记录日志
        self._log(ScheduleLog(
            timestamp=time.time(),
            account_name=selected.name,
            platform=selected.platform,
            action="select",
            reason=f"algorithm={self.algorithm.value}",
        ))
        
        return selected
    
    def release_account(self, name: str, success: bool = True, response_time: float = 0.0) -> None:
        """
        释放账号（请求完成）
        
        Args:
            name: 账号名称
            success: 是否成功
            response_time: 响应时间
        """
        account = self._accounts.get(name)
        if not account:
            return
        
        # 减少连接数
        account.current_connections = max(0, account.current_connections - 1)
        
        # 更新评分
        score = account.score
        score.total_requests += 1
        score.last_active = time.time()
        
        if success:
            score.success_requests += 1
            # 更新平均响应时间
            if response_time > 0:
                if score.avg_response_time == 0:
                    score.avg_response_time = response_time
                else:
                    # 指数移动平均
                    score.avg_response_time = score.avg_response_time * 0.7 + response_time * 0.3
        else:
            # 记录失败
            pass
        
        # 更新成功率
        if score.total_requests > 0:
            score.success_rate = score.success_requests / score.total_requests
        
        # 记录日志
        self._log(ScheduleLog(
            timestamp=time.time(),
            account_name=name,
            platform=account.platform,
            action="success" if success else "fail",
            reason=f"response_time={response_time:.2f}s",
        ))
    
    def ban_account(self, name: str, reason: str = "") -> None:
        """封禁账号"""
        account = self._accounts.get(name)
        if not account:
            return
        
        account.is_active = False
        account.score.ban_count += 1
        
        # 记录日志
        self._log(ScheduleLog(
            timestamp=time.time(),
            account_name=name,
            platform=account.platform,
            action="ban",
            reason=reason,
        ))
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(self._logs[-1])
            except Exception as e:
                print(f"[AccountScheduler] Callback error: {e}")
    
    def unban_account(self, name: str) -> None:
        """解封账号"""
        account = self._accounts.get(name)
        if not account:
            return
        
        account.is_active = True
        
        # 记录日志
        self._log(ScheduleLog(
            timestamp=time.time(),
            account_name=name,
            platform=account.platform,
            action="unban",
        ))
    
    def _round_robin_select(self, candidates: List[AccountState], platform: Optional[str]) -> AccountState:
        """加权轮询选择"""
        key = platform or "all"
        index = self._round_robin_index[key] % len(candidates)
        self._round_robin_index[key] = (index + 1) % len(candidates)
        return candidates[index]
    
    def _least_connections_select(self, candidates: List[AccountState]) -> AccountState:
        """最少连接选择"""
        return min(candidates, key=lambda a: a.current_connections)
    
    def _adaptive_select(self, candidates: List[AccountState]) -> AccountState:
        """自适应选择（按权重概率）"""
        # 计算权重
        weights = [max(0.1, acc.score.weight) for acc in candidates]
        total = sum(weights)
        
        if total == 0:
            return random.choice(candidates)
        
        # 按权重概率选择
        r = random.uniform(0, total)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return candidates[i]
        
        return candidates[-1]
    
    def _log(self, log: ScheduleLog) -> None:
        """记录日志"""
        self._logs.append(log)
        
        # 限制日志数量
        if len(self._logs) > 10000:
            self._logs = self._logs[-5000:]
    
    def add_callback(self, callback: Callable[[ScheduleLog], None]) -> None:
        """添加调度事件回调"""
        self._callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_accounts": len(self._accounts),
            "active_accounts": sum(1 for acc in self._accounts.values() if acc.is_active),
            "total_logs": len(self._logs),
            "algorithm": self.algorithm.value,
            "accounts": {},
        }
        
        for name, account in self._accounts.items():
            stats["accounts"][name] = {
                "platform": account.platform,
                "enabled": account.enabled,
                "is_active": account.is_active,
                "current_connections": account.current_connections,
                "weight": account.score.weight,
                "success_rate": account.score.success_rate,
                "avg_response_time": account.score.avg_response_time,
                "ban_count": account.score.ban_count,
                "total_requests": account.score.total_requests,
            }
        
        return stats
    
    def get_logs(
        self,
        account_name: Optional[str] = None,
        platform: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[ScheduleLog]:
        """获取调度日志"""
        logs = self._logs
        
        if account_name:
            logs = [log for log in logs if log.account_name == account_name]
        if platform:
            logs = [log for log in logs if log.platform == platform]
        if action:
            logs = [log for log in logs if log.action == action]
        
        return logs[-limit:]


# 便捷函数
def create_scheduler(algorithm: str = "adaptive") -> AccountScheduler:
    """创建调度器"""
    algo = ScheduleAlgorithm(algorithm)
    return AccountScheduler(algo)
