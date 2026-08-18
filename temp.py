import finnhub
from datetime import date, timedelta
import pandas as pd
from tabulate import tabulate
client = finnhub.Client(api_key="d0noj91r01qn5ghl2c3gd0noj91r01qn5ghl2c40")  
today = date.today()

# 抓取前 30 天，後三十天的 IPO 資料
data = client.ipo_calendar(
    _from= (today + timedelta(days=-30)).strftime("%Y-%m-%d"), #today.strftime("%Y-%m-%d"),
    to=(today + timedelta(days=30)).strftime("%Y-%m-%d")
)

df = pd.DataFrame(data['ipoCalendar']) # 將 Dictionary 轉換為 dataframe
df = df.dropna(subset=["numberOfShares"]) # 移除沒有股份(可能後來未上市)的資料
df = df[~df["exchange"].str.contains("Capital", na=False)] # 移除 exchange 欄位有 Capital 字樣的資料，這些是在二級，甚至三級市場上市
df = df.sort_values(by="date")
df = df.reset_index(drop=True)
#print(df)
print(tabulate(df, df.columns, tablefmt="grid"))

'''
📊 Nasdaq 與 NYSE 市場層級比較表
交易所 / 市場層級                      對象公司類型     上市標準（市值 / 財務 / 股東數）              投資人觀感           範例
Nasdaq Global Select Market           大型、成熟企業    最嚴格，需符合至少 4 套財務標準之一（         市場信任度最高       Apple, Microsoft, Amazon
                                                      淨收益、市值與現金流、市值與收入、資產與股
                                                      東權益等），通常市值 ≥ 1.6 億美金   
                                                      「藍籌級」公司，                        

Nasdaq Global Market                  中大型企業       標準略低於 Global Select，但高於             穩定中型公司
                                                      Capital Market，通常市值 ≥ 7500 萬美金       成長性與成熟度兼具    中型科技/醫療公司

Nasdaq Capital Market（舊稱 SmallCap） 小型、新創公司    最寬鬆，允許市值 ≥ 1500 萬美金，
                                                      公司股東人數 ≥ 300                          高風險高報酬          新創、生技小公司
                                                                                                 流動性可能偏低

NYSE（主板）                           大型、成熟企業    要求嚴格：市值 ≥ 4000 萬美金、股東數 ≥ 400、
                                                      連續獲利能力 傳統藍籌股市場，                 國際影響力大         Coca-Cola, JP Morgan, ExxonMobil

NYSE American（原 NYSE MKT / AMEX）    小型、新創公司    比 NYSE 主板寬鬆，適合小型與高成長公司  
                                                      高風險小型股市場，                           投資人認知類似       礦產、能源、生技小公司
                                                                                                  Nasdaq Capital 
                                                                                                  Market  
'''