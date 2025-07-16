"""
监控命令

提供持仓监控和交易历史查询功能
"""

import argparse
from ...core.position_manager import PositionManager
from ...config.logging_config import get_logger
from ..ui.table import print_position_table, print_summary_box
from datetime import datetime

def add_monitor_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    添加监控命令解析器
    
    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser(
        "monitor",
        help="监控模式",
        description="监控持仓盈亏和交易历史"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="显示交易历史"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="查询天数"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="显示投资组合摘要"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="导出数据到指定路径"
    )

def execute_monitor(args: argparse.Namespace) -> int:
    """
    执行监控命令
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    logger = get_logger("monitor_command")
    
    print("=== 持仓监控系统 ===")
    print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 创建持仓管理器
        position_manager = PositionManager()
        
        if args.history:
            # 显示交易历史
            print(f"📈 交易历史（最近{args.days}天）")
            print("-" * 50)
            
            trades = position_manager.get_trade_history(args.days)
            
            if not trades:
                print("无交易记录")
            else:
                for trade in trades:
                    action_emoji = "🟢" if trade.action == "BUY" else "🔴"
                    print(f"{action_emoji} {trade.timestamp} | {trade.name}({trade.code})")
                    print(f"    {trade.action} {trade.quantity}股 @ {trade.price:.2f}元")
                    print(f"    金额: {trade.amount:.2f}元")
                    if trade.reason:
                        print(f"    原因: {trade.reason}")
                    print()
            
            # 显示业绩统计
            performance = position_manager.calculate_performance(args.days)
            print(f"📊 业绩统计（最近{args.days}天）")
            print_summary_box("交易统计", {
                "总交易次数": performance["total_trades"],
                "完成交易": performance["completed_trades"],
                "胜率": f"{performance['win_rate']:.1f}%",
                "总盈亏": f"{performance['total_profit_loss']:.2f}元",
                "平均盈亏": f"{performance['average_profit_loss']:.2f}元",
                "最大盈利": f"{performance['max_profit']:.2f}元",
                "最大亏损": f"{performance['max_loss']:.2f}元"
            })
        
        else:
            # 显示当前持仓
            positions = position_manager.get_all_positions()
            
            if not positions:
                print("📭 当前无持仓")
            else:
                print(f"📊 当前持仓（{len(positions)}只股票）")
                print("-" * 50)
                
                # 转换为列表格式
                positions_list = []
                for code, position in positions.items():
                    positions_list.append({
                        "code": position.code,
                        "name": position.name,
                        "buy_price": position.buy_price,
                        "current_price": position.current_price,
                        "quantity": position.quantity,
                        "value": position.current_value,
                        "profit_loss": position.profit_loss,
                        "profit_loss_pct": position.profit_loss_pct,
                        "status": position.status
                    })
                
                print_position_table(positions_list)
        
        if args.summary:
            # 显示投资组合摘要
            summary = position_manager.get_portfolio_summary()
            print("📋 投资组合摘要")
            print_summary_box("组合统计", {
                "持仓数量": summary["total_positions"],
                "总市值": f"{summary['total_value']:.2f}元",
                "总成本": f"{summary['total_cost']:.2f}元",
                "总盈亏": f"{summary['total_profit_loss']:.2f}元",
                "总收益率": f"{summary['total_profit_loss_pct']:.2f}%"
            })
        
        if args.export:
            # 导出数据
            from pathlib import Path
            export_path = Path(args.export)
            position_manager.export_data(export_path)
            print(f"📁 数据已导出到: {export_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"监控失败: {e}")
        print(f"❌ 监控失败: {e}")
        return 1
