"""
Genera un report PDF con KPI e grafici a partire dai dati nella cartella Colab.

Uso:
  ./venv/bin/python generate_report.py ../Colab report.pdf

Il report è multipagina: riepilogo KPI, profilo orario, SOC batteria, bilancio mensile.
"""

import sys
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

from main import run_simulation_csv_mode, print_results
from visualization import (
    setup_plotting_style, plot_hourly_profile, plot_battery_soc, plot_monthly_energy
)


def create_pdf_report(results: dict, output_path: Path):
    setup_plotting_style()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(output_path) as pdf:
        # Page 1: testo riepilogativo
        fig_text = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        fig_text.clf()
        txt = []
        cfg = results['config']
        eng = results['energy_kpi']
        fin = results['financial_kpi']

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

        # Render text
        fig_text.text(0.02, 0.98, "\n".join(txt), va='top', fontsize=10, family='monospace')
        pdf.savefig(fig_text)
        plt.close(fig_text)

        # Page 2: profilo orario (prima settimana)
        fig1 = plot_hourly_profile(
            results['idx'], results['pv_kwh'], results['load_kwh'], results['grid_in'], results['grid_out'],
            title='Profilo Orario Energetico (Prima Settimana)'
        )
        pdf.savefig(fig1)
        plt.close(fig1)

        # Page 3: SOC batteria
        fig2 = plot_battery_soc(
            results['idx'], results['soc'],
            results['config'].battery.soc_min * results['config'].battery.capacity_kwh,
            results['config'].battery.soc_max * results['config'].battery.capacity_kwh,
            title='Stato di Carica Batteria (30 giorni)'
        )
        pdf.savefig(fig2)
        plt.close(fig2)

        # Page 4: bilancio mensile
        fig3 = plot_monthly_energy(
            results['idx'], results['pv_kwh'], results['load_kwh'], results['grid_in'], results['grid_out'], results['bat_ch'], results['bat_dch'],
            title='Bilancio Energetico Mensile'
        )
        pdf.savefig(fig3)
        plt.close(fig3)

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
