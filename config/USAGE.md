# -*- coding: utf-8 -*-
"""
配置中心使用文档

MediaCrawler 统一配置中心支持多种配置来源，按优先级从高到低：
1. 命令行参数
2. 环境变量（MC_ 前缀）
3. accounts.json（多账号配置）
4. base_config.py（代码配置）
5. 默认值

使用示例：
"""

# ========== 基础使用 ==========

# 1. 使用统一配置加载
from config import load_settings, get_settings

# 加载配置（自动合并所有来源）
settings = load_settings()

# 或使用单例获取
settings = get_settings()

# 访问配置
print(settings.platform)
print(settings.keywords)
print(settings.max_concurrency_num)


# ========== 环境变量配置 ==========

# 设置环境变量（MC_ 前缀）
# export MC_PLATFORM=xhs
# export MC_KEYWORDS=编程副业
# export MC_MAX_CONCURRENCY_NUM=5
# export MC_ENABLE_GET_COMMENTS=true
# export MC_DISABLE_PLAYWRIGHT=true

# 加载时会自动读取
settings = load_settings()


# ========== 程序中使用 ==========

# 向后兼容：配置会自动同步到 config 模块
settings.apply_to_config()

# 现在可以像原来一样使用
import config
print(config.PLATFORM)
print(config.KEYWORDS)


# ========== 配置校验 ==========

from config.settings import CrawlerSettings

settings = CrawlerSettings(platform='invalid', max_concurrency_num=0)
errors = settings.validate()
if errors:
    print("配置错误:")
    for error in errors:
        print(f"  - {error}")


# ========== 热重载 ==========

from config import enable_hot_reload, disable_hot_reload

# 启用热重载（需要安装 watchdog: pip install watchdog）
reloader = enable_hot_reload("config/accounts.json")

# 添加自定义回调
def on_config_changed():
    print("配置已更新！")

reloader.add_callback(on_config_changed)

# 停止热重载
disable_hot_reload()


# ========== Schema 校验 ==========

from config.schema import CrawlerConfigSchema, PlatformEnum, LoginTypeEnum

# 创建配置
schema = CrawlerConfigSchema(
    platform=PlatformEnum.XHS,
    keywords="编程副业",
    login_type=LoginTypeEnum.COOKIE,
    cookies="your_cookies_here"
)

# 校验
errors = schema.validate()
if not errors:
    print("配置合法！")


# ========== 多账号配置 ==========

# accounts.json 格式
{
  "accounts": [
    {
      "name": "xhs_01",
      "platform": "xhs",
      "cookies": "a1=...; web_session=...",
      "proxy": "http://user:pass@127.0.0.1:7890",
      "user_agent": "",
      "enabled": true
    }
  ]
}

# 加载多账号配置
settings = load_settings(account_path="config/accounts.json")
