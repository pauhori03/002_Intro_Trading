# visualization.py
"""
Visualization functions for strategy analysis
"""

import matplotlib.pyplot as plt
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
):
    """
    Plot strategy portfolio value vs buy-and-hold benchmark.

    Parameters
    ----------
    portfolio_history : pd.DataFrame
        Debe contener la columna 'portfolio_value' (salida de tu backtest).
        Idealmente también la columna 'date' para etiquetar el eje X (no obligatorio).
    df : pd.DataFrame
        DataFrame original con precios; debe contener la columna `benchmark_col` (p.ej. 'close').
        Se reindexa/realinea por índice con `portfolio_history`.
    benchmark_col : str, default 'close'
        Columna del precio para el benchmark buy-and-hold.
    normalize : bool, default True
        Si True, dibuja ambos normalizados a 1 en el inicio.
        Si False y `initial_cash` se provee, dibuja el benchmark en unidades monetarias comparables.
    initial_cash : float, optional
        Capital inicial para convertir el benchmark a valor monetario cuando normalize=False.
        Si normalize=True, este parámetro se ignora.
    title : str, default "Portfolio vs Buy-and-Hold"
        Título del gráfico.
    show : bool, default True
        Si True, hace plt.show() al final.
    save_path : str, optional
        Ruta para guardar la figura (p.ej. 'outputs/port_vs_bh.png').
    ax : matplotlib.axes.Axes, optional
        Ejes existentes; si no se pasa, crea una figura nueva.

    Returns
    -------
    matplotlib.axes.Axes
        Ejes con el plot.
    """
    if "portfolio_value" not in portfolio_history.columns:
        raise ValueError("`portfolio_history` debe contener la columna 'portfolio_value'.")

    if benchmark_col not in df.columns:
        raise ValueError(f"`df` no contiene la columna '{benchmark_col}' para el benchmark.")

    # Asegurar Series limpias y alineadas por índice
    port = pd.to_numeric(portfolio_history["portfolio_value"], errors="coerce").dropna()
    bench = pd.to_numeric(df[benchmark_col], errors="coerce").reindex(port.index).dropna()

    # Re-alinear port al índice de bench si al reindex se perdieron puntos
    # (tomamos el índice común)
    common_idx = port.index.intersection(bench.index)
    port = port.loc[common_idx]
    bench = bench.loc[common_idx]

    if len(port) < 2 or len(bench) < 2:
        raise ValueError("No hay suficientes puntos tras alinear portafolio y benchmark.")

    # Normalizaciones / escalas
    if normalize:
        port_plot = port / float(port.iloc[0])
        bench_plot = bench / float(bench.iloc[0])
        y_label = "Normalized Value (start = 1.0)"
    else:
        if initial_cash is None:
            # Si no nos dan initial_cash, igual normalizamos el benchmark al valor inicial del portafolio
            scale = float(port.iloc[0]) / float(bench.iloc[0])
            bench_plot = bench * scale
            port_plot = port
            y_label = "Value"
        else:
            bench_plot = (bench / float(bench.iloc[0])) * float(initial_cash)
            port_plot = port
            y_label = "Value"

    # Eje X: si hay fecha, úsala para ticks más bonitos
    x = portfolio_history.loc[common_idx, "date"] if "date" in portfolio_history.columns else common_idx

    # Crear axes si no existe
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
        created_fig = True

    ax.plot(x, port_plot, label="Strategy (Portfolio)", linewidth=1.6)
    ax.plot(x, bench_plot, label=f"Buy & Hold ({benchmark_col})", linewidth=1.2, alpha=0.85)
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(y_label)
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")

    # Pequeño recuadro con resultados finales
    def _pct(a, b):  # retorno total %
        return (a / b - 1.0) * 100.0

    try:
        port_ret = _pct(port.iloc[-1], port.iloc[0])
        bench_ret = _pct(bench.iloc[-1], bench.iloc[0])
        txt = f"Strategy: {port_ret: .2f}%\nBenchmark: {bench_ret: .2f}%"
        ax.text(0.01, 0.99, txt, transform=ax.transAxes, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999", alpha=0.8), fontsize=9)
    except Exception:
        pass

    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=120)

    if show and created_fig:
        plt.tight_layout()
        plt.show()

    return ax
