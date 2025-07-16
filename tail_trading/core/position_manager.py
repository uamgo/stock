"""
持仓管理器

管理交易持仓、盈亏计算和历史记录
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from ..config.settings import Settings
from ..config.logging_config import get_logger

@dataclass
class Position:
    """持仓信息"""
    code: str
    name: str
    buy_price: float
    buy_time: str
    quantity: int
    current_price: float = 0.0
    current_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    status: str = "HOLDING"  # HOLDING, SOLD, STOPPED
    
    def update_current_price(self, price: float) -> None:
        """更新当前价格"""
        self.current_price = price
        self.current_value = price * self.quantity
        self.profit_loss = self.current_value - (self.buy_price * self.quantity)
        self.profit_loss_pct = self.profit_loss / (self.buy_price * self.quantity) * 100

@dataclass
class Trade:
    """交易记录"""
    code: str
    name: str
    action: str  # BUY, SELL
    price: float
    quantity: int
    amount: float
    timestamp: str
    reason: str = ""

class PositionManager:
    """持仓管理器"""
    
    def __init__(self):
        """初始化持仓管理器"""
        self.logger = get_logger("position_manager")
        self.positions_file = Path.home() / ".tail_trading_positions.json"
        self.trades_file = Path.home() / ".tail_trading_trades.json"
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.load_data()
    
    def load_data(self) -> None:
        """加载持仓和交易数据"""
        # 加载持仓数据
        if self.positions_file.exists():
            try:
                with open(self.positions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.positions = {
                        code: Position(**pos_data) 
                        for code, pos_data in data.items()
                    }
            except Exception as e:
                self.logger.error(f"Failed to load positions: {e}")
                self.positions = {}
        
        # 加载交易数据
        if self.trades_file.exists():
            try:
                with open(self.trades_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trades = [Trade(**trade_data) for trade_data in data]
            except Exception as e:
                self.logger.error(f"Failed to load trades: {e}")
                self.trades = []
    
    def save_data(self) -> None:
        """保存持仓和交易数据"""
        # 保存持仓数据
        try:
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                data = {code: asdict(pos) for code, pos in self.positions.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save positions: {e}")
        
        # 保存交易数据
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                data = [asdict(trade) for trade in self.trades]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save trades: {e}")
    
    def add_position(self, code: str, name: str, buy_price: float, 
                    quantity: int, buy_time: str = None) -> None:
        """
        添加持仓
        
        Args:
            code: 股票代码
            name: 股票名称
            buy_price: 买入价格
            quantity: 买入数量
            buy_time: 买入时间
        """
        if buy_time is None:
            buy_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        position = Position(
            code=code,
            name=name,
            buy_price=buy_price,
            buy_time=buy_time,
            quantity=quantity
        )
        
        self.positions[code] = position
        
        # 记录交易
        trade = Trade(
            code=code,
            name=name,
            action="BUY",
            price=buy_price,
            quantity=quantity,
            amount=buy_price * quantity,
            timestamp=buy_time
        )
        self.trades.append(trade)
        
        self.save_data()
        self.logger.info(f"Added position: {code} {name} at {buy_price}")
    
    def close_position(self, code: str, sell_price: float, 
                      sell_time: str = None, reason: str = "") -> Optional[Position]:
        """
        平仓
        
        Args:
            code: 股票代码
            sell_price: 卖出价格
            sell_time: 卖出时间
            reason: 平仓原因
            
        Returns:
            被平仓的持仓信息
        """
        if code not in self.positions:
            self.logger.warning(f"Position not found: {code}")
            return None
        
        if sell_time is None:
            sell_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        position = self.positions[code]
        position.update_current_price(sell_price)
        position.status = "SOLD"
        
        # 记录交易
        trade = Trade(
            code=code,
            name=position.name,
            action="SELL",
            price=sell_price,
            quantity=position.quantity,
            amount=sell_price * position.quantity,
            timestamp=sell_time,
            reason=reason
        )
        self.trades.append(trade)
        
        # 从持仓中移除
        closed_position = self.positions.pop(code)
        
        self.save_data()
        self.logger.info(f"Closed position: {code} at {sell_price}, P&L: {position.profit_loss:.2f}")
        
        return closed_position
    
    def update_positions(self, price_data: Dict[str, float]) -> None:
        """
        更新持仓价格
        
        Args:
            price_data: 股票代码到当前价格的映射
        """
        for code, position in self.positions.items():
            if code in price_data:
                position.update_current_price(price_data[code])
        
        self.save_data()
    
    def get_position(self, code: str) -> Optional[Position]:
        """
        获取持仓信息
        
        Args:
            code: 股票代码
            
        Returns:
            持仓信息或None
        """
        return self.positions.get(code)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓
        
        Returns:
            所有持仓信息
        """
        return self.positions.copy()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        获取投资组合摘要
        
        Returns:
            投资组合摘要
        """
        if not self.positions:
            return {
                "total_positions": 0,
                "total_value": 0.0,
                "total_cost": 0.0,
                "total_profit_loss": 0.0,
                "total_profit_loss_pct": 0.0,
                "positions": []
            }
        
        total_value = 0.0
        total_cost = 0.0
        positions_info = []
        
        for position in self.positions.values():
            cost = position.buy_price * position.quantity
            value = position.current_price * position.quantity
            
            total_cost += cost
            total_value += value
            
            positions_info.append({
                "code": position.code,
                "name": position.name,
                "buy_price": position.buy_price,
                "current_price": position.current_price,
                "quantity": position.quantity,
                "cost": cost,
                "value": value,
                "profit_loss": position.profit_loss,
                "profit_loss_pct": position.profit_loss_pct,
                "status": position.status
            })
        
        total_profit_loss = total_value - total_cost
        total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_positions": len(self.positions),
            "total_value": total_value,
            "total_cost": total_cost,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_pct": total_profit_loss_pct,
            "positions": positions_info
        }
    
    def get_trade_history(self, days: int = 30) -> List[Trade]:
        """
        获取交易历史
        
        Args:
            days: 查询天数
            
        Returns:
            交易历史列表
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_trades = []
        for trade in self.trades:
            try:
                trade_date = datetime.strptime(trade.timestamp, "%Y-%m-%d %H:%M:%S")
                if trade_date >= cutoff_date:
                    recent_trades.append(trade)
            except ValueError:
                continue
        
        return sorted(recent_trades, key=lambda x: x.timestamp, reverse=True)
    
    def calculate_performance(self, days: int = 30) -> Dict[str, Any]:
        """
        计算交易业绩
        
        Args:
            days: 统计天数
            
        Returns:
            业绩统计
        """
        recent_trades = self.get_trade_history(days)
        
        if not recent_trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_profit_loss": 0.0,
                "average_profit_loss": 0.0,
                "max_profit": 0.0,
                "max_loss": 0.0
            }
        
        # 按股票代码分组计算每笔完整交易的盈亏
        completed_trades = {}
        for trade in recent_trades:
            if trade.code not in completed_trades:
                completed_trades[trade.code] = {"buy": None, "sell": None}
            
            if trade.action == "BUY":
                completed_trades[trade.code]["buy"] = trade
            elif trade.action == "SELL":
                completed_trades[trade.code]["sell"] = trade
        
        # 计算已完成交易的盈亏
        profits_losses = []
        for code, trades in completed_trades.items():
            if trades["buy"] and trades["sell"]:
                buy_amount = trades["buy"].amount
                sell_amount = trades["sell"].amount
                pl = sell_amount - buy_amount
                profits_losses.append(pl)
        
        if not profits_losses:
            return {
                "total_trades": len(recent_trades),
                "completed_trades": 0,
                "win_rate": 0.0,
                "total_profit_loss": 0.0,
                "average_profit_loss": 0.0,
                "max_profit": 0.0,
                "max_loss": 0.0
            }
        
        winning_trades = [pl for pl in profits_losses if pl > 0]
        total_profit_loss = sum(profits_losses)
        
        return {
            "total_trades": len(recent_trades),
            "completed_trades": len(profits_losses),
            "win_rate": len(winning_trades) / len(profits_losses) * 100,
            "total_profit_loss": total_profit_loss,
            "average_profit_loss": total_profit_loss / len(profits_losses),
            "max_profit": max(profits_losses) if profits_losses else 0.0,
            "max_loss": min(profits_losses) if profits_losses else 0.0
        }
    
    def clear_all_positions(self) -> None:
        """清空所有持仓"""
        self.positions.clear()
        self.save_data()
        self.logger.info("Cleared all positions")
    
    def export_data(self, export_path: Path = None) -> None:
        """
        导出数据
        
        Args:
            export_path: 导出路径
        """
        if export_path is None:
            export_path = Settings.EXPORTS_DIR / f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        Settings.ensure_directories()
        
        export_data = {
            "positions": {code: asdict(pos) for code, pos in self.positions.items()},
            "trades": [asdict(trade) for trade in self.trades],
            "export_time": datetime.now().isoformat()
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data exported to {export_path}")
