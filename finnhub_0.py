# pip install finnhub-python pandas python-dateutil pytz
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import pytz
import finnhub

API_KEY = "d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40"

# ------------------------------------------
# Finnhub client
# ------------------------------------------
fh = finnhub.Client(api_key=API_KEY)

TICKERS = ["XOM", "KSS", "SMCI", "T"]

# ------------------------------------------
# 工具函式：取得最近三個月的日收盤價
# ------------------------------------------
def get_last_3m_daily_close(symbol: str) -> pd.DataFrame:
    # 使用美中時區（使用者在 America/Chicago）
    tz = pytz.timezone("America/Chicago")
    now = datetime.now(tz)
    start = now - relativedelta(months=3)

    # 轉為 Unix 秒
    fr = int(start.timestamp())
    to = int(now.timestamp())

    # Finnhub 日線：resolution='D'
    data = fh.stock_candles(symbol, 'D', fr, to)

    # 若無資料或回傳 's' != 'ok'
    if not data or data.get('s') != 'ok':
        return pd.DataFrame(columns=["symbol", "date", "close"])

    # 組成 DataFrame
    df = pd.DataFrame({
        "date": [datetime.fromtimestamp(ts, tz).date() for ts in data["t"]],
        "close": data["c"]
    })
    df.insert(0, "symbol", symbol)
    return df

# ------------------------------------------
# 工具函式：取得最近四季 Earnings 與 Revenue（如有）
# - company_earnings: 常見欄位：
#   period, actual, estimate, surprise, surprisePercent,
#   revenueActual (可能出現), revenueEstimate (可能出現),
#   revenueSurprise (可能出現), revenueSurprisePercent (可能出現)
# Finnhub 可能對不同股票或不同季提供欄位略有差異，故做 Key 存在檢查。
# ------------------------------------------
def get_last_4q_earnings(symbol: str) -> pd.DataFrame:
    # 限制多抓幾筆，保險取到 4 季（有些季可能缺欄位或為 None）
    rows = fh.company_earnings(symbol, limit=8) or []

    # 只保留最近四筆（company_earnings 已是由近到遠排序）
    rows = rows[:4]

    records = []
    for r in rows:
        records.append({
            "symbol": symbol,
            "period": r.get("period"),  # e.g. '2025-06-30'
            # EPS / Earnings
            "eps_actual": r.get("actual"),
            "eps_estimate": r.get("estimate"),
            "eps_surprise": r.get("surprise"),
            "eps_surprise_percent": r.get("surprisePercent"),
            # Revenue（若 API 有提供這些欄位就填，否則為 None）
            "revenue_actual": r.get("revenueActual"),
            "revenue_estimate": r.get("revenueEstimate"),
            "revenue_surprise": r.get("revenueSurprise"),
            "revenue_surprise_percent": r.get("revenueSurprisePercent"),
        })
    return pd.DataFrame.from_records(records)

# ------------------------------------------
# 主流程：彙整所有股票
# ------------------------------------------
all_prices = []
all_earnings = []

for sym in TICKERS:
    try:
        # 1) 最近三個月收盤價
        px = get_last_3m_daily_close(sym)
        all_prices.append(px)

        # 2) 最近四季 earnings + revenue（如有）
        er = get_last_4q_earnings(sym)
        all_earnings.append(er)

    except finnhub.FinnhubAPIException as e:
        print(f"[{sym}] Finnhub API error:", e)
    except Exception as e:
        print(f"[{sym}] Unknown error:", e)

# 合併
prices_df = pd.concat(all_prices, ignore_index=True) if all_prices else pd.DataFrame(columns=["symbol","date","close"])
earnings_df = pd.concat(all_earnings, ignore_index=True) if all_earnings else pd.DataFrame(
    columns=[
        "symbol","period",
        "eps_actual","eps_estimate","eps_surprise","eps_surprise_percent",
        "revenue_actual","revenue_estimate","revenue_surprise","revenue_surprise_percent"
    ]
)

# 依需求排序
prices_df = prices_df.sort_values(["symbol", "date"]).reset_index(drop=True)
earnings_df = earnings_df.sort_values(["symbol", "period"], ascending=[True, False]).reset_index(drop=True)

# 輸出檢視
print("\n=== 最近三個月日收盤價（部分） ===")
print(prices_df.groupby("symbol").head(5))

print("\n=== 最近四季 Earnings / Revenue（如有） ===")
print(earnings_df)

# 可選：輸出 CSV
prices_df.to_csv("prices_last_3m.csv", index=False)
earnings_df.to_csv("earnings_last_4q.csv", index=False)
print("\n已輸出：prices_last_3m.csv, earnings_last_4q.csv")
