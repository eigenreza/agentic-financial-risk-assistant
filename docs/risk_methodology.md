# Risk Methodology

This document describes the statistical methods used by the Agentic Financial Risk Assistant to analyse financial time-series data. All metrics are computed from daily closing prices using verified Python functions in `src/risk/`.

---

## 1. Returns

### Simple returns
The percentage change in price from one day to the next:

```
r_t = (P_t - P_{t-1}) / P_{t-1}
```

Simple returns are used for VaR, Expected Shortfall, and summary statistics because they are directly interpretable as percentage gains or losses.

### Log returns
The continuously compounded return:

```
r_t = ln(P_t / P_{t-1})
```

Log returns are used for volatility calculations because they are time-additive and better approximate normality over short horizons.

### Cumulative returns
The total return from the first observed price to a given date:

```
CR_t = product(1 + r_i for i in 1..t) - 1
```

---

## 2. Volatility

### Daily volatility
The standard deviation of log returns:

```
sigma_daily = std(ln(P_t / P_{t-1}))
```

### Annualised volatility
Daily volatility scaled to an annual basis using the square-root-of-time rule:

```
sigma_annual = sigma_daily * sqrt(252)
```

The convention of 252 trading days per year is standard for equity and commodity markets.

### Rolling volatility
The annualised volatility computed over a rolling window (default: 21 trading days, approximately one calendar month):

```
sigma_rolling(t, w) = std(log_returns[t-w:t]) * sqrt(252)
```

Rolling volatility reveals changes in risk level over time, including stress periods.

**Limitations:**
- Volatility is backward-looking. It measures past price variation, not future risk.
- The square-root-of-time scaling assumes returns are independently and identically distributed — an assumption that breaks down during volatility clustering.
- A longer estimation window provides a more stable estimate but is slower to react to regime changes.

---

## 3. Drawdown

### Drawdown series
At each point in time, the drawdown measures the percentage decline from the most recent peak:

```
DD_t = (P_t - max(P_1, ..., P_t)) / max(P_1, ..., P_t)
```

Drawdown values are always <= 0. A drawdown of -0.30 means the price is 30% below its most recent peak.

### Maximum drawdown
The worst peak-to-trough decline over the entire period:

```
MDD = min(DD_t for all t)
```

Maximum drawdown is widely used as a measure of downside risk and the psychological difficulty of holding through a losing period.

**Limitations:**
- Maximum drawdown is path-dependent and sensitive to the start and end dates of the analysis period.
- It does not indicate the time required to recover from the trough.
- Past maximum drawdown underestimates future drawdown if the analysis window does not include a severe market stress event.

---

## 4. Value-at-Risk (VaR)

VaR answers: "What is the maximum loss I should expect to not exceed on X% of trading days?"

### Historical simulation VaR
Ranks all observed daily simple returns and takes the empirical quantile:

```
VaR(confidence) = -percentile(simple_returns, (1 - confidence) * 100)
```

A 95% historical VaR of 3% means that on 95% of historical trading days, the daily loss did not exceed 3%.

### Parametric (Gaussian) VaR
Assumes returns are normally distributed with observed mean and standard deviation:

```
VaR(confidence) = -(mu - z * sigma)
```

where `z` is the standard normal quantile at the confidence level (e.g. z = 1.645 for 95%).

**Limitations:**
- Historical VaR assumes future returns follow the same distribution as the sample period. It underestimates risk if the sample period was unusually calm.
- Parametric VaR assumes normality. Financial returns have fat tails — extreme losses occur more often than the normal distribution predicts.
- Both are one-day, single-asset estimates. They do not account for multi-day holding periods, liquidity risk, or portfolio correlation.
- VaR does not describe the size of losses beyond the threshold.

---

## 5. Expected Shortfall (CVaR)

Expected Shortfall answers: "Given that my loss exceeds the VaR threshold, what is the average loss?"

```
ES(confidence) = -mean(simple_returns where return <= -VaR(confidence))
```

ES is always >= VaR. It is considered a more complete measure of tail risk because it quantifies the severity of extreme losses, not just their probability threshold.

**Limitations:**
- Historical ES is highly sensitive to extreme observations in the tail.
- Small samples produce unreliable ES estimates.
- Like VaR, it is backward-looking.

---

## 6. Rolling risk metrics

### Rolling mean return
The annualised average return over a rolling window:

```
mean_return_rolling(t, w) = mean(simple_returns[t-w:t]) * 252
```

### Rolling VaR
The historical VaR computed over a rolling lookback window (default: 63 trading days, approximately one quarter):

```
VaR_rolling(t, w) = -percentile(simple_returns[t-w:t], (1 - confidence) * 100)
```

### Stress-period flag
A Boolean series that marks periods where rolling volatility exceeds 1.5 times the full-period average rolling volatility:

```
stress(t) = (rolling_vol(t) > 1.5 * mean(rolling_vol))
```

This provides a simple, model-free identification of elevated-risk regimes.

---

## 7. Important caveats for all metrics

1. **All metrics are backward-looking.** They describe past statistical behaviour, not future outcomes.
2. **Sample period matters.** A sample that excludes a major crisis (e.g. 2008, 2020) will underestimate extreme risk.
3. **Single-asset analysis.** No portfolio diversification effects are modelled.
4. **No transaction costs.** Returns are gross of fees and market impact.
5. **Data quality.** Results are only as reliable as the input price series. Missing values, corporate actions, and currency effects can distort estimates.
6. **This analysis does not constitute investment advice.**
