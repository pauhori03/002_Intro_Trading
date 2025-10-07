import optuna
import numpy as np
import pandas as pd
from signals import make_signals
from backtesting import run_backtest
from pfmn_metrics import calculate_all_metrics

# Split data function
def split_train_test(df, train_ratio=0.6, test_ratio=0.2, val_ratio=0.2):
    """
    Split data into training and testing sets
    """
    n = len(df)
    if n < 10:
        raise ValueError("DataFrame demasiado pequeño para split.")

    if train_ratio + test_ratio + val_ratio != 1.0:
        val_ratio = 1.0 - train_ratio - test_ratio
        if val_ratio <= 0:
            raise ValueError("Ratios inválidos. Asegúrate de que sumen 1 o deja val_ratio en 0.")

    i_train_end = int(n * train_ratio)
    i_test_end  = int(n * (train_ratio + test_ratio))

    train_df = df.iloc[:i_train_end].copy()
    test_df  = df.iloc[i_train_end:i_test_end].copy()
    val_df   = df.iloc[i_test_end:].copy()

    return train_df, test_df, val_df

# Objective function (maximize Calmar ratio)
def objective(trial, df):
    """
    Optuna objective function to maximize Calmar ratio
    """
    # Hyperparameters
    rsi_period = trial.suggest_int('rsi_period', 10, 30)
    rsi_overbought = trial.suggest_int('rsi_overbought', 65, 80)
    rsi_oversold = trial.suggest_int('rsi_oversold', 20, 35)
    
    ema_short = trial.suggest_int('ema_short', 10, 25)
    ema_long = trial.suggest_int('ema_long', 30, 80)
    
    bb_window = trial.suggest_int('bb_window', 10, 40)
    bb_std = trial.suggest_float('bb_std', 1.5, 3.0)
    
    n_shares = trial.suggest_float('n_shares', 0.5, 5.0)
    stop_loss_pct = trial.suggest_float('stop_loss_pct', 0.03, 0.06)
    take_profit_pct = trial.suggest_float('take_profit_pct', 0.12, 0.25)
    
    # Build parameter dictionaries
    rsi_params = {
        'period': rsi_period,
        'overbought': rsi_overbought,
        'oversold': rsi_oversold
    }
    
    ema_params = {
        'short_period': ema_short,
        'long_period': ema_long
    }
    
    bb_params = {
        'window': bb_window,
        'std': bb_std
    }
    
    # Generate signals
    try:
        df_sig = make_signals(
            df,
            rsi_period=rsi_params['period'],
            rsi_overbought=rsi_params['overbought'],
            rsi_oversold=rsi_params['oversold'],
            ema_short=ema_params['short_period'],
            ema_long=ema_params['long_period'],
            bb_window=bb_params['window'],
            bb_std=bb_params['std']
        )
    except Exception:
        return -1e6
    
    # Run backtest
    try:
        df_bt, _final_capital = run_backtest(
            df_sig,
            stop_loss=stop_loss_pct,
            take_profit=take_profit_pct,
            n_shares=n_shares,
            com=0.125/100,
            borrow_rate=0.25/100,
            price_col="close",
            initial_cash=1_000_000
        )
    except Exception:
        return -1e6
    
    # Calculate metrics
    metrics = calculate_all_metrics(df_bt, risk_free_rate=0.0, bars_per_year=24*365)
    calmar = metrics.get("calmar_ratio", np.nan)

    # Ensure at least 5 closed trades to consider valid
    closed_trades = int(df_bt.get("trade_pnl", pd.Series(dtype=float)).dropna().shape[0]) \
                    if "trade_pnl" in df_bt.columns else 0
    if closed_trades < 5:
        return -1e6

    if calmar is None or np.isnan(calmar):
        return -1e6

    # Guarda info útil del trial para inspección
    trial.set_user_attr("closed_trades", closed_trades)
    trial.set_user_attr("total_return", metrics.get("total_return"))
    trial.set_user_attr("sharpe_ratio", metrics.get("sharpe_ratio"))
    trial.set_user_attr("max_drawdown", metrics.get("max_drawdown"))
    trial.set_user_attr("win_rate", metrics.get("win_rate"))

    return float(calmar)
    
  
# Run optimization
def optimize_strategy(df, n_trials=100, n_jobs=1,
                      train_ratio=0.6, test_ratio=0.2, val_ratio=0.2,
                      use_pruner=True):
    """
    Run Optuna optimization
    """
    
    if n_trials < 50:
        n_trials = 50

    # Split temporal
    train_df, test_df, val_df = split_train_test(df, train_ratio, test_ratio, val_ratio)

    # Estudio Optuna
    pruner = optuna.pruners.MedianPruner() if use_pruner else None
    study = optuna.create_study(direction='maximize', study_name="btc_strategy_calmar", pruner=pruner)

    # Objective envuelto para optimizar en VALIDACIÓN (no en train)
    def _obj(trial):
        return objective(trial, df=val_df)

    # Ejecuta
    study.optimize(_obj, n_trials=n_trials, n_jobs=n_jobs, show_progress_bar=False)

    return study, study.best_params, (train_df, test_df, val_df)

# Print optimization results
def print_optimization_results(study: optuna.Study):
    """
    Print optimization results
    """
    print("\n=== OPTIMIZATION RESULTS (maximize Calmar) ===")
    print(f"Best Calmar: {study.best_value:.6f}")
    print("Best params:")
    for k, v in study.best_params.items():
        print(f"  - {k}: {v}")


def evaluate_on_df(df, params):
    df_sig = make_signals(
        df,
        rsi_period=params['rsi_period'],
        rsi_overbought=params['rsi_overbought'],
        rsi_oversold=params['rsi_oversold'],
        ema_short=params['ema_short'],
        ema_long=params['ema_long'],
        bb_window=params['bb_window'],
        bb_std=params['bb_std'],
    )
    df_bt, final_capital = run_backtest(
        df_sig,
        stop_loss=params['stop_loss_pct'],
        take_profit=params['take_profit_pct'],
        n_shares=params['n_shares'],
        com=0.125/100,
        borrow_rate=0.25/100,
        price_col="close",
        initial_cash=1_000_000,
    )
    metrics = calculate_all_metrics(df_bt, risk_free_rate=0.0, bars_per_year=24*365)
    return df_bt, final_capital, metrics

