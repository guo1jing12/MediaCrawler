# -*- coding: utf-8 -*-
"""
配置热重载支持
基于文件监听实现配置变更自动重载
"""

import os
import json
import asyncio
import threading
from typing import Optional, Callable, List
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

from .settings import CrawlerSettings, load_settings


class ConfigReloadHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, config_path: str, callback: Optional[Callable] = None):
        self.config_path = Path(config_path).resolve()
        self.callback = callback
        self._last_modified = 0
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        event_path = Path(event.src_path).resolve()
        if event_path == self.config_path:
            # 防抖：避免频繁触发
            current_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
            if current_time - self._last_modified < 1.0:
                return
            self._last_modified = current_time
            
            if self.callback:
                try:
                    self.callback()
                except Exception as e:
                    print(f"[ConfigReload] Callback error: {e}")


class ConfigReloader:
    """配置热重载管理器"""
    
    def __init__(self, config_path: str, settings: Optional[CrawlerSettings] = None):
        self.config_path = config_path
        self.settings = settings
        self._observer: Optional[Observer] = None
        self._handler: Optional[ConfigReloadHandler] = None
        self._callbacks: List[Callable] = []
        self._running = False
    
    def add_callback(self, callback: Callable) -> None:
        """添加配置变更回调"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        """移除配置变更回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _on_config_changed(self) -> None:
        """配置变更处理"""
        print(f"[ConfigReloader] Config changed: {self.config_path}")
        
        # 重新加载配置
        if self.settings:
            new_settings = load_settings(account_path=self.config_path)
            # 更新现有设置
            for key in self.settings.__dict__:
                if hasattr(new_settings, key):
                    setattr(self.settings, key, getattr(new_settings, key))
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[ConfigReloader] Callback error: {e}")
    
    def start(self) -> None:
        """启动文件监听"""
        if not WATCHDOG_AVAILABLE:
            print("[ConfigReloader] watchdog not installed, hot reload disabled")
            print("[ConfigReloader] Install with: pip install watchdog")
            return
        
        if self._running:
            return
        
        self._handler = ConfigReloadHandler(self.config_path, self._on_config_changed)
        self._observer = Observer()
        
        watch_dir = os.path.dirname(os.path.abspath(self.config_path))
        self._observer.schedule(self._handler, watch_dir, recursive=False)
        self._observer.start()
        
        self._running = True
        print(f"[ConfigReloader] Started watching: {self.config_path}")
    
    def stop(self) -> None:
        """停止文件监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        self._running = False
        print("[ConfigReloader] Stopped")
    
    def reload_once(self) -> None:
        """手动触发一次重载"""
        self._on_config_changed()


# 全局配置重载器实例
_reloader: Optional[ConfigReloader] = None


def get_reloader(config_path: str, settings: Optional[CrawlerSettings] = None) -> ConfigReloader:
    """获取或创建配置重载器"""
    global _reloader
    if _reloader is None:
        _reloader = ConfigReloader(config_path, settings)
    return _reloader


def enable_hot_reload(config_path: str, settings: Optional[CrawlerSettings] = None) -> ConfigReloader:
    """启用配置热重载"""
    reloader = get_reloader(config_path, settings)
    reloader.start()
    return reloader


def disable_hot_reload() -> None:
    """禁用配置热重载"""
    global _reloader
    if _reloader:
        _reloader.stop()
        _reloader = None
