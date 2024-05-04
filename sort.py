from threading import Lock, Thread, current_thread

import akshare as ak
import time
import datetime
import sys
import pandas as pd
import pandas_ta as ta
import math
import exchange_calendars as xcals
import argparse
import stock_config as config
import numpy as np


class StockA:
    parser = argparse.ArgumentParser(description='stock script args')
    parser.add_argument('-a', '--all', action='store_true', required=False, help='Using all stocks', default=False)
    parser.add_argument('-c', '--code', type=str, metavar='', required=False, help='stock code', default="0")
    parser.add_argument('-d', '--is_debug', action='store_true', required=False, help='is_debug using debug_end_time',
                        default=False)
    parser.add_argument('-n', '--concept_num', type=str, metavar='', required=False,
                        help='Top n concepts, 10 by default without -a', default="10")
    parser.add_argument('-r', '--is_rm_last_day', action='store_true', required=False,
                        help='remove last day which is included in fenshi', default=False)
    parser.add_argument('-s', '--min_score', type=int, metavar='', required=False,
                        help='min score of a stock, 30 by default', default="30")
    parser.add_argument('-t', '--debug_end_time', type=str, metavar='', required=False,
                        help='debug_end_time using 14:30 by default', default="14:30")

    args = parser.parse_args()
    conf = config.StockConfig()
    is_trading_now = conf.is_tradingNow()

    black_list = ['600865']
    rs = list()
    lock = Lock()
    stock_zh_a_gdhs_df = None
    total_trade_ellipse = 240
    xshg = xcals.get_calendar("XSHG")
    is_today_trade = xshg.is_session(datetime.datetime.now().strftime("%Y-%m-%d"))
    base_path = "/tmp/stock"
    all_codes_set = set()
    all_codes_set_lock = Lock()

    # 返回：list 包含 股票代码、策略类型、权重
    # 策略类型：900 策略一，800 策略二，700 策略三
    # 权重：100 - 100 * abs（当前价格 - 均值）/ 均值
    def filter_by_min(self, code_row):
        code = code_row['code']
        concept_name = code_row['concept_name']
        debug_code = self.args.code
        is_debug_end_time = self.args.is_debug
        debug_end_time = self.args.debug_end_time
        args_min_score = self.args.min_score
        args_concept_num = self.args.concept_num
        if debug_code != '0' and code != debug_code:
            return None
        # 返回： 股票代码
        row_code = {}
        # 获取前一日价格
        end = self.conf.last_trade_day_str.replace('-', '')
        start = self.time_fmt(60)
        day_df = None
        stock_zh_a_gdhs_detail_em_df = None
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
        if len(day_df) == 0:
            # print(f"No daily data with code={code}")
            return None

        last_huan_shou_price = day_df['收盘'].iloc[-1]
        last_day_chengjiaoe = day_df['成交额'].iloc[-1]
        last_huan_shou_lv = day_df['换手率'].iloc[-1]
        last_total_q = day_df['成交量'].iloc[-1]
        last_2_total_q = day_df['成交量'].iloc[-2]
        flow_value = last_day_chengjiaoe * 100 / last_huan_shou_lv

        if last_huan_shou_lv < 1.5:
            return None
        try:
            if not np.issubdtype(type(day_df['收盘'].iloc[0]), np.float64):
                return None
            macd_daily = day_df.ta.macd(close='收盘')['MACDh_12_26_9']
            # if macd_daily.iloc[-1] < macd_daily.iloc[-2] or macd_daily.iloc[-1] < 0:
            if macd_daily.iloc[-1] < macd_daily.iloc[-2]:
                return None
        except:
            e = sys.exc_info()[0]
            print(f"code={code}, {e}")
            return None

        min_df_hist = ak.stock_zh_a_hist_min_em(symbol=code, start_date=start, end_date=end, period="60", adjust="")
        last_min_df_day = min_df_hist['时间'].iloc[-1][:10]
        today_hist_min = min(min_df_hist['最低'].iloc[-1], min_df_hist['最低'].iloc[-2], min_df_hist['最低'].iloc[-3],
                             min_df_hist['最低'].iloc[-4])

        total_min_q = min_df_hist['成交量'].iloc[-1] + min_df_hist['成交量'].iloc[-2] + min_df_hist['成交量'].iloc[-3] + \
                      min_df_hist['成交量'].iloc[-4]
        min_df_hist['d_time_idx'] = min_df_hist.apply(lambda x: self.conf.to_datetime(x['时间']), axis=1)
        min_df_hist.set_index('d_time_idx', inplace=True)
        min_df_hist = pd.DataFrame(min_df_hist, columns=['收盘'])
        macd_min_hist = min_df_hist.ta.macd(close='收盘')['MACDh_12_26_9']

        m_tmp_min_df = min_df_hist
        price = min_df_hist['收盘'].iloc[-1]

        try:
            min_df = ak.stock_intraday_em(symbol=code)
        except:
            e = sys.exc_info()[0]
            # print(f"code={code}, {e}")
            return None
        if min_df.size == 0:
            # print(f"no data for ak.stock_intraday_em with code={code}")
            return None

        min_df = min_df[min_df["时间"] >= '09:30:00']
        price = min_df['成交价'].iloc[-1]
        zhang = int(10000 * (price - last_huan_shou_price) / last_huan_shou_price) / 100
        if zhang > 5:
            return None
        row_code['zhang'] = zhang
        min_median_q = min_df['手数'].median()
        min_over_median_q_df = min_df[min_df['手数'] >= min_median_q]
        min_buy_q_df = min_over_median_q_df[min_over_median_q_df['买卖盘性质'] == '买盘']
        min_sell_q_df = min_over_median_q_df[min_over_median_q_df['买卖盘性质'] == '卖盘']
        sell_score = self.conf.get_score(sum(min_sell_q_df['手数']), sum(min_buy_q_df['手数']))
        if sell_score < -20:
            return None
        row_code['sell_score'] = sell_score

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
        if last_1_hour_macd < last_2_hour_macd * 0.5:
            return None

        min_total_e = sum(min_df.apply(lambda x: x['成交价'] * x['手数'], axis=1))
        # 计算换手率
        huan_shou_lv = int(min_total_e * 100 * 10000 / flow_value) / 100
        if huan_shou_lv < 1.5:
            return None

        last_1_day_avg = (day_df['开盘'].iloc[-1] + day_df['收盘'].iloc[-1]) / 2
        last_2_day_avg = (day_df['开盘'].iloc[-2] + day_df['收盘'].iloc[-2]) / 2
        today_avg = (min_df['成交价'][0] + min_df['成交价'][-1]) / 2
        last_1_day_min = day_df['最低'].iloc[-1]
        today_min = min(min_df['成交价'])
        if today_min < last_1_day_min:
            return None

        today_total_q = sum(min_df['手数'])
        last_valid_q = min(last_total_q, last_2_total_q) * self.conf.get_trading_pecentage()

        score = self.conf.get_score(last_valid_q, today_total_q)
        if score < -30:
            return None

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

    def get_score(self, price_s, avg_s):
        return (10000 - int(10000 * abs(price_s - avg_s) / avg_s)) / 100

    def get_zong_gu_ben(self, stock_code):
        if self.stock_zh_a_gdhs_df is None:
            # 获取股东数、总股本等基础信息
            self.stock_zh_a_gdhs_df = ak.stock_zh_a_gdhs(symbol="最新")
        gdhs_df = self.stock_zh_a_gdhs_df
        stock_zong_gu_ben = gdhs_df[gdhs_df['代码'] == stock_code]['总股本']
        if stock_zong_gu_ben is None:
            return 1
        return stock_zong_gu_ben.iloc[0]

    def avg_diff(self, a):
        a_1 = a.iloc[0]
        a_2 = a.iloc[1]
        # print(f"a={a_1}, type={a_2}")
        if a_1 == a_2:
            return 0
        elif a_1 < a_2:
            return 1
        else:
            return -1

    def avg(self, a, b):
        if a is None or b is None:
            return None
        # print(f"a={a}")
        # print(f"a_1={type(a)}")
        # print(f"b={b}")
        # print(f"b2={b.iloc[a.index[0]]}")
        return (a.iloc[0] + b.iloc[a.index[0]]) / 2

    def time_fmt(self, day_delta):
        # 先获得时间数组格式的日期
        threeDayAgo = (datetime.datetime.now() - datetime.timedelta(days=day_delta))
        # 转换为时间戳:
        timeStamp = int(time.mktime(threeDayAgo.timetuple()))
        # 转换为其他字符串格式:
        strTime = threeDayAgo.strftime("%Y%m%d")
        return strTime

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
            s_num = 0
            if ':' not in self.args.concept_num:
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
            print(f"concept list len is: {len(stock_board_concept_name_em_df['板块名称'])}")
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
            if code in self.all_codes_set:
                continue
            n += 1
            if code in self.black_list:
                continue
            name = stock_zh_a_spot_em_df['名称'][i]
            price = stock_zh_a_spot_em_df['最新价'][i]
            if price < 4:
                continue
            if 'ST' in name or '退市' in name or 'N' in name or 'L' in name or 'C' in name or 'U' in name:
                continue
            chengjiao_val = stock_zh_a_spot_em_df['成交额'][i]
            huanshou_val = stock_zh_a_spot_em_df['换手率'][i]
            flow_val = chengjiao_val * 100 / huanshou_val
            if flow_val < 10 * 100000000 or flow_val > 200 * 100000000:
                continue
            # liang_val = stock_zh_a_spot_em_df['量比'][i]
            # if liang_val <= 1:
            #     continue

            if code.startswith("688") or code.startswith("8"):
                continue

            # 涨跌幅 小于 5%
            # zhang = stock_zh_a_spot_em_df['涨跌幅'][i]
            # if zhang >= 6:
            #    continue

            v_n += 1

            shi_val = stock_zh_a_spot_em_df['市盈率-动态'][i]
            # total_val = stock_zh_a_spot_em_df['总市值'][i]
            total_val = stock_zh_a_spot_em_df['成交量'][i]
            row = dict()
            row['code'] = code
            row['name'] = name
            # row['shi_val'] = shi_val
            # row['total_val'] = total_val
            # row['flow_val'] = flow_val
            # row['zhang'] = zhang
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
    rs = stock.run()
    # print(f"rs type = {type(rs)}")
    rs.sort(reverse=True, key=lambda r: r['score'])
    code_set = set()
    print("\n\n---------- Final result ------------\n")
    for idx, row in enumerate(rs):
        if not row['code'] in code_set:
            code_set.add(row['code'])
            print(row)

    print(f"\nTotal: {len(code_set)} stocks")
    end_ts = time.time()

    print("\nElapse: %.2f s,  %s" % ((end_ts - start_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    print("注意：交易日00:00 ~ 9:15之间的数据不准确，不要运行此脚本！")
