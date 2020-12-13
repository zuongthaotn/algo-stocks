import warnings

warnings.filterwarnings('ignore')

import os
import sys
import time
import numpy as np

ZORRO_STRATEGY_PATH = os.path.abspath('E:\\Zorro\\Strategy\\Magnus\\CounterTrend\\V3.c')
METHOD_MODULE_PATH = os.path.abspath('../..')
sys.path.insert(1, METHOD_MODULE_PATH)
import method.algofuncs as _af

path = os.getcwd()

def getPriceCounterTrendV3a(ticker_data):
    """
        Rule:
            1. Bien dong gia 3 thang(66 ngay) gan day <40%
            2. Bien dong gia 1 thang(22 ngay) gan day <20%
            3. Bien dong gia tuan(5 ngay) gan day < 15%
            4. Dang giam gia
                Price Low today is the min or smaller min5 * 3%
                Price Low today is the smaller max5 * 0.93
    :param ticker_data: pandas.core.DataFrame
    """
    last66 = ticker_data.tail(66)
    ticker_data66 = last66.copy()
    min66ByLow = ticker_data66[ticker_data66.Low == ticker_data66.Low.min()]
    minLow66 = min66ByLow.Low.values[0]
    max66ByHigh = ticker_data66[ticker_data66.High == ticker_data66.High.max()]
    maxHigh66 = max66ByHigh.High.values[0]
    diffHL66 = (maxHigh66 - minLow66) / maxHigh66
    if diffHL66 > 0.41:
        return 0
    last22 = ticker_data66.tail(22)
    ticker_data22 = last22.copy()
    min22ByLow = ticker_data22[ticker_data22.Low == ticker_data22.Low.min()]
    minLow22 = min22ByLow.Low.values[0]
    max22ByHigh = ticker_data22[ticker_data22.High == ticker_data22.High.max()]
    maxHigh22 = max22ByHigh.High.values[0]
    diffHL22 = (maxHigh22 - minLow22) / maxHigh22
    if diffHL22 > 0.21:
        return 0
    last5 = ticker_data22.tail(5)
    ticker_data5 = last5.copy()
    if ticker_data5.Volume.rolling(window=5).mean().iloc[-1] < 500000:
        return 0
    min5ByLow = ticker_data5[ticker_data5.Low == ticker_data5.Low.min()]
    minLow5 = min5ByLow.Low.values[0]
    max5ByHigh = ticker_data5[ticker_data5.High == ticker_data5.High.max()]
    maxHigh5 = max5ByHigh.High.values[0]
    diffHL5 = (maxHigh5 - minLow5) / maxHigh5
    if diffHL5 > 0.15:
        return 0
    if ticker_data5.Low.values[-1] > ticker_data5.High.values[-1] * 0.95:
        return 0
    expected_prices = np.array([minLow5, minLow5 * 1.03, minLow22, minLow22 * 1.03, minLow66, minLow66 * 1.03])
    return expected_prices.max()


DATA_PATH = os.path.abspath('../../vn-stock-data/VNX/')
vnx_file = os.path.abspath('../../vn-stock-data/VNX.csv')
ticker_follow_trending = []
hose_ticker = _af.getHOSETickers(vnx_file)
result = []
assets = ''
thresh_hold = ''
for ticker_id in hose_ticker:
    ticker_data = _af.get_pricing_by_path(DATA_PATH + '/' + ticker_id + '.csv', '2020-01-01')
    estimated_price = getPriceCounterTrendV3a(ticker_data)
    if estimated_price > 0:
        if not len(result):
            result = [[ticker_id, str(estimated_price)]]
            assets += '"' + str(ticker_id) + '"'
        else:
            result.append([ticker_id, str(estimated_price)])
            assets += ", " + '"' + str(ticker_id) + '"'
        thresh_hold += '\n\t case "' + str(ticker_id) + '": t = ' + str(estimated_price) + ';\n\t\tbreak;'

if len(result):
    template = open("zorro_template.c", "r")
    template_content = template.read()
    template.close()
    zorro_strategy = open(ZORRO_STRATEGY_PATH,"w")
    zorro_strategy.write('#include "Strategy/Magnus/fixZorro.h" \n')
    zorro_strategy.write('#include "Strategy/Magnus/Ticker.h" \n')
    zorro_strategy.write('#define RPM         '+assets + '\n')
    zorro_strategy.write('#define ASSETS      RPM \n')
    zorro_strategy.write('#define N           ' + str(len(result)) + '\n')
    zorro_strategy.write(template_content)
    zorro_strategy.write("\nvar getThreshHold(string ticker){\n");
    zorro_strategy.write("\t float t;\n");
    zorro_strategy.write("\t switch(ticker){");
    zorro_strategy.write(thresh_hold);
    zorro_strategy.write("\n\t}\n");
    zorro_strategy.write("\t return t;\n");
    zorro_strategy.write("\t}\n");
    zorro_strategy.close()
