"""
Analisi economica e KPI energetici del simulatore.

Calcolo di:
- KPI energetici (Self-Consumption, Self-Sufficiency)
- Analisi finanziaria (NPV, IRR, LPPC, Payback)
- Comparazione tra scenari
"""

import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from config import EconomicsConfig


@dataclass
class EnergyKPI:
    """KPI energetici della simulazione."""
    
    pv_production: float  # kWh totale prodotto
    load_total: float  # kWh totale consumato
    self_consumption_rate: float  # % FV autoconsumato
    self_sufficiency_rate: float  # % fabbisogno coperto da FV+batteria
    energy_from_pv_direct: float  # kWh FV diretto al carico
    energy_from_battery: float  # kWh batteria erogato al carico
    energy_to_grid: float  # kWh ceduti
    energy_from_grid: float  # kWh acquistati
    energy_battery_cycles: float  # cicli equivalenti di batteria


@dataclass
class FinancialKPI:
    """KPI finanziari della simulazione."""
    
    annual_grid_cost_fixed: float  # € acquistati a tariffa fissa
    annual_grid_income_fixed: float  # € ricavati a tariffa fissa
    annual_net_benefit_fixed: float  # € beneficio netto annuo
    
    annual_grid_cost_market: Optional[float] = None  # € a prezzi di mercato
    annual_grid_income_market: Optional[float] = None
    annual_net_benefit_market: Optional[float] = None
    
    payback_years: Optional[float] = None  # anni necessari per recuperare investimento
    npv_20y: Optional[float] = None  # VAN su 20 anni
    irr: Optional[float] = None  # TIR


class EconomicsAnalyzer:
    """Analizza gli aspetti energetici ed economici della simulazione."""
    
    def __init__(self, config: EconomicsConfig):
        self.config = config
    
    def calculate_energy_kpi(
        self,
        pv_kwh_arr: np.ndarray,
        load_kwh_arr: np.ndarray,
        grid_in: np.ndarray,
        grid_out: np.ndarray,
        bat_ch: np.ndarray,
        bat_dch: np.ndarray,
        bat_capacity_kwh: float,
        bat_efficiency_rt: float
    ) -> EnergyKPI:
        """
        Calcola i KPI energetici.
        
        Args:
            pv_kwh_arr: produzione PV oraria [kWh]
            load_kwh_arr: carico orario [kWh]
            grid_in: acquisti dalla rete [kWh]
            grid_out: vendite verso rete [kWh]
            bat_ch: carica batteria [kWh]
            bat_dch: scarica batteria [kWh]
            bat_capacity_kwh: capacità batteria [kWh]
            bat_efficiency_rt: efficienza round-trip
        
        Returns:
            EnergyKPI
        """
        pv_total = pv_kwh_arr.sum()
        load_total = load_kwh_arr.sum()
        grid_in_total = grid_in.sum()
        grid_out_total = grid_out.sum()
        bat_dch_total = bat_dch.sum()
        
        # Energia autoconsumata = carico - acquisti dalla rete
        e_selfcons = load_total - grid_in_total
        
        # Quota da FV diretto e da batteria
        e_bat_to_load = bat_dch_total
        e_pv_direct = max(e_selfcons - e_bat_to_load, 0)
        
        # Self-Consumption: quota FV autoconsumata
        sc = (pv_total - grid_out_total) / pv_total * 100 if pv_total > 0 else 0
        
        # Self-Sufficiency: quota fabbisogno coperta da FV+batteria
        ssr = (e_selfcons) / load_total * 100 if load_total > 0 else 0
        
        # Cicli equivalenti di batteria
        # Ciclo = 1 carica + 1 scarica = 2 * capacity
        cycles = (bat_ch.sum() + bat_dch.sum()) / (2 * bat_capacity_kwh) if bat_capacity_kwh > 0 else 0
        
        return EnergyKPI(
            pv_production=float(pv_total),
            load_total=float(load_total),
            self_consumption_rate=float(sc),
            self_sufficiency_rate=float(ssr),
            energy_from_pv_direct=float(e_pv_direct),
            energy_from_battery=float(e_bat_to_load),
            energy_to_grid=float(grid_out_total),
            energy_from_grid=float(grid_in_total),
            energy_battery_cycles=float(cycles)
        )
    
    def calculate_financial_kpi(
        self,
        grid_in: np.ndarray,
        grid_out: np.ndarray,
        load_total: float,
        price_arr: Optional[np.ndarray] = None,
        price_paid_arr: Optional[np.ndarray] = None,
        price_earned_arr: Optional[np.ndarray] = None
    ) -> FinancialKPI:
        """
        Calcola i KPI finanziari.
        
        Args:
            grid_in: acquisti dalla rete [kWh]
            grid_out: vendite verso rete [kWh]
            load_total: carico totale [kWh]
            price_arr: prezzi orari [€/kWh] (opzionale, per mercato)
            price_paid_arr: costi orari [€] (price-aware)
            price_earned_arr: ricavi orari [€] (price-aware)
        
        Returns:
            FinancialKPI
        """
        # Scenario TARIFFA FISSA
        cost_fixed = grid_in.sum() * self.config.price_buy_eur_kwh
        income_fixed = grid_out.sum() * self.config.price_sell_eur_kwh
        net_fixed = cost_fixed - income_fixed
        
        # Baseline tariffa fissa
        baseline_fixed = load_total * self.config.price_buy_eur_kwh
        benefit_fixed = baseline_fixed - net_fixed  # risparmio annuo
        
        # Scenario MERCATO (se disponibile)
        cost_market = None
        income_market = None
        benefit_market = None
        if price_arr is not None:
            # Assicuriamoci di usare la stessa finestra temporale per i prezzi
            n = len(grid_in)
            p = np.asarray(price_arr)
            p_trim = p[:n] if len(p) >= n else p
            # Costo e ricavo a prezzi di mercato sulle lunghezze disponibili
            cost_market = (grid_in[:len(p_trim)] * p_trim).sum() if len(p_trim) > 0 else 0.0
            income_market = (grid_out[:len(p_trim)] * p_trim).sum() if len(p_trim) > 0 else 0.0
            # Baseline market: uso prezzo medio sul periodo disponibile
            mean_price = float(p_trim.mean()) if len(p_trim) > 0 else self.config.price_buy_eur_kwh
            baseline_market = load_total * mean_price
            benefit_market = baseline_market - (cost_market - income_market)
        elif price_paid_arr is not None:
            cost_market = float(price_paid_arr.sum())
            income_market = float(price_earned_arr.sum())
            baseline_market = load_total * self.config.price_buy_eur_kwh
            benefit_market = baseline_market - (cost_market - income_market)
        
        kpi = FinancialKPI(
            annual_grid_cost_fixed=float(net_fixed),
            annual_grid_income_fixed=float(income_fixed),
            annual_net_benefit_fixed=float(benefit_fixed),
            annual_grid_cost_market=float(cost_market) if cost_market else None,
            annual_grid_income_market=float(income_market) if income_market else None,
            annual_net_benefit_market=float(benefit_market) if benefit_market else None
        )
        
        # Calcola payback, NPV, IRR
        self._calculate_investment_returns(kpi)
        
        return kpi
    
    def _calculate_investment_returns(self, kpi: FinancialKPI):
        """Calcola payback, NPV e IRR."""
        # Usa il beneficio netto (preferibilmente mercato se disponibile)
        annual_benefit = kpi.annual_net_benefit_market if kpi.annual_net_benefit_market else kpi.annual_net_benefit_fixed
        
        # Payback period
        if annual_benefit > 0:
            kpi.payback_years = self.config.capex_eur / annual_benefit
        else:
            kpi.payback_years = None
        
        # NPV e IRR su orizzonte temporale
        years = self.config.analysis_years
        rate = self.config.discount_rate
        
        # Cash flows: anno 0 = -CAPEX, anni 1-N = +beneficio - OPEX
        cashflows = [-self.config.capex_eur]
        for year in range(1, years + 1):
            cf = annual_benefit - self.config.opex_eur_year
            # Considera degradazione PV
            cf *= (1 - 0.005) ** (year - 1)
            cashflows.append(cf)
        
        # Calcola NPV
        npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))
        kpi.npv_20y = npv
        
        # Calcola IRR (approssimazione tramite ricerca)
        kpi.irr = self._calculate_irr(cashflows)
    
    def _calculate_irr(self, cashflows, max_iterations=100, tolerance=1e-6):
        """Calcola IRR usando metodo di Newton."""
        try:
            from scipy.optimize import brentq
            
            def npv_func(rate):
                return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))
            
            # Cerca IRR tra -99% e 100%
            irr = brentq(npv_func, -0.99, 1.0, maxiter=max_iterations, xtol=tolerance)
            return irr
        except (ImportError, ValueError):
            # Fallback se scipy non disponibile o IRR non esiste
            return None
