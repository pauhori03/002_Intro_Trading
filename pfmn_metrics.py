"""
Performance metrics calculation
"""

import numpy as np
import pandas as pd

# Frecuencia anual para datos horarios (BTC 24/7)
BARS_PER_YEAR_DEFAULT = 365 * 24


# -------------------------
# Funciones base (tus versiones)
# -------------------------
def max_drawdown(equity: pd.Series):
    eq = pd.to_numeric(equity, errors="coerce").dropna()
    roll_max = eq.cummax()
    dd = eq / roll_max - 1.0
    return dd.min(), dd  # min es negativo (p.ej. -0.35)

def cagr(equity: pd.Series, bars_per_year: int):
    eq = pd.to_numeric(equity, errors="coerce").dropna()
    if len(eq) < 2:
        return np.nan
    years = len(eq) / bars_per_year
    if years <= 0:
        return np.nan
    total_ret = eq.iloc[-1] / eq.iloc[0] - 1.0
    return (1.0 + total_ret) ** (1.0 / years) - 1.0

def sharpe_ratio(returns: pd.Series, bars_per_year: int, rf: float = 0.0):
    r = pd.to_numeric(returns, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if r.std(ddof=0) == 0 or len(r) == 0:
        return np.nan
    rf_bar = rf / bars_per_year  # rf anual a por-barra
    excess = r - rf_bar
    return np.sqrt(bars_per_year) * excess.mean() / excess.std(ddof=0)

def sortino_ratio(returns: pd.Series, bars_per_year: int, rf: float = 0.0):
    r = pd.to_numeric(returns, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(r) == 0:
        return np.nan
    rf_bar = rf / bars_per_year
    excess = r - rf_bar
    downside = excess[excess < 0]
    if downside.std(ddof=0) == 0 or len(downside) == 0:
        return np.nan
    return np.sqrt(bars_per_year) * excess.mean() / downside.std(ddof=0)

def calmar_ratio(equity: pd.Series, bars_per_year: int):
    cg = cagr(equity, bars_per_year)
    mdd, _ = max_drawdown(equity)
    denom = abs(mdd)
    if denom == 0 or np.isnan(denom):
        return np.nan
    return cg / denom

def win_rate(portfolio_hist: pd.DataFrame) -> float:
    if "trade_pnl" not in portfolio_hist.columns:
        return np.nan
    s = portfolio_hist["trade_pnl"].dropna()
    if s.empty:
        return np.nan
    wins = (s > 0).sum()
    losses = (s < 0).sum()
    total = wins + losses
    return (wins / total) if total > 0 else np.nan


# -------------------------
# Helpers mínimos para este módulo
# -------------------------
def _returns_from_portfolio(df: pd.DataFrame) -> pd.Series:
    """Retornos simples por barra a partir de la columna 'portfolio_value'."""
    if "portfolio_value" not in df.columns:
        raise KeyError("'portfolio_value' column not found in portfolio_hist")
    return df["portfolio_value"].pct_change().dropna()

def _total_return(df: pd.DataFrame) -> float:
    """Equity final / inicial - 1"""
    if "portfolio_value" not in df.columns:
        raise KeyError("'portfolio_value' column not found in portfolio_hist")
    eq = df["portfolio_value"]
    if len(eq) < 2:
        return np.nan
    return float(eq.iloc[-1] / eq.iloc[0] - 1.0)


# -------------------------
# API principal
# -------------------------
def calculate_all_metrics(portfolio_hist: pd.DataFrame,
                          risk_free_rate: float = 0.0,
                          bars_per_year: int = 365*24) -> dict:
    returns = portfolio_hist["portfolio_value"].pct_change().dropna()

    total_ret = portfolio_hist["portfolio_value"].iloc[-1] / portfolio_hist["portfolio_value"].iloc[0] - 1.0
    sh = sharpe_ratio(returns, bars_per_year=bars_per_year, rf=risk_free_rate)
    so = sortino_ratio(returns, bars_per_year=bars_per_year, rf=risk_free_rate)
    mdd, _ = max_drawdown(portfolio_hist["portfolio_value"])
    cal = calmar_ratio(portfolio_hist["portfolio_value"], bars_per_year=bars_per_year)
    wr = win_rate(portfolio_hist)  # <-- aquí

    return {
        "total_return": total_ret,
        "sharpe_ratio": sh,
        "sortino_ratio": so,
        "max_drawdown": mdd,
        "calmar_ratio": cal,
        "win_rate": wr,
    }