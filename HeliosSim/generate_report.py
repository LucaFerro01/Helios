"""
Genera un report PDF con KPI e grafici a partire dai dati nella cartella Data.

Uso:
    ./venv/bin/python generate_report.py ../Data report.pdf

Il report è multipagina: riepilogo KPI, profilo orario, SOC batteria, bilancio mensile.
"""

import sys
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

from main import run_simulation_csv_mode, print_results
from visualization import (
    setup_plotting_style, plot_hourly_profile, plot_battery_soc, plot_monthly_energy,
    plot_daily_average_profile, plot_energy_breakdown_pie,
    plot_npv_cashflow, plot_price_aware_comparison,
    plot_kpi_comparison, plot_financial_comparison,
)


def create_pdf_report(results: dict, output_path: Path):
    setup_plotting_style()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import numpy as np

    cfg = results['config']
    eng = results['energy_kpi']
    fin = results['financial_kpi']
    dt_h = results.get('dt_h', 1.0)
    soc_max_kwh = cfg.battery.soc_max * cfg.battery.capacity_kwh

    with PdfPages(output_path) as pdf:
        # ── Page 1: testo riepilogativo ─────────────────────────────────────
        fig_text = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        fig_text.clf()
        txt = []

        txt.append(f"HeliosSim - Report di Simulazione\n\nSito: {cfg.site_name} ({cfg.latitude}°, {cfg.longitude}°)\n")
        txt.append("=== KPI Energetici ===\n")
        txt.append(f"Produzione PV totale: {eng.pv_production:.1f} kWh\n")
        txt.append(f"Consumo totale: {eng.load_total:.1f} kWh\n")
        txt.append(f"Autoconsumato: {eng.energy_from_pv_direct + eng.energy_from_battery:.1f} kWh\n")
        txt.append(f"  - FV diretto: {eng.energy_from_pv_direct:.1f} kWh\n")
        txt.append(f"  - Da batteria: {eng.energy_from_battery:.1f} kWh\n")
        txt.append(f"Ceduto in rete: {eng.energy_to_grid:.1f} kWh\n")
        txt.append(f"Acquistato da rete: {eng.energy_from_grid:.1f} kWh\n")
        txt.append(f"Self-Consumption (SC): {eng.self_consumption_rate:.1f} %\n")
        txt.append(f"Self-Sufficiency (SSR): {eng.self_sufficiency_rate:.1f} %\n\n")

        txt.append("=== KPI Economici ===\n")
        txt.append(f"Costo acquisti (tariffa fissa): {fin.annual_grid_cost_fixed:.2f} €/anno\n")
        txt.append(f"Ricavo vendite (tariffa fissa): {fin.annual_grid_income_fixed:.2f} €/anno\n")
        txt.append(f"Beneficio netto (tariffa fissa): {fin.annual_net_benefit_fixed:.2f} €/anno\n")
        if fin.lcoe_eur_kwh is not None:
            txt.append(f"LCOE finanziario: {fin.lcoe_eur_kwh * 100:.2f} €cent/kWh\n")
        if fin.annual_net_benefit_market is not None:
            txt.append(f"Costo acquisti (market): {fin.annual_grid_cost_market:.2f} €/anno\n")
            txt.append(f"Ricavo vendite (market): {fin.annual_grid_income_market:.2f} €/anno\n")
            txt.append(f"Beneficio netto (market): {fin.annual_net_benefit_market:.2f} €/anno\n")
        if fin.payback_years is not None:
            txt.append(f"Payback: {fin.payback_years:.1f} anni\n")
        if fin.npv_20y is not None:
            txt.append(f"NPV (20y): {fin.npv_20y:.2f} €\n")
        if fin.irr is not None:
            txt.append(f"IRR: {fin.irr*100:.1f} %\n")

        fig_text.text(0.02, 0.98, "\n".join(txt), va='top', fontsize=10, family='monospace')
        pdf.savefig(fig_text)
        plt.close(fig_text)

        # ── Page 2: profilo orario (prima settimana) ────────────────────────
        fig1 = plot_hourly_profile(
            results['idx'], results['pv_kwh'], results['load_kwh'],
            results['grid_in'], results['grid_out'],
            title='Profilo Orario Energetico (Prima Settimana)'
        )
        pdf.savefig(fig1)
        plt.close(fig1)

        # ── Page 3: profilo medio giornaliero ───────────────────────────────
        fig_daily = plot_daily_average_profile(
            results['idx'], results['pv_kwh'], results['load_kwh'],
            results['grid_in'], results['grid_out'],
            dt_h=dt_h,
            title='Profilo Medio Giornaliero (media annua per ora del giorno)'
        )
        pdf.savefig(fig_daily)
        plt.close(fig_daily)

        # ── Page 4: SOC batteria (30 giorni) ────────────────────────────────
        fig2 = plot_battery_soc(
            results['idx'], results['soc'],
            cfg.battery.soc_min * cfg.battery.capacity_kwh,
            soc_max_kwh,
            title='Stato di Carica Batteria (30 giorni)'
        )
        pdf.savefig(fig2)
        plt.close(fig2)

        # ── Page 5: bilancio mensile ─────────────────────────────────────────
        fig3 = plot_monthly_energy(
            results['idx'], results['pv_kwh'], results['load_kwh'],
            results['grid_in'], results['grid_out'],
            results['bat_ch'], results['bat_dch'],
            title='Bilancio Energetico Mensile'
        )
        pdf.savefig(fig3)
        plt.close(fig3)

        # ── Page 6: ripartizione energetica (torte) ─────────────────────────
        fig_pie = plot_energy_breakdown_pie(
            pv_production=eng.pv_production,
            load_total=eng.load_total,
            energy_from_pv_direct=eng.energy_from_pv_direct,
            energy_from_battery=eng.energy_from_battery,
            energy_to_grid=eng.energy_to_grid,
            energy_from_grid=eng.energy_from_grid
        )
        pdf.savefig(fig_pie)
        plt.close(fig_pie)

        # ── Page 7: flusso di cassa / NPV cumulato ──────────────────────────
        annual_benefit = (fin.annual_net_benefit_market
                         if fin.annual_net_benefit_market is not None
                         else fin.annual_net_benefit_fixed)
        fig_npv = plot_npv_cashflow(
            capex_eur=cfg.economics.capex_eur,
            annual_benefit=annual_benefit,
            analysis_years=cfg.economics.analysis_years,
            discount_rate=cfg.economics.discount_rate,
            pv_degradation_rate=cfg.pv.degradation_yearly,
            payback_years=fin.payback_years,
            title='Flusso di Cassa Cumulato e NPV nel Tempo'
        )
        pdf.savefig(fig_npv)
        plt.close(fig_npv)

        # ── Page 8: comparazione economica ──────────────────────────────────
        fin_scenarios = {
            'Standard': {
                'cost': fin.annual_grid_cost_fixed,
                'income': fin.annual_grid_income_fixed,
            },
        }
        if fin.annual_grid_cost_market is not None:
            fin_scenarios['Price-Aware'] = {
                'cost': fin.annual_grid_cost_market,
                'income': fin.annual_grid_income_market,
            }
        baseline = eng.load_total * cfg.economics.price_buy_eur_kwh
        fig_fin = plot_financial_comparison(baseline, fin_scenarios)
        pdf.savefig(fig_fin)
        plt.close(fig_fin)

        # ── Page 9 (opzionale): confronto standard vs price-aware ───────────
        has_pa = (results.get('grid_in_pa') is not None and
                  not np.array_equal(results['grid_in'], results['grid_in_pa']))
        if has_pa:
            fig_pa = plot_price_aware_comparison(
                idx=results['idx'],
                grid_in_std=results['grid_in'],
                grid_out_std=results['grid_out'],
                soc_std=results['soc'],
                grid_in_pa=results['grid_in_pa'],
                grid_out_pa=results['grid_out_pa'],
                soc_pa=results['soc_pa'],
                soc_max=soc_max_kwh,
                title='Confronto Standard vs Price-Aware (Prima Settimana)'
            )
            pdf.savefig(fig_pa)
            plt.close(fig_pa)

    print(f"Report PDF creato: {output_path}")


def main(argv):
    if len(argv) < 3:
        print("Usage: generate_report.py <data_dir> <output_pdf>")
        return 1
    data_dir = Path(argv[1])
    output_pdf = Path(argv[2])

    results = run_simulation_csv_mode(data_dir)
    # Calcola KPI energetici/finanziari per includerli nel report
    # run_simulation_csv_mode already does these calcs
    create_pdf_report(results, output_pdf)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
