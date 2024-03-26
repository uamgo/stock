from threading import Lock, Thread, current_thread

import akshare as ak
import time
import datetime
import sys
import pandas as pd


class StockA:
    black_list = ['600865']
    policies = [900, 800, 700]
    rs = list()
    lock = Lock()
    stock_zh_a_gdhs_df = None

    # 返回：list 包含 股票代码、策略类型、权重
    # 策略类型：900 策略一，800 策略二，700 策略三
    # 权重：100 - 100 * abs（当前价格 - 均值）/ 均值
    def filter_by_min(self, code):
        debug_code = '0'
        if debug_code !='0' and code != debug_code:
            return None
        # 返回： 股票代码
        row_code = [code, 0, 0]
        # 获取前一日价格
        end = self.time_fmt(1)
        start = self.time_fmt(40)
        day_df = None
        stock_zh_a_gdhs_detail_em_df = None
        try:
            day_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
        except:
            e = sys.exc_info()[0]
            # print(f"code={code}, {e}")
            return None 
        if day_df.size == 0:
            # print(f"No daily data with code={code}")
            return None
        last_1 = day_df['收盘'].size - 1
        last_day_shou = day_df['收盘'][last_1]
        last_day_kai = day_df['开盘'][last_1]
        last_day_q = day_df['成交量'][last_1]
        last_huan_shou_lv = day_df['换手率'][last_1]
        last_day_price_avg = (last_day_kai + last_day_shou) /2

        last_2 = last_1 - 1
        last_day2_shou = day_df['收盘'][last_2]
        last_day2_kai = day_df['开盘'][last_2]
        last_day2_price_avg = (last_day2_kai + last_day2_shou) /2

        last_2day_price_avg_max = max(last_day_price_avg, last_day2_price_avg)

        # 获取股东数
        # zong_gu_ben = stock_zh_a_gdhs_detail_em_df['总股本']

        # 20 日均线
        day_df['avg20'] = day_df['收盘'].rolling(20).mean()
        if day_df['avg20'][last_1] is None or last_day_shou < day_df['avg20'][last_1]:
            return None
        day_df['avg'] = day_df['开盘'].rolling(window=1).apply(self.avg, args=(day_df['收盘'],))
        day_df['trend_2'] = day_df['avg'].rolling(2).apply(lambda a: self.avg_diff(a))
        if day_df['trend_2'][last_1] is None:
            print(f"last one in trend_2 is None!")
            return None
        day_df['trend_3'] = day_df['trend_2'].rolling(2).sum()
        if day_df['trend_3'][last_1] is None:
            print(f"last one in trend_3 is None!")
            return None
        day_df['box_up'] = day_df['最高'].rolling(3).max()
        if day_df['box_up'][last_1] is None:
            print(f"last one in box_up is None!")
            return None
        if code == debug_code:
            print("----avg----")
            print(day_df['avg'])
            print("----trend_2----")
            print(day_df['trend_2'])
            print("----trend_3----")
            print(day_df['trend_3'])


        # 注意：该接口返回的数据只有最近一个交易日的有开盘价，其他日期开盘价为 0
        min_df = None
        try:
            min_df = ak.stock_intraday_em(symbol=code)
        except:
            e = sys.exc_info()[0]
            # print(f"code={code}, {e}")
            return None
        if min_df.size == 0:
            # print(f"no data for ak.stock_intraday_em with code={code}")
            return None

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
        first_price = 0

        while i < size - 1:
            i += 1
            time_m = min_df["时间"][i]
            if not is_valid and time_m.startswith('09:30'):
                first_price = min_df['成交价'][i]
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
        today_price_avg = (first_price + price) / 2
        # total_q = total_q * 100
        # zong_gu_ben = self.get_zong_gu_ben(code)
        # huan_shou_lv = int(total_q * 100 * 100 * 100 / zong_gu_ben) / 100
        # 用昨天换手率判断
        huan_shou_lv = last_huan_shou_lv

        # 下跌不放量
        accept_q = (price > first_price and total_q < last_day_q * 1.5) or (price <= first_price and total_q < last_day_q)
        
        if code == debug_code:
            print(f"code={code}, total_q={total_q}, last_day_q={last_day_q}, price={price}, last_day_shou={last_day_shou}, first_price={first_price}, today_price_avg={today_price_avg}")
            print(f"code={code}, last_2day_price_avg_max={last_2day_price_avg_max}, last_day_price_avg={last_day_price_avg}, last_day2_price_avg={last_day2_price_avg}")
            print(f"code={code}, today_price_avg > last_2day_price_avg_max ={today_price_avg > last_2day_price_avg_max}")
            # print(f"code={code}, huan_shou_lv={huan_shou_lv}, zong_gu_ben={zong_gu_ben}")
            print(f"code={code}, huan_shou_lv={huan_shou_lv}, accept_q={accept_q}, price <= last_day_price_avg and total_q < last_day_q ={price <= last_day_price_avg and total_q < last_day_q}")
        
        # 排除换手率小于1的股票
        if huan_shou_lv < 1 or huan_shou_lv > 15:
            return None

        filter_flag = False

        # policy 1: 一、连续三天上涨突破（收盘+开盘）/2；二、无放量出逃
        if day_df['trend_3'][last_1] >= 1:
            # 条件：当前成交量小于昨天的1.5倍 && 当前平均价大于昨日平均价 && 当日开盘价大于昨天平均价
            if accept_q and price > last_day_price_avg and today_price_avg > last_day_price_avg and first_price > last_day_price_avg:
                filter_flag = True
                row_code[1] = self.policies[0]

        # policy 2: 一、箱体突破（最高价高于箱体）；二、无明显放量出
        elif max_price > day_df['box_up'][last_1]:
            # 条件：(买入量大于卖出量 || 当前总成交量小于昨日成交量的1.5倍) && 当前价格大于昨日收盘价 && 今天平均价大于前两天平均价
            if (buy_q > sell_q or accept_q) and today_price_avg > last_2day_price_avg_max:
                filter_flag = True
                row_code[1] = self.policies[1]

        # policy 3: 一、连续三天创新低；二、放量资金抄底
        elif day_df['trend_3'][last_1] <= -1:
            # 最大买单小于最大买单的50%；当前价格高于移动平均价；买单数量大约
            filter_flag = (max_s_q < max_b_q * 0.5 and price > avg and buy_q > sell_q and cnt_hight > cnt * 0.6)
            if filter_flag:
                row_code[1] = self.policies[2]

        x = 0
        if row_code[1] == 800 or row_code[1] == 900:
            x = 900

        row_code[2] = x + (10000 - int(10000 * abs(price - avg) / avg)) / 100
        if filter_flag:
            print(
                f"{code} , max_s_q={max_s_q}, max_b_q={max_b_q}, cnt_hight={cnt_hight}, cnt={cnt}, total_q={total_q}, last_day_q={last_day_q}, price={price}, avg={avg}, last_day_shou={last_day_shou}")
            return row_code

        return None

    def get_zong_gu_ben(self, stock_code):
        if self.stock_zh_a_gdhs_df is None:
            # 获取股东数、总股本等基础信息
            self.stock_zh_a_gdhs_df = ak.stock_zh_a_gdhs(symbol="最新")
        gdhs_df = self.stock_zh_a_gdhs_df
        stock_zong_gu_ben =  gdhs_df[gdhs_df['代码'] == stock_code]['总股本']
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
        return (a.iloc[0] + b.iloc[a.index[0]])/2

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
            row_code = self.filter_by_min(code)
            if row_code is not None:
                row['policy_type'] = row_code[1]
                row['score'] = row_code[2]
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

    def print_pocicy(self, p_list, policy_type):
        print(f"\n~~~policy_type={policy_type} with {len(p_list)} stocks~~~")
        if len(p_list) == 0:
            print(f"No data for policy_type={policy_type}")
            return False
        for idx, row in enumerate(p_list):
            code = row['code']
            print(
                f"""{str(idx+1)}, code={code}, name={row['name']}, 市盈率-动态={row['shi_val']}, score={row['score']}, 涨跌幅={row['zhang']}""")
            print(stock.to_link(code))
            if idx >= 4:
                print(f"\nTop 5 from {len(p_list)} stocks")
                break
        print("End~~~~~~~~~~~")
        return True


if __name__ == "__main__":
    start_ts = time.time()
    stock = StockA()
    rs = stock.run()
    # print(f"rs type = {type(rs)}") 
    rs.sort(reverse=True, key=lambda r: r['score'])
    for idx, row in enumerate(rs):
        print(row)
    print(f"\nTotal: {len(rs)} stocks")
    p_1_list = []
    p_2_list = []
    p_3_list = []
    for idx, row in enumerate(rs):
        if row['policy_type'] == stock.policies[0]:
            p_1_list.append(row)
        elif row['policy_type'] == stock.policies[1]:
            p_2_list.append(row)
        else:
            p_3_list.append(row)

    end_ts = time.time()

    print("\n~~~~~~~~~~~\n")
    stock.print_pocicy(p_1_list, "策略一：连续上涨")
    stock.print_pocicy(p_2_list, "策略二：箱体突破")
    stock.print_pocicy(p_3_list, "策略三：连续下跌")

    print("\nElapse: %.2f s,  %s" % ((end_ts - start_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
