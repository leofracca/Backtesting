import argparse
import backtrader as bt
import datetime
from Strategies.AIStrategy import AIStrategy


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--startdate',
                        help='The date from which the simulation will start, format YYYY-MM-DD',
                        type=datetime.date.fromisoformat)
    parser.add_argument('-e', '--enddate',
                        help='The date at which the simulation will end, format YYYY-MM-DD',
                        type=datetime.date.fromisoformat)
    args = parser.parse_args()

    if args.startdate:
        startdate = args.startdate
    else:
        startdate = datetime.datetime(2022, 2, 1)

    if args.enddate:
        enddate = args.enddate
    else:
        enddate = datetime.datetime(2022, 2, 8)

    return startdate, enddate


def run_simulation(startdate, enddate):
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)  # Initial cash

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
        dataname='datas/15min_BTC-USDT.csv',
        timeframe=bt.TimeFrame.Minutes,
        compression=15,
        fromdate=startdate,
        todate=enddate,
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


if __name__ == '__main__':
    start, end = parse_arguments()

    run_simulation(start, end)

