import pandas as pd
import numpy as np
import ta


def make_signals(df, 
                    rsi_period=14, rsi_overbought=70, rsi_oversold=30,
                    ema_short=8, ema_long=21,
                    bb_window=20, bb_std=2):
    """
        Construye señales de compra, venta o espera utilizando tres indicadores técnicos:
        RSI, medias móviles exponenciales (EMA) y Bandas de Bollinger. 
        La decisión final se determina aplicando una regla de consenso: al menos 
        dos de los tres indicadores deben coincidir en la misma dirección.

        Parámetros
        ----------
        df : pd.DataFrame
            DataFrame con precios; debe incluir la columna 'close'. 
            Si se cuenta con 'open', 'high', 'low' o 'volume', también pueden aprovecharse en análisis posteriores.
        bb_window : int, predeterminado=20
            Número de periodos usados para calcular la media móvil central de las Bandas de Bollinger.
        bb_std : float, predeterminado=2.0
            Cantidad de desviaciones estándar empleadas para definir las bandas superior e inferior.
        rsi_period : int, predeterminado=14
            Longitud de la ventana usada para calcular el RSI.
        rsi_overbought : int, predeterminado=70
            Nivel a partir del cual el activo se considera sobrecomprado.
        rsi_oversold : int, predeterminado=30
            Nivel por debajo del cual el activo se considera sobrevendido.
        ema_short : int, predeterminado=8
            Periodo de la media móvil exponencial corta (EMA rápida).
        ema_long : int, predeterminado=21
            Periodo de la media móvil exponencial larga (EMA lenta).

        Descripción de la lógica
        ------------------------
        - **RSI:** 
            Cuando RSI < rsi_oversold → tendencia alcista (+1)
            Cuando RSI > rsi_overbought → tendencia bajista (-1)
        - **Cruce de EMAs:** 
            EMA corta > EMA larga → señal de compra (+1)
            EMA corta < EMA larga → señal de venta (-1)
        - **Bandas de Bollinger:** 
            Precio < banda inferior → señal de compra (+1)
            Precio > banda superior → señal de venta (-1)

        Los tres indicadores emiten un voto (+1 o -1). 
        Si al menos dos coinciden en dirección positiva, la señal final será 1 (long);
        si dos o más coinciden en dirección negativa, la señal será -1 (short);
        en caso contrario, la operación se mantiene en espera (0).

        Returns
        -------
        pd.DataFrame
            Mismo DataFrame de entrada con columnas adicionales de indicadores 
            y una columna 'signal' que toma valores:
                1 → señal de compra / posición larga
                0 → sin operación / mantener posición
            -1 → señal de venta / posición corta
        """
    df = df.copy()
    
    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=rsi_period).rsi()

    # EMA
    df["ema_short"] = ta.trend.EMAIndicator(close=df["close"], window=ema_short).ema_indicator()
    df["ema_long"]  = ta.trend.EMAIndicator(close=df["close"], window=ema_long).ema_indicator()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=df["close"], window=bb_window, window_dev=bb_std)
    df["bb_mid"] = bb.bollinger_mavg()
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    
    # Individual Signals
    # RSI: oversold -> +1, overbought -> -1, otherwise 0
    df["rsi_signal"] = 0
    df.loc[df["rsi"] < rsi_oversold, "rsi_signal"] = 1
    df.loc[df["rsi"] > rsi_overbought, "rsi_signal"] = -1

    # EMA crossover: short above long -> +1, short below long -> -1
    df["ema_signal"] = 0
    df.loc[df["ema_short"] > df["ema_long"], "ema_signal"] = 1
    df.loc[df["ema_short"] < df["ema_long"], "ema_signal"] = -1

    # Bollinger Bands: price below lower band -> +1, above upper band -> -1
    df["bb_signal_ind"] = 0
    df.loc[df["close"] < df["bb_lower"], "bb_signal_ind"] = 1
    df.loc[df["close"] > df["bb_upper"], "bb_signal_ind"] = -1

    # Signal confirmation (2 out of 3 indicators must agree)
    signal_sum = df['rsi_signal'] + df['ema_signal'] + df['bb_signal_ind']

    # If sum >= 2, it's a buy (at least 2 indicators say buy)
    # If sum <= -2, it's a sell (at least 2 indicators say sell)
    # Otherwise, hold
    df['signal'] = 0
    df.loc[signal_sum >= 2, 'signal'] = 1
    df.loc[signal_sum <= -2, 'signal'] = -1
    
    return df
