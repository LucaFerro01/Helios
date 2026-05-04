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


def plot_daily_average_profile(
    idx: pd.DatetimeIndex,
    pv_arr: np.ndarray,
    load_arr: np.ndarray,
    grid_in_arr: np.ndarray,
    grid_out_arr: np.ndarray,
    dt_h: float = 1.0,
    title: str = "Profilo Medio Giornaliero",
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    Grafico del profilo medio per ora del giorno (media annua).

    Args:
        idx: indice temporale
        pv_arr: produzione PV [kWh]
        load_arr: carico [kWh]
        grid_in_arr: acquisti rete [kWh]
        grid_out_arr: vendite rete [kWh]
        dt_h: passo temporale [ore]
        title: titolo del grafico
        figsize: dimensioni figura

    Returns:
        Figure matplotlib
    """
    df = pd.DataFrame({
        'hour': idx.hour + idx.minute / 60,
        'pv': pv_arr,
        'load': load_arr,
        'grid_in': grid_in_arr,
        'grid_out': grid_out_arr,
    })

    # Raggruppa per ora intera
    df['hour_int'] = idx.hour
    grp = df.groupby('hour_int')
    hours = np.arange(24)
    pv_mean = grp['pv'].mean().reindex(hours, fill_value=0)
    pv_std = grp['pv'].std().reindex(hours, fill_value=0)
    load_mean = grp['load'].mean().reindex(hours, fill_value=0)
    load_std = grp['load'].std().reindex(hours, fill_value=0)
    grid_in_mean = grp['grid_in'].mean().reindex(hours, fill_value=0)
    grid_out_mean = grp['grid_out'].mean().reindex(hours, fill_value=0)

    if dt_h <= 0:
        raise ValueError(f"dt_h must be positive, got {dt_h}")

    # Converti kWh → W medi per il periodo dt_h
    scale = 1000.0 / dt_h

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(hours, pv_mean * scale, linewidth=2, color='#FDB462', label='PV (media)')
    ax.fill_between(hours,
                    (pv_mean - pv_std) * scale,
                    (pv_mean + pv_std) * scale,
                    alpha=0.15, color='#FDB462')

    ax.plot(hours, load_mean * scale, linewidth=2, color='#80B1D3', label='Carico (media)')
    ax.fill_between(hours,
                    (load_mean - load_std) * scale,
                    (load_mean + load_std) * scale,
                    alpha=0.15, color='#80B1D3')

    ax.fill_between(hours, 0, grid_in_mean * scale, alpha=0.25, color='red',
                    label='Acquisto rete (media)')
    ax.fill_between(hours, 0, -grid_out_mean * scale, alpha=0.25, color='green',
                    label='Vendita rete (media)')

    ax.set_xlabel('Ora del giorno')
    ax.set_ylabel('Potenza media [W]')
    ax.set_title(title)
    ax.set_xticks(hours)
    ax.legend(loc='upper left', ncol=2)
    ax.grid(True, alpha=0.3)

    return fig


def plot_energy_breakdown_pie(
    pv_production: float,
    load_total: float,
    energy_from_pv_direct: float,
    energy_from_battery: float,
    energy_to_grid: float,
    energy_from_grid: float,
    title: str = "Ripartizione Energetica Annua",
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    Doppio grafico a torta: allocazione FV e copertura del carico.

    Args:
        pv_production: produzione PV totale [kWh]
        load_total: consumo totale [kWh]
        energy_from_pv_direct: FV direttamente autoconsumato [kWh]
        energy_from_battery: scarica batteria al carico [kWh]
        energy_to_grid: ceduto in rete [kWh]
        energy_from_grid: acquistato dalla rete [kWh]
        title: titolo figura
        figsize: dimensioni figura

    Returns:
        Figure matplotlib
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # --- Torta sinistra: come viene utilizzata la produzione PV ---
    # Battery charge is estimated as: PV produced − direct self-consumption − grid export.
    # A max(0) guard handles small rounding errors; inputs are assumed internally consistent.
    bat_charge = max(pv_production - energy_from_pv_direct - energy_to_grid, 0)
    pv_sizes = [energy_from_pv_direct, bat_charge, energy_to_grid]
    pv_labels = [
        f'Autoconsumo diretto\n{energy_from_pv_direct:.0f} kWh',
        f'Carica batteria\n{bat_charge:.0f} kWh',
        f'Ceduto in rete\n{energy_to_grid:.0f} kWh',
    ]
    pv_colors = ['#FDB462', '#BEBADA', '#8DD3C7']
    pv_sizes_clean = [max(s, 0) for s in pv_sizes]
    wedges1, texts1, autotexts1 = ax1.pie(
        pv_sizes_clean, labels=pv_labels, colors=pv_colors,
        autopct='%1.1f%%', startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.55)
    )
    ax1.set_title(f'Energia FV prodotta\n({pv_production:.0f} kWh)')

    # --- Torta destra: come viene coperto il fabbisogno ---
    load_sizes = [energy_from_pv_direct, energy_from_battery, energy_from_grid]
    load_labels = [
        f'Da FV diretto\n{energy_from_pv_direct:.0f} kWh',
        f'Da batteria\n{energy_from_battery:.0f} kWh',
        f'Da rete\n{energy_from_grid:.0f} kWh',
    ]
    load_colors = ['#FDB462', '#BEBADA', '#FB8072']
    load_sizes_clean = [max(s, 0) for s in load_sizes]
    wedges2, texts2, autotexts2 = ax2.pie(
        load_sizes_clean, labels=load_labels, colors=load_colors,
        autopct='%1.1f%%', startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.55)
    )
    ax2.set_title(f'Fabbisogno energetico\n({load_total:.0f} kWh)')

    fig.suptitle(title, fontsize=12, fontweight='bold')
    fig.tight_layout()
    return fig


def plot_npv_cashflow(
    capex_eur: float,
    annual_benefit: float,
    analysis_years: int,
    discount_rate: float,
    pv_degradation_rate: float = 0.005,
    payback_years: Optional[float] = None,
    title: str = "Flusso di Cassa Cumulato e NPV",
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    Grafico del flusso di cassa cumulato (non attualizzato) e del NPV annuale.

    Args:
        capex_eur: investimento iniziale [€]
        annual_benefit: beneficio netto annuo anno 1 [€]
        analysis_years: orizzonte temporale [anni]
        discount_rate: tasso di attualizzazione
        pv_degradation_rate: degrado annuo [frazione]
        payback_years: payback semplice calcolato [anni] (opzionale, per linea verticale)
        title: titolo
        figsize: dimensioni figura

    Returns:
        Figure matplotlib
    """
    years = np.arange(0, analysis_years + 1)

    # Flusso cumulato non attualizzato
    cumulative = np.zeros(analysis_years + 1)
    cumulative[0] = -capex_eur
    for y in range(1, analysis_years + 1):
        cf = annual_benefit * (1 - pv_degradation_rate) ** (y - 1)
        cumulative[y] = cumulative[y - 1] + cf

    # NPV cumulato attualizzato
    npv_cum = np.zeros(analysis_years + 1)
    npv_cum[0] = -capex_eur
    for y in range(1, analysis_years + 1):
        cf = annual_benefit * (1 - pv_degradation_rate) ** (y - 1)
        npv_cum[y] = npv_cum[y - 1] + cf / ((1 + discount_rate) ** y)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(years, cumulative, linewidth=2, color='#80B1D3', label='Cash flow cumulato')
    ax.plot(years, npv_cum, linewidth=2, color='#FDB462', linestyle='--', label='NPV cumulato (attualizzato)')
    ax.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)

    # Evidenzia payback
    if payback_years is not None and 0 < payback_years <= analysis_years:
        ax.axvline(payback_years, color='green', linestyle=':', linewidth=1.5,
                   label=f'Payback ≈ {payback_years:.1f} anni')
        ax.annotate(f'{payback_years:.1f} anni',
                    xy=(payback_years, 0), xytext=(payback_years + 0.5, capex_eur * 0.15),
                    arrowprops=dict(arrowstyle='->', color='green'),
                    color='green', fontsize=9)

    # Zona positiva
    ax.fill_between(years, 0, cumulative, where=(cumulative >= 0),
                    alpha=0.1, color='green', label='Zona profitto')
    ax.fill_between(years, 0, cumulative, where=(cumulative < 0),
                    alpha=0.1, color='red', label='Zona perdita')

    ax.set_xlabel('Anno')
    ax.set_ylabel('Importo cumulato [€]')
    ax.set_title(title)
    ax.legend(loc='lower right')
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(True, alpha=0.3)

    return fig


def plot_price_aware_comparison(
    idx: pd.DatetimeIndex,
    grid_in_std: np.ndarray,
    grid_out_std: np.ndarray,
    soc_std: np.ndarray,
    grid_in_pa: np.ndarray,
    grid_out_pa: np.ndarray,
    soc_pa: np.ndarray,
    soc_max: float,
    n_days: int = 7,
    title: str = "Confronto Standard vs Price-Aware",
    figsize: Tuple[int, int] = (14, 8)
) -> plt.Figure:
    """
    Confronto tra strategia standard e price-aware su una finestra temporale.

    Args:
        idx: indice temporale
        grid_in_std: acquisti rete, scenario standard [kWh]
        grid_out_std: vendite rete, scenario standard [kWh]
        soc_std: SOC, scenario standard [kWh]
        grid_in_pa: acquisti rete, scenario price-aware [kWh]
        grid_out_pa: vendite rete, scenario price-aware [kWh]
        soc_pa: SOC, scenario price-aware [kWh]
        soc_max: SOC massimo [kWh] per normalizzazione percentuale
        n_days: numero di giorni da visualizzare
        title: titolo
        figsize: dimensioni figura

    Returns:
        Figure matplotlib
    """
    n = min(n_days * 24, len(idx))
    t = idx[:n]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # --- Asse 1: flussi di rete ---
    ax1.fill_between(t, 0, grid_in_std[:n] * 1000, alpha=0.4, color='red',
                     label='Acquisto std')
    ax1.fill_between(t, 0, -grid_out_std[:n] * 1000, alpha=0.4, color='#80B1D3',
                     label='Vendita std')
    ax1.plot(t, grid_in_pa[:n] * 1000, color='darkred', linewidth=1.2,
             label='Acquisto price-aware')
    ax1.plot(t, -grid_out_pa[:n] * 1000, color='navy', linewidth=1.2,
             label='Vendita price-aware')

    ax1.set_ylabel('Energia [Wh]')
    ax1.set_title(title)
    ax1.legend(loc='upper right', ncol=2, fontsize=8)
    ax1.grid(True, alpha=0.3)

    # --- Asse 2: SOC ---
    soc_std_pct = soc_std[:n] / soc_max * 100 if soc_max > 0 else soc_std[:n]
    soc_pa_pct = soc_pa[:n] / soc_max * 100 if soc_max > 0 else soc_pa[:n]

    ax2.plot(t, soc_std_pct, linewidth=1.5, color='#80B1D3', linestyle='--',
             label='SOC standard')
    ax2.plot(t, soc_pa_pct, linewidth=1.5, color='#FDB462',
             label='SOC price-aware')
    ax2.fill_between(t, soc_std_pct, soc_pa_pct, alpha=0.15, color='purple',
                     label='Differenza SOC')

    ax2.set_xlabel('Data e ora')
    ax2.set_ylabel('SOC [%]')
    ax2.set_ylim([0, 105])
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.autofmt_xdate(rotation=45, ha='right')
    fig.tight_layout()
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
