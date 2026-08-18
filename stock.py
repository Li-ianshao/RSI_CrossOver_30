import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import numpy as np

# 你的前30檔股票名單
top30 = ['XOM', 'MO', 'T', 'AAPL', 'BEN', 'AMD', 'DOW']  # 可擴充到30檔

all_results = []
summary_stats = []

for ticker in top30:
    df = yf.download(ticker, period="5y", auto_adjust=True)
    if df.empty or len(df) < 30: continue
    close_series = df['Close'].squeeze()
    df['RSI'] = ta.momentum.RSIIndicator(close_series, window=14).rsi()
    df.dropna(inplace=True)
    returns_5, returns_10, returns_15, returns_20, events = [], [], [], [], []
    for i in range(1, len(df)-20):
        if df['RSI'].iloc[i-1]<30 and df['RSI'].iloc[i]>=30:
            event_date = df.index[i]
            price0 = float(df['Close'].iloc[i])
            price5 = float(df['Close'].iloc[i+5]) if i+5 < len(df) else np.nan
            price10 = float(df['Close'].iloc[i+10]) if i+10 < len(df) else np.nan
            price15 = float(df['Close'].iloc[i+15]) if i+15 < len(df) else np.nan
            price20 = float(df['Close'].iloc[i+20]) if i+20 < len(df) else np.nan
            r5 = (price5 - price0) / price0 * 100 if not pd.isna(price5) else np.nan
            r10= (price10 - price0) / price0 * 100 if not pd.isna(price10) else np.nan
            r15= (price15 - price0) / price0 * 100 if not pd.isna(price15) else np.nan
            r20= (price20 - price0) / price0 * 100 if not pd.isna(price20) else np.nan
            returns_5.append(r5)
            returns_10.append(r10)
            returns_15.append(r15)
            returns_20.append(r20)
            events.append([
                ticker, event_date.strftime('%Y-%m-%d'),
                price0, price5, price10, price15, price20,
                r5, r10, r15, r20
            ])
    # 統計績效
    if len(returns_5) > 0:
        summary_stats.append([
            ticker,
            np.nanmean(returns_5), np.nanvar(returns_5),
            np.nanmean(returns_10), np.nanvar(returns_10),
            np.nanmean(returns_15), np.nanvar(returns_15),
            np.nanmean(returns_20), np.nanvar(returns_20),
            len(returns_5)
        ])
    all_results.extend(events)

# 1. 輸出事件紀錄CSV
result_df = pd.DataFrame(
    all_results,
    columns=["Ticker","EventDate",
             "CloseAtEvent","Close_Day5","Close_Day10","Close_Day15","Close_Day20",
             "R5(%)","R10(%)","R15(%)","R20(%)"]
)
result_df = result_df.round(2)  # 所有浮點數保留2位小數
result_df.to_csv("RSI_Crossover30_events.csv", index=False)

# 2. 輸出統計績效圖表與HTML
stat_df = pd.DataFrame(summary_stats, columns=[
    "Ticker",
    "MeanR5(%)","VarR5","MeanR10(%)","VarR10",
    "MeanR15(%)","VarR15","MeanR20(%)","VarR20","EventCount"
])
stat_df = stat_df.round(2)   # 所有浮點數保留2位小數
stat_df = stat_df.sort_values("MeanR5(%)",ascending=False)

plt.figure(figsize=(12,7))
plt.bar(stat_df["Ticker"], stat_df["MeanR5(%)"], yerr=np.sqrt(stat_df["VarR5"]), color='skyblue')
plt.axhline(0, color='red', linestyle='--', label='Mean Return = 0.0%')
plt.xticks(rotation=45)
plt.title("RSI 上穿30後5日平均報酬(%)")
plt.ylabel("Mean Return (%)")
plt.legend()
plt.tight_layout()
plt.savefig("rsi_5day_bar.png")

# 3. 簡易HTML報告
html = f"""
<html><head><title>RSI Crossover 30 策略績效報告</title></head>
<body>
<h2>RSI上穿30策略: 前30高交易量S&P500股票(5年)</h2>
<h3>5日平均報酬圖</h3>
<img src='rsi_5day_bar.png'><br>
<h3>績效統計表</h3>
{stat_df.to_html(index=False)}
<h3>歷次事件報酬紀錄(前100)</h3>
{result_df.head(100).to_html(index=False)}
</body></html>
"""
with open("rsi_strategy_report.html","w",encoding="utf-8") as f:
    f.write(html)

print("✅ 報告產出：rsi_strategy_report.html")
