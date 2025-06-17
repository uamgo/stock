import os
import time
import pandas as pd
import akshare as ak

CODES_PATH = "/tmp/stock/base/all_codes.pkl"
SAVE_DIR = "/tmp/stock/base/daily"
os.makedirs(SAVE_DIR, exist_ok=True)

def main():
    codes_df = pd.read_pickle(CODES_PATH)
    code_col = "code" if "code" in codes_df.columns else "股票代码"
    codes = codes_df[code_col].drop_duplicates().tolist()

    for idx, code in enumerate(codes, 1):
        code = str(code)
        if len(code) < 6:
            code = code.zfill(6)
        elif len(code) > 6:
            code = code[-6:]
        if not code.isdigit():
            print(f"[{idx}/{len(codes)}] {code} 不是有效的6位数字代码，跳过")
            continue
        save_path = os.path.join(SAVE_DIR, f"{code}.pkl")
        if os.path.exists(save_path):
            print(f"[{idx}/{len(codes)}] {code} 已存在，跳过")
            continue
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="")
            df.to_pickle(save_path)
            print(f"[{idx}/{len(codes)}] {code} 日线数据已保存，{len(df)} 条")
            time.sleep(1.5)
        except Exception as e:
            print(f"[{idx}/{len(codes)}] {code} 获取失败: {e}")
            break

if __name__ == "__main__":
    main()