"""
Main pipeline orchestrator - runs the complete workflow
"""

from data import load_bitcoin_data
from signals import generate_signals
from backtest import run_backtest
from metrics import calculate_metrics
from visualization import plot_results
from optimization import optimize_strategy


def main():
    """
    Main pipeline execution
    Only prints summary results, no calculations here
    """
    # Load data
    
    # Generate signals with default or optimized parameters
    
    # Run backtest
    
    # Calculate metrics
    
    # Print summary
    print("=" * 60)
    print("STRATEGY PERFORMANCE SUMMARY")
    print("=" * 60)
    # Print returns, ratios, win rate, max drawdown, etc.
    
    # Visualize results
    

def main_with_optimization():
    """
    Pipeline with hyperparameter optimization
    """
    # Load data
    
    # Run optimization
    
    # Use best parameters for final backtest
    
    # Print optimized results


if __name__ == "__main__":
    main()
