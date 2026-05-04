"""
Simulatore di batteria per sistemi di accumulo energetico.

Comprende:
- Simulazione standard (strategie di autoconsumo)
- Simulazione price-aware (ottimizzazione sui prezzi di mercato)
- Modello delle perdite round-trip
- Gestione SOC e vincoli di potenza
"""

import numpy as np
from typing import Tuple, Optional
from config import BatteryConfig, PriceAwareConfig


class BatterySimulator:
    """
    Simula il funzionamento di un sistema di accumulo energetico (batteria).
    
    Implementa:
    1. Simulazione standard (autoconsumo puro)
    2. Simulazione price-aware (arbitraggio sui prezzi)
    """
    
    def __init__(self, config: BatteryConfig, price_aware_config: Optional[PriceAwareConfig] = None):
        """
        Inizializza il simulatore di batteria.
        
        Args:
            config: BatteryConfig
            price_aware_config: PriceAwareConfig (opzionale)
        """
        self.config = config
        self.price_aware_config = price_aware_config or PriceAwareConfig()
        
        # Efficienza simmetrica: η_c = η_d = sqrt(η_rt)
        self.eta_c = self.eta_d = np.sqrt(config.efficiency_rt)
        
        # Limiti SOC in kWh
        self.soc_min = config.soc_min * config.capacity_kwh
        self.soc_max = config.soc_max * config.capacity_kwh
    
    def simulate_standard(
        self,
        pv_kwh_arr: np.ndarray,
        load_kwh_arr: np.ndarray,
        dt_h: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Simula il funzionamento della batteria in modalità standard (autoconsumo).
        
        Logica:
        - Surplus PV → carica batteria
        - Deficit → scarica batteria
        - Eccesso non immagazzinato → rete
        - Deficit non coperto → acquisto dalla rete
        
        Args:
            pv_kwh_arr: produzione PV oraria [kWh]
            load_kwh_arr: carico orario [kWh]
            dt_h: passo temporale [ore]
        
        Returns:
            tuple: (grid_in, grid_out, bat_ch, bat_dch, soc_arr)
            - grid_in: energia acquistata dalla rete [kWh/step]
            - grid_out: energia ceduta alla rete [kWh/step]
            - bat_ch: energia caricata in batteria [kWh/step]
            - bat_dch: energia scaricata dalla batteria [kWh/step]
            - soc_arr: SOC a fine ogni step [kWh]
        """
        n = len(pv_kwh_arr)
        
        # Limiti di potenza per step [kWh]
        p_ch_kwh = self.config.p_charge_kw * dt_h
        p_dc_kwh = self.config.p_discharge_kw * dt_h
        
        # Array di output
        grid_in = np.zeros(n)
        grid_out = np.zeros(n)
        bat_ch = np.zeros(n)
        bat_dch = np.zeros(n)
        soc_arr = np.zeros(n)
        
        # Condizione iniziale
        soc = self.config.soc_init * self.config.capacity_kwh
        
        # Loop step-by-step
        for i in range(n):
            pv_e = pv_kwh_arr[i]
            load_e = load_kwh_arr[i]
            soc_t = soc
            
            surplus = pv_e - load_e
            
            if surplus > 0:  # Produzione > Consumo
                # Carica batteria con eccesso
                e_ch = min(p_ch_kwh, (self.soc_max - soc_t) / self.eta_c, surplus)
                e_ch = max(e_ch, 0.0)
                
                soc = soc_t + e_ch * self.eta_c
                bat_ch[i] = e_ch
                grid_out[i] = surplus - e_ch
            
            else:  # Consumo > Produzione
                # Scarica batteria per coprire deficit
                deficit = -surplus
                e_dc = min(p_dc_kwh, (soc_t - self.soc_min) * self.eta_d, deficit)
                e_dc = max(e_dc, 0.0)
                
                soc = soc_t - e_dc / self.eta_d
                bat_dch[i] = e_dc
                grid_in[i] = deficit - e_dc
            
            # Clip di sicurezza
            soc = np.clip(soc, self.soc_min, self.soc_max)
            soc_arr[i] = soc
        
        return grid_in, grid_out, bat_ch, bat_dch, soc_arr
    
    def simulate_price_aware(
        self,
        pv_kwh_arr: np.ndarray,
        load_kwh_arr: np.ndarray,
        price_arr: np.ndarray,
        dt_h: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Simula il funzionamento della batteria con strategia price-aware.
        
        Logica di arbitraggio:
        - Prezzo basso → carica batteria anche dalla rete
        - Prezzo alto → scarica batteria e vendi FV (se look-ahead consente)
        - Look-ahead: verifica che FV futuro consenta di ricaricare
        - Prezzi negativi → non vendi, carica batteria
        
        Args:
            pv_kwh_arr: produzione PV oraria [kWh]
            load_kwh_arr: carico orario [kWh]
            price_arr: prezzi orari [€/kWh]
            dt_h: passo temporale [ore]
        
        Returns:
            tuple: (grid_in, grid_out, bat_ch, bat_dch, soc_arr, price_paid, price_earned)
        """
        n = len(pv_kwh_arr)
        
        p_ch_kwh = self.config.p_charge_kw * dt_h
        p_dc_kwh = self.config.p_discharge_kw * dt_h
        
        # Array di output
        grid_in = np.zeros(n)
        grid_out = np.zeros(n)
        bat_ch = np.zeros(n)
        bat_dch = np.zeros(n)
        soc_arr = np.zeros(n)
        price_paid = np.zeros(n)
        price_earned = np.zeros(n)
        
        # Condizione iniziale
        soc = self.config.soc_init * self.config.capacity_kwh
        
        # Pre-calcola step per giorno
        steps_per_day = int(round(24 / dt_h))
        
        # Loop step-by-step
        for i in range(n):
            pv_e = pv_kwh_arr[i]
            load_e = load_kwh_arr[i]
            p = price_arr[i]
            soc_t = soc
            
            # Calcola soglie di prezzo giornaliere
            day_start = max(0, i - (i % steps_per_day))
            day_end = min(n, day_start + steps_per_day)
            day_prices = price_arr[day_start:day_end]
            
            p_high = np.percentile(day_prices, self.price_aware_config.price_high_percentile)
            p_low = np.percentile(day_prices, self.price_aware_config.price_low_percentile)
            spread = p_high - p_low
            
            # Produzione FV attesa nelle prossime ore
            la_end = min(n, i + int(self.price_aware_config.lookahead_hours / dt_h))
            pv_ahead = pv_kwh_arr[i:la_end].sum()
            
            # Logica decisionale
            surplus = pv_e - load_e
            
            if spread > self.price_aware_config.arbitrage_min_spread and p < 0:
                # PREZZI NEGATIVI: carica batteria, non vendi
                e_ch = min(p_ch_kwh, (self.soc_max - soc_t) / self.eta_c,
                          max(surplus, 0) + p_ch_kwh)
                e_ch = min(e_ch, p_ch_kwh)
                e_ch = max(e_ch, 0.0)
                
                to_bat_from_pv = min(max(surplus, 0), e_ch)
                to_bat_from_grid = max(e_ch - to_bat_from_pv, 0)
                
                soc = soc_t + e_ch * self.eta_c
                bat_ch[i] = e_ch
                grid_in[i] = max(-surplus, 0) + to_bat_from_grid
                grid_out[i] = 0.0
                price_paid[i] = grid_in[i] * p
            
            elif spread > self.price_aware_config.arbitrage_min_spread and p >= p_high:
                # PREZZO ALTO: scarica batteria se look-ahead lo consente
                can_sell = pv_ahead > (soc_t - self.soc_min) * 0.5
                
                if can_sell and soc_t > self.soc_min + p_dc_kwh / self.eta_d:
                    e_dc = min(p_dc_kwh, (soc_t - self.soc_min) * self.eta_d)
                    e_dc = max(e_dc, 0.0)
                    
                    soc = soc_t - e_dc / self.eta_d
                    bat_dch[i] = e_dc
                    grid_out[i] = pv_e + e_dc
                    grid_in[i] = load_e
                    
                    price_paid[i] = load_e * p
                    price_earned[i] = grid_out[i] * p
                else:
                    # Look-ahead fallito: comportamento standard
                    self._apply_standard_logic(
                        surplus, soc_t, p,
                        i, bat_ch, bat_dch, grid_in, grid_out, price_paid, price_earned,
                        dt_h
                    )
                    soc = self._update_soc(soc_t, bat_ch[i], bat_dch[i])
            
            elif spread > self.price_aware_config.arbitrage_min_spread and \
                 p <= p_low and soc_t < self.soc_max - p_ch_kwh * self.eta_c:
                # PREZZO BASSO: carica da rete
                e_from_pv = max(surplus, 0.0)
                room_ac = (self.soc_max - soc_t) / self.eta_c
                
                e_ch_pv = min(p_ch_kwh, room_ac, e_from_pv)
                e_ch_pv = max(e_ch_pv, 0.0)
                
                e_ch_grid = min(p_ch_kwh - e_ch_pv, room_ac - e_ch_pv)
                e_ch_grid = max(e_ch_grid, 0.0)
                
                e_ch_total = e_ch_pv + e_ch_grid
                soc = soc_t + e_ch_total * self.eta_c
                
                bat_ch[i] = e_ch_total
                grid_in[i] = max(load_e - e_from_pv, 0) + e_ch_grid
                grid_out[i] = max(e_from_pv - e_ch_pv - load_e, 0)
                
                price_paid[i] = grid_in[i] * p
                price_earned[i] = grid_out[i] * p
            
            else:
                # Prezzo nella fascia media: comportamento standard
                self._apply_standard_logic(
                    surplus, soc_t, p,
                    i, bat_ch, bat_dch, grid_in, grid_out, price_paid, price_earned,
                    dt_h
                )
                soc = self._update_soc(soc_t, bat_ch[i], bat_dch[i])
            
            # Clip di sicurezza
            soc = np.clip(soc, self.soc_min, self.soc_max)
            soc_arr[i] = soc
        
        return grid_in, grid_out, bat_ch, bat_dch, soc_arr, price_paid, price_earned
    
    def _apply_standard_logic(
        self, surplus, soc_t, p,
        i, bat_ch, bat_dch, grid_in, grid_out, price_paid, price_earned,
        dt_h: float = 1.0
    ):
        """Helper: applica logica standard (autoconsumo)."""
        if surplus > 0:
            e_ch = min(
                self.config.p_charge_kw * dt_h,
                (self.soc_max - soc_t) / self.eta_c,
                surplus
            )
            e_ch = max(e_ch, 0.0)
            bat_ch[i] = e_ch
            grid_out[i] = surplus - e_ch
            price_earned[i] = grid_out[i] * p
        else:
            deficit = -surplus
            e_dc = min(
                self.config.p_discharge_kw * dt_h,
                (soc_t - self.soc_min) * self.eta_d,
                deficit
            )
            e_dc = max(e_dc, 0.0)
            bat_dch[i] = e_dc
            grid_in[i] = deficit - e_dc
            price_paid[i] = grid_in[i] * p
    
    def _update_soc(self, soc_t, bat_ch_val, bat_dch_val):
        """Helper: aggiorna SOC data carica/scarica."""
        if bat_ch_val > 0:
            return soc_t + bat_ch_val * self.eta_c
        else:
            return soc_t - bat_dch_val / self.eta_d
