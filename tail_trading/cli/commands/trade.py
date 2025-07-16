"""
交易命令

提供交易管理功能
"""

import argparse
from ...core.position_manager import PositionManager
from ...strategies.tail_up_strategy import TailUpStrategy
from ...config.trading_config import TradingConfig
from ...config.logging_config import get_logger
from ..ui.table import print_stock_table
from datetime import datetime

def add_trade_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    添加交易命令解析器
    
    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser(
        "trade",
        help="交易管理模式",
        description="完整的交易管理系统，包含选股、买入、卖出、风险管理"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "manual"],
        default="auto",
        help="交易模式"
    )
    
    parser.add_argument(
        "--preset",
        type=str,
        choices=["conservative", "balanced", "aggressive"],
        help="使用预设配置"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，不执行实际交易"
    )

def execute_trade(args: argparse.Namespace) -> int:
    """
    执行交易命令
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    logger = get_logger("trade_command")
    
    print("=== 尾盘交易管理系统 ===")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式: {'模拟运行' if args.dry_run else '实际交易'}")
    print()
    
    try:
        # 加载配置
        if args.preset:
            config = TradingConfig.get_preset(args.preset)
            print(f"使用预设配置: {args.preset}")
        else:
            config = TradingConfig.load()
            print("使用默认配置")
        
        # 创建管理器
        position_manager = PositionManager()
        strategy = TailUpStrategy(config)
        
        # 显示当前持仓
        positions = position_manager.get_all_positions()
        if positions:
            print(f"当前持仓: {len(positions)} 只股票")
            for code, position in positions.items():
                print(f"  {position.name}({code}): {position.quantity}股")
        else:
            print("当前无持仓")
        print()
        
        # 获取时机建议
        timing_advice = strategy.get_timing_advice()
        print("【时机分析】")
        for advice in timing_advice:
            print(f"  {advice}")
        print()
        
        # 执行选股
        if args.mode == "auto":
            print("正在执行自动选股...")
            selected_stocks = strategy.select_stocks()
            
            if selected_stocks.empty:
                print("❌ 当前没有符合条件的股票")
                return 0
            
            print(f"✅ 找到 {len(selected_stocks)} 只适合尾盘买入的股票")
            print()
            
            # 显示选股结果
            print_stock_table(selected_stocks.head(10))
            
            if args.dry_run:
                print("🔍 模拟运行模式，不执行实际交易")
            else:
                print("💡 提示：实际交易功能需要对接券商API")
        
        elif args.mode == "manual":
            print("📝 手动交易模式")
            print("请使用 'monitor' 命令查看持仓状态")
            print("请使用 'select' 命令获取选股建议")
        
        return 0
        
    except Exception as e:
        logger.error(f"交易管理失败: {e}")
        print(f"❌ 交易管理失败: {e}")
        return 1
