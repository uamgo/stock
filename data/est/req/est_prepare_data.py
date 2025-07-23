import os
import re
import traceback
from datetime import datetime, time
from typing import List
from pathlib import Path
import asyncio
import time

import pandas as pd
import exchange_calendars as xcals
from data.est.req.est_concept import EastmoneyConceptStockFetcher
from data.est.req.est_concept_codes import ConceptStockManager
from data.est.req.est_daily import EastmoneyDailyStockFetcher
from data.est.req.est_minute import EastmoneyMinuteStockFetcher
from data.est.req import est_common

FILTER_WORDS = ['*ST', 'ST', '退市', 'N', 'L', 'C', 'U', 'bj', 'BJ', '688', '83', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99']
FILTER_PATTERN = re.compile('|'.join(map(re.escape, FILTER_WORDS)), re.IGNORECASE)
DATA_DIR = Path("/tmp/stock/est_prepare_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BLACKLIST_PATH = str(DATA_DIR / "blacklist_codes.txt")
MEMBERS_DF_PATH = str(DATA_DIR / "members_df.pkl")

class EstStockPipeline:
    def __init__(self, top_n: int = 20, use_proxy: bool = False):
        self.top_n = top_n
        self.use_proxy = use_proxy
        self.concept_manager = ConceptStockManager()
        self.daily_fetcher = EastmoneyDailyStockFetcher()
        self.minute_fetcher = EastmoneyMinuteStockFetcher()
        # 添加缓存目录
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def is_market_open(self) -> bool:
        """检查A股市场是否开放"""
        from datetime import datetime, time
        now = datetime.now().time()
        # A股交易时间: 9:30-11:30, 13:00-15:00
        return (time(9, 30) <= now <= time(11, 30)) or (time(13, 0) <= now <= time(15, 0))
    
    def get_cache_duration(self) -> int:
        """根据市场状态获取缓存时长(秒)"""
        if self.is_market_open():
            return 1800  # 交易中: 30分钟缓存
        else:
            return 14400  # 收盘后: 4小时缓存 (避免频繁重算)
    
    def get_market_status(self) -> str:
        """获取市场状态描述"""
        from datetime import datetime, time
        now = datetime.now().time()
        
        if time(9, 30) <= now <= time(11, 30):
            return "上午交易中"
        elif time(11, 30) < now < time(13, 0):
            return "午间休市"
        elif time(13, 0) <= now <= time(15, 0):
            return "下午交易中"
        else:
            return "收盘后"

    async def get_top_n_concepts(self) -> List[str]:
        # 检查缓存
        concepts_cache_path = self.cache_dir / "top_concepts.pkl"
        if concepts_cache_path.exists():
            mtime = os.path.getmtime(concepts_cache_path)
            # 根据市场状态动态调整缓存时长
            cache_duration = self.get_cache_duration()
            if (datetime.now().timestamp() - mtime) < cache_duration:
                try:
                    cached_df = est_common.load_df_from_file(str(concepts_cache_path))
                    if not cached_df.empty and '热度分数' in cached_df.columns:
                        market_status = self.get_market_status()
                        cache_age_minutes = (datetime.now().timestamp() - mtime) / 60
                        print(f"使用缓存的概念板块数据 [{market_status}]，缓存时间: {datetime.fromtimestamp(mtime).strftime('%H:%M:%S')} (已缓存{cache_age_minutes:.0f}分钟)")
                        return cached_df.nlargest(self.top_n, "热度分数")["代码"].tolist()
                except Exception as e:
                    print(f"读取概念缓存失败: {e}")
        
        fetcher = EastmoneyConceptStockFetcher()
        df = fetcher.fetch_and_save()
        if df is None:
            raise RuntimeError("未能获取概念板块数据")
        
        # 使用新的4维度评分体系计算热度
        market_status = self.get_market_status()
        print(f"🔥 正在计算概念热度... [{market_status}]")
        df = self.calculate_concept_heat(df)
        
        # 保存到缓存
        try:
            est_common.save_df_to_file(df, str(concepts_cache_path))
        except Exception as e:
            print(f"保存概念缓存失败: {e}")
        
        # 显示热度排名前几名
        top_concepts = df.nlargest(min(5, len(df)), "热度分数")
        cache_info = f"[{market_status}]" + (f" 缓存{self.get_cache_duration()//3600}小时" if not self.is_market_open() else "")
        print(f"📊 热度排名TOP5 {cache_info}:")
        for _, concept in top_concepts.iterrows():
            print(f"  {concept['名称']:<15} | 涨跌: {concept['涨跌幅']:>6.2f}% | 热度: {concept['热度分数']:>5.1f}分")
        
        # 保存概念股热度分析CSV文件供前端API使用
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            csv_filename = f"/tmp/stock/concept_heat_analysis_{timestamp}.csv"
            
            # 选择前端需要的列并重命名
            frontend_df = df[['名称', '涨跌幅', '热度分数', '热度等级']].copy()
            frontend_df.rename(columns={
                '名称': '概念名称',
                '涨跌幅': '平均涨幅(%)',
                '热度分数': '热度分数',
                '热度等级': '热度等级'
            }, inplace=True)
            
            # 按热度分数降序排列
            frontend_df = frontend_df.sort_values('热度分数', ascending=False)
            
            # 保存CSV文件
            frontend_df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ 概念股热度分析已保存: {csv_filename}")
            
        except Exception as e:
            print(f"⚠️ 保存概念股热度分析CSV失败: {e}")
        
        return df.nlargest(self.top_n, "热度分数")["代码"].tolist()
    
    def calculate_concept_heat(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算概念热度分数（4维度评分体系）"""
        import numpy as np
        
        results = []
        
        for _, concept in df.iterrows():
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
            
            # 热度等级
            if total_heat >= 80:
                heat_level = "火热"
            elif total_heat >= 60:
                heat_level = "偏热"
            elif total_heat >= 40:
                heat_level = "温和"
            elif total_heat >= 20:
                heat_level = "偏冷"
            else:
                heat_level = "极冷"
            
            results.append({
                '热度分数': round(total_heat, 1),
                '热度等级': heat_level,
                '价格得分': round(price_score, 1),
                '资金得分': round(capital_score, 1),
                '活跃度得分': round(volume_score, 1),
                '技术得分': round(tech_score, 1)
            })
        
        # 将热度信息添加到原DataFrame
        heat_df = pd.DataFrame(results)
        for col in heat_df.columns:
            df[col] = heat_df[col]
        
        return df

    def get_all_members(self, concept_codes: List[str]) -> pd.DataFrame:
        print(f"正在获取 {len(concept_codes)} 个概念的成分股...")
        dfs = []
        for i, code in enumerate(concept_codes):
            if i % 5 == 0:  # 每5个概念打印一次进度
                print(f"进度: {i+1}/{len(concept_codes)}")
            df = self.concept_manager.get_concept_df(code)
            if df is not None:
                dfs.append(df)
        
        if not dfs:
            return pd.DataFrame()
        
        all_df = pd.concat(dfs, ignore_index=True)
        print(f"合并前总股票数: {len(all_df)}")
        
        # 使用更安全的过滤方式，避免正则表达式错误
        filtered_df = all_df.copy()
        
        # 逐个过滤条件，避免复杂的正则表达式
        for word in FILTER_WORDS:
            if word:  # 确保过滤词不为空
                filtered_df = filtered_df[
                    ~filtered_df["名称"].str.contains(word, case=False, na=False, regex=False)
                    & ~filtered_df["代码"].str.contains(word, case=False, na=False, regex=False)
                ]
        
        # 去重
        filtered_df = filtered_df.drop_duplicates(subset=["代码"])
        print(f"过滤后股票数: {len(filtered_df)}")
        return filtered_df

    async def run(self) -> pd.DataFrame:
        if not est_common.need_update(MEMBERS_DF_PATH):
            mtime = os.path.getmtime(MEMBERS_DF_PATH)
            print(f"{MEMBERS_DF_PATH} 无需更新，文件最后修改时间: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            return None

        t0 = time.time()
        time_stats = {}

        # 获取概念板块
        t_start = time.time()
        self.top_n = 10  # 减少概念数量以提高速度
        top_concept_codes = await self.get_top_n_concepts()
        t_end = time.time()
        time_stats["获取概念板块"] = t_end - t_start
        print("Top N 概念板块代码:", top_concept_codes)

        # 更新概念成分 - 增加并发数
        t_start = time.time()
        concurrent_count = min(15, self.top_n)  # 增加并发数
        self.concept_manager.update_all_concepts(
            top_concept_codes, use_proxy_and_concurrent=concurrent_count
        )
        t_end = time.time()
        time_stats["更新概念成分"] = t_end - t_start

        # 过滤并保存成分股
        t_start = time.time()
        members_df = self.get_all_members(top_concept_codes)
        est_common.save_df_to_file(members_df, MEMBERS_DF_PATH)
        t_end = time.time()
        time_stats["过滤并保存成分股"] = t_end - t_start
        print(f"过滤后成分股数量: {len(members_df)}，已保存 members_df 到 {MEMBERS_DF_PATH}")
        
        # 只显示前10只股票信息，减少输出时间
        display_count = min(10, len(members_df))
        for idx, row in members_df.head(display_count).iterrows():
            print(f"代码: {row['代码']}, 名称: {row['名称']}, 股价: {row['股价']}")
        if len(members_df) > display_count:
            print(f"... 还有 {len(members_df) - display_count} 只股票")

        # 并行更新日线和分钟线数据
        if not members_df.empty:
            t_start = time.time()
            # 创建任务并并行执行
            daily_task = self.update_daily_for_members(members_df, use_proxy_and_concurrent=25)
            minute_task = self.update_minute_for_members(members_df, use_proxy_and_concurrent=25)
            
            # 并行执行日线和分钟线更新
            await asyncio.gather(daily_task, minute_task)
            t_end = time.time()
            time_stats["并行更新数据"] = t_end - t_start

        # 打印代理使用次数
        print(f"代理使用次数: {getattr(est_common, 'PROXY_USE_COUNT', 0)}")
        total_time = time.time() - t0
        print("各阶段耗时统计：")
        for k, v in time_stats.items():
            print(f"{k}: {v:.2f} 秒")
        print(
            f"总耗时: {total_time:.2f} 秒 | 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return members_df

    async def update_daily_for_members(self, members_df: pd.DataFrame, period="day", adjust="qfq", use_proxy_and_concurrent=25):
        if members_df is None or members_df.empty:
            print("members_df 为空，跳过日线更新")
            return
        secids = [
            f"1.{code}" if str(code).startswith("6") else f"0.{code}"
            for code in members_df["代码"]
        ]
        print(f"开始更新 {len(secids)} 只股票的日线数据...")
        self.daily_fetcher.update_all_daily(
            secids, period=period, adjust=adjust, use_proxy_and_concurrent=use_proxy_and_concurrent
        )
        print(f"✅ 已批量更新 {len(secids)} 只股票的日线数据")

    async def update_minute_for_members(self, members_df: pd.DataFrame, period="1", use_proxy_and_concurrent=25):
        if members_df is None or members_df.empty:
            print("members_df 为空，跳过分钟线更新")
            return
        codes_df = pd.DataFrame({"symbol": members_df["代码"].tolist()})
        print(f"开始更新 {len(codes_df)} 只股票的分钟数据...")
        self.minute_fetcher.update_minute_batch(
            codes_df, period=period, use_proxy_and_concurrent=use_proxy_and_concurrent
        )
        print(f"✅ 已批量更新 {len(codes_df)} 只股票的分钟数据")

def load_members_df_from_path() -> pd.DataFrame:
    try:
        return est_common.load_df_from_file(MEMBERS_DF_PATH)
    except Exception as e:
        print(f"读取 {MEMBERS_DF_PATH} 失败: {e}")
        return pd.DataFrame()

async def main():
    # 支持快速模式参数
    import sys
    fast_mode = '--fast' in sys.argv or '-f' in sys.argv
    
    if fast_mode:
        print("🚀 启用快速模式...")
        pipeline = EstStockPipeline(top_n=8)  # 减少概念数量
    else:
        pipeline = EstStockPipeline(top_n=10)
    
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
