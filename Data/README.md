# Data

Questa cartella contiene i file dati usati per le simulazioni HeliosSim.
Non committare questi file di grandi dimensioni nel repository pubblico se non necessario;
sono mantenuti qui per comodità locale.

Contenuto:

- `Timeseries_45.068_7.628_SA3_41deg_0deg_2021_2022.csv` — serie oraria PVGIS
  - colonne tipiche: `time`, `G(i)` (irradianza sul piano inclinato in W/m²), `T2m` (temperatura 2m) e altre colonne meteorologiche
  - formato: CSV con eventuale header di metadati; il simulatore usa un parser robusto che gestisce i metadati iniziali

- `load_profile.csv` — profilo di carico orario della casa
  - colonne tipiche: `time`, `P(W)` o `P` (potenza in W)
  - ogni riga rappresenta l'energia richiesta in quell'intervallo temporale

- `prices.csv` — prezzi orari di mercato [€/kWh] (opzionale)
  - colonne tipiche: `time`, `price` (es. `20230101:0000,0.0988`)

- `pv_battery_simulator (2).ipynb`, `pv_battery_simulator_v2.ipynb` — Notebook di sviluppo e analisi (solo per riferimento)

Nota su utilizzo:
- Per eseguire il simulatore con i dati della cartella `Data`:

```bash
./venv/bin/python main.py simulate ../Data
```

- Se vuoi fornire i file a un cliente o conservarli a lungo termine, meglio archiviare i CSV e i notebook su uno storage esterno (S3, Google Drive, ecc.) e non committarli nel repository Git principale.

