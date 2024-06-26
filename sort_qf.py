from threading import Lock, Thread, current_thread

import akshare as ak
import time
import datetime
import sys
import pandas as pd
import exchange_calendars as xcals
import argparse
import stock_config as config
import numpy as np
import pandas_ta as ta

class StockA:
    parser = argparse.ArgumentParser(description='stock script args')
    parser.add_argument('-a', '--all', action='store_true', required=False, help='Using all stocks', default=False)
    parser.add_argument('-c', '--code', type=str, metavar='', required=False, help='stock code', default="0")
    parser.add_argument('-b', '--back_test', type=int, metavar='', required=False,
                        help='Back to someday, 0 by default', default="0")
    parser.add_argument('-d', '--is_debug', action='store_true', required=False, help='is_debug using debug_end_time',
                        default=False)
    parser.add_argument('-n', '--concept_num', type=str, metavar='', required=False,
                        help='Top n concepts, 10 by default without -a', default="10")
    parser.add_argument('-o', '--over_avg20', type=int, metavar='', required=False,
                        help='Allowed to over avg20 percentage, 20% by default', default="20")
    parser.add_argument('-r', '--is_rm_last_day', action='store_true', required=False,
                        help='remove last day which is included in fenshi', default=False)
    parser.add_argument('-s', '--score', type=int, metavar='', required=False,
                        help='Should over 0 by default', default="0")
    parser.add_argument('-s1', '--min_score', type=int, metavar='', required=False,
                        help='min score of a stock, -30 by default', default="-30")
    parser.add_argument('-s2', '--sell_score', type=int, metavar='', required=False,
                        help='sell_q percentage of a stock, -20 by default', default="-20")
    parser.add_argument('-t', '--debug_end_time', type=str, metavar='', required=False,
                        help='debug_end_time using 14:30 by default', default="14:30")

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
        if debug_code != '0' and code != debug_code:
            return None
        # 返回： 股票代码
        row_code = {}
        if is_back_testing:
            self.back_test_date = self.conf.format_date(self.conf.get_trade_date(back_test_days))
            end = self.back_test_date.replace('-', '')
            start = self.conf.format_date(self.conf.get_trade_date(-60)).replace('-', '')
        else:
            # -2 表示倒数第二个交易日，最后一个交易日的数据通过分时接口获得
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
            # print(f"No daily data with code={code}")
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
        last_1_avg_price = (last_1_total_kai + last_1_total_shou)/2
        last_2_avg_price = (last_2_total_kai + last_2_total_shou)/2
        max_q_5_days = max(day_df['成交量'].iloc[-1], day_df['成交量'].iloc[-2], day_df['成交量'].iloc[-3],
                           day_df['成交量'].iloc[-4], day_df['成交量'].iloc[-5])
        min_q_5_days = min(day_df['成交量'].iloc[-1], day_df['成交量'].iloc[-2], day_df['成交量'].iloc[-3],
                           day_df['成交量'].iloc[-4], day_df['成交量'].iloc[-5])
        score_min_max_5_days = 0 - self.conf.get_score(min_q_5_days, max_q_5_days)

        if score_min_max_5_days < 50:
            return None

        if last_huan_shou_lv < 1:
            return None
        try:
            if not np.issubdtype(type(day_df['收盘'].iloc[0]), np.float64):
                return None
            macd_daily = day_df.ta.macd(close='收盘')['MACDh_12_26_9']

            score_macd_daily = self.conf.get_score(macd_daily.iloc[-1], macd_daily.iloc[-2])
        except:
            e = sys.exc_info()[0]
            print(f"code={code}, {e}")
            # return None

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
            # print(f"code={code}, {e}")
            return None
        if min_df.size == 0:
            return None

        min_df = min_df[min_df["时间"] >= '09:30:00']
        price = min_df['成交价'].iloc[-1]
        today_avg_price = (last_1_total_shou + price) / 2
        # 计算加速度的变化率，得分结果 = 50 - 加速度变化率，也就是得分越高变化率越小，也就越好
        diff_acc_1_2_price = last_1_avg_price - last_2_avg_price
        diff_acc_0_1_price = today_avg_price - last_1_avg_price
        if diff_acc_0_1_price != 0:
            score_price_avg = self.conf.get_score(diff_acc_1_2_price, diff_acc_0_1_price) / 100
        else:
            score_price_avg = 0
        avg_20_df = day_df['收盘'].rolling(20).mean()
        last_1_avg_20 = avg_20_df.iloc[-1]
        score_avg20 = self.conf.get_abs_score(np.mean(min_df['成交价']), last_1_avg_20)

        zhang = int(10000 * (price - last_huan_shou_price) / last_huan_shou_price) / 100
        if zhang > 5 or zhang < -3:
            return None
        row_code['zhang'] = zhang

        min_df['d_time_idx'] = min_df.apply(lambda x: self.conf.to_datetime(x['时间']), axis=1)
        min_df.set_index('d_time_idx', inplace=True)
        tmp_min_df = min_df.resample('H').agg({
            '成交价': 'last'
        }).dropna()
        tmp_min_df = tmp_min_df.rename(columns={'成交价': '收盘'})
        m_tmp_min_df = m_tmp_min_df._append(tmp_min_df, ignore_index=False, verify_integrity=True, sort=True)

        macd_m_min_hist = m_tmp_min_df.ta.macd(close='收盘')['MACDh_12_26_9']
        last_1_hour_macd = macd_m_min_hist.iloc[-1]
        last_2_hour_macd = macd_m_min_hist.iloc[-2]
        score_macd_hourly = self.conf.get_score(last_1_hour_macd, last_2_hour_macd)

        today_total_q = sum(min_df['手数'])
        score_q = 0 - self.conf.get_score(today_total_q, min_q_5_days * self.conf.get_trading_pecentage())

        row_code['s_min_max_5_days'] = int(score_min_max_5_days)
        row_code['s_q'] = int(score_q * 0.5)
        row_code['s_avg20'] = int(score_avg20 * 0.4)
        row_code['s_macd_hourly'] = int(score_macd_hourly * 0.3)
        row_code['s_price_avg'] = int(score_price_avg)

        # score 排名，缩量评分 + 50% avg20 + 30% macd + 10% 换手率（靠近5）+ 5% 中位数以上买卖比 + 负向加速的变化率
        score = 0
        score += row_code['s_min_max_5_days']
        score += row_code['s_q']
        score += row_code['s_avg20']
        score += row_code['s_macd_hourly']
        score += row_code['s_price_avg']
        if score < self.args.score:
            return None
        print(f'''[{code}]score_min_max_5_days: {score_min_max_5_days}, score_avg20: {score_avg20}, score_macd_hourly: {score_macd_hourly}
        ''')
        row_code['code'] = code
        row_code['score'] = score
        # print(f"{row_code}")
        return row_code

    def check_existing_code(self, tmp_code):
        self.all_codes_set_lock.acquire()

        if tmp_code in self.all_codes_set:
            self.all_codes_set_lock.release()
            return True
        self.all_codes_set.add(tmp_code)

        self.all_codes_set_lock.release()
        return False

    def get_trade_diff_mins(self, end_time):
        trade_diff_09_30 = self.get_time_diff_mins('09:30', end_time)
        trade_diff_11_30 = self.get_time_diff_mins('11:30', end_time)
        trade_diff_13_00 = self.get_time_diff_mins('13:00', end_time)

        # 9:30 前 则返回 0
        if trade_diff_09_30 < 0:
            return 0
        # 9:30 - 11:30 中间 则返回和9:30间的差值
        if trade_diff_11_30 <= 0:
            return trade_diff_09_30
        # 下午13:00前 则返回 上午总交易时间 120mins
        if trade_diff_13_00 <= 0:
            return 120
        # 下午13:00 - 15:00 则返回 上午总时间 + 下午和13:00间的差值
        return 120 + trade_diff_13_00

    def get_time_diff_mins(self, start_time, end_time):
        s_time_split = start_time.split(':')
        s_hour = int(s_time_split[0])
        s_min = int(s_time_split[1])

        e_time_split = end_time.split(':')
        e_hour = int(e_time_split[0])
        e_min = int(e_time_split[1])

        return (e_hour - s_hour) * 60 + e_min - s_min

    def append_all(self, thread_rs):
        self.lock.acquire()
        try:
            self.rs.extend(thread_rs)
        finally:
            self.lock.release()

    def run_thread_check(self, codes):
        s_ts = time.time()
        s_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        thread_rs = list()
        thx_name = current_thread().name
        code_len = len(codes)
        print(f"[{thx_name}] started...: {s_date}")
        n = 0
        flag = False
        for row in codes:
            code = row['code']
            n += 1
            if n % 200 == 0:
                now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"[{thx_name}] finished {n}/{code_len} with time: {now}")
            row_code = self.filter_by_min(row)
            if row_code is not None:
                row.update(row_code)
                thread_rs.append(row)
                flag = True
                print(f'[{thx_name}] {row}')
        e_ts = "%.2f" % (time.time() - s_ts)
        e_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if flag:
            print(f"[{thx_name}] finished all: {code_len}, elapse: {e_ts} ({s_date}  ~  {e_date})")
            self.append_all(thread_rs)

    def to_link(self, code):
        code_type = ""
        if code.startswith('30') or code.startswith('00'):
            code_type = '0.'
        elif code.startswith('60'):
            code_type = '1.'
        else:
            code_type = 'no_found'
        return f"https://wap.eastmoney.com/quote/stock/{code_type}{code}.html?appfenxiang=1"

    def run(self):

        s_ts = time.time()
        stock_zh_a_spot_em_df = None
        if not self.args.all:
            # 获取所有概念板块，判断板块涨幅排名前20
            stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
            total_concepts = len(stock_board_concept_name_em_df)
            s_num = 0
            if np.issubdtype(type(self.args.concept_num), np.integer) or ':' not in self.args.concept_num:
                e_num = int(self.args.concept_num)
            else:
                num_split_str = self.args.concept_num.split(':')
                s_num = int(num_split_str[0])
                e_num = int(num_split_str[1])

            stock_top = stock_board_concept_name_em_df[s_num:e_num]
            # stock_bottom = stock_board_concept_name_em_df.nsmallest(10,'涨跌幅',keep='first')
            stock_bottom = None
            stock_board_concept_name_em_df = pd.concat([stock_top, stock_bottom], ignore_index=True)
            # stock_board_concept_name_em_df = stock_board_concept_name_em_df.nsmallest(10,'涨跌幅',keep='last')
            print(stock_board_concept_name_em_df)
            print(f"concept list len is: {len(stock_board_concept_name_em_df)} / {total_concepts}")
            stock_df = None
            for ind in stock_board_concept_name_em_df.index:
                concept_name = stock_board_concept_name_em_df["板块名称"][ind]
                concept_code = stock_board_concept_name_em_df["板块代码"][ind]
                concept_rank = stock_board_concept_name_em_df["排名"][ind]
                # 找到所有符合条件的概念股并去重
                if not self.conf.exists_concept_data(concept_code):
                    concept_tmp_df = ak.stock_board_concept_cons_em(symbol=concept_name)
                    concept_tmp_df = concept_tmp_df.assign(concept_name=f"{concept_rank}-{concept_name}")
                    self.conf.save_concept_data(concept_code, concept_tmp_df)
                else:
                    concept_tmp_df = self.conf.get_concept_data(concept_code)
                concept_tmp_len = len(concept_tmp_df["代码"])
                if concept_tmp_len > 1000:
                    print(f"Ignore concept: {concept_name} with size: {concept_tmp_len}")
                    continue
                if stock_df is None:
                    stock_df = concept_tmp_df
                else:
                    stock_df = pd.concat([stock_df, concept_tmp_df], ignore_index=True)
                print(
                    f"Covered [{ind + 1}] {concept_name}: {len(stock_df['代码'])} with concept_tmp_df: {len(concept_tmp_df['代码'])}")

            stock_df = stock_df.drop_duplicates(subset=['代码'], keep='first')
            print(f"Covered stocks: {len(stock_df['代码'])}")
            stock_zh_a_spot_em_df = stock_df
        else:
            stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
            stock_zh_a_spot_em_df = stock_zh_a_spot_em_df.assign(concept_name='all')
        # not_st_df = stock_zh_a_spot_em_df.loc['ST' not in stock_zh_a_spot_em_df['名称']
        # and '退市' not in stock_zh_a_spot_em_df['名称'] and 'N' not in stock_zh_a_spot_em_df['名称'], ['名称']]
        thread_data_dict = dict()
        thread_dict = dict()
        for i in range(1, 50):
            thread_data_dict[i] = list()
        batch_num = 1
        batch_size = 50
        n = 0
        v_n = 0

        for i in stock_zh_a_spot_em_df.index:
            code = self.conf.get_format_code(str(stock_zh_a_spot_em_df['代码'][i]))
            tmp_flag = False
            for code_i in self.code_black_prefix_list:
                if code.startswith(code_i):
                    tmp_flag = True
                    break
            if tmp_flag:
                continue
            if code in self.all_codes_set:
                continue
            n += 1
            if code in self.black_list:
                continue
            name = stock_zh_a_spot_em_df['名称'][i]
            price = stock_zh_a_spot_em_df['最新价'][i]
            if price < 4:
                continue
            tmp_flag = False
            for name_i in self.name_black_prefix_list:
                if name_i in name:
                    tmp_flag = True
                    break
            if tmp_flag:
                continue
            chengjiao_val = stock_zh_a_spot_em_df['成交额'][i]
            huanshou_val = stock_zh_a_spot_em_df['换手率'][i]
            flow_val = chengjiao_val * 100 / huanshou_val
            if flow_val < 10 * 100000000 or flow_val > 200 * 100000000:
                continue

            if code.startswith("688") or code.startswith("8"):
                continue

            v_n += 1

            row = dict()
            row['code'] = code
            row['name'] = name
            row['concept_name'] = stock_zh_a_spot_em_df['concept_name'][i]

            thread_data_dict[batch_num].append(row)
            rape_list = list()
            rape_list.append(thread_data_dict[batch_num])
            if len(thread_data_dict[batch_num]) >= batch_size:
                thread_dict[batch_num] = Thread(target=self.run_thread_check, args=rape_list, name=batch_num,
                                                daemon=True)
                thread_dict[batch_num].start()
                # print(f"Valid stock code: {batch_num*batch_size}/{n}")
                batch_num += 1

        if len(thread_data_dict[batch_num]) > 0:
            thread_dict[batch_num] = Thread(target=self.run_thread_check, args=rape_list, name=batch_num, daemon=True)
            thread_dict[batch_num].start()

        # stock_df_len = len(stock_zh_a_spot_em_df)
        e_ts = "%.2f" % (time.time() - s_ts)
        print(f"Batch size: {batch_size}, num of batches:{batch_num}, total of stock codes: {v_n}/{n}, Elapse:{e_ts}\n")
        for k in thread_dict:
            thread_dict[k].join(timeout=3600000)
            # print(f"Thread {k} done! ---")
        return self.rs


if __name__ == "__main__":
    start_ts = time.time()
    stock = StockA()
    # stock.args.concept_num = 1
    rs = stock.run()
    # print(f"rs type = {type(rs)}")
    rs.sort(reverse=True, key=lambda r: r['score'])
    code_set = set()
    print("\n\n---------- Final result ------------\n")
    for idx, row in enumerate(rs):
        if not row['code'] in code_set:
            code_set.add(row['code'])
            print(row)

    file_name = '/Users/kevin/Downloads/stocks.txt'
    with open(file_name, 'w') as f:
        print(','.join(code_set), file=f)

    print(f"\nTotal: {len(code_set)} stocks")
    end_ts = time.time()

    back_test_msg = f"回测到: {stock.back_test_date} " if stock.args.back_test > 1 else ""
    print(f'''
Elapse: {'%.2f'%(end_ts - start_ts)}, {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
注意：交易日00:00 ~ 9:15之间的数据不准确，不要运行此脚本！
{back_test_msg}
被选中的股票写入文件地址：{file_name}
    ''')
