import backtrader as bt


class AIStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # MACD
        self.macd = bt.indicators.MACDHisto()
        # Cross of macd line and signal line (of the MACD)
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        # Parabolic SAR
        self.psar = bt.indicators.PSAR()

        # 200 EMA
        self.ema200 = bt.indicators.ExponentialMovingAverage(period=200)

        # To keep track of when the crossover crosses up or down
        # (True if it crosses up, False otherwise)
        self.macd_cross_up = False

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders
        self.order = None

        # Reward for long positions (incremented at each profitable long trade, decremented otherwise)
        # Reset to 1 when the price goes below the 200 EMA
        # It represents the amount for each long trade
        self.reward_long = 1
        # Reward for short positions (incremented at each profitable short trade, decremented otherwise)
        # Reset to 1 when the price goes above the 200 EMA
        # It represents the amount for each short trade
        self.reward_short = 1
        # Check if the current trade is a short trade
        self.is_short_position = False

        # To keep track of buy and sell prices
        self.buy_price = 0
        self.sell_price = 0

        self.already_traded = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f$' % order.executed.price)
                self.buy_price = order.executed.price

                if self.is_short_position:
                    # Update the reward for short positions
                    self.reward_short += (self.sell_price - self.buy_price) * 0.0001
                    self.log('Closing short position at %.2f$, PROFIT = %.2f$' % (self.stop_loss, self.sell_price - self.buy_price))

            elif order.issell():
                self.log('SELL EXECUTED, %.2f$' % order.executed.price)
                self.sell_price = order.executed.price

                if not self.is_short_position:
                    # Update the reward for long positions
                    self.reward_long += (self.sell_price - self.buy_price) * 0.0001
                    self.log('Closing long position at %.2f$, PROFIT = %.2f$' % (self.take_profit, self.sell_price - self.buy_price))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        if self.order:
            return  # pending order execution

        # Check if we have any open position
        if not self.position:
            # Check if the MACD lines crosses up or down
            if self.crossover[0] > 0.0:
                self.macd_cross_up = True
                self.already_traded = False
            elif self.crossover[0] < 0.0:
                self.macd_cross_up = False
                self.already_traded = False

            # If not, check if the current candle closes above the 200 EMA
            if self.dataclose[0] >= self.ema200[0]:
                self.is_short_position = False
                self.reward_short = 1  # Reset reward for short positions

                # If the MACD crosses up and the current candle closes above the parabolic SAR
                if self.macd_cross_up and self.psar[0] < self.dataclose[0] and not self.already_traded:
                    # Open a long position
                    # print(self.reward_long)  # Uncomment this to see how much it will buy
                    self.buy(size=self.reward_long)
                    self.already_traded = True

                    self.calculate_stop_loss_and_take_profit()
                    self.oco_profit = self.sell(exectype=bt.Order.Limit, price=self.take_profit, size=self.reward_long)
                    self.oco_loss = self.sell(exectype=bt.Order.Stop, price=self.stop_loss, size=self.reward_long, oco=self.oco_profit)

            else:
                self.is_short_position = True
                self.reward_long = 1  # Reset reward for long positions

                # If the MACD crosses down and the current candle closes below the parabolic SAR
                if not self.macd_cross_up and self.psar[0] > self.dataclose[0] and not self.already_traded:
                    # Open a short position
                    # print(self.reward_short)  # Uncomment this to see how much it will short
                    self.sell(size=self.reward_short)
                    self.already_traded = True

                    self.calculate_stop_loss_and_take_profit()
                    self.oco_profit = self.buy(exectype=bt.Order.Limit, price=self.take_profit, size=self.reward_short)
                    self.oco_loss = self.buy(exectype=bt.Order.Stop, price=self.stop_loss, size=self.reward_short, oco=self.oco_profit)

        else:
            # We have an open position
            if not self.is_short_position:
                # Check if the price touches the 200EMA
                # If so, immediately close the position and delete the pending orders
                if self.data[0] < self.ema200[0]:
                    # Long position LOSS
                    self.sell(size=self.reward_long)
                    self.cancel(self.oco_profit)
                    self.cancel(self.oco_loss)
            else:
                # Then check if the price touches the 200EMA
                # If so, immediately close the position and delete the pending orders
                if self.data[0] > self.ema200[0]:
                    # Short position LOSS
                    self.buy(size=self.reward_short)
                    self.cancel(self.oco_profit)
                    self.cancel(self.oco_loss)

    def calculate_stop_loss_and_take_profit(self):
        # Calculate take profit and stop loss
        self.take_profit = self.dataclose[0] * 2 - self.psar[0]
        self.stop_loss = self.psar[0]
        print('TAKE PROFIT = %.2f$' % self.take_profit)
        print('STOP_LOSS = %.2f$' % self.stop_loss)
