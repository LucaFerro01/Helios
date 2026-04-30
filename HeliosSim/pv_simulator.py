"""
Simulatore fotovoltaico per il calcolo della produzione di energia solare.

Comprende modelli di temperatura (NOCT), correzione termica della potenza,
e pre-calcoli vettorizzati per efficienza.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from config import PVConfig


class PVSimulator:
    """
    Calcola la produzione PV oraria facendo uso di:
    - Modello NOCT (IEC 60904-5) per la temperatura della cella
    - Correzione termica della potenza (coefficiente gamma)
    - Perdite di sistema aggregate (Performance Ratio)
    """
    
    def __init__(self, config: PVConfig):
        """
        Inizializza il simulatore PV.
        
        Args:
            config: configurazione PV (PVConfig)
        """
        self.config = config
    
    def calculate_cell_temperature(
        self,
        G_arr: np.ndarray,
        T_amb_arr: np.ndarray
    ) -> np.ndarray:
        """
        Calcola la temperatura della cella PV usando il modello NOCT.
        
        Formula: T_cell = T_amb + (NOCT - 20) / 800 * G
        
        Args:
            G_arr: irradianza [W/m²]
            T_amb_arr: temperatura ambiente [°C]
        
        Returns:
            array temperatura cella [°C]
        """
        T_cell = T_amb_arr + (self.config.noct - 20.0) / 800.0 * G_arr
        return T_cell
    
    def calculate_temperature_factor(self, T_cell_arr: np.ndarray) -> np.ndarray:
        """
        Calcola il fattore di correzione termica della potenza.
        
        Formula: temp_factor = 1 + gamma * (T_cell - 25)
        
        Args:
            T_cell_arr: temperatura cella [°C]
        
        Returns:
            array fattore correttivo (adimensionale)
        """
        temp_factor = 1.0 + self.config.gamma * (T_cell_arr - 25.0)
        return temp_factor
    
    def calculate_production(
        self,
        G_arr: np.ndarray,
        T_amb_arr: np.ndarray,
        dt_h: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calcola la produzione PV oraria.
        
        Formula: P_pv = (G/1000) * P_picco * (1-losses) * temp_factor * dt
        
        Args:
            G_arr: irradianza [W/m²]
            T_amb_arr: temperatura ambiente [°C]
            dt_h: passo temporale [ore, default=1.0]
        
        Returns:
            tuple: (produzione_kWh, temperatura_cella_°C, fattore_termico)
        """
        # Calcola temperatura cella
        T_cell_arr = self.calculate_cell_temperature(G_arr, T_amb_arr)
        
        # Calcola fattore termico
        temp_factor = self.calculate_temperature_factor(T_cell_arr)
        
        # Calcola produzione (in kWh per passo dt_h)
        pv_kwh = np.maximum(
            (G_arr / 1000.0)  # normalizzazione a STC
            * self.config.kwp * 1000.0  # potenza picco in W
            * (1.0 - self.config.losses)  # perdite di sistema
            * temp_factor,  # correzione temperatura
            0.0
        ) * dt_h / 1000.0  # conversione W·h → kWh
        
        return pv_kwh, T_cell_arr, temp_factor


def calculate_ambient_temperature(
    idx: pd.DatetimeIndex,
    t_amb_monthly: dict,
    t_amb_swing: float = 6.0
) -> np.ndarray:
    """
    Calcola la temperatura ambiente oraria usando modello sinusoidale.
    
    Formula: T(h) = T_media_mese + T_swing * sin(2π*(h-6)/24 - π/2)
    
    Minimo alle 6:00, massimo alle 15:00 (approssimazione).
    
    Args:
        idx: indice temporale (DatetimeIndex)
        t_amb_monthly: dict con temperature medie mensili {1: 5, 2: 6, ...}
        t_amb_swing: escursione termica ±°C (default 6.0)
    
    Returns:
        array temperatura ambiente [°C]
    """
    T_amb_arr = np.array([
        t_amb_monthly[ts.month]
        + t_amb_swing * np.sin(2 * np.pi * (ts.hour - 6) / 24 - np.pi / 2)
        for ts in idx
    ])
    return T_amb_arr
