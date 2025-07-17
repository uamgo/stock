"""
选股命令

提供股票选择功能
"""

import argparse
from typing import Any
from ...strategies.tail_up_strategy import TailUpStrategy
from ...config.trading_config import TradingConfig
from ...config.logging_config import get_logger
from ...config.settings import Settings
from ..ui.table import print_stock_table
from datetime import datetime
import json

def add_select_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    添加选股命令解析器
    
    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser(
        "select",
        help="选股模式",
        description="基于技术分析选择适合尾盘买入的股票"
    )
    
    parser.add_argument(
        "--preset",
        type=str,
        choices=["conservative", "balanced", "aggressive"],
        help="使用预设配置"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json", "csv"],
        default="table",
        help="输出格式"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="最大显示数量"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细的筛选过程信息"
    )

def execute_select(args: argparse.Namespace) -> int:
    """
    执行选股命令
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    logger = get_logger("select_command")
    
    # 根据 verbose 参数设置日志级别
    if args.verbose:
        import logging
        logging.getLogger("tail_up_strategy").setLevel(logging.DEBUG)
        strategy_logger = get_logger("tail_up_strategy")
        strategy_logger.setLevel(logging.DEBUG)
    
    print("=== 尾盘选股系统 ===")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 加载配置
        if args.preset:
            config = TradingConfig.get_preset(args.preset)
            print(f"使用预设配置: {args.preset}")
        else:
            config = TradingConfig.load()
            print("使用默认配置")
        
        # 创建策略
        strategy = TailUpStrategy(config)
        
        # 显示策略信息
        timing_advice = strategy.get_timing_advice()
        print("【时机分析】")
        for advice in timing_advice:
            print(f"  {advice}")
        print()
        
        # 执行选股
        print("正在分析股票...")
        selected_stocks = strategy.select_stocks()
        
        if selected_stocks.empty:
            print("❌ 当前没有符合条件的股票")
            return 0
        
        # 限制显示数量
        if len(selected_stocks) > args.limit:
            selected_stocks = selected_stocks.head(args.limit)
        
        print(f"✅ 找到 {len(selected_stocks)} 只适合尾盘买入的股票")
        print()
        
        # 输出结果
        if args.format == "table":
            print_stock_table(selected_stocks)
        elif args.format == "json":
            print(selected_stocks.to_json(orient="records", indent=2, force_ascii=False))
        elif args.format == "csv":
            print(selected_stocks.to_csv(index=False))
        
        # 保存结果
        output_path = args.output
        if output_path is None:
            # 根据预设配置生成文件名
            preset_suffix = f"_{args.preset}" if args.preset else ""
            output_path = str(Settings.DEFAULT_OUTPUT_DIR / f"selected_stocks{preset_suffix}.txt")
        
        # 保存股票代码
        codes = ",".join(map(str, selected_stocks["代码"]))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(codes)
        
        print(f"📁 股票代码已保存到: {output_path}")
        
        # 保存详细报告
        preset_suffix = f"_{args.preset}" if args.preset else ""
        report_path = str(Settings.DEFAULT_OUTPUT_DIR / f"stock_analysis_report{preset_suffix}.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== 尾盘选股分析报告 ===\n\n")
            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"使用配置: {args.preset or 'default'}\n")
            f.write(f"符合条件股票数量: {len(selected_stocks)}\n\n")
            
            f.write("【时机分析】\n")
            for advice in timing_advice:
                f.write(f"  {advice}\n")
            f.write("\n")
            
            f.write("【选股结果】\n")
            for i, (_, row) in enumerate(selected_stocks.iterrows()):
                f.write(f"【排名 {i+1}】{row['名称']}（{row['代码']}）\n")
                f.write(f"  涨跌幅: {row['涨跌幅']:.2f}%\n")
                f.write(f"  次日补涨概率: {row['次日补涨概率']:.0f}分\n")
                f.write(f"  风险评分: {row['风险评分']:.0f}分\n")
                f.write(f"  量比: {row['量比']:.2f}倍\n")
                f.write(f"  收盘价: {row['收盘价']:.2f}元\n")
                f.write(f"  20日位置: {row['20日位置']:.1f}%\n")
                f.write("\n")
        
        print(f"📄 详细报告已保存到: {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"选股失败: {e}")
        print(f"❌ 选股失败: {e}")
        return 1
