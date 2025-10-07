"""
Technical indicators and trading signal generation
"""

import pandas as pd
import numpy as np


def generate_signals(df, 
                    rsi_period=14, rsi_overbought=70, rsi_oversold=30,
                    ema_short=12, ema_long=26,
                    macd_fast=12, macd_slow=26, macd_signal=9):
    """
    Generate trading signals based on RSI, EMA, and MACD indicators.
    Final signal requires 2 out of 3 indicators to agree.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Must contain 'close' column
    rsi_period : int
        Period for RSI calculation
    rsi_overbought : int
        RSI overbought threshold
    rsi_oversold : int
        RSI oversold threshold
    ema_short : int
        Short EMA period
    ema_long : int
        Long EMA period
    macd_fast : int
        MACD fast period
    macd_slow : int
        MACD slow period
    macd_signal : int
        MACD signal line period
    
    Returns:
    --------
    pd.DataFrame
        Original dataframe with added indicator columns and final 'signal' column
        signal: 1 (buy), 0 (hold), -1 (sell)
    """
    df = df.copy()
    
    # ========== RSI Calculation ==========
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # RSI Signal: 1 (buy) if oversold, -1 (sell) if overbought, 0 (hold) otherwise
    df['rsi_signal'] = 0
    df.loc[df['rsi'] < rsi_oversold, 'rsi_signal'] = 1
    df.loc[df['rsi'] > rsi_overbought, 'rsi_signal'] = -1
    
    # ========== EMA Calculation ==========
    df['ema_short'] = df['close'].ewm(span=ema_short, adjust=False).mean()
    df['ema_long'] = df['close'].ewm(span=ema_long, adjust=False).mean()
    
    # EMA Signal: 1 (buy) if short > long, -1 (sell) if short < long
    df['ema_signal'] = 0
    df.loc[df['ema_short'] > df['ema_long'], 'ema_signal'] = 1
    df.loc[df['ema_short'] < df['ema_long'], 'ema_signal'] = -1
    
    # ========== MACD Calculation ==========
    ema_fast = df['close'].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=macd_slow, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=macd_signal, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # MACD Signal: 1 (buy) if MACD > signal, -1 (sell) if MACD < signal
    df['macd_signal_ind'] = 0
    df.loc[df['macd'] > df['macd_signal'], 'macd_signal_ind'] = 1
    df.loc[df['macd'] < df['macd_signal'], 'macd_signal_ind'] = -1
    
    # ========== Consensus Signal (2 out of 3) ==========
    signal_sum = df['rsi_signal'] + df['ema_signal'] + df['macd_signal_ind']
    
    # If sum >= 2, it's a buy (at least 2 indicators say buy)
    # If sum <= -2, it's a sell (at least 2 indicators say sell)
    # Otherwise, hold
    df['signal'] = 0
    df.loc[signal_sum >= 2, 'signal'] = 1
    df.loc[signal_sum <= -2, 'signal'] = -1
    
    return df