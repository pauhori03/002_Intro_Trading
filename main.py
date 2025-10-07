"""
Main pipeline orchestrator - runs the complete workflow
"""
import pandas as pd
import numpy as np
import ta
from plotting import plot_portfolio_vs_benchmark
from signals import make_signals
from backtesting import run_backtest
from pfmn_metrics import calculate_all_metrics
# from visualization import plot_results
from optimization import optimize_strategy, print_optimization_results, split_train_test, evaluate_on_df

df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
df = df.iloc[::-1].reset_index(drop=True)
df.columns = df.columns.str.strip().str.lower()



# Generate buy/sell signals
df_signals = make_signals(df)

# Run backtest
df_bt, final_capital = run_backtest(
    df_signals,
    stop_loss=0.02,
    take_profit=0.04,
    n_shares=1,
    com=0.125/100,
    borrow_rate=0.25/100,
    price_col="close",
    initial_cash=1_000_000
)

print(f"Final portfolio value (capital): {final_capital:,.2f}")
print(df_bt[["date", "close", "portfolio_value"]].tail())

# Calculate performance metrics
metrics = calculate_all_metrics(df_bt, risk_free_rate=0.0, bars_per_year=24 * 365)

print("PERFORMANCE SUMMARY")
print("-" * 40)
for k, v in metrics.items():
    print(f"{k}: {v}")

# Run optimization
study, best_params, (df_train, df_test, df_val) = optimize_strategy(
    df,           # pásale el DF crudo (sin señales)
    n_trials=120, # > 50 like you asked
    n_jobs=1      # pon >1 si tu entorno lo soporta
)
print_optimization_results(study)

# Run final backtest with best params on test set
df_train, df_test, df_val = split_train_test(df)
df_holdout = df_test  # o test verdadero
df_bt_test, cash_test, m_test = evaluate_on_df(df_holdout, best_params)

print("\n=== TEST METRICS ===")
for k, v in m_test.items():
    if k in ("total_return","max_drawdown","win_rate"): 
        print(f"{k}: {float(v)*100:.2f}%")
    else:
        print(f"{k}: {float(v):.4f}")
print(f"Final portfolio (test): {cash_test:,.2f}")

# Plot portfolio vs benchmark
plot_portfolio_vs_benchmark(
    portfolio_history=df_bt,
    df=df,
    benchmark_col="close",
    normalize=True,
    title="Estrategia vs Buy & Hold (BTC/USDT)",
    save_path="outputs/plot_perf.png"  # o None si no quieres guardar
)