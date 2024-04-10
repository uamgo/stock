import os.path
import json
import exchange_calendars as xcals
import datetime


class StockConfig:

    base_path = "/tmp/stock"
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    daily_path = f"{base_path}/daily"
    minute_path = f"{base_path}/{today_str}"
    config_file = f"{minute_path}/config.json"
    values = None
    xshg = xcals.get_calendar("XSHG")

    def __init__(self):
        self.init_path()
        self.init_config()

    def init_path(self):
        if not os.path.isdir(self.base_path):
            os.mkdir(self.base_path)
        self.daily_path = f"{self.base_path}/daily"
        if not os.path.isdir(self.daily_path):
            os.mkdir(self.daily_path)
        e_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.minute_path = f"{self.base_path}/{e_date}"
        if not os.path.isdir(self.minute_path):
            os.mkdir(self.minute_path)

    def init_config(self):
        if not os.path.exists(self.config_file):
            last_trade_day_ts = self.xshg.schedule.loc[self.xshg.schedule['open'] < self.today_str]['open'][-1]
            last_trade_day_str = last_trade_day_ts.strftime("%Y-%m-%d")
            if last_trade_day_str == self.today_str:
                last_trade_day_ts = self.xshg.schedule.index[-2]
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
