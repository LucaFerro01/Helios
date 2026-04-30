"""
Visualizzazione grafica dei risultati della simulazione HeliosSim.

Genera grafici professionali e leggibili per:
- Produzione e consumi orari
- Stato di carica batteria
- Flussi energetici
- KPI energetici ed economici
- Comparazione tra scenari
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from pathlib import Path


def setup_plotting_style():
    """Configura lo stile globale dei grafici."""
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': '#f9f9f9',
        'axes.grid': True,
        'grid.color': '#e0e0e0',
        'grid.linewidth': 0.6,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'font.size': 10,
        'legend.framealpha': 0.95,
    })


def plot_hourly_profile(
    idx: pd.DatetimeIndex,
    pv_arr: np.ndarray,
    load_arr: np.ndarray,
    grid_in_arr: np.ndarray,
    grid_out_arr: np.ndarray,
    title: str = "Profilo Orario Energetico",
    figsize: Tuple[int, int] = (14, 6)
) -> plt.Figure:
    """
    Grafico del profilo orario: produzione PV, consumi, flussi rete.
    
    Args:
        idx: indice temporale
        pv_arr: produzione PV [kWh]
        load_arr: carico [kWh]
        grid_in_arr: acquisti rete [kWh]
        grid_out_arr: vendite rete [kWh]
        title: titolo del grafico
        figsize: dimensioni figura
    
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Seleziona una settimana di dati (più leggibile)
    n_days = 7
    n_points = n_days * 24
    idx_7d = idx[:n_points]
    pv_7d = pv_arr[:n_points]
    load_7d = load_arr[:n_points]
    grid_in_7d = grid_in_arr[:n_points]
    grid_out_7d = grid_out_arr[:n_points]
    
    # Grafico
    ax.plot(idx_7d, pv_7d * 1000, 'o-', linewidth=2, markersize=2, 
            label='Produzione PV', color='#FDB462')
    ax.plot(idx_7d, load_7d * 1000, 'o-', linewidth=2, markersize=2,
            label='Consumo', color='#80B1D3')
    ax.fill_between(idx_7d, 0, grid_in_7d * 1000, alpha=0.3, color='red',
                     label='Acquisto rete')
    ax.fill_between(idx_7d, 0, -grid_out_7d * 1000, alpha=0.3, color='green',
                     label='Vendita rete')
    
    ax.set_xlabel('Data e ora')
    ax.set_ylabel('Potenza [W]')
    ax.set_title(title)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Formattazione asse x
    fig.autofmt_xdate(rotation=45, ha='right')
    
    return fig


def plot_battery_soc(
    idx: pd.DatetimeIndex,
    soc_arr: np.ndarray,
    soc_min: float,
    soc_max: float,
    title: str = "Stato di Carica Batteria (30 giorni)",
    figsize: Tuple[int, int] = (14, 5)
) -> plt.Figure:
    """
    Grafico dello stato di carica della batteria nel tempo.
    
    Args:
        idx: indice temporale
        soc_arr: SOC [kWh]
        soc_min: SOC minimo [kWh]
        soc_max: SOC massimo [kWh]
        title: titolo del grafico
        figsize: dimensioni figura
    
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Seleziona 30 giorni
    n_points = min(30 * 24, len(soc_arr))
    idx_30d = idx[:n_points]
    soc_30d = soc_arr[:n_points]
    
    # Converti in percentuale
    soc_pct = soc_30d / soc_max * 100
    
    ax.fill_between(idx_30d, soc_pct, alpha=0.3, color='#80B1D3')
    ax.plot(idx_30d, soc_pct, linewidth=2, color='#80B1D3', label='SOC')
    
    # Linee di soglia
    soc_min_pct = soc_min / soc_max * 100
    soc_max_pct = soc_max / soc_max * 100
    ax.axhline(soc_min_pct, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Min SOC')
    ax.axhline(soc_max_pct, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Max SOC')
    
    ax.set_xlabel('Data')
    ax.set_ylabel('SOC [%]')
    ax.set_title(title)
    ax.set_ylim([0, 105])
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    fig.autofmt_xdate(rotation=45, ha='right')
    
    return fig


def plot_monthly_energy(
    idx: pd.DatetimeIndex,
    pv_arr: np.ndarray,
    load_arr: np.ndarray,
    grid_in_arr: np.ndarray,
    grid_out_arr: np.ndarray,
    bat_ch_arr: np.ndarray,
    bat_dch_arr: np.ndarray,
    title: str = "Bilancio Energetico Mensile",
    figsize: Tuple[int, int] = (14, 6)
) -> plt.Figure:
    """
    Grafico del bilancio energetico mensile (aggregato per mesi).
    
    Args:
        idx: indice temporale
        pv_arr: produzione PV [kWh]
        load_arr: carico [kWh]
        grid_in_arr: acquisti [kWh]
        grid_out_arr: vendite [kWh]
        bat_ch_arr: carica batteria [kWh]
        bat_dch_arr: scarica batteria [kWh]
        title: titolo
        figsize: dimensioni figura
    
    Returns:
        Figure matplotlib
    """
    # Crea DataFrame per aggregazione mensile
    df = pd.DataFrame({
        'timestamp': idx,
        'pv': pv_arr,
        'load': load_arr,
        'grid_in': grid_in_arr,
        'grid_out': grid_out_arr,
        'bat_ch': bat_ch_arr,
        'bat_dch': bat_dch_arr,
    })
    
    df['month'] = df['timestamp'].dt.to_period('M')
    monthly = df.groupby('month')[['pv', 'load', 'grid_in', 'grid_out', 'bat_ch', 'bat_dch']].sum()
    
    # Reindex per tutti i mesi (anche se vuoti)
    full_index = pd.period_range(start=monthly.index[0], end=monthly.index[-1], freq='M')
    monthly = monthly.reindex(full_index, fill_value=0)
    
    # Grafico
    fig, ax = plt.subplots(figsize=figsize)
    
    x = np.arange(len(monthly))
    width = 0.15
    
    ax.bar(x - 2.5*width, monthly['pv'], width, label='PV Prodotto', color='#FDB462')
    ax.bar(x - 1.5*width, monthly['load'], width, label='Consumo', color='#80B1D3')
    ax.bar(x - 0.5*width, monthly['grid_in'], width, label='Acquisto rete', color='red', alpha=0.7)
    ax.bar(x + 0.5*width, monthly['grid_out'], width, label='Vendita rete', color='green', alpha=0.7)
    ax.bar(x + 1.5*width, monthly['bat_ch'], width, label='Carica bat', color='#BEBADA', alpha=0.7)
    ax.bar(x + 2.5*width, monthly['bat_dch'], width, label='Scarica bat', color='#FB8072', alpha=0.7)
    
    ax.set_xlabel('Mese')
    ax.set_ylabel('Energia [kWh]')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels([str(m) for m in monthly.index], rotation=45, ha='right')
    ax.legend(loc='upper left', ncol=2)
    ax.grid(True, alpha=0.3, axis='y')
    
    return fig


def plot_kpi_comparison(
    scenarios: dict,
    title: str = "Comparazione KPI Energetici",
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """
    Grafico a barre per comparare KPI tra scenari.
    
    Args:
        scenarios: dict {nome_scenario: {'sc': %, 'ssr': %, ...}}
        title: titolo
        figsize: dimensioni figura
    
    Returns:
        Figure matplotlib
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    names = list(scenarios.keys())
    sc_values = [scenarios[s]['sc'] for s in names]
    ssr_values = [scenarios[s]['ssr'] for s in names]
    
    x = np.arange(len(names))
    width = 0.35
    
    ax1.bar(x - width/2, sc_values, width, label='Self-Consumption', color='#FDB462')
    ax1.bar(x + width/2, ssr_values, width, label='Self-Sufficiency', color='#80B1D3')
    ax1.set_ylabel('Percentuale [%]')
    ax1.set_title('KPI Energetici')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim([0, 100])
    
    # Secondo grafico: costi
    cost_fixed = [scenarios[s]['cost_fixed'] for s in names if 'cost_fixed' in scenarios[s]]
    if cost_fixed:
        ax2.bar(range(len(cost_fixed)), cost_fixed, color='red', alpha=0.7)
        ax2.set_ylabel('Costo Annuo [€]')
        ax2.set_title('Costo Energetico Annuo')
        ax2.set_xticks(range(len(cost_fixed)))
        ax2.set_xticklabels([n for n in names if 'cost_fixed' in scenarios[n]], rotation=15, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
    
    fig.tight_layout()
    return fig


def plot_financial_comparison(
    baseline_cost: float,
    scenarios: dict,
    title: str = "Comparazione Economica",
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    Grafico della comparazione economica tra scenari.
    
    Args:
        baseline_cost: costo baseline (solo rete)
        scenarios: dict {nome_scenario: {'cost': €, 'income': €, ...}}
        title: titolo
        figsize: dimensioni figura
    
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    names = list(scenarios.keys())
    costs = [scenarios[s]['cost'] for s in names]
    incomes = [scenarios[s]['income'] for s in names]
    
    x = np.arange(len(names))
    width = 0.35
    
    ax.bar(x - width/2, costs, width, label='Costo acquisti', color='red', alpha=0.7)
    ax.bar(x + width/2, incomes, width, label='Ricavo vendite', color='green', alpha=0.7)
    
    # Linea baseline
    ax.axhline(baseline_cost, color='black', linestyle='--', linewidth=2, label='Baseline (solo rete)')
    
    ax.set_ylabel('Importo [€/anno]')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    return fig


def save_all_plots(
    figures: dict,
    output_dir: Path
):
    """
    Salva tutti i grafici in una directory.
    
    Args:
        figures: dict {nome_grafico: Figure}
        output_dir: directory dove salvare
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for name, fig in figures.items():
        filepath = output_dir / f"{name}.png"
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"Salvato: {filepath}")
    
    plt.close('all')
