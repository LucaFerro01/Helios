"""
Caricamento robusto di file CSV per il simulatore HeliosSim.

Gestisce i diversi formati PVGIS, profili di carico e prezzi di mercato,
inclusa la rimozione di metadati liberi in testa ai file.
"""

import pandas as pd
import numpy as np
from io import StringIO
from typing import Tuple, Optional, List
from pathlib import Path


def load_csv_robust(filepath: str, candidate_cols: List[str]) -> Tuple[pd.DataFrame, str]:
    """
    Carica un file CSV gestendo il formato PVGIS e altre varianti.
    
    Il formato PVGIS include righe di metadati libere in testa (latitudine, database, slope)
    non precedute da '#', che causano ParserError. Questa funzione:
    1. Legge il file come testo grezzo
    2. Trova la prima riga che contiene 'time' e separatori CSV
    3. Fallback euristico: se 'time' non esiste, usa la riga con più separatori
    4. Rileva automaticamente il separatore (virgola o punto e virgola)
    5. Cerca la colonna dati per nome parziale tra i candidati forniti
    
    Args:
        filepath: percorso al file CSV
        candidate_cols: lista di nomi parziali da cercare (es. ['G(i)', 'Gi'])
    
    Returns:
        tuple: (DataFrame con tutte le colonne, nome della colonna dati trovata)
    
    Raises:
        FileNotFoundError: se il file non esiste
        ValueError: se nessuna colonna candidata è stata trovata
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File non trovato: {filepath}")
    
    # Leggi tutte le righe come testo grezzo
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        raw_lines = f.readlines()
    
    # Ricerca dinamica della riga header
    header_idx = None
    for i, line in enumerate(raw_lines):
        s = line.strip().lower()
        # La riga header contiene 'time' ed è una riga CSV valida (ha separatori)
        if 'time' in s and (',' in s or ';' in s):
            header_idx = i
            break
    
    if header_idx is None:
        # Fallback: nessuna riga con 'time' trovata
        # Usa la riga con il maggior numero di separatori (euristica robusta)
        sep_counts = [l.count(',') + l.count(';') for l in raw_lines]
        header_idx = sep_counts.index(max(sep_counts))
    
    # Parsing del blocco dati
    raw = ''.join(raw_lines[header_idx:])
    
    # Rileva separatore: se ci sono più ';' che ',' → separatore è ';'
    sep = ';' if raw.count(';') > raw.count(',') else ','
    
    # on_bad_lines='skip': ignora eventuali righe malformate (es. footer PVGIS)
    df = pd.read_csv(StringIO(raw), sep=sep, on_bad_lines='skip')
    df.columns = df.columns.str.strip()  # rimuovi spazi dai nomi colonne
    
    # Ricerca colonna dati per nome parziale
    found = None
    for cand in candidate_cols:
        matches = [c for c in df.columns if cand.lower() in c.lower()]
        if matches:
            found = matches[0]
            break
    
    if found is None:
        raise ValueError(
            f"Colonna non trovata tra {candidate_cols}. "
            f"Colonne disponibili nel file: {list(df.columns)}"
        )
    
    # Converti a numerico: valori non parsabili diventano NaN, poi 0
    df[found] = pd.to_numeric(df[found], errors='coerce').fillna(0)
    
    return df, found


def load_pvgis_data(filepath: str) -> Tuple[np.ndarray, pd.DatetimeIndex, np.ndarray, dict]:
    """
    Carica dati irradianza e temperatura da file PVGIS CSV.
    
    Args:
        filepath: percorso al file PVGIS
    
    Returns:
        tuple: (array irradianza [W/m²], DatetimeIndex, array temperatura o None, metadata dict)
    """
    df, col_G = load_csv_robust(filepath, ['G(i)', 'Gi', 'G_i', 'irr', 'glob'])
    
    # Estrai irradianza
    G_arr = df[col_G].values.astype(float)
    
    # Estrai temperature se disponibili
    T2m_arr = None
    if 'T2m' in df.columns:
        T2m_arr = pd.to_numeric(df['T2m'], errors='coerce').ffill().values.astype(float)
    
    # Inferisci passo temporale dal numero di righe
    n = len(df)
    dt_h = 1.0  # default
    if n >= 30000:
        dt_h = 0.25
    elif n >= 15000:
        dt_h = 0.50
    
    # Crea indice temporale
    idx = pd.date_range('2023-01-01', periods=n, freq=f'{int(dt_h*60)}min')
    
    metadata = {
        'n_points': n,
        'dt_h': dt_h,
        'G_mean_daylight': float(G_arr[G_arr > 0].mean()) if (G_arr > 0).any() else 0,
        'G_max': float(G_arr.max()),
        'has_temperature': T2m_arr is not None,
    }
    
    return G_arr, idx, T2m_arr, metadata


def load_load_profile(filepath: str) -> Tuple[np.ndarray, str]:
    """
    Carica profilo di carico orario della casa.
    
    Args:
        filepath: percorso al file profilo carico
    
    Returns:
        tuple: (array carico [W], colonna carico trovata)
    """
    df, col_L = load_csv_robust(filepath, ['P(W)', 'P', 'power', 'load', 'kw', 'w'])
    L_arr = df[col_L].values.astype(float)
    return L_arr, col_L


def load_market_prices(filepath: Optional[str]) -> Optional[np.ndarray]:
    """
    Carica prezzi orari di mercato dell'energia.
    
    Args:
        filepath: percorso al file prezzi (o None per disabilitare)
    
    Returns:
        array prezzi [€/kWh] o None
    """
    if filepath is None:
        return None
    
    try:
        df, col_P = load_csv_robust(filepath, ['price', 'p', 'prezzo', 'eur', '€/kwh'])
        P_arr = df[col_P].values.astype(float)
        return P_arr
    except (FileNotFoundError, ValueError) as e:
        print(f"Attenzione: non è stato possibile caricare il file prezzi: {e}")
        return None


def align_timeseries(*arrays: np.ndarray) -> Tuple[np.ndarray, ...]:
    """
    Allinea serie temporali di lunghezza diversa al minimo.
    
    Args:
        *arrays: array NumPy da allineare
    
    Returns:
        tuple: array allineati al minimo comune
    """
    n_min = min(len(arr) for arr in arrays)
    return tuple(arr[:n_min] for arr in arrays)
