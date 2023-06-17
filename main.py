from threading import Lock, Thread, current_thread

import akshare as ak
import time
import datetime


class StockA:
    black_list = ['600865']
    rs = list()
    lock = Lock()

    def filter_by_week(self, code, week_delta):
        day_delta = week_delta * 10
        end = self.time_fmt(0)
        start = self.time_fmt(day_delta)
        week_df = ak.stock_zh_a_hist(symbol=code, period="weekly", start_date=start, end_date=end, adjust="")
        if week_df.empty:
            return False
        num_of_rows = week_df.iloc[:, 0].size
        rev_week_df = week_df.reindex(index=week_df.index[::-1])
        lowest = 10000
        counter = 0
        for i in rev_week_df.index:
            if i == num_of_rows:
                continue
            close_price = rev_week_df['收盘'][i]
            lowest = min(lowest, close_price)
            counter += 1
            if counter >= week_delta:
                break
        close_price = rev_week_df['收盘'][0]

        if close_price <= lowest:
            return False
        return True

    def filter_by_day(self, code, day_delta):
        end = self.time_fmt(0)
        start = self.time_fmt(day_delta + 10)
        day_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
        if day_df.empty:
            return False
        num_of_rows = day_df.iloc[:, 0].size
        if num_of_rows < day_delta:
            return False
        rev_day_df = day_df.reindex(index=day_df.index[::-1])
        # print(rev_day_df)
        lowest = 10000
        last_i = day_delta - 1
        counter = 0
        for i in rev_day_df.index:
            if counter == 0:
                close_price = rev_day_df['收盘'][i]
                low_price = rev_day_df['最低'][i]
                counter += 1
                continue
            if counter == 1:
                close_price_1 = rev_day_df['收盘'][i]
                max_price_1 = rev_day_df['最高'][i]
            low = rev_day_df['最低'][i]
            lowest = min(lowest, low)
            counter += 1
            if counter >= day_delta:
                break
        # if low_price < lowest :
        if close_price < lowest:
            return False
        # if close_price < close_price_1:
        if close_price < max_price_1:
            # print(f"code={code}, size={num_of_rows}, last_i={last_i}, close={close_price}, close_1={close_price_1}")
            # print(rev_day_df)
            return True
        return False

    def rm_by_max(self, rev_min_df):
        # if max green > max_read*0.9
        max_up = 0
        max_down = 0
        cnt = 0
        for i in rev_min_df.index:
            cnt += 1
            if cnt > 300:
                break
            q = rev_min_df['成交量'][i]
            open_price = rev_min_df['开盘'][i]
            close_price = rev_min_df['收盘'][i]
            if open_price > close_price:
                max_down = max(max_down, q)
            elif open_price < close_price:
                max_up = max(max_up, q)
        if max_down > 0.8 * max_up:
            return False

        return True

    def filter_by_min(self, code):
        # 注意：该接口返回的数据只有最近一个交易日的有开盘价，其他日期开盘价为 0
        min_df = ak.stock_zh_a_hist_min_em(symbol=code, start_date="2021-09-01 09:32:00",
                                           end_date="2025-09-06 09:32:00", period='1', adjust='')
        rev_min_df = min_df.reindex(index=min_df.index[::-1])
        if not self.rm_by_max(rev_min_df):
            return False
        # print(rev_min_df)
        nums = 0
        avg = 0
        # q should be max(200, xxx) * 10
        max_q = 0
        cnt_for_max_q = 0
        counter = 0
        for i in rev_min_df.index:
            counter += 1
            if counter > 300:
                return False
            q = rev_min_df['成交量'][i]
            open_price = rev_min_df['开盘'][i]
            close_price = rev_min_df['收盘'][i]
            last_close_price = close_price
            if i - 1 >= 0:
                last_close_price = rev_min_df['收盘'][i - 1]
                # if avg > 0 and q > 10 * avg:
            if max_q > 0 and q > 10 * max(max_q, 200):
                if close_price > open_price:
                    print(
                        f"code={code}, counter={counter}, nums={nums}, avg={avg}, q={q}, max_q={max_q}, cnt_for_max_q={cnt_for_max_q}")
                    # print(rev_min_df)
                    return True
                else:
                    return False
            if close_price < open_price or (close_price == open_price and close_price < last_close_price):
                nums += 1
                avg = ((nums - 1) * avg + q) / nums
                if max_q != q:
                    cnt_for_max_q = counter
                max_q = max(max_q, q)
                # print(f"nums={nums}, avg={avg}, q={q}, open={open_price}, close={close_price}")
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
        thread_rs = list()
        thx_name = current_thread().getName()
        code_len = len(codes)
        print(f"[{thx_name}] total len: {code_len}")
        n = 0
        for row in codes:
            code = row['code']
            n += 1
            if n % 100 == 0:
                print(f"[{thx_name}] finished {n}/{code_len}")
            # print(code)
            if self.filter_by_day(code, 5) and self.filter_by_min(code):
                thread_rs.append(row)
                print(f'{row}')
                print('-------------------\n')
        print(f"[{thx_name}] finished all: {code_len}")
        if len(thread_rs) > 0:
            self.append_all(thread_rs)

    def run(self):
        stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        stock_df_len = len(stock_zh_a_spot_em_df)
        print(f"Total stocks: {stock_df_len}")
        # not_st_df = stock_zh_a_spot_em_df.loc['ST' not in stock_zh_a_spot_em_df['名称'] and '退市' not in stock_zh_a_spot_em_df['名称'] and 'N' not in stock_zh_a_spot_em_df['名称'], ['名称']]
        thread_data_dict = dict()
        thread_dict = dict()
        for i in range(1, 50):
            thread_data_dict[i] = list()
        batch_num = 1
        n = 0
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
            liang_val = stock_zh_a_spot_em_df['量比'][i]
            if liang_val <= 1:
                continue

            if code.startswith("688"):
                continue
            shi_val = stock_zh_a_spot_em_df['市盈率-动态'][i]
            total_val = stock_zh_a_spot_em_df['总市值'][i]
            row = dict()
            row['code'] = code
            row['name'] = name
            row['shi_val'] = shi_val
            row['total_val'] = total_val
            row['flow_val'] = flow_val
            thread_data_dict[batch_num].append(row)
            rape_list = list()
            rape_list.append(thread_data_dict[batch_num])
            if len(thread_data_dict[batch_num]) >= 200:
                thread_dict[batch_num] = Thread(target=self.run_thread_check, args=rape_list, name=batch_num,
                                                daemon=True)
                thread_dict[batch_num].start()
                print(f"Valid stock code: {batch_num*200}/{n}")
                batch_num += 1

        if len(thread_data_dict[batch_num]) > 0:
            thread_dict[batch_num] = Thread(target=self.run_thread_check, args=rape_list, name=batch_num, daemon=True)
            thread_dict[batch_num].start()

        for k in thread_dict:
            thread_dict[k].join(timeout=3600000)
            print(f"{k} finished! ")
        return self.rs


if __name__ == "__main__":
    stock = StockA()
    rs = stock.run()
    rs.sort(key=lambda r: r['code'])
    for idx, row in enumerate(rs):
        print(
            f"{str(idx)}, code={row['code']}, name={row['name']}, 市盈率-动态={row['shi_val']}, 总市值={row['total_val']}, 流通市值={row['flow_val']}")
