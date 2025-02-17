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
        fixedStopLossPct=1,      # Now 1% instead of 0.01
        fixedTakeProfitPct=2,    # Now 2% instead of 0.02
        fixedTrailingPct=1.5,    # Now 1.5% instead of 0.01
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
        # Initialize trade log list
        self.trade_log = []

    def next(self):
        # Determine overall trend and generate entry signals (simplified logic)
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
            # For demonstration: exit logic using Fixed exit method.
            entry_price = self.position.price
            if self.position.size > 0:
                # Note: Since our fixed percentages are now whole numbers representing percentages,
                # we convert them to factors by dividing by 100.
                if self.params.exitMethod == "Fixed":
                    stop = entry_price - (self.atr[0] * self.params.atrStopLossFactor) if self.params.useAtrStopLoss else entry_price * (1 - self.params.fixedStopLossPct / 100)
                    target = entry_price * (1 + self.params.fixedTakeProfitPct / 100)
                    if self.data.close[0] <= stop or self.data.close[0] >= target:
                        self.close()
            elif self.position.size < 0:
                if self.params.exitMethod == "Fixed":
                    stop = entry_price + (self.atr[0] * self.params.atrStopLossFactor) if self.params.useAtrStopLoss else entry_price * (1 + self.params.fixedStopLossPct / 100)
                    target = entry_price * (1 - self.params.fixedTakeProfitPct / 100)
                    if self.data.close[0] >= stop or self.data.close[0] <= target:
                        self.close()

    def notify_trade(self, trade):
        # Log trade details when a trade is closed.
        if trade.isclosed:
            self.trade_log.append({
                'Entry Date': self.data.num2date(trade.dtopen).strftime("%Y-%m-%d %H:%M:%S"),
                'Exit Date': self.data.num2date(trade.dtclose).strftime("%Y-%m-%d %H:%M:%S"),
                'Size': trade.size,
                'Entry Price': trade.price,
                'Profit': trade.pnl
            })
