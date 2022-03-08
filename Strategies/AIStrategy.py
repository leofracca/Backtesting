import backtrader as bt


# Create a Stratey
class AIStrategy(bt.Strategy):

    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('atrperiod', 14),  # ATR Period (standard)
        ('atrdist', 3.0),  # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.params.macd1,
                                       period_me2=self.params.macd2,
                                       period_signal=self.params.macdsig)
        # Cross of macd.macd and macd.signal
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        self.psar = bt.indicators.PSAR()

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        if self.order:
            return  # pending order execution

        # if self.mcross[0] > 0.0 and self.smadir < 0.0 and not self.position:
        if not self.position:
            if self.crossover and self.psar[0] < self.dataclose[0]:  # or self.rsi < 30:
                self.buy()
                print('BOUGHT AT {}'.format(self.dataclose[0]))

        # elif ((self.mcross[0] <= 0.0 and self.smadir >= 0.0) or self.rsi > 70) and self.position:
        else:
            if self.crossover == -1:  # or self.rsi > 70:
                self.close()
                print('SOLD AT {}'.format(self.dataclose[0]))
