import os
import math
import pandas as pd
import requests
from datetime import datetime
from data.est.req import est_common
import traceback
import threading

class ConceptStockManager:
    def __init__(self, save_dir="/tmp/stock/concept"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def get_save_path(self, concept_code: str) -> str:
        return os.path.join(self.save_dir, f"{concept_code}.pkl")

    def file_mtime_is_today(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return mtime.date() == datetime.now().date()

    def get_base_url(self, concept_code: str, page: int = 1, pz: int = 50) -> str:
        return (
            "https://push2.eastmoney.com/api/qt/clist/get"
            "?cb=json"
            f"&fid=f62&po=1&pz={pz}&pn={page}&np=1&fltt=2&invt=2"
            "&ut=8dec03ba335b81bf4ebdf7b29ec27d15"
            f"&fs=b%3A{concept_code}"
            "&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124%2Cf1%2Cf13"
        )

    def fetch_concept_members(self, concept_code: str, proxy=None) -> pd.DataFrame:
        base_url = self.get_base_url(concept_code, page="{page}")
        proxies = proxy

        import requests

        all_rows, _ = est_common.fetch_all_pages(base_url, proxies=proxies)

        if all_rows:
            df = pd.DataFrame(all_rows).rename(
                columns={"f12": "代码", "f14": "名称", "f3": "涨跌幅", "f13": "前缀"}
            )
            df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
            return df.sort_values(by="涨跌幅", ascending=False).reset_index(drop=True)
        return None

    def save_concept_members(self, concept_code: str, df: pd.DataFrame):
        if df is not None:
            df.to_pickle(self.get_save_path(concept_code))

    def _update_chunk(self, codes_chunk, progress_counter):
        proxy = est_common.get_proxy()
        for code in codes_chunk:
            retry_count = 0
            while retry_count < 3:
                try:
                    df = self.fetch_concept_members(code, proxy=proxy)
                    self.save_concept_members(code, df)
                    progress_counter["count"] += 1
                    print(f"[{threading.current_thread().name}] 完成 {code}，进度 {progress_counter['count']}/{progress_counter['total']}")
                    break
                except Exception as fetch_exc:
                    retry_count += 1
                    print(f"获取概念成员失败，尝试更换代理({retry_count}/3): {fetch_exc}")
                    if retry_count < 3:
                        proxy = est_common.get_proxy()
                    else:
                        print(f"更新概念 {code} 失败: 连续三次更换代理均失败")
                        traceback.print_exc()
                        return

    def update_all_concepts(self, concept_codes, use_proxy_and_concurrent=10):
        progress_counter = {"count": 0, "total": len(concept_codes)}
        # 过滤掉所有 need_update_simple 为 False 的概念代码
        concept_codes = [code for code in concept_codes if est_common.need_update_simple(self.get_save_path(code))]
        progress_counter["total"] = len(concept_codes)
        if not concept_codes:
            print(f"所有概念数据均为最新，无需更新。数据保存目录: {self.save_dir}")
            return

        chunk_size = max(5, math.ceil(len(concept_codes) / use_proxy_and_concurrent) if use_proxy_and_concurrent > 0 else len(concept_codes))
        chunked_codes = [concept_codes[i:i + chunk_size] for i in range(0, len(concept_codes), chunk_size)]
        threads = []
        for codes_chunk in chunked_codes:
            t = threading.Thread(target=self._update_chunk, args=(codes_chunk, progress_counter))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def get_concept_df(self, concept_code: str) -> pd.DataFrame:
        path = self.get_save_path(concept_code)
        if os.path.exists(path):
            return pd.read_pickle(path)
        print(f"{path} 文件不存在，请先运行 update_all_concepts 获取数据。")
        return None

    def get_members_codes(self, concept_codes) -> pd.DataFrame:
        dfs = []
        for code in concept_codes:
            df = self.get_concept_df(code)
            if df is not None:
                df = df[["代码", "名称"]].copy()
                df["concept_code"] = code
                dfs.append(df)
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame(columns=["代码", "名称", "concept_code"])

if __name__ == "__main__":
    manager = ConceptStockManager()
    all_concept_codes = ['BK0816', 'BK1051', 'BK0983', 'BK1071', 'BK1152', 'BK0883', 'BK0603', 'BK1075', 'BK0606', 'BK0818']
    manager.update_all_concepts(all_concept_codes, use_proxy_and_concurrent=2)
    df = manager.get_concept_df("BK0816")
    print(df)
    codes_df = manager.get_members_codes(["BK0816", "BK1051"])
    print(codes_df)
