"""
Data loading and preprocessing
"""

import pandas as pd


def load_bitcoin_data(filepath="bitcoin_hourly.csv"):
    """
    Load Bitcoin hourly price data from CSV
    
    Parameters:
    -----------
    filepath : str
        Path to the CSV file
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with timestamp, open, high, low, close, volume
    """
    pass




def split_train_test(df, train_ratio=0.6, test_ratio=0.2, val_ratio=0.2):
    """
    Split data into training and testing sets
    
    Parameters:
    -----------
    df : pd.DataFrame
    train_ratio : float
    test_ratio : float
    val_ratio : float
    
    Returns:
    --------
    tuple
        (train_df, test_df, val_df)
    """
    pass