import scipy.stats as stats

# 設定參數
lambda_ =10   # Poisson 分配的 λ（期望
k = 3  # 欲計算的值

# 計算 CDF
k5 = stats.poisson.pmf(5, lambda_)

k4 = stats.poisson.cdf(4, lambda_)
k3 = stats.poisson.cdf(3, lambda_)
k2 = stats.poisson.cdf(2, lambda_)
k1 = stats.poisson.cdf(1, lambda_)
k0 = stats.poisson.cdf(0, lambda_)

cdf = k5 + k4 + k3 + k2 + k1 + k0

print(f"Poisson 分配的 CDF 在 k={k}，λ={lambda_} 的值為: {cdf}")
print(k5)