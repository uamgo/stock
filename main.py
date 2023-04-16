import akshare as ak
import time
import datetime


def filter_by_week(code, week_delta):
    day_delta = week_delta * 10
    end =  time_fmt(0)
    start =  time_fmt(day_delta)
    week_df = ak.stock_zh_a_hist(symbol=code, period="weekly", start_date=start, end_date=end, adjust="")
    if week_df.empty:
        return False
    num_of_rows = week_df.iloc[:,0].size
    rev_week_df = week_df.reindex(index=week_df.index[::-1])
    lowest = 10000
    counter = 0
    for i in rev_week_df.index:
        if i == num_of_rows:
           continue
        close_price  = rev_week_df['收盘'][i]
        lowest = min(lowest, close_price)
        counter += 1
        if counter >= week_delta:
            break
    close_price = rev_week_df['收盘'][0]

    if close_price <= lowest:
        return False
    return True


    

def filter_by_day(code, day_delta):
    end =  time_fmt(0)
    start =  time_fmt(day_delta + 10)
    day_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
    if day_df.empty:
        return False
    num_of_rows = day_df.iloc[:,0].size
    if num_of_rows < day_delta:
        return False
    rev_day_df = day_df.reindex(index=day_df.index[::-1])
    #print(rev_day_df)
    lowest = 10000
    last_i = day_delta - 1
    counter = 0
    for i in rev_day_df.index:
        if counter == 0:
            close_price  = rev_day_df['收盘'][i] 
            counter += 1
            continue
        if counter == 1:
            close_price_1  = rev_day_df['收盘'][i]
            max_price_1  = rev_day_df['最高'][i]
        low = rev_day_df['最低'][i]
        lowest = min(lowest, low)
        counter += 1
        if counter >= day_delta:
            break
    if close_price < lowest :
        return False
    #if close_price < close_price_1:
    if close_price < max_price_1:
        #print(f"code={code}, size={num_of_rows}, last_i={last_i}, close={close_price}, close_1={close_price_1}")
        #print(rev_day_df)
        return True
    return False


def filter_by_min(code):
    # 注意：该接口返回的数据只有最近一个交易日的有开盘价，其他日期开盘价为 0
    min_df = ak.stock_zh_a_hist_min_em(symbol=code, start_date="2021-09-01 09:32:00", end_date="2025-09-06 09:32:00", period='1', adjust='')
    rev_min_df = min_df.reindex(index=min_df.index[::-1])
    #print(rev_min_df)
    nums = 0
    avg = 0
    #q should be max(200, xxx) * 10
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
       if i-1 >= 0:
            last_close_price = rev_min_df['收盘'][i-1] 
       #if avg > 0 and q > 10 * avg:
       if max_q > 0 and q > 10 * max(max_q, 200):
            if close_price > open_price:
                print(f"code={code}, counter={counter}, nums={nums}, avg={avg}, q={q}, max_q={max_q}, cnt_for_max_q={cnt_for_max_q}")
                #print(rev_min_df)
                return True
            else:
                return False
       if close_price < open_price or (close_price == open_price and close_price < last_close_price):  
            nums += 1
            avg = ((nums - 1) * avg + q)/nums
            if max_q != q:
                cnt_for_max_q = counter
            max_q= max(max_q, q)
            #print(f"nums={nums}, avg={avg}, q={q}, open={open_price}, close={close_price}")
    return False


def time_fmt(day_delta):
    #先获得时间数组格式的日期
    threeDayAgo = (datetime.datetime.now() - datetime.timedelta(days = day_delta))
    #转换为时间戳:
    timeStamp = int(time.mktime(threeDayAgo.timetuple()))
    #转换为其他字符串格式:
    strTime = threeDayAgo.strftime("%Y%m%d")
    return strTime


if __name__ == "__main__":
    stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
    #not_st_df = stock_zh_a_spot_em_df.loc['ST' not in stock_zh_a_spot_em_df['名称'] and '退市' not in stock_zh_a_spot_em_df['名称'] and 'N' not in stock_zh_a_spot_em_df['名称'], ['名称']]
    n = 0
    for i in stock_zh_a_spot_em_df.index:
        if i%500 ==0:
            print(f"i={i}")
        name = stock_zh_a_spot_em_df['名称'][i]
        if 'ST' in name or '退市' in name or 'N' in name or 'L' in name or 'C' in name or 'U' in name:
            continue
        flow_val = stock_zh_a_spot_em_df['流通市值'][i]
        if flow_val < 1000000000:
            continue
        liang_val = stock_zh_a_spot_em_df['量比'][i]
        if liang_val <= 1 :
            continue
        code = stock_zh_a_spot_em_df['代码'][i]
        if code.startswith("688") :
            continue
        if filter_by_day(code, 5) and filter_by_min(code):
            n += 1
            shi_val = stock_zh_a_spot_em_df['市盈率-动态'][i]
            total_val = stock_zh_a_spot_em_df['总市值'][i]
            print(f'{str(n)}, code={code}, name={name}, 市盈率-动态={shi_val}, 总市值={total_val}, 流通市值={flow_val}')
            print('-------------------\n')
            if n>=100:
                break
