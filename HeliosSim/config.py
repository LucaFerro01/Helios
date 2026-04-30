"""
Parametri di configurazione predefiniti per il simulatore HeliosSim.

Questi parametri possono essere sovrascritti caricando da CSV (modalità File)
o tramite input interattivo da CLI (modalità Interactive).
"""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class PVConfig:
    """Parametri del sistema fotovoltaico."""
    
    kwp: float = 6.0
    """Potenza di picco [kW] - potenza nominale STC (1000 W/m², 25°C)"""
    
    losses: float = 0.14
    """Perdite di sistema [0-1] - perdite inverter, cablaggio, sporco (~10-20%)"""
    
    gamma: float = -0.004
    """Coefficiente termico [1/°C] - variazione potenza per °C di scostamento da 25°C"""
    
    noct: float = 45.0
    """Nominal Operating Cell Temperature [°C] - temperatura cella in condizioni NOCT"""
    
    degradation_yearly: float = 0.005
    """Degrado annuo della potenza [frazione/anno] - tipicamente 0.4-0.7%"""


@dataclass
class BatteryConfig:
    """Parametri del sistema di accumulo."""
    
    capacity_kwh: float = 10.0
    """Capacità nominale [kWh]"""
    
    p_charge_kw: float = 5.0
    """Potenza massima di carica lato AC [kW]"""
    
    p_discharge_kw: float = 5.0
    """Potenza massima di scarica lato AC [kW]"""
    
    soc_init: float = 0.50
    """State of Charge iniziale [0-1] - 0=vuota, 1=carica"""
    
    soc_min: float = 0.10
    """SOC minimo ammesso [0-1] - protezione sovrascarica profonda"""
    
    soc_max: float = 0.95
    """SOC massimo ammesso [0-1] - protezione sovraccarica"""
    
    efficiency_rt: float = 0.90
    """Efficienza round-trip DC-DC [0-1] - rapporto E_out/E_in per ciclo completo"""


@dataclass
class EconomicsConfig:
    """Parametri economici e analisi finanziaria."""
    
    price_buy_eur_kwh: float = 0.25
    """Prezzo di acquisto dalla rete [€/kWh] - usa la tariffa effettiva del contratto"""
    
    price_sell_eur_kwh: float = 0.08
    """Prezzo di vendita in rete [€/kWh] - Ritiro Dedicato GSE o Scambio sul Posto"""
    
    capex_eur: float = 12000.0
    """Capital Expenditure totale IVA inclusa [€] - investimento iniziale"""
    
    opex_eur_year: float = 150.0
    """Operating Expenditure annuo [€/anno] - manutenzione, assicurazione, etc."""
    
    discount_rate: float = 0.05
    """Tasso di attualizzazione [frazione] - per calcolo NPV e LCOE (es. 0.05 = 5%)"""
    
    analysis_years: int = 20
    """Orizzonte temporale analisi [anni] - vita utile economica dell'impianto"""


@dataclass
class PriceAwareConfig:
    """Parametri dell'algoritmo di ottimizzazione price-aware."""
    
    enabled: bool = True
    """Abilitare la modalità di ottimizzazione sui prezzi di mercato"""
    
    lookahead_hours: float = 4.0
    """Finestra temporale look-ahead [ore] - per valutare FV futuro prima di vendere"""
    
    arbitrage_min_spread: float = 0.05
    """Spread minimo per avviare arbitraggio [€/kWh] - soglia di convenienza"""
    
    price_high_percentile: float = 75.0
    """Percentile per calcolo prezzo "alto" [0-100] - soglia di vendita"""
    
    price_low_percentile: float = 25.0
    """Percentile per calcolo prezzo "basso" [0-100] - soglia di acquisto"""


@dataclass
class SimulationConfig:
    """Parametri complessivi della simulazione."""
    
    pv: PVConfig = None
    battery: BatteryConfig = None
    economics: EconomicsConfig = None
    price_aware: PriceAwareConfig = None
    
    # Metadati
    site_name: str = "Simulazione PV"
    latitude: float = 45.068
    longitude: float = 7.628
    elevation_m: int = 269
    
    # Temperature ambiente mensili [°C] - fallback se T2m non disponibile
    t_amb_monthly: Dict[int, float] = None
    t_amb_swing: float = 6.0
    """Escursione termica diurna ±°C"""
    
    def __post_init__(self):
        """Inizializza i campi di configurazione con valori di default."""
        if self.pv is None:
            self.pv = PVConfig()
        if self.battery is None:
            self.battery = BatteryConfig()
        if self.economics is None:
            self.economics = EconomicsConfig()
        if self.price_aware is None:
            self.price_aware = PriceAwareConfig()
        
        if self.t_amb_monthly is None:
            # Temperature medie mensili Italia centro-nord
            self.t_amb_monthly = {
                1: 5, 2: 6, 3: 9, 4: 14, 5: 19,
                6: 24, 7: 27, 8: 27, 9: 22,
                10: 16, 11: 10, 12: 6
            }


# Configurazione predefinita globale
DEFAULT_CONFIG = SimulationConfig()
