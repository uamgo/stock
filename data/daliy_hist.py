import datetime
import logging
import time
import pandas as pd
import akshare as ak
from pathlib import Path
import shutil
import pickle
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def get_today_str(fmt='%Y-%m-%d'):
    return datetime.datetime.now().strftime(fmt)

def get_proxy_files():
    today = get_today_str()
    base = Path(f'/tmp/proxies/{today}')
    return base / '89ip_proxies_ok.txt', base / '89ip_proxies_running_failed.txt'

def load_lines(path: Path) -> list[str]:
    if path.exists():
        with path.open() as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_line(path: Path, line: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(line + '\n')

def get_cache_dir() -> Path:
    cache_dir = Path(f'/tmp/{get_today_str("%Y%m%d")}')
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def set_proxy_env(proxy: str, scheme: str = "http"):
    url = f"{scheme}://{proxy}"
    os.environ["http_proxy"] = url
    os.environ["https_proxy"] = url

def clear_proxy_env():
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)

def load_or_cache_pickle(file_path: Path, fetch_func, *args, use_proxy=False, proxies=None, failed_proxies=None, **kwargs):
    if file_path.exists():
        with file_path.open('rb') as f:
            return pickle.load(f)
    df = None
    if use_proxy and proxies:
        for proxy in proxies:
            if failed_proxies and proxy in failed_proxies:
                continue
            logging.info(f"Trying proxy: {proxy}, remaining proxies: {len([p for p in proxies if p not in (failed_proxies or set())])}")
            for scheme in ("http", "https"):
                try:
                    set_proxy_env(proxy, scheme)
                    df = fetch_func(*args, **kwargs)
                    clear_proxy_env()
                    break
                except Exception:
                    clear_proxy_env()
                    if failed_proxies is not None:
                        failed_proxies.add(proxy)
                    continue
            if df is not None:
                break
        if df is None:
            raise RuntimeError("All proxies failed")
    else:
        df = fetch_func(*args, **kwargs)
    with file_path.open('wb') as f:
        pickle.dump(df, f)
    return df

def filter_stocks(df: pd.DataFrame) -> pd.DataFrame:
    cond = pd.Series(True, index=df.index)
    if '名称' in df.columns:
        cond &= ~df['名称'].str.contains('ST|st|京A|科创', regex=True)
    if '代码' in df.columns:
        cond &= ~df['代码'].str.contains('[A-Za-z]', regex=True)
    if '60日涨跌幅' in df.columns:
        cond &= (df['60日涨跌幅'] >= 0)
    if '量比' in df.columns:
        cond &= (df['量比'] <= 1)
    return df[cond]

def get_top_concept_codes(concept_df: pd.DataFrame, top_n: int, cache_dir: Path, use_proxy=False, proxies=None, failed_proxies=None) -> set:
    top_concepts = concept_df.head(top_n)['板块名称'].tolist()
    hot_codes = set()
    for concept in top_concepts:
        try:
            concept_id = concept_df.loc[concept_df['板块名称'] == concept, '板块代码'].values[0]
            concept_cache = cache_dir / f'concept_{concept_id}.pkl'
            members = load_or_cache_pickle(concept_cache, ak.stock_board_concept_cons_em, concept,
                                           use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)
            hot_codes.update(members['代码'].tolist())
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"Failed to fetch members for concept: {concept}, skipping: {e}")
    return hot_codes

def filter_by_hist(df: pd.DataFrame, cache_dir: Path, use_proxy=False, proxies=None, failed_proxies=None) -> pd.DataFrame:
    filtered_codes = []
    for code in df['代码']:
        try:
            hist_cache = cache_dir / f"{code}_hist.pkl"
            hist = load_or_cache_pickle(hist_cache, ak.stock_zh_a_hist, symbol=code, period="daily",
                                        start_date=None, end_date=None, adjust="",
                                        use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)
            if len(hist) < 3:
                continue
            last_3 = hist.iloc[-3:]
            last_vol = last_3['成交量'].iloc[-1]
            min_vol = last_3['成交量'].min()
            if last_vol != min_vol:
                continue
            max_vol_row = last_3.loc[last_3['成交量'].idxmax()]
            open_p, close_p, high_p, low_p = max_vol_row['开盘'], max_vol_row['收盘'], max_vol_row['最高'], max_vol_row['最低']
            upper_shadow = high_p - max(open_p, close_p)
            lower_shadow = min(open_p, close_p) - low_p
            if upper_shadow > lower_shadow or close_p < open_p:
                continue
            filtered_codes.append(code)
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"Failed to fetch data for {code}, skipping: {e}")
    return df[df['代码'].isin(filtered_codes)]

def fetch_filtered_stocks(top_n: int = 30, use_proxy=False) -> pd.DataFrame:
    proxies_file, failed_file = get_proxy_files()
    proxies = load_lines(proxies_file)
    failed_proxies = set(load_lines(failed_file))
    cache_dir = get_cache_dir()
    spot_cache = cache_dir / 'spot_raw.pkl'
    try:
        df = load_or_cache_pickle(spot_cache, ak.stock_zh_a_spot_em, use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)
    except Exception:
        df = load_or_cache_pickle(spot_cache, ak.stock_zh_a_spot, use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)

    filtered_cache = cache_dir / f'spot_top{top_n}.pkl'
    if filtered_cache.exists():
        with filtered_cache.open('rb') as f:
            df = pickle.load(f)
    else:
        df = filter_stocks(df)
        with filtered_cache.open('wb') as f:
            pickle.dump(df, f)

    concept_cache = cache_dir / 'concepts.pkl'
    concept_df = load_or_cache_pickle(concept_cache, ak.stock_board_concept_name_em, use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)
    hot_concept_codes = get_top_concept_codes(concept_df, top_n, cache_dir, use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)
    df = df[df['代码'].isin(hot_concept_codes)]
    return filter_by_hist(df, cache_dir, use_proxy=use_proxy, proxies=proxies, failed_proxies=failed_proxies)

def main():
    use_proxy = False
    force_delete = False
    cache_dir = get_cache_dir()
    if force_delete and cache_dir.exists():
        shutil.rmtree(cache_dir)
    start_time = time.perf_counter()
    logging.info("Start fetching and filtering stocks...")
    result_df = fetch_filtered_stocks(top_n=20, use_proxy=use_proxy)
    filtered_stocks = result_df['代码'].tolist()
    Path('/Users/kevin/Downloads/filtered_stocks_hist.txt').write_text(','.join(filtered_stocks))
    logging.info(f"剩余过滤出来的股票数量: {len(filtered_stocks)}")
    logging.info(f"Total time taken: {time.perf_counter() - start_time:.2f}s")

if __name__ == "__main__":
    main()
