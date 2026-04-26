# MediaCrawler 仪表盘

## 快速开始

### 1. 启动后端 API

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动服务
uvicorn dashboard.api:app --host 0.0.0.0 --port 8080 --reload
```

服务启动后访问：
- API 文档：http://localhost:8080/docs
- API 根路径：http://localhost:8080/

### 2. 前端开发

```bash
# 创建 React 项目
cd dashboard/frontend
npm create vite@latest . -- --template react-ts

# 安装依赖
npm install
npm install echarts @ant-design/charts
npm install antd
npm install @tanstack/react-query
npm install axios

# 启动开发服务器
npm run dev
```

### 3. 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/dashboard/overview` | GET | 概览数据 |
| `/api/dashboard/platform_stats` | GET | 平台统计 |
| `/api/dashboard/accounts` | GET | 账号列表 |
| `/api/dashboard/keywords` | GET | 关键词排行 |
| `/api/dashboard/timeline` | GET | 时间趋势 |
| `/api/dashboard/risk_events` | GET | 风险事件 |
| `/api/dashboard/scheduler_stats` | GET | 调度器统计 |
| `/api/dashboard/realtime` | GET | 实时数据 |

### 4. 数据刷新

建议轮询频率：
- 概览数据：30 秒
- 实时数据：10 秒
- 风险事件：60 秒

## 部署

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn

EXPOSE 8080
CMD ["uvicorn", "dashboard.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
docker build -t mediacrawler-dashboard .
docker run -p 8080:8080 mediacrawler-dashboard
```

## 开发计划

### Phase 1: 基础仪表盘
- [ ] 概览卡片（总帖子数、评论数、账号数）
- [ ] 平台分布图表
- [ ] 账号状态列表
- [ ] 关键词排行

### Phase 2: 趋势分析
- [ ] 时间趋势图（7/30/90天）
- [ ] 平台对比分析
- [ ] 关键词趋势

### Phase 3: 监控告警
- [ ] 风险事件列表
- [ ] 实时状态监控
- [ ] 告警通知

### Phase 4: 高级功能
- [ ] 数据导出
- [ ] 自定义报表
- [ ] 权限管理
