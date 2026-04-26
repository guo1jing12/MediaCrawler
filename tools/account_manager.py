import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import config
from proxy.types import IpInfoModel
from tools import utils


@dataclass(frozen=True)
class AccountProfile:
    name: str
    platform: str
    cookies: str = ""
    proxy: str = ""
    user_agent: str = ""
    enabled: bool = True


def _normalize_account(raw: Dict[str, Any], index: int) -> AccountProfile:
    return AccountProfile(
        name=str(raw.get("name") or raw.get("account_name") or f"account_{index + 1}"),
        platform=str(raw.get("platform") or config.PLATFORM),
        cookies=str(raw.get("cookies") or raw.get("cookie") or ""),
        proxy=str(raw.get("proxy") or ""),
        user_agent=str(raw.get("user_agent") or ""),
        enabled=bool(raw.get("enabled", True)),
    )


def load_account_profiles(path: Optional[str] = None, platform: Optional[str] = None) -> List[AccountProfile]:
    account_path = path or config.ACCOUNT_CONFIG_PATH
    if not account_path or not os.path.exists(account_path):
        utils.logger.warning(f"[account_manager] Account config file not found: {account_path}")
        return []

    with open(account_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_accounts = data.get("accounts", data) if isinstance(data, dict) else data
    if not isinstance(raw_accounts, list):
        raise ValueError("Account config must be a list or an object containing an 'accounts' list")

    target_platform = platform or config.PLATFORM
    profiles = [
        profile
        for index, raw in enumerate(raw_accounts)
        for profile in [_normalize_account(raw, index)]
        if profile.enabled and profile.platform == target_platform
    ]
    return profiles


def apply_account_profile(profile: AccountProfile) -> None:
    config.ACCOUNT_NAME = profile.name
    config.COOKIES = profile.cookies
    config.ACCOUNT_PROXY = profile.proxy
    config.ACCOUNT_USER_AGENT = profile.user_agent
    if profile.cookies:
        config.LOGIN_TYPE = "cookie"


def reset_account_profile() -> None:
    config.ACCOUNT_NAME = "default"
    config.ACCOUNT_PROXY = ""
    config.ACCOUNT_USER_AGENT = ""
    config.COOKIES = ""
    config.LOGIN_TYPE = "qrcode"


def proxy_url_to_formats(proxy_url: str):
    if not proxy_url:
        return None, None

    parsed = urlparse(proxy_url)
    if not parsed.hostname or not parsed.port:
        raise ValueError(f"Invalid ACCOUNT_PROXY value: {proxy_url}")

    ip_info = IpInfoModel(
        ip=parsed.hostname,
        port=parsed.port,
        user=parsed.username or "",
        password=parsed.password or "",
        expired_time_ts=0,
    )
    return utils.format_proxy_info(ip_info)


async def resolve_proxy_formats(ip_proxy_pool=None):
    if config.ACCOUNT_PROXY:
        return proxy_url_to_formats(config.ACCOUNT_PROXY)

    if not config.ENABLE_IP_PROXY:
        return None, None

    pool = ip_proxy_pool
    if pool is None:
        from proxy.proxy_ip_pool import create_ip_pool

        pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
    ip_proxy_info = await pool.get_proxy()
    return utils.format_proxy_info(ip_proxy_info)
