# plotting.py
"""
Visualization functions for strategy analysis
"""

import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_portfolio_vs_benchmark(
    portfolio_history: pd.DataFrame,
    df: pd.DataFrame,
    benchmark_col: str = "close",
    *,
    normalize: bool = True,
    initial_cash: float = None,
    title: str = "Portfolio vs Buy-and-Hold",
    show: bool = True,
    save_path: str = None,
    ax=None,
    max_points: int = 5000,  # downsample para ploteo
):
    """
    Plot strategy portfolio value vs buy-and-hold benchmark.

    Parameters
    ----------
    portfolio_history : pd.DataFrame
        Debe contener 'portfolio_value'. Ideal si trae columna 'date'.
    df : pd.DataFrame
        Datos originales; debe contener la columna de benchmark (p.ej. 'close').
    benchmark_col : str, default 'close'
        Columna del precio para el benchmark buy-and-hold.
    normalize : bool, default True
        Si True, normaliza ambas curvas a 1 al inicio (comparación tipo índice).
        Si False y se pasa `initial_cash`, el benchmark se escala a dinero.
    initial_cash : float, optional
        Capital inicial para comparar en dinero cuando normalize=False.
    title : str
        Título del gráfico.
    show : bool
        Si True, muestra el gráfico (plt.show()).
    save_path : str, optional
        Ruta para guardar la figura (e.g. 'outputs/plot_perf.png').
    ax : matplotlib.axes.Axes, optional
        Ejes existentes para dibujar; si no, crea nueva figura.
    max_points : int
        Máximo de puntos a dibujar (downsample visual, no afecta cálculos).
    """
    # ---------- Validaciones ----------
    if "portfolio_value" not in portfolio_history.columns:
        raise ValueError("`portfolio_history` debe contener la columna 'portfolio_value'.")
    if benchmark_col not in df.columns:
        raise ValueError(f"`df` no contiene la columna '{benchmark_col}'.")

    # ---------- Alinear series por índice ----------
    port = pd.to_numeric(portfolio_history["portfolio_value"], errors="coerce").dropna()
    bench = pd.to_numeric(df[benchmark_col], errors="coerce").reindex(port.index).dropna()

    # índice común
    common_idx = port.index.intersection(bench.index)
    if len(common_idx) < 2:
        raise ValueError("Insuficientes puntos tras alinear portafolio y benchmark por índice.")

    port = port.loc[common_idx]
    bench = bench.loc[common_idx]

    # ---------- Escalas / normalización ----------
    if normalize:
        port_plot = port / float(port.iloc[0])
        bench_plot = bench / float(bench.iloc[0])
        y_label = "Normalized Value (start = 1.0)"
    else:
        if initial_cash is None:
            # escalamos el benchmark al valor inicial del portafolio
            scale = float(port.iloc[0]) / float(bench.iloc[0])
            bench_plot = bench * scale
            port_plot = port
        else:
            bench_plot = (bench / float(bench.iloc[0])) * float(initial_cash)
            port_plot = port
        y_label = "Value"

    # ---------- Helper robusto de fechas ----------
    def _as_datetime(series_like: pd.Series) -> pd.Series:
        s = series_like
        if pd.api.types.is_datetime64_any_dtype(s):
            return s
        # ISO / mixed
        try:
            return pd.to_datetime(s, format="ISO8601", errors="raise")
        except Exception:
            pass
        # con milisegundos explícitos
        try:
            return pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S.%f", errors="raise")
        except Exception:
            pass
        # genérico tolerante
        return pd.to_datetime(s, errors="coerce")

    # ---------- Construir eje X ----------
    if "date" in portfolio_history.columns:
        x_raw = portfolio_history.loc[common_idx, "date"]
        x = _as_datetime(x_raw)
    else:
        # intentamos interpretar el índice común como datetime
        try:
            x = pd.to_datetime(common_idx, errors="coerce")
        except Exception:
            # fallback: usa el índice tal cual
            x = pd.Series(common_idx, index=common_idx)

    # Armamos un DF de ploteo y filtramos filas con fechas inválidas (NaT)
    plot_df = pd.DataFrame(
        {
            "x": x,
            "port": port_plot.values,
            "bench": bench_plot.values,
        },
        index=common_idx,
    ).dropna(subset=["x"])

    if len(plot_df) < 2:
        raise ValueError("Insuficientes puntos con fechas válidas tras parseo de 'date'.")

    # ---------- Downsample visual ----------
    n = len(plot_df)
    if n > max_points:
        step = max(1, n // max_points)
        plot_df = plot_df.iloc[::step]

    # ---------- Crear axes si no existe ----------
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
        created_fig = True

    # ---------- Plot ----------
    ax.plot(plot_df["x"], plot_df["port"], label="Strategy (Portfolio)", linewidth=1.4)
    ax.plot(plot_df["x"], plot_df["bench"], label=f"Buy & Hold ({benchmark_col})", linewidth=1.1, alpha=0.9)

    # Formateador de fechas eficiente
    if pd.api.types.is_datetime64_any_dtype(plot_df["x"]):
        locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")

    # ---------- Recuadro con retornos (%), usando series originales alineadas ----------
    try:
        # usa los extremos del rango ploteado (no necesariamente todos los datos)
        p0 = plot_df["port"].iloc[0]
        p1 = plot_df["port"].iloc[-1]
        b0 = plot_df["bench"].iloc[0]
        b1 = plot_df["bench"].iloc[-1]
        port_ret = (p1 / p0 - 1.0) * 100.0
        bench_ret = (b1 / b0 - 1.0) * 100.0
        txt = f"Strategy: {port_ret: .2f}%\nBenchmark: {bench_ret: .2f}%"
        ax.text(
            0.01,
            0.99,
            txt,
            transform=ax.transAxes,
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999", alpha=0.8),
            fontsize=9,
        )
    except Exception:
        pass

    # ---------- Guardar / Mostrar ----------
    ax.set_yscale("log")

    if save_path:
        # crear carpeta si no existe
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.tight_layout()
        plt.savefig(save_path, dpi=120)

    if show and created_fig:
        # más ligero que tight_layout para grandes series
        try:
            fig.autofmt_xdate()
            plt.subplots_adjust(bottom=0.18)
        except Exception:
            pass
        plt.show()

    return ax

