"""
命令模块

包含所有CLI命令的实现
"""

from .select import add_select_parser, execute_select
from .trade import add_trade_parser, execute_trade
from .monitor import add_monitor_parser, execute_monitor
from .config import add_config_parser, execute_config
from .update import add_update_parser, execute_update

__all__ = [
    "add_select_parser",
    "execute_select",
    "add_trade_parser", 
    "execute_trade",
    "add_monitor_parser",
    "execute_monitor",
    "add_config_parser",
    "execute_config",
    "add_update_parser",
    "execute_update"
]
