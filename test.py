import pandas as pd
import yfinance as yf
import ta
import json
import requests

def to_frames(payload: dict, *, inplace: bool = False) -> dict:
    """
    將 payload['data'] 底下的每個成員（list of dict）轉為 DataFrame。
    - 會做欄位標準化（industry/Industry 合併為 Industry）
    - 轉型：RSI / Yields / 最大跌幅(%) / Div_Date / 布林值欄位
    - 回傳：{ section_name: DataFrame, ... }
    - 若 inplace=True，會直接把 payload['data'] 替換為 DataFrame 後回傳 payload
    """
    data = payload.get("data", {})
    frames = {}

    for key, items in data.items():
        # 轉 DataFrame（空清單會得到空 DF）
        df = pd.DataFrame(items)

        # 欄名一致化
        if "industry" in df.columns and "Industry" not in df.columns:
            df = df.rename(columns={"industry": "Industry"})

        # 各分區型別調整
        if key in ("RSI", "RSI_Below30"):
            if "RSI" in df.columns:
                df["RSI"] = pd.to_numeric(df["RSI"], errors="coerce").astype("Int64")
            for col in ("SNP100", "股市貴族"):
                if col in df.columns:
                    df[col] = (
                        df[col].astype(str).str.lower()
                        .map({"true": True, "false": False})
                    )

        elif key == "dividends":
            if "Yields" in df.columns:
                df["Yields"] = pd.to_numeric(df["Yields"], errors="coerce")
            if "Div_Date" in df.columns:
                df["Div_Date"] = pd.to_datetime(df["Div_Date"], errors="coerce")
            for col in ("SNP100", "股息貴族"):
                if col in df.columns:
                    df[col] = (
                        df[col].astype(str).str.lower()
                        .map({"true": True, "false": False})
                    )

        elif key == "drops":
            # 將 '最大跌幅' 例如 '48.08%' -> 48.08 (數值)
            if "最大跌幅" in df.columns:
                pct = (
                    df["最大跌幅"].astype(str)
                    .str.replace("%", "", regex=False)
                )
                df["最大跌幅(%)"] = pd.to_numeric(pct, errors="coerce")
                # 若想要 0~1 的小數比率，改成：
                # df["最大跌幅"] = df["最大跌幅(%)"] / 100
            for col in ("SNP100", "股市貴族"):
                if col in df.columns:
                    df[col] = (
                        df[col].astype(str).str.lower()
                        .map({"true": True, "false": False})
                    )

        frames[key] = df

    if inplace:
        payload["data"] = frames
        return payload
    return frames

url = "https://stock-web-real-cfcydzdxg3c0hnck.centralus-01.azurewebsites.net/core/api/stockdata/"

params = {"data": "AAPL"}           # 可選：查詢參數
headers = {"Accept": "application/json"}

resp = requests.get(url, params=params, headers=headers, timeout=10)
resp.raise_for_status()                # 非 2xx 會丟錯
data = resp.json()                     # 轉成 Python dict
#print("status code:", resp.status_code)
#print("JSON:", data)

frames = to_frames(data)        # 不改原物件，得到 dict of DataFrames
# 或者：payload = to_frames(payload, inplace=True)  # 直接把 payload['data'] 變成 DataFrames

# 取用
rsi_df = frames["RSI"]
div_df = frames["dividends"]
drops_df = frames["drops"]

print(rsi_df)

print('\n\n\n')
print(div_df)

print('\n\n\n')
print(drops_df)
#print(rsi_df.dtypes)
#print(div_df.dtypes)
#print(drops_df[["Ticker","最大跌幅(%)"]].head())

