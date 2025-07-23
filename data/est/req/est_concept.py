import os
from datetime import datetime
import pandas as pd
import requests
from data.est.req import est_common

class EastmoneyConceptStockFetcher:
    def __init__(self, save_dir: str = "/tmp/stock/base"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.save_path = os.path.join(self.save_dir, "eastmoney_concept_stocks.pkl")
        self.proxy = None

    def file_mtime_is_today(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return mtime.date() == datetime.now().date()

    def fetch_concept_stocks(self) -> pd.DataFrame | None:
        base_url = (
            "https://push2.eastmoney.com/api/qt/clist/get"
            "?fid=f62&po=1&pz=5000&pn={page}&np=1&fltt=2&invt=2"
            "&ut=8dec03ba335b81bf4ebdf7b29ec27d15"
            "&fs=m%3A90+t%3A3"
            "&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124%2Cf1%2Cf13"
        )
        # 先检查是否有缓存数据用于分析
        if os.path.exists(self.save_path):
            cached_df = pd.read_pickle(self.save_path)
            if not cached_df.empty:
                print("🔍 使用缓存数据进行字段分析...")
                self.analyze_fields(cached_df)
        
        if not est_common.need_update(self.save_path):
            print(f"{self.save_path} 已是最新，无需更新。")
            return pd.read_pickle(self.save_path)
        self.proxy = est_common.get_proxy()
        all_rows = []
        page = 1
        total = None
        while True:
            url = base_url.format(page=page)
            try:
                resp = requests.get(url, proxies=self.proxy, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("data", {}).get("diff", [])
                if not rows:
                    print(f"第{page}页未获取到数据，当前累计行数: {len(all_rows)}")
                    break
                all_rows.extend(rows)
                total = data.get("data", {}).get("total", 0)
                print(f"已获取第{page}页，累计行数: {len(all_rows)}，总数: {total}")
                if len(all_rows) >= total:
                    break
                page += 1
            except Exception as e:
                print(f"请求第{page}页失败: {e}，URL: {url}")
                break
        if all_rows:
            if total is not None and len(all_rows) < total:
                print(f"警告：累计行数 {len(all_rows)} 少于 total {total}，可能有数据缺失！")
            df = pd.DataFrame(all_rows)
            
            # 打印字段含义分析
            self.analyze_fields(df)
            
            df = df.rename(columns={
                "f12": "代码",
                "f14": "名称", 
                "f2": "最新价",
                "f3": "涨跌幅",
                "f62": "主力净流入",
                "f184": "概念名称",
                "f66": "成交额",
                "f69": "换手率",
                "f72": "平均价",
                "f75": "量比",
                "f78": "振幅",
                "f81": "总市值",
                "f84": "市盈率",
                "f87": "流通市值",
                "f204": "涨速",
                "f205": "5分钟涨跌",
                "f124": "更新时间",
                "f1": "市场标识",
                "f13": "市场名称"
            })
            return df
        print("未获取到概念股数据")
        return None

    def analyze_fields(self, df: pd.DataFrame):
        """分析并打印每个字段的含义"""
        print("\n" + "="*80)
        print("📊 东方财富概念股接口字段分析")
        print("="*80)
        
        if df.empty:
            print("❌ 数据为空，无法分析字段")
            return
            
        # 获取第一行数据作为示例
        sample_row = df.iloc[0]
        
        # 字段映射表（基于东方财富API文档和实际测试）
        field_mappings = {
            "f1": {"name": "市场标识", "desc": "交易所标识(0=深圳,1=上海,116=北交所等)", "type": "int"},
            "f2": {"name": "最新价", "desc": "当前最新价格", "type": "float", "unit": "元"},
            "f3": {"name": "涨跌幅", "desc": "今日涨跌幅", "type": "float", "unit": "%"},
            "f12": {"name": "股票代码", "desc": "6位股票代码", "type": "string"},
            "f13": {"name": "市场名称", "desc": "交易所名称", "type": "string"},
            "f14": {"name": "股票名称", "desc": "股票简称", "type": "string"},
            "f62": {"name": "主力净流入", "desc": "主力资金净流入额", "type": "float", "unit": "万元"},
            "f66": {"name": "成交额", "desc": "今日成交金额", "type": "float", "unit": "万元"},
            "f69": {"name": "换手率", "desc": "今日换手率", "type": "float", "unit": "%"},
            "f72": {"name": "平均价", "desc": "今日均价", "type": "float", "unit": "元"},
            "f75": {"name": "量比", "desc": "量比指标", "type": "float"},
            "f78": {"name": "振幅", "desc": "今日振幅", "type": "float", "unit": "%"},
            "f81": {"name": "总市值", "desc": "总市值", "type": "float", "unit": "万元"},
            "f84": {"name": "市盈率", "desc": "动态市盈率", "type": "float"},
            "f87": {"name": "流通市值", "desc": "流通市值", "type": "float", "unit": "万元"},
            "f124": {"name": "更新时间", "desc": "数据更新时间戳", "type": "timestamp"},
            "f184": {"name": "概念名称", "desc": "概念板块名称", "type": "string"},
            "f204": {"name": "涨速", "desc": "涨跌速度", "type": "float", "unit": "%"},
            "f205": {"name": "5分钟涨跌", "desc": "近5分钟涨跌幅", "type": "float", "unit": "%"}
        }
        
        print(f"📋 数据样本分析（第一行数据）:")
        print("-" * 80)
        
        for field_code, field_info in field_mappings.items():
            if field_code in sample_row:
                value = sample_row[field_code]
                field_name = field_info["name"]
                field_desc = field_info["desc"]
                field_type = field_info["type"]
                unit = field_info.get("unit", "")
                
                # 格式化显示值
                if pd.isna(value) or value == "" or value == "-":
                    display_value = "无数据"
                elif field_type == "timestamp" and value != "无数据":
                    try:
                        # 时间戳转换
                        timestamp = int(value)
                        dt = datetime.fromtimestamp(timestamp)
                        display_value = f"{value} ({dt.strftime('%Y-%m-%d %H:%M:%S')})"
                    except:
                        display_value = str(value)
                elif field_type == "float":
                    try:
                        num_value = float(value)
                        if unit:
                            display_value = f"{num_value:.2f} {unit}"
                        else:
                            display_value = f"{num_value:.2f}"
                    except:
                        display_value = str(value)
                else:
                    display_value = str(value)
                
                print(f"{field_code:>4} | {field_name:<12} | {field_desc:<25} | {display_value}")
            else:
                field_name = field_info["name"]
                field_desc = field_info["desc"]
                print(f"{field_code:>4} | {field_name:<12} | {field_desc:<25} | 字段不存在")
        
        print("-" * 80)
        print(f"📊 数据统计:")
        print(f"  总记录数: {len(df)}")
        print(f"  总字段数: {len(df.columns)}")
        print(f"  有效字段: {len([col for col in df.columns if col in field_mappings])}")
        
        # 统计各字段的数据完整性
        print(f"\n📈 字段数据完整性分析:")
        print("-" * 60)
        for field_code in df.columns:
            if field_code in field_mappings:
                field_name = field_mappings[field_code]["name"]
                non_null_count = df[field_code].count()
                null_count = len(df) - non_null_count
                completeness = (non_null_count / len(df)) * 100
                print(f"{field_code:>4} | {field_name:<12} | {completeness:>6.1f}% | 有效:{non_null_count:>4} 缺失:{null_count:>4}")
        
        print("="*80)

    def save_df(self, df: pd.DataFrame):
        if df is not None:
            if "涨跌幅" in df.columns:
                df = df.sort_values(by="涨跌幅", ascending=False).reset_index(drop=True)
            df.to_pickle(self.save_path)
            print(f"已保存到 {self.save_path}")

    def fetch_and_save(self, force_update: bool = False) -> pd.DataFrame | None:
        print(f"概念股文件将保存到: {self.save_path}")
        force_update = force_update or est_common.need_update(self.save_path)
        if not force_update and os.path.exists(self.save_path) and self.file_mtime_is_today(self.save_path):
            print(f"{self.save_path} 已是今日文件，无需更新。")
            return pd.read_pickle(self.save_path)
        df = self.fetch_concept_stocks()
        if df is not None:
            self.save_df(df)
        return df

    def get_concept_df(self) -> pd.DataFrame | None:
        if os.path.exists(self.save_path):
            return pd.read_pickle(self.save_path)
        print(f"{self.save_path} 文件不存在，请先运行 fetch_and_save() 获取数据。")
        return None

if __name__ == "__main__":
    fetcher = EastmoneyConceptStockFetcher()
    df = fetcher.fetch_and_save(force_update=True)  # 强制更新来触发字段分析
    if df is not None:
        print(df.head(10))
        print(f"总计拿到的行数: {len(df)}")
    else:
        print("未获取到数据")
