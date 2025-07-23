#!/usr/bin/env python3
"""
热门概念分析工具

分析当前市场热门概念板块，提供多维度热门度评估
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.est.req.est_concept import EastmoneyConceptStockFetcher
from data.est.req.est_concept_codes import ConceptStockManager
import json

class HotConceptAnalyzer:
    def __init__(self):
        self.concept_fetcher = EastmoneyConceptStockFetcher()
        self.concept_manager = ConceptStockManager()
        
    def get_hot_concepts(self, top_n=20):
        """获取热门概念板块"""
        print("📊 正在获取概念板块数据...")
        df = self.concept_fetcher.fetch_and_save()
        if df is None or df.empty:
            print("❌ 无法获取概念板块数据")
            return None
            
        return df.head(top_n)
    
    def analyze_concept_heat(self, concepts_df):
        """分析概念热门度 - 使用新的4维度评估方法"""
        if concepts_df is None or concepts_df.empty:
            return None
            
        print("🔍 正在进行热门度综合分析...")
        
        # 使用基于实际字段的4维度热度计算方法
        heat_scores = []
        
        for _, concept in concepts_df.iterrows():
            # 1. 板块涨跌幅得分 (40%)
            price_change = concept.get('涨跌幅', 0)
            price_score = np.clip((price_change + 10) * 5, 0, 100)
            
            # 2. 主力资金净流入得分 (30%)
            capital_flow = concept.get('f62', 0) / 100000000  # 转换为亿元
            capital_score = np.clip(capital_flow * 2 + 50, 0, 100)
            
            # 3. 成交活跃度得分 (20%)
            volume = abs(concept.get('f66', 0)) / 100000000  # 转换为亿元
            volume_score = np.clip(np.log10(volume + 1) * 20, 0, 100)
            
            # 4. 技术指标得分 (10%) - 基于振幅
            amplitude = abs(concept.get('f78', 0)) / 1000000
            tech_score = np.clip(amplitude * 5, 0, 100)
            
            # 加权计算总热度
            total_heat = (price_score * 0.4 + capital_score * 0.3 + 
                          volume_score * 0.2 + tech_score * 0.1)
            
            # 详细评分信息
            details = {
                '板块涨跌幅得分': round(price_score, 1),
                '资金流入得分': round(capital_score, 1),
                '成交活跃度得分': round(volume_score, 1),
                '技术指标得分': round(tech_score, 1),
                '总得分': round(total_heat, 1),
                '原始数据': {
                    '涨跌幅': price_change,
                    '主力净流入_亿': round(capital_flow, 1),
                    '成交额_亿': round(volume, 1),
                    '振幅指标': round(amplitude, 2)
                }
            }
            
            heat_scores.append(details)
        
        # 添加热门度评分到dataframe
        concepts_df = concepts_df.copy()
        concepts_df['热门度评分'] = [score['总得分'] for score in heat_scores]
        concepts_df['评分详情'] = heat_scores
        
        # 按热门度重新排序
        concepts_df = concepts_df.sort_values('热门度评分', ascending=False)
        
        return concepts_df
    
    def get_concept_members_count(self, concept_codes):
        """获取概念成分股数量"""
        member_counts = {}
        print("📈 正在统计概念成分股数量...")
        
        for i, code in enumerate(concept_codes):
            if i % 5 == 0:
                print(f"进度: {i+1}/{len(concept_codes)}")
            try:
                df = self.concept_manager.get_concept_df(code)
                member_counts[code] = len(df) if df is not None else 0
            except:
                member_counts[code] = 0
                
        return member_counts
    
    def print_hot_analysis(self, concepts_df, show_details=False):
        """打印热门概念分析结果"""
        if concepts_df is None or concepts_df.empty:
            print("❌ 没有概念数据可供分析")
            return
            
        print("\n🔥 热门概念板块综合分析")
        print("=" * 100)
        print(f"{'排名':<4} {'代码':<8} {'概念名称':<20} {'涨跌幅':<8} {'热门度':<8} {'热度等级':<10}")
        print("-" * 100)
        
        for i, (_, concept) in enumerate(concepts_df.iterrows()):
            rank = i + 1
            code = concept['代码']
            name = concept['名称'][:18] + '..' if len(concept['名称']) > 18 else concept['名称']
            change_pct = concept.get('涨跌幅', 0)
            heat_score = concept.get('热门度评分', 0)
            
            # 热度等级 - 基于新的0-100分制
            if heat_score >= 80:
                heat_level = "🔥🔥🔥火热"
            elif heat_score >= 60:
                heat_level = "🔥🔥偏热"
            elif heat_score >= 40:
                heat_level = "🔥温和"
            elif heat_score >= 20:
                heat_level = "😐偏冷"
            else:
                heat_level = "❄️极冷"
            
            print(f"{rank:<4} {code:<8} {name:<20} {change_pct:>6.2f}% {heat_score:>6.1f} {heat_level:<10}")
            
            if show_details and i < 10:  # 只显示前10个的详情
                details = concept.get('评分详情', {})
                print(f"     └─ 详情: 涨跌幅{details.get('涨跌幅得分', 0):.1f} + 成交额{details.get('成交额得分', 0):.1f} + 市值{details.get('市值得分', 0):.1f} + 热词{details.get('热词得分', 0):.1f}")
    
    def save_hot_concepts(self, concepts_df, filename=None):
        """保存热门概念到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/Users/kevin/Downloads/hot_concepts_{timestamp}.txt"
        
        if concepts_df is None or concepts_df.empty:
            print("❌ 没有数据可保存")
            return
            
        # 保存概念代码
        hot_codes = concepts_df['代码'].head(20).tolist()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(','.join(hot_codes))
        
        print(f"💾 热门概念代码已保存到: {filename}")
        print(f"📋 概念代码: {','.join(hot_codes[:10])}...")
        
        # 保存详细报告
        report_filename = filename.replace('.txt', '_report.json')
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_concepts": len(concepts_df),
            "hot_concepts": []
        }
        
        for _, concept in concepts_df.head(20).iterrows():
            report_data["hot_concepts"].append({
                "代码": concept['代码'],
                "名称": concept['名称'],
                "涨跌幅": concept.get('涨跌幅', 0),
                "热门度评分": concept.get('热门度评分', 0),
                "评分详情": concept.get('评分详情', {})
            })
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📊 详细报告已保存到: {report_filename}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='热门概念分析工具')
    parser.add_argument('--top', '-t', type=int, default=20, help='显示前N个概念 (默认20)')
    parser.add_argument('--details', '-d', action='store_true', help='显示详细评分信息')
    parser.add_argument('--save', '-s', action='store_true', help='保存结果到文件')
    
    args = parser.parse_args()
    
    analyzer = HotConceptAnalyzer()
    
    # 获取概念数据
    concepts_df = analyzer.get_hot_concepts(top_n=50)  # 获取更多数据用于分析
    
    if concepts_df is None:
        return
    
    # 分析热门度
    print("🔍 正在进行热门度综合分析...")
    hot_concepts_df = analyzer.analyze_concept_heat(concepts_df)
    
    # 显示结果
    analyzer.print_hot_analysis(hot_concepts_df.head(args.top), show_details=args.details)
    
    # 保存结果
    if args.save:
        analyzer.save_hot_concepts(hot_concepts_df)
    
    # 显示热门概念建议
    print(f"\n💡 投资建议:")
    print(f"1. 🔥火热(≥80分): 极度关注，但需控制风险")
    print(f"2. 🔥偏热(60-80分): 重点关注，适合短线操作")
    print(f"3. 🔥温和(40-60分): 中等关注，可适度参与")
    print(f"4. 😐偏冷(20-40分): 关注度低，需谨慎操作")
    print(f"5. ❄️极冷(<20分): 市场冷淡，建议观望")
    print(f"6. 可用命令: python scripts/hot_concept_analyzer.py --details --save")

if __name__ == "__main__":
    main()
