#!/usr/bin/env python3
"""
涨停逻辑分析系统

每日分析涨停股票的逻辑，提取共性特征并应用到选股策略中
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import re
import sys
import os
from collections import Counter

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from tail_trading.data.eastmoney.daily_fetcher import EastmoneyDataFetcher
except ImportError:
    print("⚠️ 无法导入数据模块，使用模拟数据")

class LimitUpLogicAnalyzer:
    """涨停逻辑分析器"""
    
    def __init__(self):
        try:
            self.data_fetcher = EastmoneyDataFetcher()
        except:
            self.data_fetcher = None
        
        # 涨停逻辑分类
        self.logic_categories = {
            "题材概念": ["AI", "ChatGPT", "数字经济", "新能源", "芯片", "5G", "元宇宙", "碳中和", "军工", "医药"],
            "政策驱动": ["国企改革", "央企整合", "区域发展", "产业政策", "补贴政策"],
            "业绩驱动": ["业绩预增", "订单增长", "产能扩张", "新产品", "技术突破"],
            "资金驱动": ["机构调研", "股东增持", "回购", "资金流入", "北向资金"],
            "事件驱动": ["重组并购", "中标项目", "合作协议", "分拆上市", "股权激励"],
            "技术突破": ["底部放量", "突破平台", "均线多头", "量价齐升", "MACD金叉"]
        }
        
        # 板块热点词汇
        self.sector_keywords = {
            "科技": ["人工智能", "芯片", "半导体", "软件", "云计算", "大数据"],
            "新能源": ["锂电池", "光伏", "风电", "储能", "充电桩", "氢能源"],
            "医药": ["疫苗", "创新药", "医疗器械", "CRO", "医美", "中药"],
            "消费": ["白酒", "食品", "服装", "家电", "汽车", "旅游"],
            "金融": ["银行", "保险", "券商", "信托", "租赁"],
            "周期": ["钢铁", "有色", "化工", "建材", "煤炭", "石油"]
        }
    
    def get_daily_limit_up_stocks(self, date: str = None) -> List[Dict[str, Any]]:
        """
        获取指定日期的涨停股票（使用真实数据）
        
        Args:
            date: 日期，格式YYYY-MM-DD，默认为今天
            
        Returns:
            涨停股票列表
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 使用真实数据源获取涨停股票
        try:
            # 方法1：通过概念股数据筛选涨停股票
            if hasattr(self, 'data_fetcher') and self.data_fetcher:
                try:
                    # 获取股票列表
                    stock_list = self.data_fetcher.get_stock_list()
                    if stock_list is not None and not stock_list.empty:
                        # 获取今日涨停股票（涨跌幅>=9.8%的股票）
                        limit_up_stocks = []
                        
                        for _, stock in stock_list.head(50).iterrows():  # 限制检查数量
                            code = stock.get("代码", "")
                            name = stock.get("名称", "")
                            
                            if code:
                                try:
                                    # 获取当日数据
                                    daily_data = self.data_fetcher.get_daily_data(code, days=1)
                                    if daily_data is not None and not daily_data.empty:
                                        latest = daily_data.iloc[-1]
                                        pct_change = float(latest.get("涨跌幅", 0))
                                        
                                        # 涨停标准：涨幅>=9.8%
                                        if pct_change >= 9.8:
                                            limit_up_stocks.append({
                                                "代码": code,
                                                "名称": name,
                                                "涨跌幅": pct_change,
                                                "板块": self._get_stock_sector(code),
                                                "概念": self._get_stock_concept(code),
                                                "收盘价": float(latest.get("收盘", 0)),
                                                "成交量": float(latest.get("成交量", 0))
                                            })
                                except Exception as e:
                                    continue
                        
                        if limit_up_stocks:
                            print(f"✅ 获取到 {len(limit_up_stocks)} 只涨停股票")
                            return limit_up_stocks
                
                except Exception as e:
                    print(f"⚠️ 真实数据获取失败: {e}")
            
            # 方法2：通过概念板块数据获取
            try:
                from data.est.req.est_concept import EastmoneyConceptStockFetcher
                concept_fetcher = EastmoneyConceptStockFetcher()
                concept_df = concept_fetcher.get_concept_df()
                
                if concept_df is not None and not concept_df.empty:
                    # 筛选涨停股票
                    limit_up_df = concept_df[concept_df["涨跌幅"] >= 9.8]
                    
                    if not limit_up_df.empty:
                        limit_up_stocks = []
                        for _, row in limit_up_df.iterrows():
                            limit_up_stocks.append({
                                "代码": row.get("代码", ""),
                                "名称": row.get("名称", ""),
                                "涨跌幅": float(row.get("涨跌幅", 0)),
                                "板块": self._get_stock_sector_from_concept(row),
                                "概念": row.get("概念名称", ""),
                                "收盘价": float(row.get("最新价", 0)),
                                "成交量": float(row.get("成交量", 0))
                            })
                        
                        print(f"✅ 从概念数据获取到 {len(limit_up_stocks)} 只涨停股票")
                        return limit_up_stocks
                        
            except Exception as e:
                print(f"⚠️ 概念数据获取失败: {e}")
            
            # 备用方案：使用有代表性的示例数据（但会标注为模拟）
            print("⚠️ 无法获取真实涨停数据，使用模拟数据")
            sample_limit_up = [
                {"代码": "300001", "名称": "特锐德", "涨跌幅": 10.01, "板块": "充电桩", "概念": "新能源汽车"},
                {"代码": "000858", "名称": "五粮液", "涨跌幅": 10.02, "板块": "白酒", "概念": "消费升级"},
                {"代码": "002415", "名称": "海康威视", "涨跌幅": 9.98, "板块": "安防", "概念": "人工智能"},
                {"代码": "300122", "名称": "智飞生物", "涨跌幅": 10.00, "板块": "疫苗", "概念": "医药创新"},
                {"代码": "600036", "名称": "招商银行", "涨跌幅": 10.05, "板块": "银行", "概念": "金融改革"}
            ]
            
            return sample_limit_up
            
        except Exception as e:
            print(f"❌ 涨停数据获取完全失败: {e}")
            return []
    
    def _get_stock_sector(self, code: str) -> str:
        """根据股票代码推断板块"""
        try:
            # 根据代码前缀进行简单分类
            if code.startswith("60"):
                if code in ["600519", "000858"]:
                    return "白酒"
                elif code in ["600036", "601318", "000001"]:
                    return "银行"
                elif code in ["600276", "600887"]:
                    return "医药"
                else:
                    return "主板"
            elif code.startswith("00"):
                if code in ["000858"]:
                    return "白酒"
                elif code in ["002415", "002027"]:
                    return "科技"
                else:
                    return "深主板"
            elif code.startswith("30"):
                return "创业板"
            elif code.startswith("688"):
                return "科创板"
            else:
                return "其他"
        except:
            return "未知"
    
    def _get_stock_concept(self, code: str) -> str:
        """根据股票代码推断概念"""
        try:
            # 简单的概念映射
            concept_map = {
                "300001": "新能源汽车",
                "000858": "消费升级",
                "002415": "人工智能",
                "300122": "医药创新",
                "600036": "金融改革",
                "600519": "消费白马",
                "000001": "深圳本地",
                "002027": "半导体"
            }
            return concept_map.get(code, "待分析")
        except:
            return "未知"
    
    def _get_stock_sector_from_concept(self, row) -> str:
        """从概念数据中提取板块信息"""
        try:
            name = row.get("名称", "")
            concept = row.get("概念名称", "")
            
            # 根据股票名称推断板块
            if any(word in name for word in ["银行", "金融"]):
                return "银行"
            elif any(word in name for word in ["科技", "软件", "电子"]):
                return "科技"
            elif any(word in name for word in ["医药", "生物", "制药"]):
                return "医药"
            elif any(word in name for word in ["酒", "饮料"]):
                return "食品饮料"
            elif any(word in concept for word in ["新能源", "锂电", "光伏"]):
                return "新能源"
            else:
                return "其他"
        except:
            return "未知"
    
    def analyze_limit_up_logic(self, limit_up_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析涨停股票的共同逻辑
        
        Args:
            limit_up_stocks: 涨停股票列表
            
        Returns:
            涨停逻辑分析结果
        """
        if not limit_up_stocks:
            return {"error": "没有涨停股票数据"}
        
        # 板块分析
        sector_analysis = self._analyze_sectors(limit_up_stocks)
        
        # 概念分析
        concept_analysis = self._analyze_concepts(limit_up_stocks)
        
        # 技术特征分析
        technical_analysis = self._analyze_technical_features(limit_up_stocks)
        
        # 市场情绪分析
        sentiment_analysis = self._analyze_market_sentiment(limit_up_stocks)
        
        # 主导逻辑识别
        dominant_logic = self._identify_dominant_logic(sector_analysis, concept_analysis)
        
        return {
            "涨停总数": len(limit_up_stocks),
            "板块分析": sector_analysis,
            "概念分析": concept_analysis,
            "技术特征": technical_analysis,
            "市场情绪": sentiment_analysis,
            "主导逻辑": dominant_logic,
            "分析日期": datetime.now().strftime("%Y-%m-%d"),
            "热点排行": self._rank_hot_topics(sector_analysis, concept_analysis)
        }
    
    def _analyze_sectors(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析涨停股票的板块分布"""
        
        sectors = [stock.get("板块", "未知") for stock in stocks]
        sector_counts = Counter(sectors)
        
        # 计算板块集中度
        total_stocks = len(stocks)
        concentration = max(sector_counts.values()) / total_stocks if total_stocks > 0 else 0
        
        # 主要板块
        top_sectors = sector_counts.most_common(5)
        
        return {
            "板块分布": dict(sector_counts),
            "主要板块": top_sectors,
            "集中度": round(concentration, 3),
            "板块数量": len(set(sectors))
        }
    
    def _analyze_concepts(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析涨停股票的概念分布"""
        
        concepts = []
        for stock in stocks:
            concept_str = stock.get("概念", "")
            # 分割概念（如果有多个概念用分号或逗号分隔）
            stock_concepts = re.split('[,;，；]', concept_str)
            concepts.extend([c.strip() for c in stock_concepts if c.strip()])
        
        concept_counts = Counter(concepts)
        
        # 概念热度排行
        hot_concepts = concept_counts.most_common(10)
        
        return {
            "概念分布": dict(concept_counts),
            "热门概念": hot_concepts,
            "概念总数": len(set(concepts))
        }
    
    def _analyze_technical_features(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析涨停股票的技术特征"""
        
        # 这里需要获取个股的技术数据进行分析
        # 简化版分析
        
        features = {
            "平均涨幅": np.mean([stock.get("涨跌幅", 0) for stock in stocks]),
            "涨停强度": "强" if len(stocks) > 50 else "中" if len(stocks) > 20 else "弱",
            "封板程度": "待分析",  # 需要分时数据
            "资金性质": "待分析"   # 需要资金流向数据
        }
        
        return features
    
    def _analyze_market_sentiment(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析市场情绪"""
        
        limit_up_count = len(stocks)
        
        # 情绪强度判断
        if limit_up_count > 100:
            sentiment = "极度亢奋"
            level = 5
        elif limit_up_count > 50:
            sentiment = "亢奋"
            level = 4
        elif limit_up_count > 30:
            sentiment = "积极"
            level = 3
        elif limit_up_count > 10:
            sentiment = "一般"
            level = 2
        else:
            sentiment = "低迷"
            level = 1
        
        return {
            "情绪类型": sentiment,
            "情绪等级": level,
            "涨停数量": limit_up_count,
            "市场状态": "投机活跃" if level >= 4 else "理性投资" if level >= 2 else "谨慎观望"
        }
    
    def _identify_dominant_logic(self, sector_analysis: Dict, concept_analysis: Dict) -> Dict[str, Any]:
        """识别主导逻辑"""
        
        # 获取最强板块和概念
        top_sector = sector_analysis["主要板块"][0] if sector_analysis["主要板块"] else ("未知", 0)
        top_concept = concept_analysis["热门概念"][0] if concept_analysis["热门概念"] else ("未知", 0)
        
        # 判断逻辑类型
        sector_concentration = sector_analysis["集中度"]
        
        if sector_concentration > 0.4:
            logic_type = "板块轮动"
            description = f"市场主要围绕{top_sector[0]}板块展开"
        elif top_concept[1] > 5:
            logic_type = "概念炒作"
            description = f"{top_concept[0]}概念成为市场热点"
        else:
            logic_type = "普涨行情"
            description = "市场呈现多点开花态势"
        
        return {
            "逻辑类型": logic_type,
            "描述": description,
            "主导板块": top_sector[0],
            "主导概念": top_concept[0],
            "强度": "强" if sector_concentration > 0.3 else "中" if sector_concentration > 0.2 else "弱"
        }
    
    def _rank_hot_topics(self, sector_analysis: Dict, concept_analysis: Dict) -> List[Dict[str, Any]]:
        """热点话题排行"""
        
        hot_topics = []
        
        # 板块热点
        for sector, count in sector_analysis["主要板块"][:3]:
            hot_topics.append({
                "类型": "板块",
                "名称": sector,
                "热度": count,
                "权重": count / sector_analysis.get("板块数量", 1)
            })
        
        # 概念热点
        for concept, count in concept_analysis["热门概念"][:3]:
            hot_topics.append({
                "类型": "概念",
                "名称": concept,
                "热度": count,
                "权重": count / concept_analysis.get("概念总数", 1)
            })
        
        # 按热度排序
        hot_topics.sort(key=lambda x: x["热度"], reverse=True)
        
        return hot_topics[:5]
    
    def generate_selection_strategy(self, logic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于涨停逻辑生成选股策略
        
        Args:
            logic_analysis: 涨停逻辑分析结果
            
        Returns:
            选股策略
        """
        dominant_logic = logic_analysis.get("主导逻辑", {})
        hot_topics = logic_analysis.get("热点排行", [])
        sentiment = logic_analysis.get("市场情绪", {})
        
        strategy = {
            "策略名称": f"基于{dominant_logic.get('逻辑类型', '市场')}的选股策略",
            "适用周期": "1-3个交易日",
            "核心逻辑": dominant_logic.get("描述", "跟随市场热点"),
            "选股条件": [],
            "风险等级": self._assess_strategy_risk(sentiment),
            "预期收益": self._estimate_expected_return(logic_analysis)
        }
        
        # 生成具体选股条件
        strategy["选股条件"] = self._generate_selection_criteria(logic_analysis)
        
        # 操作建议
        strategy["操作建议"] = self._generate_operation_advice(logic_analysis)
        
        return strategy
    
    def _generate_selection_criteria(self, logic_analysis: Dict[str, Any]) -> List[str]:
        """生成选股条件"""
        
        criteria = []
        
        dominant_logic = logic_analysis.get("主导逻辑", {})
        hot_topics = logic_analysis.get("热点排行", [])
        sentiment = logic_analysis.get("市场情绪", {})
        
        # 基于主导板块的条件
        main_sector = dominant_logic.get("主导板块")
        if main_sector and main_sector != "未知":
            criteria.append(f"优先选择{main_sector}板块股票")
        
        # 基于热门概念的条件
        main_concept = dominant_logic.get("主导概念")
        if main_concept and main_concept != "未知":
            criteria.append(f"关注{main_concept}概念相关股票")
        
        # 基于市场情绪的条件
        sentiment_level = sentiment.get("情绪等级", 1)
        if sentiment_level >= 4:
            criteria.extend([
                "选择强势股票，避免滞涨品种",
                "关注连板股票的跟风机会",
                "控制单股仓位，分散风险"
            ])
        elif sentiment_level >= 2:
            criteria.extend([
                "选择基本面良好的股票",
                "关注技术形态突破的品种",
                "适度控制仓位"
            ])
        else:
            criteria.extend([
                "选择超跌反弹的优质股票",
                "避免追涨杀跌",
                "谨慎控制仓位"
            ])
        
        # 技术条件
        criteria.extend([
            "股价在重要均线之上",
            "成交量有效放大",
            "技术形态良好"
        ])
        
        return criteria
    
    def _generate_operation_advice(self, logic_analysis: Dict[str, Any]) -> List[str]:
        """生成操作建议"""
        
        advice = []
        
        sentiment = logic_analysis.get("市场情绪", {})
        sentiment_level = sentiment.get("情绪等级", 1)
        
        if sentiment_level >= 4:
            advice.extend([
                "市场情绪亢奋，注意及时止盈",
                "可适当参与强势品种，但要控制仓位",
                "避免盲目追高，等待回调机会"
            ])
        elif sentiment_level >= 2:
            advice.extend([
                "市场情绪较好，可正常操作",
                "选择有基本面支撑的品种",
                "设置合理的止损止盈位"
            ])
        else:
            advice.extend([
                "市场情绪低迷，以防守为主",
                "等待市场企稳信号",
                "可关注超跌优质股票"
            ])
        
        # 通用建议
        advice.extend([
            "严格执行选股条件",
            "分批建仓，控制风险",
            "关注政策面和基本面变化"
        ])
        
        return advice
    
    def _assess_strategy_risk(self, sentiment: Dict[str, Any]) -> str:
        """评估策略风险等级"""
        
        sentiment_level = sentiment.get("情绪等级", 1)
        
        if sentiment_level >= 5:
            return "极高风险"
        elif sentiment_level >= 4:
            return "高风险"
        elif sentiment_level >= 3:
            return "中等风险"
        elif sentiment_level >= 2:
            return "低风险"
        else:
            return "极低风险"
    
    def _estimate_expected_return(self, logic_analysis: Dict[str, Any]) -> str:
        """估算预期收益"""
        
        sentiment = logic_analysis.get("市场情绪", {})
        sentiment_level = sentiment.get("情绪等级", 1)
        dominant_logic = logic_analysis.get("主导逻辑", {})
        strength = dominant_logic.get("强度", "弱")
        
        if sentiment_level >= 4 and strength == "强":
            return "5-15%"
        elif sentiment_level >= 3 and strength in ["强", "中"]:
            return "3-8%"
        elif sentiment_level >= 2:
            return "1-5%"
        else:
            return "0-3%"

def main():
    """主函数"""
    print("📈 涨停逻辑分析系统")
    print("=" * 50)
    
    analyzer = LimitUpLogicAnalyzer()
    
    try:
        # 获取今日涨停股票
        print("📊 获取今日涨停股票...")
        limit_up_stocks = analyzer.get_daily_limit_up_stocks()
        
        if not limit_up_stocks:
            print("❌ 今日暂无涨停股票数据")
            return
        
        print(f"✅ 发现 {len(limit_up_stocks)} 只涨停股票")
        
        # 分析涨停逻辑
        print("\n🔍 分析涨停逻辑...")
        logic_analysis = analyzer.analyze_limit_up_logic(limit_up_stocks)
        
        # 显示分析结果
        print(f"\n📋 涨停逻辑分析报告 ({logic_analysis['分析日期']})")
        print("=" * 60)
        
        # 基本统计
        print(f"📊 基本统计:")
        print(f"  涨停总数: {logic_analysis['涨停总数']} 只")
        print(f"  涉及板块: {logic_analysis['板块分析']['板块数量']} 个")
        print(f"  涉及概念: {logic_analysis['概念分析']['概念总数']} 个")
        
        # 市场情绪
        sentiment = logic_analysis["市场情绪"]
        print(f"\n🌡️ 市场情绪:")
        print(f"  情绪类型: {sentiment['情绪类型']}")
        print(f"  情绪等级: {sentiment['情绪等级']}/5")
        print(f"  市场状态: {sentiment['市场状态']}")
        
        # 主导逻辑
        dominant = logic_analysis["主导逻辑"]
        print(f"\n🎯 主导逻辑:")
        print(f"  逻辑类型: {dominant['逻辑类型']}")
        print(f"  描述: {dominant['描述']}")
        print(f"  主导板块: {dominant['主导板块']}")
        print(f"  主导概念: {dominant['主导概念']}")
        print(f"  强度: {dominant['强度']}")
        
        # 热点排行
        print(f"\n🔥 热点排行:")
        for i, topic in enumerate(logic_analysis["热点排行"], 1):
            print(f"  {i}. {topic['类型']}: {topic['名称']} (热度: {topic['热度']})")
        
        # 板块分析
        print(f"\n📈 主要板块:")
        for sector, count in logic_analysis["板块分析"]["主要板块"][:5]:
            print(f"  {sector}: {count} 只")
        
        # 生成选股策略
        print(f"\n🎯 生成今日选股策略...")
        strategy = analyzer.generate_selection_strategy(logic_analysis)
        
        print(f"\n📋 选股策略: {strategy['策略名称']}")
        print("-" * 50)
        print(f"核心逻辑: {strategy['核心逻辑']}")
        print(f"适用周期: {strategy['适用周期']}")
        print(f"风险等级: {strategy['风险等级']}")
        print(f"预期收益: {strategy['预期收益']}")
        
        print(f"\n📝 选股条件:")
        for i, condition in enumerate(strategy['选股条件'], 1):
            print(f"  {i}. {condition}")
        
        print(f"\n💡 操作建议:")
        for i, advice in enumerate(strategy['操作建议'], 1):
            print(f"  {i}. {advice}")
        
        # 保存策略到文件
        strategy_file = f"scripts/daily_strategy_{datetime.now().strftime('%Y%m%d')}.json"
        import json
        try:
            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "logic_analysis": logic_analysis,
                    "strategy": strategy
                }, f, ensure_ascii=False, indent=2)
            print(f"\n💾 策略已保存到: {strategy_file}")
        except Exception as e:
            print(f"⚠️ 策略保存失败: {e}")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
