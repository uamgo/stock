from threading import Lock, Thread, current_thread
import akshare as ak
import time
import datetime
import pandas as pd
import exchange_calendars as xcals
import argparse
import stock_config as config
import numpy as np
import pandas_ta as ta

class StockA:
    parser = argparse.ArgumentParser(description='stock script args')
    parser.add_argument('-a', '--all', action='store_true', help='Using all stocks', default=False)
    parser.add_argument('-c', '--code', type=str, metavar='', help='stock code', default="0")
    parser.add_argument('-b', '--back_test', type=int, metavar='', help='Back to someday, 0 by default', default="0")
    parser.add_argument('-d', '--is_debug', action='store_true', help='is_debug using debug_end_time', default=False)
    parser.add_argument('-n', '--concept_num', type=str, metavar='', help='Top n concepts, 10 by default without -a', default="10")
    parser.add_argument('-o', '--over_avg20', type=int, metavar='', help='Allowed to over avg20 percentage, 20% by default', default="20")
    parser.add_argument('-r', '--is_rm_last_day', action='store_true', help='remove last day which is included in fenshi', default=False)
    parser.add_argument('-s', '--score', type=int, metavar='', help='Should over 0 by default', default="0")
    parser.add_argument('-s1', '--min_score', type=int, metavar='', help='min score of a stock, -30 by default', default="-30")
    parser.add_argument('-s2', '--sell_score', type=int, metavar='', help='sell_q percentage of a stock, -20 by default', default="-20")
    parser.add_argument('-t', '--debug_end_time', type=str, metavar='', help='debug_end_time using 14:30 by default', default="14:30")

    args = parser.parse_args()
    conf = config.StockConfig()
    is_trading_now = conf.is_tradingNow()
    back_test_date = conf.last_trade_day_ts

    black_list = ['600865']
    code_black_prefix_list = ['20', '40']
    name_black_prefix_list = ['ST', '退市', 'N', 'L', 'C', 'U']
    rs = list()
    lock = Lock()
    stock_zh_a_gdhs_df = None
    total_trade_ellipse = 240
    xshg = xcals.get_calendar("XSHG")
    is_today_trade = xshg.is_session(datetime.datetime.now().strftime("%Y-%m-%d"))
    base_path = "/tmp/stock"
    all_codes_set = set()
    all_codes_set_lock = Lock()

    def filter_by_min(self, code_row):
        code = code_row['code']
        debug_code = self.args.code
        back_test_days = 0 - self.args.back_test
        is_back_testing = (back_test_days <= -2)
        trading_percentage = self.conf.get_trading_pecentage()
        if is_back_testing:
            trading_percentage = 1
        if debug_code != '0' and code != debug_code:
            return None
        row_code = {}
        if is_back_testing:
            self.back_test_date = self.conf.format_date(self.conf.get_trade_date(back_test_days))
            end = self.back_test_date.replace('-', '')
            start = self.conf.format_date(self.conf.get_trade_date(-60)).replace('-', '')
        else:
            end = self.conf.format_date(self.conf.get_trade_date(-2)).replace('-', '')
            start = self.conf.format_date(self.conf.get_trade_date(-60)).replace('-', '')
        try:
            if not self.conf.exists_daily_data(code):
                day_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
                self.conf.save_daily_data(code, day_df)
            else:
                day_df = self.conf.get_daily_data(code)
        except:
            e = sys.exc_info()[0]
            print(f"code={code}, {e}")
            return None
        if len(day_df) <= 35:
            return None

        last_huan_shou_price = day_df['收盘'].iloc[-1]
        last_day_chengjiaoe = day_df['成交额'].iloc[-1]
        last_huan_shou_lv = day_df['换手率'].iloc[-1]
        last_total_q = day_df['成交量'].iloc[-1]
        last_2_total_q = day_df['成交量'].iloc[-2]
        flow_value = last_day_chengjiaoe * 100 / last_huan_shou_lv
        last_1_total_kai = day_df['开盘'].iloc[-1]
        last_1_total_shou = day_df['收盘'].iloc[-1]
        last_2_total_kai = day_df['开盘'].iloc[-2]
        last_2_total_shou = day_df['收盘'].iloc[-2]
        last_1_avg_price = (last_1_total_kai + last_1_total_shou) / 2
        last_2_avg_price = (last_2_total_kai + last_2_total_shou) / 2
        max_q_5_days = max(day_df['成交量'].iloc[-5:])
        min_q_5_days = min(day_df['成交量'].iloc[-5:])
        score_min_max_5_days = 0 - self.conf.get_score(min_q_5_days, max_q_5_days)

        if score_min_max_5_days < 50 or last_huan_shou_lv < 1:
            return None

        score_macd_daily = 0
        try:
            if not np.issubdtype(type(day_df['收盘'].iloc[0]), np.float64):
                return None
            macd_daily = day_df.ta.macd(close='收盘')['MACDh_12_26_9']
            score_macd_daily = 10 if macd_daily.iloc[-1] > macd_daily.iloc[-2] else -100
            score_macd_daily += 10 if macd_daily.iloc[-2] > macd_daily.iloc[-3] else -100
        except:
            e = sys.exc_info()[0]
            print(f"code={code}, {e}")

        min_df_hist = ak.stock_zh_a_hist_min_em(symbol=code, start_date=start, end_date=end, period="60", adjust="")
        min_df_hist['d_time_idx'] = min_df_hist.apply(lambda x: self.conf.to_datetime(x['时间']), axis=1)
        min_df_hist.set_index('d_time_idx', inplace=True)
        min_df_hist = pd.DataFrame(min_df_hist, columns=['收盘'])

        m_tmp_min_df = min_df_hist

        try:
            if is_back_testing:
                min_date = self.conf.format_date(self.conf.get_trade_date(back_test_days + 1))
                min_df = ak.stock_zh_a_hist_min_em(symbol="000001", start_date=f"{min_date} 09:30:00",
                                                   end_date=f"{min_date} 15:00:00", period="1", adjust="")
            else:
                min_df = ak.stock_intraday_em(symbol=code)
        except:
            e = sys.exc_info()[0]
            return None
        if min_df.size == 0:
            return None

        min_df = min_df[min_df["时间"] >= '09:30:00']
        price = min_df['成交价'].iloc[-1]
        today_avg_price = (last_1_total_shou + price) / 2
        diff_acc_1_2_price = last_1_avg_price - last_2_avg_price
        diff_acc_0_1_price = today_avg_price - last_1_avg_price
        score_price_avg = -20 if diff_acc_0_1_price > diff_acc_1_2_price else 10

        avg_20_df = day_df['收盘'].rolling(20).mean()
        last_1_avg_20 = avg_20_df.iloc[-1]
        score_avg20 = self.conf.get_abs_score(np.mean(min_df['成交价']), last_1_avg_20)

        zhang = int(10000 * (price - last_huan_shou_price) / last_huan_shou_price) / 100
        row_code['zhang'] = zhang

        min_df['d_time_idx'] = min_df.apply(lambda x: self.conf.to_datetime(x['时间']), axis=1)
        min_df.set_index('d_time_idx', inplace=True)
        tmp_min_df = min_df.resample('H').agg({'成交价': 'last'}).dropna()
        tmp_min_df = tmp_min_df.rename(columns={'成交价': '收盘'})
        m_tmp_min_df = m_tmp_min_df._append(tmp_min_df, ignore_index=False, verify_integrity=True, sort=True)

        macd_m_min_hist = m_tmp_min_df.ta.macd(close='收盘')['MACDh_12_26_9']
        last_1_hour_macd = macd_m_min_hist.iloc[-1]
        last_2_hour_macd = macd_m_min_hist.iloc[-2]
        last_3_hour_macd = macd_m_min_hist.iloc[-3]
        score_macd_hourly = 10 if last_1_hour_macd > last_2_hour_macd else -100
        score_macd_hourly += 10 if last_2_hour_macd > last_3_hour_macd else -100

        today_total_q = sum(min_df['手数'])
        score_q = 0 - self.conf.get_score(today_total_q, min_q_5_days * trading_percentage)

        row_code.update({
            's_m_x_5_days': int(score_min_max_5_days),
            's_q': int(score_q * 0.5),
            's_avg20': int(score_avg20 * 0.4),
            's_macd_hourly': score_macd_hourly,
            's_macd_daily': score_macd_daily,
            's_price_avg': int(score_price_avg)
        })

        score = sum(row_code.values())
        if score < self.args.score:
            return None
        print(f"[{code}]score_min_max_5_days: {score_min_max_5_days}, score_avg20: {score_avg20}, score_macd_hourly: {score_macd_hourly}")
        row_code['code'] = code
        row_code['score'] = score
        return row_code

    def check_existing_code(self, tmp_code):
        with self.all_codes_set_lock:
            if tmp_code in self.all_codes_set:
                return True
            self.all_codes_set.add(tmp_code)
        return False

    def get_trade_diff_mins(self, end_time):
        trade_diff_09_30 = self.get_time_diff_mins('09:30', end_time)
        trade_diff_11_30 = self.get_time_diff_mins('11:30', end_time)
        trade_diff_13_00 = self.get_time_diff_mins('13:00', end_time)

        if trade_diff_09_30 < 0:
            return 0
        if trade_diff_11_30 <= 0:
            return trade_diff_09_30
        if trade_diff_13_00 <= 0:
            return 120
        return 120 + trade_diff_13_00

    def get_time_diff_mins(self, start_time, end_time):
        s_hour, s_min = map(int, start_time.split(':'))
        e_hour, e_min = map(int, end_time.split(':'))
        return (e_hour - s_hour) * 60 + e_min - s_min

    def append_all(self, thread_rs):
        with self.lock:
            self.rs.extend(thread_rs)

    def run_thread_check(self, codes):
        s_ts = time.time()
        s_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        thread_rs = []
        thx_name = current_thread().name
        code_len = len(codes)
        print(f"[{thx_name}] started...: {s_date}")
        for n, row in enumerate(codes, 1):
            if n % 200 == 0:
                now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"[{thx_name}] finished {n}/{code_len} with time: {now}")
            row_code = self.filter_by_min(row)
            if row_code:
                row.update(row_code)
                thread_rs.append(row)
                print(f'[{thx_name}] {row}')
        e_ts = "%.2f" % (time.time() - s_ts)
        e_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if thread_rs:
            print(f"[{thx_name}] finished all: {code_len}, elapse: {e_ts} ({s_date}  ~  {e_date})")
            self.append_all(thread_rs)

    def to_link(self, code):
        code_type = '0.' if code.startswith(('30', '00')) else '1.' if code.startswith('60') else 'no_found'
        return f"https://wap.eastmoney.com/quote/stock/{code_type}{code}.html?appfenxiang=1"

    def run(self):
        s_ts = time.time()
        stock_zh_a_spot_em_df = None
        if not self.args.all:
            stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
            total_concepts = len(stock_board_concept_name_em_df)
            s_num, e_num = 0, int(self.args.concept_num)
            if ':' in self.args.concept_num:
                s_num, e_num = map(int, self.args.concept_num.split(':'))
            stock_top = stock_board_concept_name_em_df[s_num:e_num]
            stock_board_concept_name_em_df = pd.concat([stock_top], ignore_index=True)
            print(stock_board_concept_name_em_df)
            print(f"concept list len is: {len(stock_board_concept_name_em_df)} / {total_concepts}")
            stock_df = None
            for ind in stock_board_concept_name_em_df.index:
                concept_name = stock_board_concept_name_em_df["板块名称"][ind]
                concept_code = stock_board_concept_name_em_df["板块代码"][ind]
                concept_rank = stock_board_concept_name_em_df["排名"][ind]
                if not self.conf.exists_concept_data(concept_code):
                    concept_tmp_df = ak.stock_board_concept_cons_em(symbol=concept_name)
                    concept_tmp_df = concept_tmp_df.assign(concept_name=f"{concept_rank}-{concept_name}")
                    self.conf.save_concept_data(concept_code, concept_tmp_df)
                else:
                    concept_tmp_df = self.conf.get_concept_data(concept_code)
                if len(concept_tmp_df["代码"]) > 1000:
                    print(f"Ignore concept: {concept_name} with size: {len(concept_tmp_df['代码'])}")
                    continue
                stock_df = pd.concat([stock_df, concept_tmp_df], ignore_index=True) if stock_df is not None else concept_tmp_df
                print(f"Covered [{ind + 1}] {concept_name}: {len(stock_df['代码'])} with concept_tmp_df: {len(concept_tmp_df['代码'])}")
            stock_df = stock_df.drop_duplicates(subset=['代码'], keep='first')
            print(f"Covered stocks: {len(stock_df['代码'])}")
            stock_zh_a_spot_em_df = stock_df
        else:
            stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
            stock_zh_a_spot_em_df = stock_zh_a_spot_em_df.assign(concept_name='all')

        thread_data_dict = {i: [] for i in range(1, 50)}
        thread_dict = {}
        batch_num = 1
        batch_size = 50
        n, v_n = 0, 0

        for i in stock_zh_a_spot_em_df.index:
            code = self.conf.get_format_code(str(stock_zh_a_spot_em_df['代码'][i]))
            if any(code.startswith(prefix) for prefix in self.code_black_prefix_list) or code in self.all_codes_set or code in self.black_list:
                continue
            name = stock_zh_a_spot_em_df['名称'][i]
            price = stock_zh_a_spot_em_df['最新价'][i]
            if price < 4 or any(prefix in name for prefix in self.name_black_prefix_list):
                continue
            chengjiao_val = stock_zh_a_spot_em_df['成交额'][i]
            huanshou_val = stock_zh_a_spot_em_df['换手率'][i]
            if huanshou_val == 0:
                continue
            flow_val = chengjiao_val * 100 / huanshou_val
            if flow_val < 10 * 100000000 or flow_val > 200 * 100000000 or code.startswith(("688", "8")):
                continue

            v_n += 1
            row = {'code': code, 'name': name, 'concept_name': stock_zh_a_spot_em_df['concept_name'][i]}
            thread_data_dict[batch_num].append(row)
            if len(thread_data_dict[batch_num]) >= batch_size:
                thread_dict[batch_num] = Thread(target=self.run_thread_check, args=(thread_data_dict[batch_num],), name=batch_num, daemon=True)
                thread_dict[batch_num].start()
                batch_num += 1

        if thread_data_dict[batch_num]:
            thread_dict[batch_num] = Thread(target=self.run_thread_check, args=(thread_data_dict[batch_num],), name=batch_num, daemon=True)
            thread_dict[batch_num].start()

        e_ts = "%.2f" % (time.time() - s_ts)
        print(f"Batch size: {batch_size}, num of batches:{batch_num}, total of stock codes: {v_n}/{n}, Elapse:{e_ts}\n")
        for k in thread_dict:
            thread_dict[k].join(timeout=3600000)
        return self.rs

if __name__ == "__main__":
    start_ts = time.time()
    stock = StockA()
    rs = stock.run()
    rs.sort(reverse=True, key=lambda r: r['score'])
    code_list = [row['code'] for row in rs if row['code'] not in code_list]
    print("\n\n---------- Final result ------------\n")