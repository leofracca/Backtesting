import backtrader as bt
import datetime  # For datetime objects
from Strategies.testStrategy import TestStrategy
from Strategies.AIStrategy import AIStrategy

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
        dataname='datas/15min_BTC-USDT.csv',
        # Do not pass values before this date
        fromdate=datetime.datetime(2021, 1, 1),
        # Do not pass values after this date
        todate=datetime.datetime(2021, 1, 4),
        dtformat="%Y-%m-%d %H:%M:%S",
        timeframe=bt.TimeFrame.Minutes,
        compression=1)
    data.addfilter(bt.filters.SessionFilter(data))

    cerebro.adddata(data)
    cerebro.addstrategy(AIStrategy)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candlestick')
