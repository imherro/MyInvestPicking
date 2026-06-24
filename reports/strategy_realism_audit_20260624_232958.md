# Strategy Realism Audit

Generated at: 2026-06-24T23:29:58
Top N: 20

## Validation Summary

Status: passed

Completed checks:
- A1_multi_date_strategy_realism
- A1_historical_vs_current_split
- A2_signal_churn_overfit_check
- A2_regime_dependency_check
- A3_transaction_cost_pressure
- A4_extreme_regime_windows
- A5_signal_consistency_audit
- A6_equity_drawdown_exposure_curves
- real_data_mode_check

## Snapshot Results

### 2020-03-23
Source: tushare | Mock mode: False
Regime: crash | Confidence: 1.0
Signals: BUY 0, HOLD 0, NO_TRADE 20 | Buy exposure: 0
Backtest: CAGR -0.008013, Sharpe -0.04928, MDD -0.02525, Turnover 8.9
Top signals: 600399.SH NO_TRADE 0.8189, 600021.SH NO_TRADE 0.8174, 601139.SH NO_TRADE 0.8084, 600475.SH NO_TRADE 0.8024, 600874.SH NO_TRADE 0.7926

### 2022-10-31
Source: tushare | Mock mode: False
Regime: range | Confidence: 0.621
Signals: BUY 18, HOLD 2, NO_TRADE 0 | Buy exposure: 0.764909
Backtest: CAGR 0.236658, Sharpe 1.218863, MDD -0.077253, Turnover 2.6
Top signals: 300230.SZ BUY 0.8222, 601555.SH BUY 0.822, 688009.SH BUY 0.8212, 601108.SH BUY 0.8163, 600718.SH BUY 0.8134

### 2024-02-05
Source: tushare | Mock mode: False
Regime: crash | Confidence: 1.0
Signals: BUY 12, HOLD 0, NO_TRADE 8 | Buy exposure: 0.24
Backtest: CAGR 0.090073, Sharpe 1.47313, MDD -0.023059, Turnover 8.9
Top signals: 601939.SH BUY 0.8549, 603077.SH BUY 0.8461, 601006.SH BUY 0.844, 600919.SH BUY 0.8348, 000983.SZ BUY 0.8262

### 2026-06-24
Source: tushare | Mock mode: False
Regime: range | Confidence: 0.55
Signals: BUY 0, HOLD 0, NO_TRADE 20 | Buy exposure: 0
Backtest: CAGR -0.2823, Sharpe -2.000676, MDD -0.099264, Turnover 2.6
Top signals: 000728.SZ NO_TRADE 0.8265, 600713.SH NO_TRADE 0.8201, 603456.SH NO_TRADE 0.8152, 601901.SH NO_TRADE 0.7983, 600999.SH NO_TRADE 0.7891


## Signal Stability

Average BUY overlap Jaccard: 0.0
- 2020-03-23 -> 2022-10-31: overlap 0.0 (0 buys -> 18 buys)
- 2022-10-31 -> 2024-02-05: overlap 0.0 (18 buys -> 12 buys)
- 2024-02-05 -> 2026-06-24: overlap 0.0 (12 buys -> 0 buys)

## Cost Stress

### 2020-03-23
Base CAGR: -0.008013, Sharpe: -0.04928, Max drawdown: -0.02525
- Slippage 0.001: estimated CAGR -0.016913
- Slippage 0.003: estimated CAGR -0.034713
- Slippage 0.005: estimated CAGR -0.052513
### 2022-10-31
Base CAGR: 0.236658, Sharpe: 1.218863, Max drawdown: -0.077253
- Slippage 0.001: estimated CAGR 0.234058
- Slippage 0.003: estimated CAGR 0.228858
- Slippage 0.005: estimated CAGR 0.223658
### 2024-02-05
Base CAGR: 0.090073, Sharpe: 1.47313, Max drawdown: -0.023059
- Slippage 0.001: estimated CAGR 0.081173
- Slippage 0.003: estimated CAGR 0.063373
- Slippage 0.005: estimated CAGR 0.045573
### 2026-06-24
Base CAGR: -0.2823, Sharpe: -2.000676, Max drawdown: -0.099264
- Slippage 0.001: estimated CAGR -0.2849
- Slippage 0.003: estimated CAGR -0.2901
- Slippage 0.005: estimated CAGR -0.2953

## Regime Audit

{
  "regime_counts": {
    "crash": 2,
    "range": 2
  },
  "average_buy_exposure_by_regime": {
    "crash": 0.12,
    "range": 0.382454
  }
}

## Boundary

This audit validates the signal layer with real Tushare data where available. It does not connect execution, broker accounts, or live order routing.
