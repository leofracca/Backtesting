import backtrader as bt
import datetime
from Strategies.AIStrategy import AIStrategy

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)  # Initial cash

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
        dataname='datas/15min_BTC-USDT.csv',
        timeframe=bt.TimeFrame.Minutes,
        compression=15,
        fromdate=datetime.datetime(2022, 1, 1),
        todate=datetime.datetime(2022, 1, 7),
        dtformat='%Y-%m-%d %H:%M:%S',
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
    )
    data.addfilter(bt.filters.SessionFilter(data))

    cerebro.adddata(data)
    cerebro.addstrategy(AIStrategy)  # Choose a strategy

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candlestick')
