from threading import Lock, Thread, current_thread

import akshare as ak
import time
import datetime


class StockA:
    black_list = ['600865']
    rs = list()
    lock = Lock()

    def filter_by_min(self, code):
        # 获取前一日价格
        end = self.time_fmt(0)
        start = self.time_fmt(20)
        day_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
        last_1 = day_df['收盘'].size - 1
        last_day_shou = day_df['收盘'][last_1]
        last_day_q = day_df['成交量'][last_1]

        # 注意：该接口返回的数据只有最近一个交易日的有开盘价，其他日期开盘价为 0
        min_df = ak.stock_intraday_em(symbol=code)
        max_q = 0
        max_m_q = 0
        size = min_df['开盘'].size
        i = max(0, size - 300)
        last_close_price = 0
        cnt = 0
        sum_close = 0
        cnt_hight = 0
        total_q = 0
        now_t = min_df["时间"][size - 1][:10]

        while i < size - 1:
            i += 1
            if not min_df["时间"][i].startswith(now_t):
                continue
            # print(f"i={i}, df size={size}")
            open_price = min_df['开盘'][i]
            if open_price == 0:
                continue
            q = min_df['成交量'][i]

            close_price = min_df['收盘'][i]
            if last_close_price == 0:
                last_close_price = close_price
            if close_price < open_price or (close_price == open_price and close_price < last_close_price):
                max_m_q = max(max_m_q, q)
            elif close_price > open_price:
                max_q = max(max_q, q)

            total_q += q
            last_close_price = min_df['收盘'][i - 1]
            cnt += 1
            sum_close += last_close_price
            if last_close_price > (sum_close/cnt):
                cnt_hight += 1

        avg = sum_close/cnt
        if max_m_q < max_q * 0.5 and close_price > avg and cnt_hight > (cnt/2)\
                and total_q > last_day_q and total_q < last_day_q * 2\
                and last_close_price > last_day_shou:
            return True

        return False

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
        thx_name = current_thread().getName()
        code_len = len(codes)
        # print(f"[{thx_name}] total len: {code_len}")
        n = 0
        flag = False
        for row in codes:
            code = row['code']
            n += 1
            if n % 200 == 0:
                now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"[{thx_name}] finished {n}/{code_len} with time: {now}")
            if self.filter_by_min(code):
                thread_rs.append(row)
                flag = True
                print(f'[{thx_name}] {row}')
                print('-------------------\n')
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
        stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        # not_st_df = stock_zh_a_spot_em_df.loc['ST' not in stock_zh_a_spot_em_df['名称']
        # and '退市' not in stock_zh_a_spot_em_df['名称'] and 'N' not in stock_zh_a_spot_em_df['名称'], ['名称']]
        thread_data_dict = dict()
        thread_dict = dict()
        for i in range(1, 50):
            thread_data_dict[i] = list()
        batch_num = 1
        batch_size = 100
        n = 0
        v_n = 0
        for i in stock_zh_a_spot_em_df.index:
            code = stock_zh_a_spot_em_df['代码'][i]
            n += 1
            if code in self.black_list:
                continue
            name = stock_zh_a_spot_em_df['名称'][i]
            price = stock_zh_a_spot_em_df['最新价'][i]
            if price < 4:
                continue
            if 'ST' in name or '退市' in name or 'N' in name or 'L' in name or 'C' in name or 'U' in name:
                continue
            flow_val = stock_zh_a_spot_em_df['流通市值'][i]
            if flow_val < 1000000000 or flow_val > 100000000000:
                continue
            # liang_val = stock_zh_a_spot_em_df['量比'][i]
            # if liang_val <= 1:
            #     continue

            if code.startswith("688") or code.startswith("8"):
                continue

            zhang = stock_zh_a_spot_em_df['涨跌幅'][i]
            if zhang >= 0:
                continue

            v_n += 1

            shi_val = stock_zh_a_spot_em_df['市盈率-动态'][i]
            total_val = stock_zh_a_spot_em_df['总市值'][i]
            row = dict()
            row['code'] = code
            row['name'] = name
            row['shi_val'] = shi_val
            row['total_val'] = total_val
            row['flow_val'] = flow_val
            row['zhang'] = zhang
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
    rs.sort(key=lambda r: r['code'])
    end_ts = time.time()

    print("\n~~~~~~~~~~~\n")
    for idx, row in enumerate(rs):
        code = row['code']
        print(
            f"""{str(idx+1)}, code={code}, name={row['name']}, 市盈率-动态={row['shi_val']}, 总市值={row['total_val']}, 流通市值={row['flow_val']}, 涨跌幅={row['zhang']}""")
        print(stock.to_link(code))
    print("\nElapse: %.2f s,  %s" % ((end_ts - start_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
