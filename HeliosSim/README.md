# HeliosSim - Simulatore Fotovoltaico con Batteria

Simulatore Python modulare e professionale per impianti fotovoltaici domestici con batteria di accumulo.

## ✨ Caratteristiche Principali

- **Simulazione energetica dettagliata**: modello NOCT per temperatura di cella, correzione termica della potenza
- **Due modalità operative**:
  - **CSV Mode**: carica i dati da file CSV (irradianza PVGIS, profilo carico, prezzi di mercato)
  - **CLI Mode**: interfaccia interattiva per inserire i parametri manualmente
- **Strategie di gestione batteria**:
  - Standard: massimizzazione dell'autoconsumo
  - Price-Aware: arbitraggio sui prezzi di mercato orari
- **Analisi economica completa**: KPI energetici, analisi finanziaria (NPV, IRR, Payback, LCOE)
- **Grafici professionali**: profili orari, stato batteria, bilancio mensile, comparazioni
- **Modularità**: struttura clean with separation of concerns

## 📋 Struttura del Progetto

```
HeliosSim/
├── config.py              # Configurazione (dataclass per parametri)
├── data_loader.py         # Caricamento robusto file CSV
├── pv_simulator.py        # Calcoli fotovoltaici (NOCT, temperatura, ecc.)
├── battery_simulator.py   # Simulazione batteria (standard + price-aware)
├── economics.py           # KPI energetici e analisi economica
├── visualization.py       # Generazione grafici professionali
├── cli.py                 # Interfaccia interattiva da riga di comando
├── main.py                # Script principale (orchiestra la simulazione)
├── __init__.py            # Package initialization
└── README.md              # Questo file
```

## 🚀 Quick Start

### Prerequisiti

```bash
Python 3.8+
pip install pandas numpy matplotlib scipy
```

### Installazione

```bash
cd /path/to/HeliosSim
pip install -r requirements.txt
```

### Uso - Modalità CSV (consigliato per i tuoi dati)

Per caricare i dati dalla cartella `Data`:

```bash
python main.py simulate ../Data
```

Questo caricherà automaticamente:
- `Timeseries_45.068_7.628_SA3_41deg_0deg_2021_2022.csv` (irradianza PVGIS)
- `load_profile.csv` (profilo carico casa)
- `prices.csv` (prezzi di mercato, opzionale)

### Uso - Modalità Interattiva (CLI)

Per inserire i parametri manualmente:

```bash
python main.py
```

Il programma chiederà interattivamente:
1. Metadati del sito (latitudine, longitudine, elevazione)
2. Parametri impianto PV (potenza, perdite, coefficiente termico)
3. Parametri batteria (capacità, potenza carica/scarica, SOC min/max)
4. Parametri economici (prezzi acquisto/vendita, investimento iniziale)
5. Parametri strategia mercato (se abilitare price-aware)

Disponibilità di valori di default e suggerimenti per valori tipici per ogni parametro.

## 📊 Output

### Console Output

```
======================================================================
  RISULTATI SIMULAZIONE: Simulazione PV
======================================================================

📊 KPI ENERGETICI (passo 60 min):
----------------------------------------------------------------------
  Produzione PV totale      :    7854.3 kWh
  Consumo totale            :    6234.5 kWh
  Autoconsumato             :    4891.2 kWh
    di cui FV diretto       :    3456.7 kWh
    di cui da batteria      :    1434.5 kWh
  Ceduto in rete            :    2963.1 kWh
  Acquistato dalla rete     :    1343.3 kWh
----------------------------------------------------------------------
  Self-Consumption (SC)     :      78.4 %
  Self-Sufficiency (SSR)    :      72.1 %

💰 KPI ECONOMICI (tariffa fissa):
----------------------------------------------------------------------
  Costo acquisti            :     335.82 €/anno
  Ricavo vendite            :     237.05 €/anno
  Beneficio netto           :     856.23 €/anno
  LCOE finanziario          :       6.2 €cent/kWh
  Payback investimento      :      14.0 anni
  NPV (20 anni)             : 2847.36 €
  IRR                       :       6.8 %

🏪 KPI ECONOMICI (mercato libero):
----------------------------------------------------------------------
  Costo acquisti (market)   :     312.45 €/anno
  Ricavo vendite (market)   :     298.76 €/anno
  Beneficio netto (market)  :     923.48 €/anno
  Premium strategia         :     +67.25 €/anno
=====================================================================
```

### Grafici Generati

1. **01_hourly_profile.png**: Profilo orario (prima settimana) con:
   - Produzione PV [W]
   - Consumo carico [W]
   - Flussi rete (acquisto/vendita)

2. **02_battery_soc.png**: Stato di carica batteria (30 giorni) con:
   - SOC attuale [%]
   - Soglie min/max

3. **03_monthly_energy.png**: Bilancio energetico mensile con:
   - Produzione PV
   - Consumo
   - Acquisti/vendite rete
   - Carica/scarica batteria

I grafici vengono salvati in `./results/`

## 📚 Guida ai Parametri

### PV (Fotovoltaico)

| Parametro | Unità | Tipico | Descrizione |
|-----------|-------|--------|-------------|
| **kwp** | kW | 4-10 | Potenza di picco STC |
| **losses** | % | 0.10-0.20 | Perdite di sistema aggregate |
| **gamma** | 1/°C | -0.003 a -0.005 | Coefficiente termico (vedi datasheet pannello) |
| **noct** | °C | 42-48 | Temperatura nominale operativa cella |
| **degradation** | %/anno | 0.4-0.7 | Degrado annuo della potenza |

### Batteria

| Parametro | Unità | Tipico | Descrizione |
|-----------|-------|--------|-------------|
| **capacity** | kWh | 5-15 | Capacità nominale |
| **p_charge** | kW | 3-10 | Potenza max carica |
| **p_discharge** | kW | 3-10 | Potenza max scarica |
| **soc_init** | 0-1 | 0.50 | SOC iniziale |
| **soc_min** | 0-1 | 0.10 | SOC minimo (protezione) |
| **soc_max** | 0-1 | 0.95 | SOC massimo (protezione) |
| **efficiency_rt** | % | 88-95 | Efficienza round-trip (carica + scarica) |

### Economico

| Parametro | Unità | Tipico | Descrizione |
|-----------|-------|--------|-------------|
| **price_buy** | €/kWh | 0.20-0.35 | Tariffa acquisto rete |
| **price_sell** | €/kWh | 0.05-0.12 | Corrispettivo vendita rete |
| **capex** | € | 10000-15000 | Investimento iniziale |
| **opex** | €/anno | 100-300 | Costi gestione annuali |
| **discount_rate** | % | 3-8 | Tasso sconto (analisi financial) |

### Price-Aware (Mercato Libero)

| Parametro | Unità | Tipico | Descrizione |
|-----------|-------|--------|-------------|
| **lookahead_hours** | ore | 2-6 | Finestra previsione FV futuro |
| **arbitrage_spread** | €/kWh | 0.03-0.10 | Spread minimo per ottimizzazione |
| **price_high_percentile** | % | 70-80 | Soglia prezzo "alto" (percentile) |
| **price_low_percentile** | % | 20-30 | Soglia prezzo "basso" (percentile) |

## 🔬 Modelli Fisici

### Modello NOCT (Temperatura Cella PV)

```
T_cell = T_amb + (NOCT - 20) / 800 * G

Dove:
- T_amb: temperatura ambiente [°C]
- NOCT: temperatura nominale operativa cella [°C, tipico 45°C]
- G: irradianza [W/m²]
```

A parità di irradianza, ogni °C di aumento della temperatura della cella riduce
la potenza del pannello del`gamma` (tipicamente -0.4% per °C).

### Modello Batteria

**Modalità Standard (Autoconsumo)**:
- Surplus PV → carica batteria (vincolo: potenza max, SOC max)
- Deficit → scarica batteria (vincolo: potenza max, SOC min)
- Eccessi/dificit non coperti → flusso rete

**Modalità Price-Aware (Arbitraggio)**:
- Prezzo alto + FV futuro sufficiente → scarica batteria e vendi
- Prezzo basso → carica batteria dalla rete (se conveniente)
- Prezzo negativo → carica, non vendi
- Altrimenti → comportamento standard

### Efficienza Round-Trip

```
η_carica = η_scarica = √(η_rt)

Esempio: η_rt = 0.90 → η_c = η_d ≈ 0.9487
- Stoccare 1 kWh_DC richiede 1/0.9487 ≈ 1.054 kWh_AC
- Erogare 1 kWh_DC fornisce 0.9487 kWh_AC
```

## 📈 Interpretazione KPI

### Self-Consumption (SC)

```
SC = (FV prodotto - ceduto rete) / FV prodotto * 100 [%]
```

- Misura la quota della produzione PV autoconsumata (non ceduta)
- **SC alto** (>80%) = poco spreco, efficiente accumulo
- **SC basso** (<50%) = surplus non utilizzato, considerare batteria più grande

### Self-Sufficiency (SSR)

```
SSR = (carico - acquisto rete) / carico * 100 [%]
```

- Misura l'indipendenza dalla rete
- **SSR alto** (>70%) = elevata autonomia, pochi acquisti rete
- **SSR basso** (<40%) = ancora dipendente dalla rete

## 💡 Casi d'Uso

### 1. Dimostrazione a Cliente

Usa **CLI Mode** per mostrare l'impatto di diversi dimensionamenti:

```bash
# Cliente vuole vedere scenario conservativo (4 kW, 5 kWh)
python main.py

# Cliente vuole vedere scenario aggressivo (10 kW, 15 kWh)
python main.py
```

Ogni run richiede ~2 minuti di configurazione interattiva.

### 2. Studio Fattibilità Sito

Usa **CSV Mode** con dati reali PVGIS + profili misurati (cartella `Data`):

```bash
python main.py simulate /path/to/Data
```

Genera report automatico con grafici da presentare agli stakeholder.

### 3. Ottimizzazione Economica

Modifica `config.py` e lancia serie di simulazioni per trovare il dimensionamento ottimale:

```python
# Es: varia la capacità batteria
for capacity in [5, 8, 10, 12, 15, 20]:
    config.battery.capacity_kwh = capacity
    results = run_simulation_core(...)
    print(f"Capacity {capacity} kWh: NPV = {results['financial_kpi'].npv_20y} €")
```

## 🛠️ Estensioni Possibili

- [ ] Supporto file meteo diversi (dati PVGIS raw, ERA5, stazioni locali)
- [ ] Modello degradazione batteria su cicli di carica
- [ ] Previsione di produzione FV (semplici modelli ML)
- [ ] Dashboard web interattivo (Streamlit/Dash)
- [ ] Export su Excel con analisi di sensibilità
- [ ] Integrazione con dati ENTSO-E per prezzi reali di mercato

## 📝 Licenza

MIT License - Vedi LICENSE file

## 👥 Autore

Creato per simulazioni fotovoltaiche domestiche con batteria
