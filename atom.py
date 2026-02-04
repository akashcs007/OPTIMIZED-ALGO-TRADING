import backtrader as bt
import yfinance as yf
import pandas as pd
import numpy as np

class FinalProfitableStrategy(bt.Strategy):
    """
    Buy-and-Hold with Trend Filter Strategy
    
    Core Insight: SPY trends up over time. The key is to:
    1. Only hold during confirmed uptrends
    2. Exit during downtrends/corrections
    3. Minimize trading frequency
    4. Use position sizing to manage risk
    
    This is essentially a tactical buy-and-hold approach.
    """

    params = dict(
        # Trend identification
        fast_ema=50,
        slow_ema=200,
        
        # Risk management
        position_pct=0.95,  # Nearly full investment when in uptrend
        atr_period=14,
        stop_atr_multiplier=8.0,  # Very wide stop
    )

    def __init__(self):
        self.fast_ema = bt.indicators.EMA(self.data.close, period=self.p.fast_ema)
        self.slow_ema = bt.indicators.EMA(self.data.close, period=self.p.slow_ema)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.entry_price = None
        self.stop_price = None
        self.trade_count = 0

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.trade_count += 1
            elif order.issell():
                self.entry_price = None

    def notify_trade(self, trade):
        if trade.isclosed:
            result = "WIN" if trade.pnl > 0 else "LOSS"
            pnl_pct = (trade.pnlcomm / abs(trade.price * trade.size)) * 100 if trade.size != 0 else 0
            print(f"Trade #{self.trade_count} [{result}] | P&L: ${trade.pnlcomm:.2f} ({pnl_pct:.2f}%)")

    def next(self):
        if self.position:
            # Exit if trend reverses (fast EMA crosses below slow EMA)
            if self.fast_ema[0] < self.slow_ema[0]:
                self.close()
                print(f"EXIT: Trend reversal at ${self.data.close[0]:.2f}")
                return
            
            # Very wide stop loss
            if self.stop_price and self.data.close[0] < self.stop_price:
                self.close()
                print(f"EXIT: Stop loss at ${self.data.close[0]:.2f}")
                return
        else:
            # Enter when fast EMA crosses above slow EMA (golden cross)
            if (self.fast_ema[0] > self.slow_ema[0] and 
                self.fast_ema[-1] <= self.slow_ema[-1]):
                
                portfolio_value = self.broker.getvalue()
                size = int((portfolio_value * self.p.position_pct) / self.data.close[0])
                
                if size >= 1:
                    self.buy(size=size)
                    self.stop_price = self.data.close[0] - (self.atr[0] * self.p.stop_atr_multiplier)
                    print(f"\nENTRY: ${self.data.close[0]:.2f} | Size: {size} | Stop: ${self.stop_price:.2f}")


def run_backtest():
    cerebro = bt.Cerebro(stdstats=False)

    print("Downloading SPY 1-hour data...")
    df = yf.download("SPY", period="730d", interval="1h", progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df.dropna(inplace=True)
    print(f"Data: {len(df)} bars\n")

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(FinalProfitableStrategy)

    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Minutes, compression=60, riskfreerate=0.02)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    print(f"Starting: ${cerebro.broker.getvalue():,.2f}")
    print("="*60 + "\n")
    
    results = cerebro.run()
    strat = results[0]
    final_value = cerebro.broker.getvalue()

    print("\n" + "="*60)
    print("FINAL STRATEGY RESULTS")
    print("="*60)
    
    total_return = ((final_value - 100000) / 100000) * 100
    print(f"\nPortfolio:")
    print(f"  Starting: $100,000.00")
    print(f"  Final: ${final_value:,.2f}")
    print(f"  Return: {total_return:+.2f}%")
    print(f"  P&L: ${final_value - 100000:+,.2f}")
    
    sharpe = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe.get('sharperatio', 0) or 0
    
    dd = strat.analyzers.drawdown.get_analysis()
    print(f"\nRisk:")
    print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {dd['max']['drawdown']:.2f}%")
    
    trades = strat.analyzers.trades.get_analysis()
    total_trades = trades.get('total', {}).get('total', 0)
    
    print(f"\nTrades: {total_trades}")
    
    if total_trades > 0:
        won = trades.get('won', {}).get('total', 0)
        lost = trades.get('lost', {}).get('total', 0)
        win_rate = won / total_trades
        
        total_won = trades.get('won', {}).get('pnl', {}).get('total', 0)
        total_lost = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0))
        profit_factor = total_won / total_lost if total_lost > 0 else float('inf')
        
        print(f"  Won: {won} | Lost: {lost}")
        print(f"  Win Rate: {win_rate:.2%}")
        print(f"  Profit Factor: {profit_factor:.2f}")
    
    print("\n" + "="*60)
    print("FINAL COMPARISON")
    print("="*60)
    print(f"\nOriginal:  $94,498 (-5.50%) | SR: -51.08")
    print(f"Final:     ${final_value:,.0f} ({total_return:+.2f}%) | SR: {sharpe_ratio:.2f}")
    print(f"\nImprovement: ${final_value - 94498.28:+,.2f}")
    print("="*60 + "\n")
    
    try:
        cerebro.plot(style='candlestick', volume=False)
    except:
        pass


if __name__ == "__main__":
    run_backtest()