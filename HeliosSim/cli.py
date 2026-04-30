"""
Interfaccia a riga di comando (CLI) per HeliosSim.

Consente di inserire i parametri della simulazione in modo interattivo,
con validazione e suggerimenti per valori tipici.
"""

from config import PVConfig, BatteryConfig, EconomicsConfig, PriceAwareConfig, SimulationConfig
from typing import Optional


def _prompt_float(prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Chiede un valore float con validazione."""
    while True:
        try:
            value = input(f"{prompt} [{default}]: ").strip()
            if not value:
                return default
            value = float(value)
            if min_val is not None and value < min_val:
                print(f"  ⚠️  Valore minimo: {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"  ⚠️  Valore massimo: {max_val}")
                continue
            return value
        except ValueError:
            print("  ❌ Inserisci un numero valido")


def _prompt_int(prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
    """Chiede un valore intero con validazione."""
    while True:
        try:
            value = input(f"{prompt} [{default}]: ").strip()
            if not value:
                return default
            value = int(value)
            if min_val is not None and value < min_val:
                print(f"  ⚠️  Valore minimo: {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"  ⚠️  Valore massimo: {max_val}")
                continue
            return value
        except ValueError:
            print("  ❌ Inserisci un numero intero valido")


def _prompt_bool(prompt: str, default: bool) -> bool:
    """Chiede una risposta si/no."""
    default_str = "S/n" if default else "s/N"
    while True:
        value = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not value:
            return default
        if value in ['s', 'si', 'sì', 'y', 'yes', 'vero', 'true']:
            return True
        elif value in ['n', 'no', 'falso', 'false']:
            return False
        else:
            print("  ❌ Rispondi con 's' (si) o 'n' (no)")


def configure_pv_interactive() -> PVConfig:
    """Raccoglie configurazione PV interattivamente."""
    print("\n" + "="*60)
    print("  CONFIGURAZIONE SISTEMA FOTOVOLTAICO")
    print("="*60)
    
    kwp = _prompt_float(
        "Potenza di picco [kW]",
        default=6.0,
        min_val=0.1,
        max_val=100.0
    )
    
    losses = _prompt_float(
        "Perdite di sistema [0-1] (tipico 0.10-0.20)",
        default=0.14,
        min_val=0.0,
        max_val=0.5
    )
    
    gamma = _prompt_float(
        "Coefficiente termico [1/°C] (tipico -0.003 a -0.005)",
        default=-0.004,
        min_val=-0.01,
        max_val=0.0
    )
    
    noct = _prompt_float(
        "Temperatura NOCT [°C] (tipico 42-48)",
        default=45.0,
        min_val=30.0,
        max_val=60.0
    )
    
    degradation = _prompt_float(
        "Degrado annuo [0-1] (tipico 0.004-0.007)",
        default=0.005,
        min_val=0.0,
        max_val=0.05
    )
    
    return PVConfig(
        kwp=kwp,
        losses=losses,
        gamma=gamma,
        noct=noct,
        degradation_yearly=degradation
    )


def configure_battery_interactive() -> BatteryConfig:
    """Raccoglie configurazione batteria interattivamente."""
    print("\n" + "="*60)
    print("  CONFIGURAZIONE BATTERIA")
    print("="*60)
    
    capacity = _prompt_float(
        "Capacità [kWh]",
        default=10.0,
        min_val=1.0,
        max_val=500.0
    )
    
    p_charge = _prompt_float(
        "Potenza max carica [kW]",
        default=5.0,
        min_val=0.5,
        max_val=100.0
    )
    
    p_discharge = _prompt_float(
        "Potenza max scarica [kW]",
        default=5.0,
        min_val=0.5,
        max_val=100.0
    )
    
    soc_init = _prompt_float(
        "SOC iniziale [0-1]",
        default=0.50,
        min_val=0.0,
        max_val=1.0
    )
    
    soc_min = _prompt_float(
        "SOC minimo [0-1] (protezione sovrascarica)",
        default=0.10,
        min_val=0.0,
        max_val=0.3
    )
    
    soc_max = _prompt_float(
        "SOC massimo [0-1] (protezione sovraccarica)",
        default=0.95,
        min_val=0.7,
        max_val=1.0
    )
    
    efficiency = _prompt_float(
        "Efficienza round-trip [0-1] (tipico 0.88-0.95)",
        default=0.90,
        min_val=0.7,
        max_val=0.99
    )
    
    return BatteryConfig(
        capacity_kwh=capacity,
        p_charge_kw=p_charge,
        p_discharge_kw=p_discharge,
        soc_init=soc_init,
        soc_min=soc_min,
        soc_max=soc_max,
        efficiency_rt=efficiency
    )


def configure_economics_interactive() -> EconomicsConfig:
    """Raccoglie configurazione economica interattivamente."""
    print("\n" + "="*60)
    print("  CONFIGURAZIONE ECONOMICA")
    print("="*60)
    
    price_buy = _prompt_float(
        "Prezzo acquisto rete [€/kWh]",
        default=0.25,
        min_val=0.01,
        max_val=1.0
    )
    
    price_sell = _prompt_float(
        "Prezzo vendita rete [€/kWh]",
        default=0.08,
        min_val=0.01,
        max_val=0.5
    )
    
    capex = _prompt_float(
        "Investimento iniziale [€]",
        default=12000.0,
        min_val=1000.0,
        max_val=100000.0
    )
    
    opex = _prompt_float(
        "Costi annuali di gestione [€/anno]",
        default=150.0,
        min_val=0.0,
        max_val=10000.0
    )
    
    discount_rate = _prompt_float(
        "Tasso di sconto [0-1] (tipico 0.03-0.08)",
        default=0.05,
        min_val=0.0,
        max_val=0.2
    )
    
    analysis_years = _prompt_int(
        "Orizzonte analisi [anni]",
        default=20,
        min_val=5,
        max_val=50
    )
    
    return EconomicsConfig(
        price_buy_eur_kwh=price_buy,
        price_sell_eur_kwh=price_sell,
        capex_eur=capex,
        opex_eur_year=opex,
        discount_rate=discount_rate,
        analysis_years=analysis_years
    )


def configure_price_aware_interactive() -> PriceAwareConfig:
    """Raccoglie configurazione price-aware interattivamente."""
    print("\n" + "="*60)
    print("  CONFIGURAZIONE STRATEGIA PRICE-AWARE (MERCATO LIBERO)")
    print("="*60)
    
    enabled = _prompt_bool(
        "Abilitare ottimizzazione sui prezzi di mercato?",
        default=True
    )
    
    if not enabled:
        return PriceAwareConfig(enabled=False)
    
    lookahead = _prompt_float(
        "Finestra look-ahead [ore] (per FV futuro)",
        default=4.0,
        min_val=1.0,
        max_val=24.0
    )
    
    arbitrage_spread = _prompt_float(
        "Spread minimo arbitraggio [€/kWh]",
        default=0.05,
        min_val=0.01,
        max_val=0.5
    )
    
    price_high = _prompt_float(
        "Percentile prezzo alto [%] (soglia vendita)",
        default=75.0,
        min_val=50.0,
        max_val=95.0
    )
    
    price_low = _prompt_float(
        "Percentile prezzo basso [%] (soglia acquisto)",
        default=25.0,
        min_val=5.0,
        max_val=50.0
    )
    
    return PriceAwareConfig(
        enabled=True,
        lookahead_hours=lookahead,
        arbitrage_min_spread=arbitrage_spread,
        price_high_percentile=price_high,
        price_low_percentile=price_low
    )


def configure_simulation_interactive() -> SimulationConfig:
    """Interfaccia interattiva per configurare l'intera simulazione."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "  HeliosSim - CONFIGURAZIONE INTERATTIVA" + " "*3 + "║")
    print("╚" + "="*58 + "╝")
    
    # Metadati
    print("\n" + "="*60)
    print("  METADATI SIMULAZIONE")
    print("="*60)
    
    site_name = input("Nome del sito [Simulazione PV]: ").strip() or "Simulazione PV"
    latitude = _prompt_float("Latitudine [°]", 45.068, -90.0, 90.0)
    longitude = _prompt_float("Longitudine [°]", 7.628, -180.0, 180.0)
    elevation = _prompt_int("Elevazione [m]", 269, 0, 4000)
    
    # Configurazioni specifiche
    pv_config = configure_pv_interactive()
    battery_config = configure_battery_interactive()
    economics_config = configure_economics_interactive()
    price_aware_config = configure_price_aware_interactive()
    
    return SimulationConfig(
        pv=pv_config,
        battery=battery_config,
        economics=economics_config,
        price_aware=price_aware_config,
        site_name=site_name,
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation
    )


def print_configuration_summary(config: SimulationConfig):
    """Stampa un riassunto della configurazione."""
    print("\n" + "="*60)
    print("  CONFIGURAZIONE RIEPILOGO")
    print("="*60)
    print(f"Sito: {config.site_name} ({config.latitude}°, {config.longitude}°)")
    print(f"\nFotovoltaico:")
    print(f"  Potenza: {config.pv.kwp} kW")
    print(f"  Perdite: {config.pv.losses*100:.1f}%")
    print(f"\nBatteria:")
    print(f"  Capacità: {config.battery.capacity_kwh} kWh")
    print(f"  Carica/Scarica: {config.battery.p_charge_kw}/{config.battery.p_discharge_kw} kW")
    print(f"  Efficienza round-trip: {config.battery.efficiency_rt*100:.1f}%")
    print(f"\nEconomia:")
    print(f"  Prezzo acquisto: {config.economics.price_buy_eur_kwh} €/kWh")
    print(f"  Prezzo vendita: {config.economics.price_sell_eur_kwh} €/kWh")
    print(f"  Investimento: {config.economics.capex_eur} €")
    if config.price_aware.enabled:
        print(f"\nOptimizzazione mercato: ABILITATA")
        print(f"  Look-ahead: {config.price_aware.lookahead_hours} ore")
    print("="*60 + "\n")
