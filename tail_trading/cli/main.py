"""
主命令行程序

提供统一的命令行接口
"""

import argparse
import sys
from typing import List, Optional
from ..config.logging_config import setup_logging
from ..config.settings import Settings

def main(args: Optional[List[str]] = None) -> int:
    """
    主入口函数
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    # 设置日志
    setup_logging()
    
    # 确保目录存在
    Settings.ensure_directories()
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="A股尾盘交易系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  tail-trading select                    # 选股
  tail-trading select --preset conservative  # 使用保守配置选股
  tail-trading trade                     # 交易管理
  tail-trading monitor                   # 监控持仓
  tail-trading monitor --history         # 查看历史
  tail-trading config --list             # 查看配置
  tail-trading config --preset balanced  # 设置配置
  tail-trading update                    # 更新数据
  tail-trading update --top-n 20         # 更新top20板块数据
        """
    )
    
    # 添加版本信息
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 3.0.0"
    )
    
    # 添加全局选项
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--config-file",
        type=str,
        help="指定配置文件路径"
    )
    
    # 添加子命令
    subparsers = parser.add_subparsers(
        dest="command",
        help="可用命令",
        metavar="COMMAND"
    )
    
    # 选股命令
    from .commands.select import add_select_parser
    add_select_parser(subparsers)
    
    # 交易命令
    from .commands.trade import add_trade_parser
    add_trade_parser(subparsers)
    
    # 监控命令
    from .commands.monitor import add_monitor_parser
    add_monitor_parser(subparsers)
    
    # 配置命令
    from .commands.config import add_config_parser
    add_config_parser(subparsers)
    
    # 数据更新命令
    from .commands.update import add_update_parser
    add_update_parser(subparsers)
    
    # 解析参数
    parsed_args = parser.parse_args(args)
    
    # 如果没有指定命令，显示帮助
    if not parsed_args.command:
        parser.print_help()
        return 0
    
    try:
        # 执行相应命令
        if parsed_args.command == "select":
            from .commands.select import execute_select
            return execute_select(parsed_args)
        elif parsed_args.command == "trade":
            from .commands.trade import execute_trade
            return execute_trade(parsed_args)
        elif parsed_args.command == "monitor":
            from .commands.monitor import execute_monitor
            return execute_monitor(parsed_args)
        elif parsed_args.command == "config":
            from .commands.config import execute_config
            return execute_config(parsed_args)
        elif parsed_args.command == "update":
            from .commands.update import execute_update
            return execute_update(parsed_args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 1
    except Exception as e:
        print(f"错误: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
