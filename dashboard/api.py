# -*- coding: utf-8 -*-
"""
仪表盘 API 服务
提供数据接口给前端可视化仪表盘
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

app = FastAPI(
    title="MediaCrawler Dashboard API",
    description="爬虫数据可视化仪表盘后端接口",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 数据模型 ==========

class OverviewResponse:
    """概览数据"""
    total_notes: int
    total_comments: int
    total_creators: int
    active_accounts: int
    today_notes: int
    today_comments: int
    success_rate: float
    avg_response_time: float


class PlatformStat:
    """平台统计"""
    platform: str
    notes: int
    comments: int
    accounts: int
    success_rate: float


class AccountInfo:
    """账号信息"""
    name: str
    platform: str
    status: str  # active / banned / idle
    last_crawl: str
    success_rate: float
    today_notes: int
    total_notes: int


class KeywordStat:
    """关键词统计"""
    keyword: str
    notes_count: int
    trend: str  # up / down / stable
    change: str


class TimelineData:
    """时间线数据"""
    dates: List[str]
    notes: List[int]
    comments: List[int]
    accounts: List[int]


class RiskEvent:
    """风险事件"""
    timestamp: str
    platform: str
    signal: str
    level: str
    account: str
    message: str


# ========== 模拟数据（后续替换为真实数据库查询） ==========

_mock_overview = {
    "total_notes": 15234,
    "total_comments": 89201,
    "total_creators": 3456,
    "active_accounts": 5,
    "today_notes": 1234,
    "today_comments": 5678,
    "success_rate": 0.95,
    "avg_response_time": 2.3,
}

_mock_platform_stats = {
    "xhs": {"notes": 8000, "comments": 45000, "accounts": 2, "success_rate": 0.93},
    "dy": {"notes": 4000, "comments": 25000, "accounts": 1, "success_rate": 0.96},
    "ks": {"notes": 3234, "comments": 19201, "accounts": 1, "success_rate": 0.97},
    "bili": {"notes": 0, "comments": 0, "accounts": 0, "success_rate": 0.0},
    "wb": {"notes": 0, "comments": 0, "accounts": 0, "success_rate": 0.0},
    "tieba": {"notes": 0, "comments": 0, "accounts": 0, "success_rate": 0.0},
    "zhihu": {"notes": 0, "comments": 0, "accounts": 0, "success_rate": 0.0},
}

_mock_accounts = [
    {"name": "xhs_01", "platform": "xhs", "status": "active", "last_crawl": "2026-04-27T10:00:00Z", "success_rate": 0.95, "today_notes": 523, "total_notes": 5234},
    {"name": "xhs_02", "platform": "xhs", "status": "banned", "last_crawl": "2026-04-26T15:00:00Z", "success_rate": 0.0, "today_notes": 0, "total_notes": 2766},
    {"name": "dy_01", "platform": "dy", "status": "active", "last_crawl": "2026-04-27T09:30:00Z", "success_rate": 0.96, "today_notes": 345, "total_notes": 4000},
    {"name": "ks_01", "platform": "ks", "status": "active", "last_crawl": "2026-04-27T08:00:00Z", "success_rate": 0.97, "today_notes": 366, "total_notes": 3234},
]

_mock_keywords = [
    {"keyword": "编程副业", "notes_count": 5234, "trend": "up", "change": "+12%"},
    {"keyword": "编程兼职", "notes_count": 3456, "trend": "down", "change": "-5%"},
    {"keyword": "Python教程", "notes_count": 2890, "trend": "stable", "change": "0%"},
    {"keyword": "爬虫技术", "notes_count": 2341, "trend": "up", "change": "+8%"},
    {"keyword": "数据分析", "notes_count": 1890, "trend": "up", "change": "+15%"},
]

_mock_risk_events = [
    {"timestamp": "2026-04-27T09:30:00Z", "platform": "xhs", "signal": "rate_limit", "level": "medium", "account": "xhs_01", "message": "访问频繁"},
    {"timestamp": "2026-04-27T08:15:00Z", "platform": "dy", "signal": "captcha", "level": "high", "account": "dy_01", "message": "触发验证码"},
    {"timestamp": "2026-04-26T20:00:00Z", "platform": "xhs", "signal": "account_ban", "level": "critical", "account": "xhs_02", "message": "账号异常"},
]


# ========== API 路由 ==========

@app.get("/api/dashboard/overview")
async def get_overview() -> Dict[str, Any]:
    """获取概览数据"""
    return _mock_overview


@app.get("/api/dashboard/platform_stats")
async def get_platform_stats() -> Dict[str, Any]:
    """获取各平台统计"""
    return _mock_platform_stats


@app.get("/api/dashboard/accounts")
async def get_accounts(
    platform: Optional[str] = Query(None, description="筛选平台"),
    status: Optional[str] = Query(None, description="筛选状态"),
) -> List[Dict[str, Any]]:
    """获取账号列表"""
    accounts = _mock_accounts
    
    if platform:
        accounts = [a for a in accounts if a["platform"] == platform]
    if status:
        accounts = [a for a in accounts if a["status"] == status]
    
    return accounts


@app.get("/api/dashboard/keywords")
async def get_keywords(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
) -> List[Dict[str, Any]]:
    """获取关键词排行"""
    return _mock_keywords[:limit]


@app.get("/api/dashboard/timeline")
async def get_timeline(
    days: int = Query(7, ge=1, le=30, description="天数"),
) -> Dict[str, Any]:
    """获取时间趋势"""
    # 生成模拟数据
    dates = []
    notes = []
    comments = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i - 1)
        dates.append(date.strftime("%m-%d"))
        notes.append(1000 + i * 100 + hash(date.strftime("%Y%m%d")) % 500)
        comments.append(4000 + i * 300 + hash(date.strftime("%Y%m%d")) % 1500)
    
    return {
        "dates": dates,
        "notes": notes,
        "comments": comments,
    }


@app.get("/api/dashboard/risk_events")
async def get_risk_events(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    platform: Optional[str] = Query(None, description="筛选平台"),
) -> List[Dict[str, Any]]:
    """获取风险事件"""
    events = _mock_risk_events
    
    if platform:
        events = [e for e in events if e["platform"] == platform]
    
    return events[:limit]


@app.get("/api/dashboard/scheduler_stats")
async def get_scheduler_stats() -> Dict[str, Any]:
    """获取调度器统计"""
    return {
        "algorithm": "adaptive",
        "total_accounts": 4,
        "active_accounts": 3,
        "banned_accounts": 1,
        "avg_weight": 75.5,
        "avg_success_rate": 0.95,
    }


@app.get("/api/dashboard/realtime")
async def get_realtime() -> Dict[str, Any]:
    """获取实时数据（用于轮询）"""
    return {
        "timestamp": datetime.now().isoformat(),
        "crawling": True,
        "current_account": "xhs_01",
        "current_keyword": "编程副业",
        "current_page": 3,
        "today_notes": 1234,
        "today_comments": 5678,
        "queue_size": 5,
    }


# ========== 健康检查 ==========

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """健康检查"""
    return {"status": "ok"}


@app.get("/")
async def root() -> Dict[str, Any]:
    """API 根路径"""
    return {
        "service": "MediaCrawler Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/api/dashboard/overview",
            "/api/dashboard/platform_stats",
            "/api/dashboard/accounts",
            "/api/dashboard/keywords",
            "/api/dashboard/timeline",
            "/api/dashboard/risk_events",
            "/api/dashboard/scheduler_stats",
            "/api/dashboard/realtime",
        ],
    }


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
