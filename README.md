# Helios

Helios è un progetto Python modulare per simulare impianti fotovoltaici domestici con batteria di accumulo, a partire dai dati esportati da PVGIS e dai profili di carico della casa.

Il cuore del progetto è il package [HeliosSim](HeliosSim/README.md), che mette a disposizione:
- simulazione energetica con modello PV NOCT e correzione termica
- gestione batteria in modalità standard e price-aware
- KPI energetici e finanziari, inclusi NPV, IRR, Payback e LCOE
- grafici leggibili e report PDF
- esecuzione da CSV oppure da CLI interattiva

## Struttura

- [HeliosSim/](HeliosSim/) - codice sorgente del simulatore
- [Data/](Data/) - dati locali usati per le simulazioni
- [.gitignore](.gitignore) - esclusioni Git per ambienti Python, notebook e output generati

## Avvio rapido

Dalla cartella `HeliosSim/`:

```bash
./venv/bin/python main.py simulate ../Data
```

Per generare il report PDF:

```bash
./venv/bin/python generate_report.py ../Data HeliosSim_report.pdf
```

Per la modalità interattiva:

```bash
./venv/bin/python main.py
```

## Dati

La cartella [Data/](Data/) contiene i file CSV utilizzati localmente per le simulazioni:
- `Timeseries_*.csv` - serie PVGIS
- `load_profile.csv` - profilo di carico
- `prices.csv` - prezzi orari di mercato, opzionali
- notebook di sviluppo per riferimento locale

## Output

Le simulazioni generano grafici e report nella cartella `HeliosSim/results/` e nel file PDF indicato in output.

## Documentazione

La documentazione tecnica del simulatore si trova in [HeliosSim/README.md](HeliosSim/README.md).
