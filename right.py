from threading import Lock, Thread, current_thread

import akshare as ak
import time
import datetime
import sys
import pandas as pd


class StockA:
    black_list = ['600865']
    rs = list()
    lock = Lock()

    def filter_by_min(self, code):
        filtered_code = '300321'
        # 获取前一日价格
        end = self.time_fmt(1)
        start = self.time_fmt(40)
        day_df = None
        try:
            day_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
        except:
            e = sys.exc_info()[0]
            # print(f"code={code}, {e}")
            return False
        if day_df.size == 0:
            # print(f"No daily data with code={code}")
            return False
        last_1 = day_df['收盘'].size - 1
        last_day_shou = day_df['收盘'][last_1]
        last_day_q = day_df['成交量'][last_1]

        # 20 日均线
        day_df['avg20'] = day_df['收盘'].rolling(20).mean()
        if day_df['avg20'][last_1] is None or last_day_shou < day_df['avg20'][last_1]:
            return False
        day_df['avg'] = day_df.apply(lambda r: self.avg(r['开盘'], r['收盘']), axis=1)
        day_df['trend_2'] = day_df['avg'].rolling(2).apply(lambda a, b: self.avg_diff(a, b), axis=1)
        if day_df['trend_2'][last_1] is None:
            print(f"last one in trend_2 is None!")
            return False
        day_df['trend_3'] = day_df['trend_2'].rolling(2).sum()
        if day_df['trend_3'][last_1] is None:
            print(f"last one in trend_3 is None!")
            return False
        day_df['box_up'] = day_df['最高'].rolling(3).max()
        if day_df['box_up'][last_1] is None:
            print(f"last one in box_up is None!")
            return False

        # 注意：该接口返回的数据只有最近一个交易日的有开盘价，其他日期开盘价为 0
        min_df = None
        try:
            min_df = ak.stock_intraday_em(symbol=code)
        except:
            e = sys.exc_info()[0]
            # print(f"code={code}, {e}")
            return False
        if min_df.size == 0:
            # print(f"no data for ak.stock_intraday_em with code={code}")
            return False

        last_min_i = min_df['成交价'].size - 1

        max_b_q = 0
        max_s_q = 0
        size = min_df['成交价'].size
        i = 0
        last_close_price = 0
        cnt = 0
        sum_close = 0
        cnt_hight = 0
        total_q = 0
        buy_q = 0
        sell_q = 0
        is_valid = False
        max_price = 0

        while i < size - 1:
            i += 1
            time_m = min_df["时间"][i]
            if not is_valid and time_m.startswith('09:30'):
                is_valid = True
            if not is_valid:
                continue
            price = min_df['成交价'][i]
            if price == 0:
                continue
            max_price = max(max_price, price)
            q = min_df['手数'][i]
            # if code == '002360':
            #     print(f"price: {price} hour: {min_df['时间'][i]} q: {q}")
            if int(q) == 0:
                continue
            direct = min_df['买卖盘性质'][i]
            is_buy = (direct == '买盘')
            is_sell = (direct == '卖盘')

            if is_buy:
                buy_q += q 
                max_b_q = max(max_b_q, q)
            elif is_sell:
                sell_q += q 
                max_s_q = max(max_s_q, q)

            total_q += int(q)
            cnt += 1
            sum_close += int(price * q * 100)/100
            try:
                # print(f"sum_close/total_q={sum_close}/{total_q}")
                if price > (int(sum_close * 100) / int(total_q))/100:
                    cnt_hight += 1
            except:
                print(f"sum_close/total_q={sum_close}/{total_q}")

        avg = sum_close/total_q
        total_q = total_q * 100

        filter_flag = False
        # policy 1: 一、连续三天上涨突破（收盘+开盘）/2；二、无放量出逃
        if day_df['trend_3'][last_1] >= 1:
            total_q < last_day_q * 1.5
            filter_flag = True
        # policy 2: 一、箱体突破（最高价高于箱体）；二、无明显放量出逃
        if max_price > day_df['box_up'][last_1]:
            if buy_q > sell_q:
                filter_flag = True
            elif total_q < last_day_q * 1.5:
                filter_flag = True

        # policy 3: 一、连续三天创新低；二、放量资金抄底
        if day_df['trend_3'][last_1] <= -1:
            # 最大买单小于最大买单的50%；当前价格高于移动平均价；买单数量大约
            filter_flag = (max_s_q < max_b_q * 0.5 and price > avg and buy_q > sell_q and cnt_hight > cnt * 0.6)

        if filter_flag:
            print(
                f"{code} , max_s_q={max_s_q}, max_b_q={max_b_q}, cnt_hight={cnt_hight}, cnt={cnt}, total_q={total_q}, last_day_q={last_day_q}, price={price}, avg={avg}, last_day_shou={last_day_shou}")
            return True

        return False

    def avg_diff(self, a, b):
        if a == b:
            return 0
        elif a > b:
            return 1
        else:
            return -1

    def avg(self, a, b):
        if a is None or b is None:
            return None
        return (a+b)/2

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
        # 获取所有概念板块，判断板块涨幅排名前20
        stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
        stock_top = stock_board_concept_name_em_df.nlargest(10,'涨跌幅',keep='first')
        stock_bottom = stock_board_concept_name_em_df.nsmallest(10,'涨跌幅',keep='first')
        stock_board_concept_name_em_df = pd.concat([stock_top, stock_bottom],ignore_index=True)
        # stock_board_concept_name_em_df = stock_board_concept_name_em_df.nsmallest(10,'涨跌幅',keep='last')
        print(stock_board_concept_name_em_df)
        print(f"concept list len is: {len(stock_board_concept_name_em_df['板块名称'])}")
        stock_df = None
        for ind in stock_board_concept_name_em_df.index:
            concept_name = stock_board_concept_name_em_df["板块名称"][ind]
            # 找到所有符合条件的概念股并去重
            concept_tmp_df = ak.stock_board_concept_cons_em(symbol = concept_name)
            concept_tmp_len = len(concept_tmp_df["代码"])
            if concept_tmp_len > 1000:
                print(f"Ignore concept: {concept_name} with size: {concept_tmp_len}")
                continue
            if stock_df is None:
                stock_df = concept_tmp_df
            else:
                print(f"Covered  {concept_name}: {len(stock_df['代码'])} with concept_tmp_df: {len(concept_tmp_df['代码'])}")
                stock_df = pd.concat([stock_df, concept_tmp_df],ignore_index=True)

        # stock_df = stock_df.drop_duplicates(subset=[''])
        # stock_df = stock_df.drop_duplicates(subset=['代码', '名称', '涨跌幅', '市盈率-动态', '成交量', '成交额'], keep='first')
        stock_df = stock_df.drop_duplicates(subset=['代码'], keep='first')
        print(f"Covered stocks: {len(stock_df['代码'])}")
        s_ts = time.time()
        # stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        stock_zh_a_spot_em_df = stock_df 
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
            # print("----------code--------")
            # print(code)
            n += 1
            if code in self.black_list:
                continue
            name = stock_zh_a_spot_em_df['名称'][i]
            price = stock_zh_a_spot_em_df['最新价'][i]
            if price < 4:
                continue
            if 'ST' in name or '退市' in name or 'N' in name or 'L' in name or 'C' in name or 'U' in name:
                continue
            flow_val = stock_zh_a_spot_em_df['成交额'][i]
            # flow_val = stock_zh_a_spot_em_df['流通市值'][i]
            # if flow_val < 10 * 100000000 or flow_val > 300 * 100000000:
            #    continue
            # liang_val = stock_zh_a_spot_em_df['量比'][i]
            # if liang_val <= 1:
            #     continue

            if code.startswith("688") or code.startswith("8"):
                continue

            # 涨跌幅 小于 5%
            zhang = stock_zh_a_spot_em_df['涨跌幅'][i]
            if zhang >= 5:
                continue

            v_n += 1

            shi_val = stock_zh_a_spot_em_df['市盈率-动态'][i]
            #total_val = stock_zh_a_spot_em_df['总市值'][i]
            total_val = stock_zh_a_spot_em_df['成交量'][i]
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
        code = row['code']#
        print(
            f"""{str(idx+1)}, code={code}, name={row['name']}, 市盈率-动态={row['shi_val']}, 成交量={row['total_val']}, 成交额={row['flow_val']}, 涨跌幅={row['zhang']}""")
        print(stock.to_link(code))
    print("\nElapse: %.2f s,  %s" % ((end_ts - start_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
