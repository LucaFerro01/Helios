"""
Esempio di utilizzo di HeliosSim come libreria Python.

Mostra come usare le classi direttamente nel proprio codice senza passare
da CLI o main.py, per integrazioni custom.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Import dei moduli HeliosSim
from config import (
    PVConfig, BatteryConfig, EconomicsConfig, PriceAwareConfig, SimulationConfig
)
from pv_simulator import PVSimulator, calculate_ambient_temperature
from battery_simulator import BatterySimulator
from economics import EconomicsAnalyzer
from data_loader import load_pvgis_data, load_load_profile, load_market_prices


def example_basic_simulation():
    """Esempio 1: Simulazione di base con dati sintetici."""
    print("\n" + "="*70)
    print("  ESEMPIO 1: Simulazione di Base con Dati Sintetici")
    print("="*70)
    
    # Crea configurazione
    config = SimulationConfig()
    
    # Genera dati sintetici (1 anno di dati orari)
    n_hours = 8760
    idx = pd.date_range('2023-01-01', periods=n_hours, freq='1H')
    hours = np.arange(n_hours)
    
    # Irradianza sintetica (ciclo giorno/notte + stagionale)
    G_arr = 500 * (1 + 0.5*np.sin(2*np.pi*hours/8760)) * np.maximum(
        np.sin(2*np.pi*((hours % 24)/24 - 0.25)), 0
    ) + np.random.normal(0, 20, n_hours)
    G_arr = np.maximum(G_arr, 0)
    
    # Carico sintetico (consumo domestico con picchi sera/mattina)
    L_arr = 500 + 200*np.sin(2*np.pi*((hours % 24)/24)) + np.random.normal(0, 50, n_hours)
    L_arr = np.maximum(L_arr, 100)
    
    # Temperatura ambiente
    T_amb_arr = calculate_ambient_temperature(idx, config.t_amb_monthly, config.t_amb_swing)
    
    # Simulazione PV
    print("\n1️⃣  Calcolo produzione PV...")
    pv_sim = PVSimulator(config.pv)
    pv_kwh_arr, T_cell_arr, temp_factor = pv_sim.calculate_production(
        G_arr, T_amb_arr, dt_h=1.0
    )
    print(f"   ✓ Produzione PV annua: {pv_kwh_arr.sum():.1f} kWh")
    
    # Conversione carico
    load_kwh_arr = L_arr * 1.0 / 1000.0  # 1 ora × potenza → energia
    print(f"   ✓ Consumo annuo: {load_kwh_arr.sum():.1f} kWh")
    
    # Simulazione batteria in modalità standard
    print("\n2️⃣  Simulazione batteria (standard)...")
    bat_sim = BatterySimulator(config.battery)
    grid_in, grid_out, bat_ch, bat_dch, soc_arr = bat_sim.simulate_standard(
        pv_kwh_arr, load_kwh_arr, dt_h=1.0
    )
    print(f"   ✓ Acquisti rete: {grid_in.sum():.1f} kWh")
    print(f"   ✓ Vendite rete: {grid_out.sum():.1f} kWh")
    print(f"   ✓ Cicli batteria: {(bat_ch.sum() + bat_dch.sum()) / (2*config.battery.capacity_kwh):.2f}")
    
    # Analisi economica
    print("\n3️⃣  Analisi economica...")
    econ = EconomicsAnalyzer(config.economics)
    energy_kpi = econ.calculate_energy_kpi(
        pv_kwh_arr, load_kwh_arr, grid_in, grid_out, bat_ch, bat_dch,
        config.battery.capacity_kwh, config.battery.efficiency_rt
    )
    print(f"   ✓ Self-Consumption: {energy_kpi.self_consumption_rate:.1f}%")
    print(f"   ✓ Self-Sufficiency: {energy_kpi.self_sufficiency_rate:.1f}%")
    
    financial_kpi = econ.calculate_financial_kpi(
        grid_in, grid_out, energy_kpi.load_total, energy_kpi.pv_production
    )
    print(f"   ✓ Costo annuo acquisti: {financial_kpi.annual_grid_cost_fixed:.2f} €")
    print(f"   ✓ Beneficio netto: {financial_kpi.annual_net_benefit_fixed:.2f} €")
    if financial_kpi.payback_years:
        print(f"   ✓ Payback period: {financial_kpi.payback_years:.1f} anni")


def example_csv_data():
    """Esempio 2: Simulazione con dati CSV reali."""
    print("\n" + "="*70)
    print("  ESEMPIO 2: Simulazione con Dati CSV (Data)")
    print("="*70)
    
    data_dir = Path("../Data")
    if not data_dir.exists():
        print(f"   ⚠️ Directory {data_dir} non trovata")
        return
    
    try:
        print("\n1️⃣  Caricamento dati...")
        G_arr, idx, T2m_arr, metadata = load_pvgis_data(
            data_dir / "Timeseries_45.068_7.628_SA3_41deg_0deg_2021_2022.csv"
        )
        print(f"   ✓ PVGIS: {metadata['n_points']} punti, {metadata['dt_h']*60:.0f} min")
        
        L_arr, col_L = load_load_profile(data_dir / "load_profile.csv")
        print(f"   ✓ Carico: {len(L_arr)} punti")
        
        price_arr = load_market_prices(data_dir / "prices.csv")
        if price_arr is not None:
            print(f"   ✓ Prezzi: {len(price_arr)} punti")
        
        # Allinea serie
        min_len = min(len(G_arr), len(L_arr))
        G_arr = G_arr[:min_len]
        L_arr = L_arr[:min_len]
        if price_arr is not None:
            price_arr = price_arr[:min_len]
        
        # Usa temperatura dal file o sintetico
        config = SimulationConfig()
        if T2m_arr is not None:
            T_amb_arr = T2m_arr[:min_len]
        else:
            T_amb_arr = calculate_ambient_temperature(
                idx[:min_len], config.t_amb_monthly, config.t_amb_swing
            )
        
        # Simulazione veloce
        dt_h = metadata['dt_h']
        print(f"\n2️⃣  Simulazione (dt={dt_h*60:.0f} min)...")
        
        pv_sim = PVSimulator(config.pv)
        pv_kwh_arr, _, _ = pv_sim.calculate_production(G_arr, T_amb_arr, dt_h=dt_h)
        load_kwh_arr = L_arr * dt_h / 1000.0
        
        bat_sim = BatterySimulator(config.battery)
        grid_in, grid_out, bat_ch, bat_dch, soc_arr = bat_sim.simulate_standard(
            pv_kwh_arr, load_kwh_arr, dt_h=dt_h
        )
        
        econ = EconomicsAnalyzer(config.economics)
        energy_kpi = econ.calculate_energy_kpi(
            pv_kwh_arr, load_kwh_arr, grid_in, grid_out, bat_ch, bat_dch,
            config.battery.capacity_kwh, config.battery.efficiency_rt
        )
        
        print(f"   ✓ Produzione PV: {energy_kpi.pv_production:.1f} kWh")
        print(f"   ✓ Self-Consumption: {energy_kpi.self_consumption_rate:.1f}%")
        print(f"   ✓ Self-Sufficiency: {energy_kpi.self_sufficiency_rate:.1f}%")
        
    except FileNotFoundError as e:
        print(f"   ⚠️ Errore: {e}")


def example_parameter_sweep():
    """Esempio 3: Sweep parametri per trovare dimensionamento ottimale."""
    print("\n" + "="*70)
    print("  ESEMPIO 3: Parameter Sweep (Ottimizzazione Dimensionamento)")
    print("="*70)
    
    # Genera dati sintetici una volta
    n_hours = 8760
    idx = pd.date_range('2023-01-01', periods=n_hours, freq='1H')
    hours = np.arange(n_hours)
    
    G_arr = 500 * (1 + 0.5*np.sin(2*np.pi*hours/8760)) * np.maximum(
        np.sin(2*np.pi*((hours % 24)/24 - 0.25)), 0
    ) + np.random.normal(0, 20, n_hours)
    G_arr = np.maximum(G_arr, 0)
    
    L_arr = 500 + 200*np.sin(2*np.pi*((hours % 24)/24)) + np.random.normal(0, 50, n_hours)
    L_arr = np.maximum(L_arr, 100)
    
    config = SimulationConfig()
    T_amb_arr = calculate_ambient_temperature(idx, config.t_amb_monthly, config.t_amb_swing)
    
    # PV non cambia
    pv_sim = PVSimulator(config.pv)
    pv_kwh_arr, _, _ = pv_sim.calculate_production(G_arr, T_amb_arr, dt_h=1.0)
    load_kwh_arr = L_arr * 1.0 / 1000.0
    
    print("\n1️⃣  Sweep della capacità batteria...")
    print(f"{'Capacità [kWh]':<15} {'SC [%]':<10} {'SSR [%]':<10} {'Payback [y]':<12}")
    print("-" * 50)
    
    econ = EconomicsAnalyzer(config.economics)
    bat_sim_base = BatterySimulator(config.battery)
    
    for capacity in [5, 8, 10, 15, 20]:
        # Modifica solo la capacità batteria
        bat_config = BatteryConfig(
            capacity_kwh=capacity,
            p_charge_kw=config.battery.p_charge_kw,
            p_discharge_kw=config.battery.p_discharge_kw,
            efficiency_rt=config.battery.efficiency_rt,
            soc_min=config.battery.soc_min,
            soc_max=config.battery.soc_max,
            soc_init=config.battery.soc_init
        )
        bat_sim = BatterySimulator(bat_config)
        
        grid_in, grid_out, bat_ch, bat_dch, soc_arr = bat_sim.simulate_standard(
            pv_kwh_arr, load_kwh_arr, dt_h=1.0
        )
        
        energy_kpi = econ.calculate_energy_kpi(
            pv_kwh_arr, load_kwh_arr, grid_in, grid_out, bat_ch, bat_dch,
            capacity, config.battery.efficiency_rt
        )
        
        financial_kpi = econ.calculate_financial_kpi(
            grid_in, grid_out, energy_kpi.load_total, energy_kpi.pv_production
        )
        
        payback = financial_kpi.payback_years or 0
        print(f"{capacity:<15.1f} {energy_kpi.self_consumption_rate:<10.1f} "
              f"{energy_kpi.self_sufficiency_rate:<10.1f} {payback:<12.1f}")
    
    print("\n   💡 Osservazione: aumentare la capacità migliora SC/SSR ma peggiora il payback")


if __name__ == '__main__':
    print("\n" + "🔬 ESEMPI DI UTILIZZO HELIOSIM".center(70, "="))
    
    # Esegui gli esempi
    example_basic_simulation()
    example_csv_data()
    example_parameter_sweep()
    
    print("\n" + "="*70)
    print("  ✅ Esempi completati!")
    print("="*70 + "\n")
