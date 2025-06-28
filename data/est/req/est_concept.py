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
        if not est_common.need_update(self.save_path):
            print(f"{self.save_path} 已是最新，无需更新。")
            return pd.read_pickle(self.save_path)
        self.proxy = est_common.get_proxy()
        all_rows = []
        page = 1
        total = None
        while True:
            url = base_url.format(page=page)
            print(f"请求URL: {url}")
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
                print(f"请求第{page}页失败: {e}")
                break
        if all_rows:
            if total is not None and len(all_rows) < total:
                print(f"警告：累计行数 {len(all_rows)} 少于 total {total}，可能有数据缺失！")
            df = pd.DataFrame(all_rows)
            df = df.rename(columns={
                "f12": "代码",
                "f14": "名称",
                "f3": "涨跌幅",
                "f184": "概念名称"
            })
            return df
        print("未获取到概念股数据")
        return None

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
    df = fetcher.fetch_and_save(force_update=True)
    if df is not None:
        print(df.head(10))
        print(f"总计拿到的行数: {len(df)}")
    else:
        print("未获取到数据")
