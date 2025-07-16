"""
配置命令

提供配置管理功能
"""

import argparse
from ...config.trading_config import TradingConfig
from ...config.logging_config import get_logger
from ..ui.table import print_summary_box
from datetime import datetime
import json

def add_config_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    添加配置命令解析器
    
    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser(
        "config",
        help="配置管理",
        description="管理交易配置和系统设置"
    )
    
    parser.add_argument(
        "--preset",
        type=str,
        choices=["conservative", "balanced", "aggressive"],
        help="设置预设配置"
    )
    
    parser.add_argument(
        "--show",
        action="store_true",
        help="显示当前配置"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用预设"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="导出配置到指定文件"
    )
    
    parser.add_argument(
        "--import",
        type=str,
        dest="import_file",
        help="从指定文件导入配置"
    )

def execute_config(args: argparse.Namespace) -> int:
    """
    执行配置命令
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    logger = get_logger("config_command")
    
    print("=== 配置管理系统 ===")
    print(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        if args.list:
            # 列出所有预设配置
            print("📋 可用预设配置:")
            print("-" * 40)
            
            presets = TradingConfig.get_available_presets()
            for name, description in presets.items():
                print(f"  {name:12} - {description}")
            
            print()
            print("使用方法: tail-trading config --preset <配置名>")
        
        elif args.preset:
            # 设置预设配置
            config = TradingConfig.get_preset(args.preset)
            config.save()
            
            print(f"✅ 已设置为 {args.preset} 配置")
            print()
            
            # 显示配置详情
            _show_config_details(config)
        
        elif args.show:
            # 显示当前配置
            config = TradingConfig.load()
            print("📊 当前配置:")
            print("-" * 30)
            _show_config_details(config)
        
        elif args.export:
            # 导出配置
            config = TradingConfig.load()
            
            with open(args.export, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"📁 配置已导出到: {args.export}")
        
        elif args.import_file:
            # 导入配置
            with open(args.import_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            config = TradingConfig.from_dict(config_data)
            config.save()
            
            print(f"📁 配置已从 {args.import_file} 导入")
            print()
            
            # 显示导入的配置
            _show_config_details(config)
        
        else:
            # 默认显示当前配置
            config = TradingConfig.load()
            print("📊 当前配置:")
            print("-" * 30)
            _show_config_details(config)
        
        return 0
        
    except Exception as e:
        logger.error(f"配置管理失败: {e}")
        print(f"❌ 配置管理失败: {e}")
        return 1

def _show_config_details(config: TradingConfig) -> None:
    """
    显示配置详情
    
    Args:
        config: 交易配置
    """
    # 策略参数
    print_summary_box("策略参数", {
        "最小涨跌幅": f"{config.min_pct_chg:.1f}%",
        "最大涨跌幅": f"{config.max_pct_chg:.1f}%",
        "最小量比": f"{config.min_volume_ratio:.1f}倍",
        "最大量比": f"{config.max_volume_ratio:.1f}倍",
        "最大位置比例": f"{config.max_position_ratio*100:.1f}%"
    })
    
    # 风险控制
    print_summary_box("风险控制", {
        "单只股票仓位": f"{config.max_single_position*100:.1f}%",
        "总仓位上限": f"{config.max_total_position*100:.1f}%",
        "止损比例": f"{config.stop_loss_ratio*100:.1f}%",
        "止盈比例": f"{config.take_profit_ratio*100:.1f}%",
        "最大连续亏损": f"{config.max_consecutive_losses}次"
    })
    
    # 技术指标
    print_summary_box("技术指标", {
        "均线周期": f"{config.ma_period}日",
        "成交量均线": f"{config.volume_ma_period}日",
        "最小下影线比例": f"{config.min_shadow_ratio:.1f}",
        "最大上影线比例": f"{config.max_upper_shadow_ratio:.1f}",
        "回看天数": f"{config.lookback_days}天"
    })
    
    # 评分阈值
    print_summary_box("评分阈值", {
        "低风险阈值": f"{config.low_risk_threshold}分",
        "中风险阈值": f"{config.medium_risk_threshold}分",
        "高风险阈值": f"{config.high_risk_threshold}分",
        "高概率阈值": f"{config.high_prob_threshold}分",
        "中概率阈值": f"{config.medium_prob_threshold}分"
    })
