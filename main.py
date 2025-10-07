"""
Main pipeline orchestrator - runs the complete workflow
"""
import pandas as pd
import numpy as np
import ta
# from data import load_bitcoin_data
from signals import make_signals
# from backtest import run_backtest
# from metrics import calculate_metrics
# from visualization import plot_results
# from optimization import optimize_strategy

df = pd.read_csv("data/Binance_BTCUSDT_1h.csv")
df = df.iloc[::-1].reset_index(drop=True)
df.columns = df.columns.str.strip().str.lower()
print(df.head())

# Generate buy/sell signals
df_signals = make_signals(df)
print(df_signals.head(20))
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
