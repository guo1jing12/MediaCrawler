# -*- coding: utf-8 -*-
"""
反风控策略库使用文档

## 快速开始

### 1. 基础风控检测

```python
from tools.anti_risk import RiskDetector, RiskLevel

detector = RiskDetector()

# 检测风控信号
event = detector.detect(
    platform="xhs",
    status_code=429,
    response_text="访问频繁，请稍后重试",
    response_time=2.5,
)

print(f"信号: {event.signal.value}")
print(f"等级: {event.level.value}")
print(f"消息: {event.message}")

# 根据风险等级处理
if event.level == RiskLevel.HIGH:
    # 暂停爬取，切换账号/代理
    pass
elif event.level == RiskLevel.MEDIUM:
    # 降低并发，增加延迟
    pass
```

### 2. 带重试执行操作

```python
from tools.anti_risk import RetryStrategy, RetryConfig, RetryPolicy

# 配置重试策略
config = RetryConfig(
    max_retries=3,
    base_delay=2.0,
    retry_policy=RetryPolicy.ADAPTIVE,  # 自适应策略
)

strategy = RetryStrategy(config)

# 执行带重试的操作
result = await strategy.execute("xhs", fetch_data, url="https://...")
```

### 3. 熔断器模式

```python
from tools.anti_risk import RetryConfig, RetryPolicy

# 启用熔断器
config = RetryConfig(
    retry_policy=RetryPolicy.CIRCUIT_BREAKER,
    circuit_breaker_threshold=5,    # 5次失败熔断
    circuit_breaker_timeout=300.0,  # 5分钟后恢复
)

strategy = RetryStrategy(config)

# 连续失败5次后，熔断器打开，后续请求直接失败
# 5分钟后进入半开状态，允许一次探测请求
```

### 4. 自定义平台规则

```python
from tools.anti_risk import PlatformRiskRules, RiskSignal, register_platform_rules

# 定义自定义规则
custom_rules = PlatformRiskRules("custom_platform")
custom_rules.status_code_rules[418] = RiskSignal.RATE_LIMIT  # 茶壶状态码
custom_rules.content_keywords["自定义关键词"] = RiskSignal.ACCOUNT_BAN

# 注册规则
register_platform_rules("custom_platform", custom_rules)
```

### 5. 风险事件回调

```python
from tools.anti_risk import RiskDetector, RiskEvent

detector = RiskDetector()

# 添加风险事件处理回调
def on_risk_detected(event: RiskEvent):
    print(f"[ALERT] {event.platform}: {event.signal.value} - {event.level.value}")
    
    # 发送告警通知
    # send_alert(event)
    
    # 记录日志
    # log_risk_event(event)

detector.add_callback(on_risk_detected)
```

### 6. 获取统计信息

```python
# 风险事件历史
history = detector.get_history(platform="xhs", limit=50)

# 统计信息
stats = detector.get_stats()
print(f"总事件数: {stats['total_events']}")
print(f"按信号类型: {stats['by_signal']}")
print(f"按风险等级: {stats['by_level']}")

# 重试策略统计
retry_stats = strategy.get_stats()
print(f"重试次数: {retry_stats['retry_counts']}")
print(f"熔断器状态: {retry_stats['circuit_breakers']}")
```

## 平台支持

| 平台 | 规则文件 | 特有风控特征 |
|------|----------|-------------|
| 小红书 | XiaoHongShuRules | 461/471验证码，严格限流 |
| 抖音 | DouYinRules | 设备封禁，滑动验证 |
| B站 | BilibiliRules | 相对宽松，请求频繁限制 |
| 微博 | WeiboRules | 登录状态失效，频次限制 |
| 快手 | 默认规则 | - |
| 贴吧 | 默认规则 | - |
| 知乎 | 默认规则 | - |

## 配置建议

### 小红书
```python
config = RetryConfig(
    max_retries=2,          # 重试次数少（风控严格）
    base_delay=3.0,         # 基础延迟长
    retry_policy=RetryPolicy.ADAPTIVE,
    circuit_breaker_threshold=3,  # 熔断阈值低
)
```

### B站
```python
config = RetryConfig(
    max_retries=5,          # 重试次数多（风控宽松）
    base_delay=1.0,         # 基础延迟短
    retry_policy=RetryPolicy.EXPONENTIAL,
    circuit_breaker_threshold=10,  # 熔断阈值高
)
```

## 集成到现有代码

```python
# 在 client.py 中使用
from tools.anti_risk import RiskDetector, with_retry

class XiaoHongShuClient:
    async def request(self, method, url, **kwargs):
        try:
            response = await self._do_request(method, url, **kwargs)
            
            # 检测风控信号
            detector = RiskDetector()
            event = detector.detect(
                platform="xhs",
                status_code=response.status_code,
                response_text=response.text,
            )
            
            if event.level.value in ("high", "critical"):
                # 抛出异常触发重试
                raise Exception(f"Risk detected: {event.signal.value}")
            
            return response
            
        except Exception as e:
            # 使用重试策略
            return await with_retry("xhs", self._do_request, method, url, **kwargs)
```
