import yfinance as yf
import ta
import pywt
import numpy as np
import matplotlib.pyplot as plt

df = yf.download("AAPL", period="2y")
macd = ta.trend.MACD(df['Close'].squeeze())
hist = macd.macd_diff()

hist_1d = np.array(hist).flatten()
coeffs = pywt.wavedec(hist_1d, 'db4', level=2)
coeffs[1:] = [np.zeros_like(c) for c in coeffs[1:]]
hist_denoised = pywt.waverec(coeffs, 'db4')

n = min(len(hist), len(hist_denoised))
plt.plot(hist.index[:n], hist_1d[:n], label='Original MACD Histogram', alpha=0.5)
plt.plot(hist.index[:n], hist_denoised[:n], label='Smoothed Wavelet', lw=2)
plt.legend()
plt.show()