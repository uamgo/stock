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
    def is_trading(self, code):
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

    def get_format_code(self, stock_code):
        return stock_code.zfill(6)

    def save_minute_data(self, code, minute_df):
        file_name = f"{self.minute_path}/{code}.json"
        if not os.path.exists(file_name):
            minute_df.to_json(file_name, orient='split', compression='infer', index='true')

    def get_minute_data(self, code):
        file_name = f"{self.minute_path}/{code}.json"
        return pd.read_json(file_name, orient='split', compression='infer')

    def save_concept_data(self, concept_code, concept_df):
        file_name = f"{self.concept_path}/{concept_code}.json"
        if not os.path.exists(file_name):
            concept_df.to_json(file_name, orient='split', compression='infer', index='true')

    def get_concept_data(self, concept_code):
        file_name = f"{self.concept_path}/{concept_code}.json"
        return pd.read_json(file_name, orient='split', compression='infer')

    def exists_concept_data(self, concept_code):
        file_name = f"{self.concept_path}/{concept_code}.json"
        return os.path.exists(file_name)

    def save_daily_data(self, code, daily_df):
        file_name = f"{self.daily_path}/{code}.json"
        if not os.path.exists(file_name):
            daily_df.to_json(file_name, orient='split', compression='infer', index='true')

    def get_daily_data(self, code):
        file_name = f"{self.daily_path}/{code}.json"
        return pd.read_json(file_name, orient='split', compression='infer')

    def exists_daily_data(self, code):
        file_name = f"{self.daily_path}/{code}.json"
        return os.path.exists(file_name)

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
