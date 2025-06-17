import os
import pandas as pd

class AllCodesGenerator:
    def __init__(self, concepts_dir="/tmp/stock/base/concepts", save_path="/tmp/stock/base/all_codes.pkl"):
        self.concepts_dir = concepts_dir
        self.save_path = save_path

    def generate(self, force_update=False):
        # 如果不强制更新且文件已存在则跳过
        if not force_update and os.path.exists(self.save_path):
            print(f"{self.save_path} 已存在，跳过保存")
            codes_df = pd.read_pickle(self.save_path)
            print(codes_df)
            print(f"已保存去重后的股票代码到 {self.save_path}，共 {len(codes_df)} 条")
            return

        # 读取所有pkl文件并合并
        dfs = []
        for fname in os.listdir(self.concepts_dir):
            if fname.endswith(".pkl"):
                df = pd.read_pickle(os.path.join(self.concepts_dir, fname))
                dfs.append(df)
        if not dfs:
            print("未找到任何成分股数据")
            return
        all_df = pd.concat(dfs, ignore_index=True)
        # 获取所有去重后的股票代码
        code_col = "code" if "code" in all_df.columns else "股票代码"
        symbol_col = "symbol" if "symbol" in all_df.columns else "股票简称"
        codes_df = all_df[[code_col, symbol_col]].drop_duplicates(subset=[code_col]).reset_index(drop=True)

        # 保存
        codes_df.to_pickle(self.save_path)
        print(codes_df)
        print(f"已保存去重后的股票代码到 {self.save_path}，共 {len(codes_df)} 条")

if __name__ == "__main__":
    generator = AllCodesGenerator()
    generator.generate(force_update=False)  # 默认不强制更新