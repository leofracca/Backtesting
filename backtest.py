import backtrader as bt
import datetime  # For datetime objects
from Strategies.testStrategy import TestStrategy
from Strategies.AIStrategy import AIStrategy

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname='datas/oracle.csv',
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values after this date
        todate=datetime.datetime(2000, 12, 31))#,
        #reverse=False)

    cerebro.adddata(data)
    cerebro.addstrategy(AIStrategy)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candlestick')
