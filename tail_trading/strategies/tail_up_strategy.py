"""
尾盘上涨策略

基于原有up_up.py策略，重构为标准的策略类
"""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from ..core.strategy import BaseStrategy
from ..config.trading_config import TradingConfig
from ..data.eastmoney.daily_fetcher import EastmoneyDataFetcher

class TailUpStrategy(BaseStrategy):
    """
    尾盘买入次日补涨策略
    
    选择适合尾盘买入、次日补涨卖出的股票，基于以下条件：
    1. 当日涨跌幅在 1-6% 之间（有上涨但不过热）
    2. 成交量适中放大（避免过度炒作）
    3. 技术形态良好（下影线较长，上影线较短）
    4. 近期趋势向好（短期均线上涨）
    5. 没有连续大涨（避免追高风险）
    6. 股价在合理区间（避免高位接盘）
    """
    
    def __init__(self, config: TradingConfig = None):
        """
        初始化策略
        
        Args:
            config: 交易配置
        """
        super().__init__(config)
        self.data_fetcher = EastmoneyDataFetcher()
        
    def select_stocks(self, stocks_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        选择股票
        
        Args:
            stocks_data: 股票数据（如果为None，则自动获取）
            
        Returns:
            选中的股票数据
        """
        if stocks_data is None:
            stocks_data = self.data_fetcher.get_stock_list()
        
        if stocks_data is None or stocks_data.empty or "代码" not in stocks_data.columns:
            self.logger.warning("No stock data available")
            return pd.DataFrame()
        
        # 创建股票代码到名称的映射
        stock_names = {}
        if "名称" in stocks_data.columns:
            stock_names = dict(zip(stocks_data["代码"], stocks_data["名称"]))
        
        result = []
        
        for _, row in stocks_data.iterrows():
            code = row["代码"]
            name = stock_names.get(code, "")
            
            try:
                # 获取日线数据
                daily_df = self.data_fetcher.get_daily_data(code, days=self.config.lookback_days)
                
                if daily_df is None or daily_df.empty or len(daily_df) < self.config.lookback_days:
                    continue
                
                # 分析股票
                stock_analysis = self._analyze_stock(code, daily_df, name)
                
                if stock_analysis is None:
                    continue
                
                # 应用选股条件
                if self._meets_selection_criteria(stock_analysis):
                    result.append(stock_analysis)
                    
            except Exception as e:
                self.logger.error(f"Error analyzing stock {code}: {e}")
                continue
        
        if not result:
            return pd.DataFrame()
        
        # 转换为DataFrame并排序
        df = pd.DataFrame(result)
        return df.sort_values(by="次日补涨概率", ascending=False).reset_index(drop=True)
    
    def _analyze_stock(self, code: str, daily_df: pd.DataFrame, name: str = "") -> Dict[str, Any]:
        """
        分析单只股票
        
        Args:
            code: 股票代码
            daily_df: 日线数据
            name: 股票名称
            
        Returns:
            分析结果字典
        """
        try:
            # 获取最新一天的数据
            last_daily = daily_df.iloc[-1]
            
            # 解析基本数据
            pct_chg = float(last_daily.get("涨跌幅", 0))
            
            # 解析价格数据
            close_prices = pd.to_numeric(daily_df["收盘"], errors="coerce")
            high_prices = pd.to_numeric(daily_df["最高"], errors="coerce")
            low_prices = pd.to_numeric(daily_df["最低"], errors="coerce")
            open_prices = pd.to_numeric(daily_df["开盘"], errors="coerce")
            
            if (close_prices.isnull().any() or high_prices.isnull().any() or 
                low_prices.isnull().any() or open_prices.isnull().any()):
                return None
            
            # 解析成交量数据
            vol = pd.to_numeric(daily_df["成交量"], errors="coerce")
            if vol.isnull().any():
                return None
            
            # 计算技术指标
            today_vol = vol.iloc[-1]
            avg_vol = vol.iloc[-self.config.volume_ma_period:].mean()
            volume_ratio = today_vol / avg_vol if avg_vol > 0 else 0
            
            # 当日价格数据
            today_high = high_prices.iloc[-1]
            today_low = low_prices.iloc[-1]
            today_open = open_prices.iloc[-1]
            today_close = close_prices.iloc[-1]
            
            # 计算影线
            upper_shadow = today_high - max(today_open, today_close)
            lower_shadow = min(today_open, today_close) - today_low
            body_length = abs(today_close - today_open)
            
            # 计算20日位置
            high_20 = high_prices.iloc[-20:].max()
            low_20 = low_prices.iloc[-20:].min()
            position_ratio = (today_close - low_20) / (high_20 - low_20) if high_20 > low_20 else 0
            
            # 计算次日补涨概率
            prob_score = self._calculate_probability_score(
                pct_chg, volume_ratio, lower_shadow, body_length, position_ratio, close_prices
            )
            
            # 构建分析结果
            analysis = {
                "代码": code,
                "名称": name,
                "涨跌幅": pct_chg,
                "量比": volume_ratio,
                "收盘价": today_close,
                "上影线": upper_shadow,
                "下影线": lower_shadow,
                "实体长度": body_length,
                "影线比": lower_shadow / body_length if body_length > 0 else 0,
                "20日位置": position_ratio * 100,
                "次日补涨概率": prob_score,
                "position_ratio": position_ratio,
                "volume_ratio": volume_ratio,
                "pct_chg": pct_chg,
                "upper_shadow": upper_shadow,
                "body_length": body_length,
                "lower_shadow": lower_shadow
            }
            
            # 计算风险评分
            analysis["风险评分"] = self.calculate_risk_score(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in stock analysis for {code}: {e}")
            return None
    
    def _meets_selection_criteria(self, analysis: Dict[str, Any]) -> bool:
        """
        检查是否满足选股条件
        
        Args:
            analysis: 股票分析结果
            
        Returns:
            是否满足条件
        """
        # 条件1：涨跌幅在指定范围内
        if not (self.config.min_pct_chg <= analysis["涨跌幅"] <= self.config.max_pct_chg):
            return False
        
        # 条件2：量比在合理范围内
        if not (self.config.min_volume_ratio <= analysis["量比"] <= self.config.max_volume_ratio):
            return False
        
        # 条件3：技术形态良好
        body_length = analysis["实体长度"]
        upper_shadow = analysis["上影线"]
        lower_shadow = analysis["下影线"]
        
        if body_length <= 0.5:
            # 小实体情况
            if upper_shadow > 2.0:
                return False
        else:
            # 正常实体情况
            if lower_shadow < upper_shadow * 0.8:
                return False
            if upper_shadow > body_length * self.config.max_upper_shadow_ratio:
                return False
        
        # 条件4：位置不能太高
        if analysis["position_ratio"] > self.config.max_position_ratio:
            return False
        
        # 条件5：风险评分不能太高
        if analysis["风险评分"] > self.config.high_risk_threshold:
            return False
        
        return True
    
    def _calculate_probability_score(self, pct_chg: float, volume_ratio: float, 
                                   lower_shadow: float, body_length: float, 
                                   position_ratio: float, close_prices: pd.Series) -> float:
        """
        计算次日补涨概率评分
        
        Args:
            pct_chg: 涨跌幅
            volume_ratio: 量比
            lower_shadow: 下影线
            body_length: 实体长度
            position_ratio: 位置比例
            close_prices: 收盘价序列
            
        Returns:
            概率评分 (0-100)
        """
        score = 0
        
        # 1. 涨跌幅评分
        if 2.0 <= pct_chg <= 4.0:
            score += 25 * self.config.price_weight
        elif 1.0 <= pct_chg < 2.0:
            score += 20 * self.config.price_weight
        elif 4.0 < pct_chg <= 6.0:
            score += 15 * self.config.price_weight
        
        # 2. 量比评分
        if 1.5 <= volume_ratio <= 2.5:
            score += 25 * self.config.volume_weight
        elif 1.2 <= volume_ratio < 1.5:
            score += 20 * self.config.volume_weight
        elif 2.5 < volume_ratio <= 3.0:
            score += 15 * self.config.volume_weight
        else:
            score += 10 * self.config.volume_weight
        
        # 3. 技术形态评分
        if body_length > 0:
            shadow_ratio = lower_shadow / body_length
            if shadow_ratio >= 0.8:
                score += 25 * self.config.technical_weight
            elif shadow_ratio >= 0.5:
                score += 20 * self.config.technical_weight
            elif shadow_ratio >= 0.2:
                score += 15 * self.config.technical_weight
            else:
                score += 10 * self.config.technical_weight
        else:
            # 十字星等小实体情况
            if lower_shadow >= 0:
                score += 20 * self.config.technical_weight
            else:
                score += 15 * self.config.technical_weight
        
        # 4. 位置评分
        if position_ratio <= 0.4:
            score += 20 * self.config.position_weight
        elif position_ratio <= 0.6:
            score += 15 * self.config.position_weight
        elif position_ratio <= 0.8:
            score += 10 * self.config.position_weight
        else:
            score += 5 * self.config.position_weight
        
        # 5. 趋势评分
        if len(close_prices) >= 6:
            ma3_today = close_prices.iloc[-3:].mean()
            ma3_3days_ago = close_prices.iloc[-6:-3].mean()
            ma3_slope = (ma3_today - ma3_3days_ago) / ma3_3days_ago * 100
            if ma3_slope > 1:
                score += 5
            elif ma3_slope > 0:
                score += 3
        
        return min(score, 100)
    
    def calculate_score(self, stock_data: Dict[str, Any]) -> float:
        """
        计算股票评分
        
        Args:
            stock_data: 股票数据
            
        Returns:
            评分 (0-100)
        """
        return stock_data.get("次日补涨概率", 0)
    
    def get_strategy_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            策略描述文本
        """
        return """
=== 尾盘买入次日补涨策略 ===

【策略原理】
1. 筛选当日涨幅1-6%的股票，避免追高
2. 要求量比适中（1.1-3.0倍），避免过度炒作
3. 技术形态要求下影线支撑，上影线不过长
4. 短期均线向上，确保趋势良好
5. 近期无大幅异动，价格在合理区间

【最佳买入时机】
周内时机：
- 周一、周二、周三：最佳操作日（流动性好，确定性高）
- 周四：较好（但需关注周五风险）
- 周五：谨慎操作（周末风险，建议避免）

日内时机：
- 14:30-14:50：黄金时段（推荐）
- 14:50-15:00：最后确认（备选）
- 避免：9:30-11:30（早盘波动大）
- 避免：13:00-14:00（午后开盘不稳定）

【操作建议】
1. 尾盘14:30-15:00之间买入（避免太早买入被套）
2. 次日开盘或上午择机卖出（T+1操作）
3. 设置止损：如次日低开超过-3%，开盘即止损
4. 目标收益：2-5%，不贪心

【风险控制】
1. 单只股票仓位不超过10%
2. 总仓位不超过30%
3. 连续亏损3次暂停操作
4. 遇到大盘系统性风险立即止损
"""
