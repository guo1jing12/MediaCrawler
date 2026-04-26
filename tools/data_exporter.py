# -*- coding: utf-8 -*-
"""
数据导出模块
支持 CSV/Excel 导出
"""

import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class ExportConfig:
    """导出配置"""
    date_format: str = "%Y-%m-%d %H:%M:%S"
    encoding: str = "utf-8-sig"  # 带BOM，Excel兼容
    delimiter: str = ","


class DataExporter:
    """数据导出器"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
    
    def export_csv(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        导出 CSV
        
        Args:
            data: 数据列表
            columns: 指定导出的列（None表示全部）
            headers: 列名映射 {字段名: 显示名}
        
        Returns:
            str: CSV 内容
        """
        if not data:
            return ""
        
        # 确定列
        if columns is None:
            columns = list(data[0].keys())
        
        # 创建 StringIO
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        header_row = []
        for col in columns:
            display_name = headers.get(col, col) if headers else col
            header_row.append(display_name)
        writer.writerow(header_row)
        
        # 写入数据
        for row in data:
            data_row = []
            for col in columns:
                value = row.get(col, "")
                # 处理特殊类型
                if isinstance(value, datetime):
                    value = value.strftime(self.config.date_format)
                elif isinstance(value, date):
                    value = value.strftime("%Y-%m-%d")
                elif isinstance(value, (list, dict)):
                    value = str(value)
                data_row.append(value)
            writer.writerow(data_row)
        
        return output.getvalue()
    
    def export_excel(
        self,
        data: List[Dict[str, Any]],
        sheet_name: str = "Sheet1",
        columns: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """
        导出 Excel
        
        Args:
            data: 数据列表
            sheet_name: 工作表名称
            columns: 指定导出的列
            headers: 列名映射
        
        Returns:
            bytes: Excel 文件内容
        """
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
        
        if not data:
            return b""
        
        # 确定列
        if columns is None:
            columns = list(data[0].keys())
        
        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # 写入表头
        header_row = []
        for col in columns:
            display_name = headers.get(col, col) if headers else col
            header_row.append(display_name)
        ws.append(header_row)
        
        # 写入数据
        for row in data:
            data_row = []
            for col in columns:
                value = row.get(col, "")
                # 处理特殊类型
                if isinstance(value, datetime):
                    value = value.strftime(self.config.date_format)
                elif isinstance(value, date):
                    value = value.strftime("%Y-%m-%d")
                elif isinstance(value, (list, dict)):
                    value = str(value)
                data_row.append(value)
            ws.append(data_row)
        
        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()
    
    def export_notes(
        self,
        notes: List[Dict[str, Any]],
        format: str = "csv",
    ) -> Any:
        """
        导出帖子数据
        
        Args:
            notes: 帖子数据列表
            format: 导出格式 csv/excel
        
        Returns:
            str/bytes: 导出内容
        """
        columns = ["note_id", "title", "desc", "type", "user_id", "nickname", 
                   "likes", "collects", "comments", "shares", "create_time", "keyword"]
        headers = {
            "note_id": "帖子ID",
            "title": "标题",
            "desc": "描述",
            "type": "类型",
            "user_id": "用户ID",
            "nickname": "昵称",
            "likes": "点赞数",
            "collects": "收藏数",
            "comments": "评论数",
            "shares": "分享数",
            "create_time": "创建时间",
            "keyword": "关键词",
        }
        
        if format == "csv":
            return self.export_csv(notes, columns, headers)
        elif format == "excel":
            return self.export_excel(notes, "帖子数据", columns, headers)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_accounts(
        self,
        accounts: List[Dict[str, Any]],
        format: str = "csv",
    ) -> Any:
        """
        导出账号数据
        
        Args:
            accounts: 账号数据列表
            format: 导出格式 csv/excel
        
        Returns:
            str/bytes: 导出内容
        """
        columns = ["name", "platform", "status", "success_rate", "total_notes", "today_notes", "last_crawl"]
        headers = {
            "name": "账号名称",
            "platform": "平台",
            "status": "状态",
            "success_rate": "成功率",
            "total_notes": "总帖子数",
            "today_notes": "今日帖子数",
            "last_crawl": "最后爬取时间",
        }
        
        if format == "csv":
            return self.export_csv(accounts, columns, headers)
        elif format == "excel":
            return self.export_excel(accounts, "账号数据", columns, headers)
        else:
            raise ValueError(f"Unsupported format: {format}")


# 便捷函数
def export_to_csv(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    """便捷导出 CSV"""
    exporter = DataExporter()
    return exporter.export_csv(data, columns)


def export_to_excel(data: List[Dict[str, Any]], sheet_name: str = "Sheet1") -> bytes:
    """便捷导出 Excel"""
    exporter = DataExporter()
    return exporter.export_excel(data, sheet_name)
