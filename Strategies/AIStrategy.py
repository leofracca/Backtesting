import backtrader as bt


# Create a Stratey
class AIStrategy(bt.Strategy):

    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9)
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # MACD
        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.params.macd1,
                                       period_me2=self.params.macd2,
                                       period_signal=self.params.macdsig)
        # Cross of macd line and signal line (of the MACD)
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        # Parabolic SAR
        self.psar = bt.indicators.PSAR()

        # 200 EMA
        self.ema200 = bt.indicators.ExponentialMovingAverage(period=200)

        # RSI
        self.rsi = bt.indicators.RSI_SMA()

        # To keep track of when the crossover crosses up or down
        # (True if it crosses up, False otherwise)
        self.macd_cross_up = False

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

        # self.log('')
        # print(self.macd_cross_up)

        # Check if we have any open position
        if not self.position:
            # If not, check if the current candle closes above the 200 EMA
            if self.dataclose[0] > self.ema200[0]:

                # Check if the MACD lines crosses up or down
                if self.crossover[0] > 0.0:
                    self.macd_cross_up = True
                elif self.crossover[0] < 0.0:
                    self.macd_cross_up = False

                # If the MACD crosses up and the current candle closes above the parabolic SAR
                if self.macd_cross_up and self.psar[0] < self.dataclose[0]:
                    # Buy
                    self.buy()
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    # Reset this variable for the next trade
                    self.macd_cross_up = False

                    # Calculate take profit and stop loss (for sell order)
                    self.take_profit = self.dataclose[0] * 2 - self.psar[0]
                    self.stop_loss = self.psar[0]
                    print('TAKE PROFIT = ' + str(self.take_profit))
                    print('STOP_LOSS = ' + str(self.stop_loss))
                    # oco_profit = self.sell(exectype=bt.Order.Limit, price=take_profit)
                    # oco_loss = self.sell(exectype=bt.Order.Stop, price=stop_loss, oco=oco_profit)

        else:
            # We have an open position
            # So check if the current candle hits the take profit or the stop loss and sell
            if self.dataclose[0] >= self.take_profit or self.dataclose[0] < self.stop_loss:
                # Sell
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
