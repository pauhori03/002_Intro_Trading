"""
Main pipeline orchestrator - runs the complete workflow
"""
import pandas as pd
import numpy as np
import ta
# from data import load_bitcoin_data
from signals import make_signals
from backtesting import run_backtest
from pfmn_metrics import calculate_all_metrics
# from visualization import plot_results
# from optimization import optimize_strategy

df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
df = df.iloc[::-1].reset_index(drop=True)
df.columns = df.columns.str.strip().str.lower()
print(df.head())

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


# def main():
# """
#     Main pipeline execution
#     Only prints summary results, no calculations here
#     """
#     # Load data


    # Generate signals with default or optimized parameters
    
    # Run backtest
    
    # Calculate metrics
    
    # Print summary
    # print("=" * 60)
    # print("STRATEGY PERFORMANCE SUMMARY")
    # print("=" * 60)
    # Print returns, ratios, win rate, max drawdown, etc.
    
    # Visualize results
    

# def main_with_optimization():
#     """
#     Pipeline with hyperparameter optimization
#     """
#     # Load data

#     # Run optimization
    
    # Use best parameters for final backtest
    
    # Print optimized results


#if __name__ == "__main__":
    # main()
