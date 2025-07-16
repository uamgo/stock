"""
表格显示工具

提供美观的表格输出功能
"""

import pandas as pd
from typing import List, Dict, Any

def print_stock_table(stocks_df: pd.DataFrame) -> None:
    """
    打印股票表格
    
    Args:
        stocks_df: 股票数据DataFrame
    """
    if stocks_df.empty:
        print("没有数据可显示")
        return
    
    # 定义显示列和格式
    display_columns = [
        ("排名", ""),
        ("代码", "代码"),
        ("名称", "名称"),
        ("涨跌幅", "涨跌幅"),
        ("补涨概率", "次日补涨概率"),
        ("风险评分", "风险评分"),
        ("量比", "量比"),
        ("收盘价", "收盘价"),
        ("20日位置", "20日位置")
    ]
    
    # 计算列宽
    col_widths = {}
    for display_name, col_name in display_columns:
        if display_name == "排名":
            col_widths[display_name] = 6
        elif display_name == "代码":
            col_widths[display_name] = 10
        elif display_name == "名称":
            if col_name in stocks_df.columns:
                # 计算名称的最大宽度
                max_width = max(len(str(val)) for val in stocks_df[col_name]) if not stocks_df[col_name].empty else 4
                col_widths[display_name] = max(min(max_width, 12), 6)  # 最小6，最大12
            else:
                col_widths[display_name] = 6
        elif display_name == "涨跌幅":
            col_widths[display_name] = 10
        elif display_name == "补涨概率":
            col_widths[display_name] = 10
        elif display_name == "风险评分":
            col_widths[display_name] = 10
        elif display_name == "量比":
            col_widths[display_name] = 10
        elif display_name == "收盘价":
            col_widths[display_name] = 10
        elif display_name == "20日位置":
            col_widths[display_name] = 10
        else:
            col_widths[display_name] = 8
    
    # 打印表头
    header = "┌" + "─" * (sum(col_widths.values()) + len(col_widths) * 3 - 1) + "┐"
    print(header)
    
    # 打印列名
    header_row = "│"
    for display_name, _ in display_columns:
        width = col_widths[display_name]
        header_row += f" {display_name:^{width}} │"
    print(header_row)
    
    # 打印分隔线
    separator = "├"
    for display_name, _ in display_columns:
        width = col_widths[display_name]
        separator += "─" * (width + 2) + "┼"
    separator = separator[:-1] + "┤"
    print(separator)
    
    # 打印数据行
    for i, (_, row) in enumerate(stocks_df.iterrows()):
        data_row = "│"
        
        for display_name, col_name in display_columns:
            width = col_widths[display_name]
            
            if display_name == "排名":
                value = f"{i+1}"
                data_row += f" {value:^{width}} │"
            elif col_name in stocks_df.columns:
                raw_value = row[col_name]
                
                # 格式化数据
                if col_name == "涨跌幅":
                    color = "🟢" if raw_value > 0 else "🔴"
                    value = f"{color}{raw_value:.2f}%"
                elif col_name == "次日补涨概率":
                    if raw_value >= 75:
                        value = f"🟢{raw_value:.0f}分"
                    elif raw_value >= 65:
                        value = f"🟡{raw_value:.0f}分"
                    else:
                        value = f"🟠{raw_value:.0f}分"
                elif col_name == "风险评分":
                    if raw_value <= 40:
                        value = f"🟢{raw_value:.0f}分"
                    elif raw_value <= 60:
                        value = f"🟡{raw_value:.0f}分"
                    else:
                        value = f"🔴{raw_value:.0f}分"
                elif col_name == "量比":
                    value = f"{raw_value:.2f}倍"
                elif col_name == "收盘价":
                    value = f"{raw_value:.2f}元"
                elif col_name == "20日位置":
                    value = f"{raw_value:.1f}%"
                else:
                    value = str(raw_value)
                
                # 截断过长的文本
                if len(value) > width:
                    value = value[:width-2] + ".."
                
                data_row += f" {value:<{width}} │"
            else:
                data_row += f" {'':<{width}} │"
        
        print(data_row)
    
    # 打印底部
    footer = "└" + "─" * (sum(col_widths.values()) + len(col_widths) * 3 - 1) + "┘"
    print(footer)
    print()

def print_position_table(positions: List[Dict[str, Any]]) -> None:
    """
    打印持仓表格
    
    Args:
        positions: 持仓数据列表
    """
    if not positions:
        print("没有持仓数据")
        return
    
    # 定义显示列
    display_columns = [
        ("代码", "code"),
        ("名称", "name"),
        ("买入价", "buy_price"),
        ("现价", "current_price"),
        ("数量", "quantity"),
        ("市值", "value"),
        ("盈亏", "profit_loss"),
        ("盈亏率", "profit_loss_pct"),
        ("状态", "status")
    ]
    
    # 计算列宽
    col_widths = {display_name: 8 for display_name, _ in display_columns}
    col_widths["名称"] = 10
    col_widths["代码"] = 8
    
    # 打印表头
    header = "┌" + "─" * (sum(col_widths.values()) + len(col_widths) * 3 - 1) + "┐"
    print(header)
    
    # 打印列名
    header_row = "│"
    for display_name, _ in display_columns:
        width = col_widths[display_name]
        header_row += f" {display_name:^{width}} │"
    print(header_row)
    
    # 打印分隔线
    separator = "├"
    for display_name, _ in display_columns:
        width = col_widths[display_name]
        separator += "─" * (width + 2) + "┼"
    separator = separator[:-1] + "┤"
    print(separator)
    
    # 打印数据行
    for position in positions:
        data_row = "│"
        
        for display_name, col_name in display_columns:
            width = col_widths[display_name]
            raw_value = position.get(col_name, "")
            
            # 格式化数据
            if col_name in ["buy_price", "current_price"]:
                value = f"{raw_value:.2f}元"
            elif col_name == "quantity":
                value = f"{raw_value}股"
            elif col_name == "value":
                value = f"{raw_value:.2f}元"
            elif col_name == "profit_loss":
                color = "🟢" if raw_value > 0 else "🔴"
                value = f"{color}{raw_value:.2f}元"
            elif col_name == "profit_loss_pct":
                color = "🟢" if raw_value > 0 else "🔴"
                value = f"{color}{raw_value:.2f}%"
            elif col_name == "status":
                status_map = {
                    "HOLDING": "持有",
                    "SOLD": "已卖出",
                    "STOPPED": "已止损"
                }
                value = status_map.get(raw_value, raw_value)
            else:
                value = str(raw_value)
            
            # 截断过长的文本
            if len(value) > width:
                value = value[:width-2] + ".."
            
            data_row += f" {value:<{width}} │"
        
        print(data_row)
    
    # 打印底部
    footer = "└" + "─" * (sum(col_widths.values()) + len(col_widths) * 3 - 1) + "┘"
    print(footer)
    print()

def print_summary_box(title: str, data: Dict[str, Any]) -> None:
    """
    打印摘要信息框
    
    Args:
        title: 标题
        data: 数据字典
    """
    # 计算最大宽度
    max_width = max(len(str(v)) for v in data.values()) + 20
    max_width = max(max_width, len(title) + 4)
    
    # 打印标题框
    print("┌" + "─" * (max_width - 2) + "┐")
    print(f"│ {title:^{max_width-4}} │")
    print("├" + "─" * (max_width - 2) + "┤")
    
    # 打印数据
    for key, value in data.items():
        if isinstance(value, float):
            if "比例" in key or "%" in key:
                formatted_value = f"{value:.2f}%"
            else:
                formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        
        print(f"│ {key}: {formatted_value:>{max_width-len(key)-6}} │")
    
    print("└" + "─" * (max_width - 2) + "┘")
    print()
