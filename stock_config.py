import os.path
import json
import exchange_calendars as xcals
import datetime
import pandas as pd


class StockConfig:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    root_path = "/tmp/stock"
    xshg = xcals.get_calendar("XSHG")
    last_trade_day_ts = xshg.schedule.loc[xshg.schedule['open'] < today_str]['open'][-1]
    last_trade_day_str = last_trade_day_ts.strftime("%Y-%m-%d")
    is_trading_today = xshg.is_session(datetime.datetime.now().strftime("%Y-%m-%d"))
    tmp_latest_trade_day = last_trade_day_str
    if is_trading_today:
        tmp_latest_trade_day = today_str
    base_path = f"{root_path}/{tmp_latest_trade_day}"

    concept_path = f"{base_path}/concept"
    daily_path = f"{base_path}/daily"
    minute_path = f"{base_path}/minute"
    config_file = f"{minute_path}/config.json"
    values = None

    def __init__(self):
        self.init_path()
        self.init_config()

    # trading and file not exists, then return True
    def is_minute_data_expired(self, code):
        file_name = f"{self.minute_path}/{code}.json"
        # file need to be download if not exist, then marked trading
        if not os.path.isfile(file_name):
            return True
        # file exists and not a trading day, no need to download again
        if not self.is_trading_today:
            return False

        c_time = os.path.getctime(file_name)
        now_time = datetime.datetime.now()
        # 交易日的9:30 - 11:30 and 13:00 - 15:00 期间都实时获取分时数据，其他时间不用重复获取
        now_9_30 = datetime.datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        now_11_30 = datetime.datetime.now().replace(hour=11, minute=30, second=0, microsecond=0)
        now_13_00 = datetime.datetime.now().replace(hour=13, minute=0, second=0, microsecond=0)
        now_15_00 = datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        # 当前时间在开盘前，或者分时文件创建在15点后则不需要重新生成文件
        if now_9_30 < now_time < now_11_30 or now_13_00 < now_time < now_15_00:
            return True

        if now_time < now_9_30 or c_time > now_15_00:
            return False
        if now_11_30 < now_time < now_13_00 and c_time > now_11_30:
            return False
        if now_time > now_15_00 and c_time > now_15_00:
            return False

        return True

    def is_tradingNow(self):
        now_9_30 = datetime.datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        now_11_30 = datetime.datetime.now().replace(hour=11, minute=30, second=0, microsecond=0)
        now_13_00 = datetime.datetime.now().replace(hour=13, minute=0, second=0, microsecond=0)
        now_15_00 = datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        now_time = datetime.datetime.now()
        return self.is_trading_today and now_9_30 <= now_time <= now_15_00

    def after_kai_pan(self):
        now_9_30 = datetime.datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        now_time = datetime.datetime.now()
        return now_time > now_9_30

    def to_datetime(self, m_time):
        if '-' in m_time:
            tmp_date = m_time[:10].split('-')
            t_year = int(tmp_date[0])
            t_mon = int(tmp_date[1])
            t_day = int(tmp_date[2])
            m_time_a = m_time[11:].split(':')
            t_hour = int(m_time_a[0])
            t_min = int(m_time_a[1])
            t_sec = int(m_time_a[2])
        else:
            t_now = datetime.datetime.now()
            t_year = t_now.year
            t_mon = t_now.month
            t_day = t_now.day
            m_time_a = m_time.split(':')
            t_hour = int(m_time_a[0])
            t_min = int(m_time_a[1])
            t_sec = int(m_time_a[2])
        return datetime.datetime.now().replace(
            year=t_year,month=t_mon,day=t_day,
            hour=t_hour, minute=t_min, second=t_sec, microsecond=0)

    def get_format_code(self, stock_code):
        return stock_code.zfill(6)

    def save_concept_data(self, concept_code, concept_df):
        print(f"{concept_code} save_concept_data")
        file_name = f"{self.concept_path}/{concept_code}.json"
        concept_df.to_json(file_name, orient='split', compression='infer', index='true')

    def get_concept_data(self, concept_code):
        file_name = f"{self.concept_path}/{concept_code}.json"
        return pd.read_json(file_name, orient='split', compression='infer')

    def exists_concept_data(self, concept_code):
        file_name = f"{self.concept_path}/{concept_code}.json"
        return os.path.exists(file_name)

    def save_daily_data(self, code, daily_df):
        print(f"{code} save_daily_data")
        file_name = f"{self.daily_path}/{code}.json"
        daily_df.to_json(file_name, orient='split', compression='infer', index='true')

    def get_daily_data(self, code):
        file_name = f"{self.daily_path}/{code}.json"
        return pd.read_json(file_name, orient='split', compression='infer')

    def exists_daily_data(self, code):
        file_name = f"{self.daily_path}/{code}.json"
        return os.path.exists(file_name)

    def save_minute_data(self, code, min_df):
        if not self.is_tradingNow():
            print(f"{code} save_minute_data")
            file_name = f"{self.minute_path}/{code}.json"
            min_df.to_json(file_name, orient='split', compression='infer', index='true')

    def get_minute_data(self, code):
        file_name = f"{self.minute_path}/{code}.json"
        return pd.read_json(file_name, orient='split', compression='infer')

    def exists_minute_data(self, code):
        return not self.is_minute_data_expired(code)

    def init_path(self):
        if not os.path.isdir(self.root_path):
            os.mkdir(self.root_path)
        if not os.path.isdir(self.base_path):
            os.mkdir(self.base_path)
        if not os.path.isdir(self.daily_path):
            os.mkdir(self.daily_path)
        if not os.path.isdir(self.minute_path):
            os.mkdir(self.minute_path)
        if not os.path.isdir(self.concept_path):
            os.mkdir(self.concept_path)

    def init_config(self):
        if not os.path.exists(self.config_file):
            last_trade_day_ts = self.xshg.schedule.loc[self.xshg.schedule['open'] < self.today_str]['open'][-1]
            last_trade_day_str = last_trade_day_ts.strftime("%Y-%m-%d")
            conf_str = f'''{{
    "code":"0", 
    "concept_num":"10",
    "is_debug":"False",
    "is_rm_last_day":"False", 
    "min_score":"30", 
    "debug_end_time":"14:30", 
    "last_trade_day_str":"{last_trade_day_str}"
}}
            '''
            self.values = json.loads(conf_str)
            with open(self.config_file, "w") as outfile:
                outfile.write(conf_str)
        else:
            with open(self.config_file, 'r') as openfile:
                # Reading from json file
                self.values = json.load(openfile)


if __name__ == "__main__":
    config = StockConfig()

    print(config.values)
