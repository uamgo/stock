import os
import pandas as pd

CONCEPTS_DIR = "/tmp/stock/base/concepts"
SAVE_PATH = "/tmp/stock/base/all_codes.pkl"

def main():
    # 读取所有pkl文件并合并
    dfs = []
    for fname in os.listdir(CONCEPTS_DIR):
        if fname.endswith(".pkl"):
            df = pd.read_pickle(os.path.join(CONCEPTS_DIR, fname))
            dfs.append(df)
    if not dfs:
        print("未找到任何成分股数据")
        return
    all_df = pd.concat(dfs, ignore_index=True)
    # print(all_df)
    # 获取所有去重后的股票代码
    # 兼容不同字段名
    code_col = "code" if "code" in all_df.columns else "股票代码"
    symbol_col = "symbol" if "symbol" in all_df.columns else "股票简称"
    codes_df = all_df[[code_col, symbol_col]].drop_duplicates(subset=[code_col]).reset_index(drop=True)

    # 保存
    codes_df.to_pickle(SAVE_PATH)
    print(codes_df)
    print(f"已保存去重后的股票代码到 {SAVE_PATH}，共 {len(codes_df)} 条")

if __name__ == "__main__":
    main()