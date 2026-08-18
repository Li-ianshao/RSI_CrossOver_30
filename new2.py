import yfinance as yf
import pandas as pd
import ta
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 負號正常顯示

# 參數設定
symbol = 'WDAY'
holding_days = [5, 10, 15, 20, 25, 30, 40]  # 可自訂多組

# 抓10年資料
df = yf.download(symbol, period="10y", auto_adjust=True)

df['RSI'] = ta.momentum.RSIIndicator(df['Close'].squeeze(), window=14).rsi()
df.dropna(inplace=True)

# 尋找所有 RSI 上穿 30 的買點
signals = []
for i in range(1, len(df) - max(holding_days)):
	if df['RSI'].iloc[i-1] < 30 and df['RSI'].iloc[i] >= 30:  # 不同策略
		buy_date = df.index[i]  # 紀錄訊號發生的日期
		#buy_price = float(df['Close'].iloc[i]) # 紀錄訊號發生的收盤價

		buy_price = float(df['Close'].iloc[i].item() if isinstance(df['Close'].iloc[i], pd.Series) else df['Close'].iloc[i])
		#high_price = float(df['High'].iloc[i].item() if isinstance(df['High'].iloc[i], pd.Series) else df['High'].iloc[i])

		row = [buy_date.strftime('%Y-%m-%d'), buy_price]
        
        # 計算各持有日數的賣出價和報酬
		for n in holding_days:
			if i + n < len(df):
			    sell_price = float(df['Close'].iloc[i + n].item() if isinstance(df['Close'].iloc[i + n], pd.Series) else df['Close'].iloc[i + n])
			    high_val = float(df['High'].iloc[i + n].item() if isinstance(df['Close'].iloc[i + n], pd.Series) else df['Close'].iloc[i + n])
			    ret = (sell_price - buy_price) / buy_price * 100
			    goal_reached_5Percent = 1 if high_val >= buy_price * 1.05 else 0 # 目標設定為獲利 5%
			    goal_reached_10Percent = 1 if high_val >= buy_price * 1.1 else 0 # 目標設定為獲利 10%
			else:
			    sell_price = np.nan
			    ret = np.nan
			    goal_reached = np.nan
			row.extend([sell_price, ret, high_val, goal_reached_5Percent, goal_reached_10Percent])
		signals.append(row) # Signals 是 list of lists

# 整理 DataFrame
cols = ['BuyDate', 'BuyPrice']

for n in holding_days:
	cols += [f'Sell_{n}d', f'Return_{n}d(%)', f'High_{n}d', f'Goal5_{n}d', f'Goal10_{n}d']

signals_df = pd.DataFrame(signals, columns=cols)
signals_df = signals_df.round(2)
signals_df.to_csv("RSI_Crossover30_signals.csv", index=False)
#print(signals_df)

# 策略績效統計
print("=== RSI Crossover 30 Backtest on", symbol, "===")
print(f"股票代碼:{symbol}")
print(f"訊號發生次數:{len(signals_df)}")

for n in holding_days:
	colGoal5 = "Goal5_" + str(n) +  "d"
	colGoal10 = "Goal10_" + str(n) +  "d"
	sumColGoal5 = signals_df[colGoal5].sum()
	sumColGoal10 = signals_df[colGoal10].sum()

	returns = signals_df[f'Return_{n}d(%)'].dropna()
	print(f"\n持有{n}日:")
	#print(f"  事件數量: {len(returns)}")
	print(f"  平均報酬: {returns.mean():.2f}%")
	print(f"  報酬變異數: {returns.var():.2f}")
	print(f"  勝率(>0): {(returns>0).mean()*100:.2f}%")
	print(f"  最大損失: {returns.min():.2f}%")
	print(f"  5%達標機率：{sumColGoal5/len(returns):.2f}")
	print(f"  10%達標機率：{sumColGoal10/len(returns):.2f}")

# 報酬分布圖
plt.figure(figsize=(10,5))
for n in holding_days:
	returns = signals_df[f'Return_{n}d(%)'].dropna()
	plt.hist(returns, bins=20, alpha=0.4, label=f'{n}d')
plt.axvline(0, color='red', linestyle='--')
plt.legend()
plt.title(f'{symbol} RSI上穿30策略報酬分布')
plt.xlabel('Return (%)')
plt.ylabel('Count')
plt.tight_layout()
plt.show()

# 畫出RSI與進場點
plt.figure(figsize=(14,6))
plt.subplot(211)
plt.plot(df['Close'], label='Close')
buy_dates = pd.to_datetime(signals_df['BuyDate'])
plt.scatter(buy_dates, df.loc[buy_dates, 'Close'], color='red', marker='^', label='RSI Crossover 30 Buy', zorder=10)
plt.legend()
plt.title(f"{symbol} Price & RSI Crossover 30 Entry")

plt.subplot(212)
plt.plot(df['RSI'], label='RSI')
plt.axhline(30, color='grey', linestyle='--')
plt.scatter(buy_dates, df.loc[buy_dates, 'RSI'], color='red', marker='^', label='RSI Crossover')
plt.legend()
plt.tight_layout()
plt.show()
