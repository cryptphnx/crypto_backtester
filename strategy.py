# strategy.py
import backtrader as bt

class PineStrategy(bt.Strategy):
    params = dict(
        # EMA parameters
        longTermFastLen=50,
        longTermSlowLen=200,
        shortTermFastLen=10,
        shortTermSlowLen=20,
        # Exit method: "Fixed", "Trailing", or "ATR"
        exitMethod="Fixed",
        fixedStopLossPct=1,      # expressed as percent (e.g., 1 means 1%)
        fixedTakeProfitPct=2,    # expressed as percent (e.g., 2 means 2%)
        fixedTrailingPct=1.5,    # expressed as percent (e.g., 1.5 means 1.5%)
        atrPeriod=14,
        atrStopLossFactor=1.0,
        atrTakeProfitFactor=2.0,
        useAtrStopLoss=False,
        # Filter parameters (disabled by default)
        useAdxFilter=False,
        adxPeriod=14,
        adxThreshold=20.0,
        useVolumeFilter=False,
        volumeMALen=20,
        useRSIFilter=False,
        rsiPeriod=14,
        rsiLongThreshold=50.0,
        rsiShortThreshold=50.0,
        useAtrFilter=False,
        atrFilterThreshold=0.01,
        enableHigherTFFilter=False,
        enableSessionFilter=False
    )

    def __init__(self):
        # Compute EMAs
        self.emaLongFast = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.longTermFastLen)
        self.emaLongSlow = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.longTermSlowLen)
        self.emaShortFast = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.shortTermFastLen)
        self.emaShortSlow = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.shortTermSlowLen)
        # ATR indicator
        self.atr = bt.indicators.ATR(self.data, period=self.params.atrPeriod)
        # Initialize trade log and temporary storage for order details and exit reason.
        self.trade_log = []
        self.entry_order_info = {}
        self.exit_order_info = {}
        self._exit_reason = None

    def notify_order(self, order):
        # Log order execution details.
        if order.status == order.Completed:
            if order.isbuy():
                self.entry_order_info = {
                    "Type": "Buy",
                    "Price": order.executed.price,
                    "Size": order.executed.size,
                    "Datetime": self.data.num2date(order.executed.dt).strftime("%Y-%m-%d %H:%M:%S")
                }
            elif order.issell():
                self.exit_order_info = {
                    "Type": "Sell",
                    "Price": order.executed.price,
                    "Size": order.executed.size,
                    "Datetime": self.data.num2date(order.executed.dt).strftime("%Y-%m-%d %H:%M:%S")
                }

    def next(self):
        # Determine overall trend and generate entry signals.
        bullTrend = self.emaLongFast[0] > self.emaLongSlow[0]
        bearTrend = self.emaLongFast[0] < self.emaLongSlow[0]
        
        longSignal = bullTrend and self.emaShortFast[0] > self.emaShortSlow[0] and \
                     self.emaShortFast[-1] <= self.emaShortSlow[-1]
        shortSignal = bearTrend and self.emaShortFast[0] < self.emaShortSlow[0] and \
                      self.emaShortFast[-1] >= self.emaShortSlow[-1]
        
        if not self.position:
            if longSignal:
                self.buy()
            elif shortSignal:
                self.sell()
        else:
            # Exit logic (using Fixed exit method)
            entry_price = self.position.price
            # Convert percentages from whole numbers to factors.
            if self.position.size > 0:
                if self.params.exitMethod == "Fixed":
                    stop = entry_price - (self.atr[0] * self.params.atrStopLossFactor) if self.params.useAtrStopLoss \
                           else entry_price * (1 - self.params.fixedStopLossPct / 100)
                    target = entry_price * (1 + self.params.fixedTakeProfitPct / 100)
                    if self.data.close[0] <= stop:
                        self._exit_reason = "Stop Loss"
                        self.close()
                    elif self.data.close[0] >= target:
                        self._exit_reason = "Take Profit"
                        self.close()
            elif self.position.size < 0:
                if self.params.exitMethod == "Fixed":
                    stop = entry_price + (self.atr[0] * self.params.atrStopLossFactor) if self.params.useAtrStopLoss \
                           else entry_price * (1 + self.params.fixedStopLossPct / 100)
                    target = entry_price * (1 - self.params.fixedTakeProfitPct / 100)
                    if self.data.close[0] >= stop:
                        self._exit_reason = "Stop Loss"
                        self.close()
                    elif self.data.close[0] <= target:
                        self._exit_reason = "Take Profit"
                        self.close()

    def notify_trade(self, trade):
        # When a trade is closed, log detailed information.
        if trade.isclosed:
            log_entry = {
                'Entry Date': self.data.num2date(trade.dtopen).strftime("%Y-%m-%d %H:%M:%S"),
                'Exit Date': self.data.num2date(trade.dtclose).strftime("%Y-%m-%d %H:%M:%S"),
                'Size': trade.size,
                'Entry Price': trade.price,
                'Profit': trade.pnl,
                'Exit Reason': self._exit_reason if self._exit_reason is not None else "N/A",
                'Entry Order': self.entry_order_info,
                'Exit Order': self.exit_order_info
            }
            self.trade_log.append(log_entry)
            # Reset temporary storage.
            self._exit_reason = None
            self.entry_order_info = {}
            self.exit_order_info = {}

    def stop(self):
        # At the end of the backtest, if a position remains open, force a closure.
        if self.position:
            self._exit_reason = "End of Data"
            self.close()
