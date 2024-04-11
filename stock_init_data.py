import time

import akshare as ak

import stock_config as config


class StockInitData:

    conf = config.StockConfig()

    def init_concept(self):
        stock_board_concept_name_em_df = ak.stock_board_concept_name_em()
        concept_len = len(stock_board_concept_name_em_df)
        print(f"Start to loop all [{concept_len}] concepts")
        for ind in stock_board_concept_name_em_df.index:
            concept_name = stock_board_concept_name_em_df["板块名称"][ind]
            concept_code = stock_board_concept_name_em_df["板块代码"][ind]
            if not self.conf.exists_concept_data(concept_code):
                concept_tmp_df = ak.stock_board_concept_cons_em(symbol=concept_name)
                self.conf.save_concept_data(concept_code, concept_tmp_df)
            print(f"Finished [{ind + 1}/{concept_len}] {concept_code} {concept_name}")

    def init_daily(self):
        stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        stock_len = len(stock_zh_a_spot_em_df)
        print(f"Start to loop all [{stock_len}] stocks")
        for ind in stock_zh_a_spot_em_df.index:
            code = stock_zh_a_spot_em_df['代码'][ind]
            name = stock_zh_a_spot_em_df['名称'][ind]
            if 'ST' in name or '退市' in name or 'N' in name or 'L' in name or 'C' in name or 'U' in name:
                continue
            if not self.conf.exists_daily_data(code):
                day_df = ak.stock_zh_a_hist(symbol=code, period="daily")
                self.conf.save_daily_data(code, day_df)
            print(f"Finished [{ind + 1}/{stock_len}] {code} {name}")


if __name__ == "__main__":
    start_ts = time.time()
    stock_data = StockInitData()

    stock_data.init_concept()
    end_ts = time.time()
    print("\nConcept data elapse: %.2f s,  %s" % ((end_ts - start_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    stock_data.init_daily()
    end_2_ts = time.time()
    print("\nDaily data elapse: %.2f s,  %s" % ((end_2_ts - end_ts), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
