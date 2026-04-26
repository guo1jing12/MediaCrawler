# -*- coding: utf-8 -*-
"""
告警通知模块
支持飞书、钉钉 webhook 通知
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import urllib.request
import urllib.parse

from tools.anti_risk import RiskEvent, RiskLevel


@dataclass
class AlertConfig:
    """告警配置"""
    feishu_webhook: str = ""          # 飞书 webhook URL
    dingtalk_webhook: str = ""        # 钉钉 webhook URL
    
    # 告警阈值
    min_level: RiskLevel = RiskLevel.MEDIUM  # 最低告警等级
    rate_limit_interval: int = 300    # 同类告警间隔（秒）
    
    # 开关
    enable_feishu: bool = False
    enable_dingtalk: bool = False


class AlertNotifier:
    """告警通知器"""
    
    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig()
        self._last_alert_time: Dict[str, float] = {}  # 告警类型 -> 最后发送时间
    
    def _should_send(self, alert_type: str) -> bool:
        """检查是否应该发送（防刷屏）"""
        now = datetime.now().timestamp()
        last_time = self._last_alert_time.get(alert_type, 0)
        
        if now - last_time < self.config.rate_limit_interval:
            return False
        
        self._last_alert_time[alert_type] = now
        return True
    
    def _build_feishu_message(self, event: RiskEvent) -> Dict[str, Any]:
        """构建飞书消息"""
        level_colors = {
            RiskLevel.LOW: "blue",
            RiskLevel.MEDIUM: "orange",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "red",
        }
        
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 爬虫风控告警 - {event.platform}"
                    },
                    "template": level_colors.get(event.level, "red")
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**平台:** {event.platform}\n**等级:** {event.level.value}\n**类型:** {event.signal.value}\n**账号:** {event.metadata.get('account', 'N/A')}\n**时间:** {datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n**详情:** {event.message}"
                        }
                    }
                ]
            }
        }
    
    def _build_dingtalk_message(self, event: RiskEvent) -> Dict[str, Any]:
        """构建钉钉消息"""
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": f"爬虫风控告警 - {event.platform}",
                "text": f"## 🚨 爬虫风控告警\n\n**平台:** {event.platform}\n**等级:** {event.level.value}\n**类型:** {event.signal.value}\n**账号:** {event.metadata.get('account', 'N/A')}\n**时间:** {datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n**详情:** {event.message}"
            }
        }
    
    async def send_alert(self, event: RiskEvent) -> bool:
        """
        发送告警
        
        Args:
            event: 风险事件
        
        Returns:
            bool: 是否发送成功
        """
        # 检查等级
        if event.level.value < self.config.min_level.value:
            return False
        
        alert_type = f"{event.platform}:{event.signal.value}"
        
        # 检查频率限制
        if not self._should_send(alert_type):
            return False
        
        success = True
        
        # 发送飞书
        if self.config.enable_feishu and self.config.feishu_webhook:
            try:
                message = self._build_feishu_message(event)
                await self._send_webhook(self.config.feishu_webhook, message)
            except Exception as e:
                print(f"[AlertNotifier] Feishu send failed: {e}")
                success = False
        
        # 发送钉钉
        if self.config.enable_dingtalk and self.config.dingtalk_webhook:
            try:
                message = self._build_dingtalk_message(event)
                await self._send_webhook(self.config.dingtalk_webhook, message)
            except Exception as e:
                print(f"[AlertNotifier] DingTalk send failed: {e}")
                success = False
        
        return success
    
    async def _send_webhook(self, url: str, message: Dict[str, Any]) -> None:
        """发送 webhook 请求"""
        data = json.dumps(message).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        # 使用 asyncio 执行同步请求
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, urllib.request.urlopen, req)
    
    def set_feishu_webhook(self, url: str) -> None:
        """设置飞书 webhook"""
        self.config.feishu_webhook = url
        self.config.enable_feishu = True
    
    def set_dingtalk_webhook(self, url: str) -> None:
        """设置钉钉 webhook"""
        self.config.dingtalk_webhook = url
        self.config.enable_dingtalk = True


# 全局通知器实例
_default_notifier: Optional[AlertNotifier] = None


def get_notifier() -> AlertNotifier:
    """获取默认通知器"""
    global _default_notifier
    if _default_notifier is None:
        _default_notifier = AlertNotifier()
    return _default_notifier
