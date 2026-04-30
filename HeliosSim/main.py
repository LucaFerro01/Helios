"""
HeliosSim - Simulatore Fotovoltaico con Batteria

Script principale che orchiestra la simulazione in due modalità:
1. CSV Mode: carica parametri da file CSV
2. CLI Mode: chiede i parametri interattivamente

Usage:
    python main.py                    # Modalità interattiva
    python main.py simulate ../Data  # Modalità CSV (legge da cartella Data)
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Import moduli locali
from config import SimulationConfig, DEFAULT_CONFIG
from data_loader import load_pvgis_data, load_load_profile, load_market_prices, align_timeseries
from pv_simulator import PVSimulator, calculate_ambient_temperature
from battery_simulator import BatterySimulator
from economics import EconomicsAnalyzer
from visualization import (
    setup_plotting_style, plot_hourly_profile, plot_battery_soc,
    plot_monthly_energy, plot_kpi_comparison, plot_financial_comparison,
    save_all_plots
)
from cli import configure_simulation_interactive, print_configuration_summary


def run_simulation_csv_mode(data_dir: Path) -> dict:
    """
    Modalità CSV: carica i dati dalla cartella Colab.
    
    Args:
        data_dir: directory containing CSV files (e.g., ../Colab)
    
    Returns:
        dict con risultati della simulazione
    """
    print(f"\n📁 Modalità CSV: caricamento da {data_dir}")
    
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Directory non trovata: {data_dir}")
    
    # Carica i file CSV
    print("  Caricamento PVGIS...")
    pvgis_file = next(data_dir.glob("Timeseries_*.csv"), None)
    if not pvgis_file:
        raise FileNotFoundError("File PVGIS non trovato (Timeseries_*.csv)")
    
    G_arr, idx, T2m_arr, pvgis_metadata = load_pvgis_data(str(pvgis_file))
    print(f"    {pvgis_file.name} ({pvgis_metadata['n_points']} step)")
    
    print("  Caricamento profilo carico...")
    load_file = data_dir / "load_profile.csv"
    L_arr, col_L = load_load_profile(str(load_file))
    print(f"    load_profile.csv")
    
    print("  Caricamento prezzi di mercato...")
    price_file = data_dir / "prices.csv"
    price_arr = load_market_prices(str(price_file) if price_file.exists() else None)
    if price_arr is not None:
        print(f"    prices.csv ({len(price_arr)} step)")
    else:
        print("    prices.csv (non trovato, modalità prezzo fisso)")
    
    # Allinea le serie
    if price_arr is not None:
        G_arr, L_arr, price_arr = align_timeseries(G_arr, L_arr, price_arr)
    else:
        G_arr, L_arr = align_timeseries(G_arr, L_arr)
    
    if T2m_arr is not None:
        T2m_arr = T2m_arr[:len(G_arr)]
    
    # Usa configurazione di default
    config = DEFAULT_CONFIG
    
    # Calcola temperatura ambiente
    if T2m_arr is not None:
        T_amb_arr = T2m_arr
    else:
        T_amb_arr = calculate_ambient_temperature(idx[:len(G_arr)], config.t_amb_monthly, config.t_amb_swing)
    
    # Esegui simulazione
    return run_simulation_core(config, G_arr, L_arr, T_amb_arr, idx[:len(G_arr)], price_arr)


def run_simulation_cli_mode() -> dict:
    """
    Modalità CLI: chiede i parametri interattivamente.
    
    Returns:
        dict con risultati della simulazione
    """
    print("\n🛠️  Modalità Interattiva: configurazione parameters manuale")
    
    # Raccoglie configurazione
    config = configure_simulation_interactive()
    print_configuration_summary(config)
    
    # Genera dati sintetici per dimostrazione
    print("Generazione dati sintetici per dimostrazione...")
    n_days = 365
    n_hours = n_days * 24
    idx = pd.date_range('2023-01-01', periods=n_hours, freq='1H')
    
    # Sintesi irradianza (curva sinusoidale + rumore)
    hours_in_year = np.arange(n_hours)
    G_arr = 500 * (1 + np.sin(2*np.pi*hours_in_year/8760)) * np.maximum(
        np.sin(2*np.pi*((hours_in_year % 24)/24 - 0.25)),
        0
    ) + np.random.normal(0, 20, n_hours)
    G_arr = np.maximum(G_arr, 0)
    
    # Sintesi carico (picchi mattino/sera + variazione casuale)
    L_arr = 500 + 200*np.sin(2*np.pi*((hours_in_year % 24)/24)) + np.random.normal(0, 50, n_hours)
    L_arr = np.maximum(L_arr, 100)
    
    # Temperatura ambiente
    T_amb_arr = calculate_ambient_temperature(idx, config.t_amb_monthly, config.t_amb_swing)
    
    # Prezzi sintetici (opzionale)
    if config.price_aware.enabled:
        price_arr = 0.15 + 0.05*np.sin(2*np.pi*((hours_in_year % 24)/24)) + np.random.normal(0, 0.01, n_hours)
        price_arr = np.maximum(price_arr, 0.05)
    else:
        price_arr = None
    
    # Esegui simulazione
    return run_simulation_core(config, G_arr, L_arr, T_amb_arr, idx, price_arr)


def run_simulation_core(
    config: SimulationConfig,
    G_arr: np.ndarray,
    L_arr: np.ndarray,
    T_amb_arr: np.ndarray,
    idx: pd.DatetimeIndex,
    price_arr: np.ndarray = None
) -> dict:
    """
    Core della simulazione: esegue PV, batteria, economica.
    
    Args:
        config: configurazione simulazione
        G_arr: irradianza [W/m²]
        L_arr: carico [W]
        T_amb_arr: temperatura [°C]
        idx: indice temporale
        price_arr: prezzi [€/kWh] opzionale
    
    Returns:
        dict con risultati
    """
    print("\n▶️  Esecuzione simulazione...")
    
    # Inferisci passo temporale
    dt_h = 1.0  # Default
    if len(G_arr) >= 30000:
        dt_h = 0.25
    elif len(G_arr) >= 15000:
        dt_h = 0.50
    
    # Converti carico da W a kWh
    load_kwh_arr = L_arr * dt_h / 1000.0
    
    # Converti irradianza se è in W (normalizza a [W/m²])
    # Assumi che G_arr sia già in W/m²
    
    # === Calcoli PV ===
    print("  • Calcoli fotovoltaici...")
    pv_sim = PVSimulator(config.pv)
    pv_kwh_arr, T_cell_arr, temp_factor = pv_sim.calculate_production(G_arr, T_amb_arr, dt_h)
    
    # === Simulazione STANDARD ===
    print("  • Simulazione batteria (modalità standard)...")
    bat_sim = BatterySimulator(config.battery)
    grid_in, grid_out, bat_ch, bat_dch, soc_arr = bat_sim.simulate_standard(pv_kwh_arr, load_kwh_arr, dt_h)
    
    # === Simulazione PRICE-AWARE ===
    grid_in_pa = grid_in.copy()
    grid_out_pa = grid_out.copy()
    bat_ch_pa = bat_ch.copy()
    bat_dch_pa = bat_dch.copy()
    soc_arr_pa = soc_arr.copy()
    price_paid_pa = None
    price_earned_pa = None
    
    if config.price_aware.enabled and price_arr is not None:
        print("  • Simulazione batteria (modalità price-aware)...")
        grid_in_pa, grid_out_pa, bat_ch_pa, bat_dch_pa, soc_arr_pa, price_paid_pa, price_earned_pa = \
            bat_sim.simulate_price_aware(pv_kwh_arr, load_kwh_arr, price_arr, dt_h)
    
    # === KPI Energetici ===
    print("  • Calcolo KPI energetici...")
    econ = EconomicsAnalyzer(config.economics)
    
    energy_kpi = econ.calculate_energy_kpi(
        pv_kwh_arr, load_kwh_arr, grid_in, grid_out, bat_ch, bat_dch,
        config.battery.capacity_kwh, config.battery.efficiency_rt
    )
    
    # === KPI Economici ===
    print("  • Calcolo KPI economici...")
    financial_kpi = econ.calculate_financial_kpi(
        grid_in, grid_out, energy_kpi.load_total, energy_kpi.pv_production,
        price_arr if config.price_aware.enabled else None,
        price_paid_pa, price_earned_pa
    )
    
    print("\n✅ Simulazione completata!\n")
    
    # Prepara risultati
    return {
        'config': config,
        'idx': idx,
        'pv_kwh': pv_kwh_arr,
        'load_kwh': load_kwh_arr,
        'T_cell': T_cell_arr,
        'grid_in': grid_in,
        'grid_out': grid_out,
        'bat_ch': bat_ch,
        'bat_dch': bat_dch,
        'soc': soc_arr,
        'grid_in_pa': grid_in_pa,
        'grid_out_pa': grid_out_pa,
        'bat_ch_pa': bat_ch_pa,
        'bat_dch_pa': bat_dch_pa,
        'soc_pa': soc_arr_pa,
        'price_paid_pa': price_paid_pa,
        'price_earned_pa': price_earned_pa,
        'energy_kpi': energy_kpi,
        'financial_kpi': financial_kpi,
        'dt_h': dt_h
    }


def print_results(results: dict):
    """Stampa i risultati della simulazione."""
    config = results['config']
    eng = results['energy_kpi']
    fin = results['financial_kpi']
    dt_h = results['dt_h']
    
    print("="*70)
    print(f"  RISULTATI SIMULAZIONE: {config.site_name}")
    print("="*70)
    
    print(f"\n📊 KPI ENERGETICI (passo {dt_h*60:.0f} min):")
    print("-"*70)
    print(f"  Produzione PV totale      : {eng.pv_production:10.1f} kWh")
    print(f"  Consumo totale            : {eng.load_total:10.1f} kWh")
    print(f"  Autoconsumato             : {eng.energy_from_pv_direct + eng.energy_from_battery:10.1f} kWh")
    print(f"    di cui FV diretto       : {eng.energy_from_pv_direct:10.1f} kWh")
    print(f"    di cui da batteria      : {eng.energy_from_battery:10.1f} kWh")
    print(f"  Ceduto in rete            : {eng.energy_to_grid:10.1f} kWh")
    print(f"  Acquistato dalla rete     : {eng.energy_from_grid:10.1f} kWh")
    print(f"  Cicli batteria annui      : {eng.energy_battery_cycles:10.1f}")
    print("-"*70)
    print(f"  Self-Consumption (SC)     : {eng.self_consumption_rate:10.1f} %")
    print(f"  Self-Sufficiency (SSR)    : {eng.self_sufficiency_rate:10.1f} %")
    
    print(f"\n💰 KPI ECONOMICI (tariffa fissa):")
    print("-"*70)
    print(f"  Costo acquisti            : {fin.annual_grid_cost_fixed:10.2f} €/anno")
    print(f"  Ricavo vendite            : {fin.annual_grid_income_fixed:10.2f} €/anno")
    print(f"  Beneficio netto           : {fin.annual_net_benefit_fixed:10.2f} €/anno")
    if fin.lcoe_eur_kwh is not None:
        print(f"  LCOE finanziario          : {fin.lcoe_eur_kwh * 100:10.2f} €cent/kWh")
    if fin.payback_years is not None:
        print(f"  Payback investimento      : {fin.payback_years:10.1f} anni")
    if fin.npv_20y is not None:
        print(f"  NPV (20 anni)             : {fin.npv_20y:10.2f} €")
    if fin.irr is not None:
        print(f"  IRR                       : {fin.irr*100:10.1f} %")
    
    if fin.annual_net_benefit_market is not None:
        print(f"\n🏪 KPI ECONOMICI (mercato libero):")
        print("-"*70)
        print(f"  Costo acquisti (market)   : {fin.annual_grid_cost_market:10.2f} €/anno")
        print(f"  Ricavo vendite (market)   : {fin.annual_grid_income_market:10.2f} €/anno")
        print(f"  Beneficio netto (market)  : {fin.annual_net_benefit_market:10.2f} €/anno")
        arbitrage_premium = fin.annual_net_benefit_market - fin.annual_net_benefit_fixed
        print(f"  Premium strategia         : {arbitrage_premium:+10.2f} €/anno")
    
    print("="*70 + "\n")


def generate_plots(results: dict, output_dir: Path = None):
    """Genera e salva i grafici."""
    if output_dir is None:
        output_dir = Path("./results")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    setup_plotting_style()
    
    print(f"\n📈 Generazione grafici...")
    figures = {}
    
    # Grafico profilo orario
    fig = plot_hourly_profile(
        results['idx'],
        results['pv_kwh'],
        results['load_kwh'],
        results['grid_in'],
        results['grid_out'],
        title="Profilo Orario Energetico (Prima Settimana)"
    )
    figures['01_hourly_profile'] = fig
    
    # Grafico SOC batteria
    fig = plot_battery_soc(
        results['idx'],
        results['soc'],
        results['config'].battery.soc_min * results['config'].battery.capacity_kwh,
        results['config'].battery.soc_max * results['config'].battery.capacity_kwh
    )
    figures['02_battery_soc'] = fig
    
    # Grafico bilancio mensile
    fig = plot_monthly_energy(
        results['idx'],
        results['pv_kwh'],
        results['load_kwh'],
        results['grid_in'],
        results['grid_out'],
        results['bat_ch'],
        results['bat_dch']
    )
    figures['03_monthly_energy'] = fig
    
    # Salva
    save_all_plots(figures, output_dir)
    print(f"✅ Grafici salvati in {output_dir}\n")
    
    return figures


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="HeliosSim - Simulatore Fotovoltaico con Batteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python main.py                    # Modalità interattiva
    python main.py simulate ../Data  # Modalità CSV (legge da cartella Data)
        """
    )
    
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['simulate'],
        help="Modalità di esecuzione"
    )
    parser.add_argument(
        'data_dir',
        nargs='?',
        help="Directory con file CSV (per modalità simulate)"
    )
    
    args = parser.parse_args()
    
    try:
        # Modalità CSV
        if args.mode == 'simulate' and args.data_dir:
            results = run_simulation_csv_mode(args.data_dir)
        # Modalità CLI (interattiva)
        else:
            results = run_simulation_cli_mode()
        
        # Stampa risultati
        print_results(results)
        
        # Genera grafici
        generate_plots(results)
        
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
