# utils.py

import os
import streamlit as st
import pandas as pd
from datetime import datetime

def generate_unique_id(prefix="ID", length=8):
    """Génère un identifiant unique basé sur la date et un préfixe."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    suffix = ''.join(random.choices('0123456789ABCDEF', k=length))
    return f"{prefix}-{timestamp}-{suffix}"

def save_uploaded_file(uploaded_file, target_dir):
    """
    Sauvegarde un fichier uploadé par Streamlit dans un répertoire local.
    Retourne le chemin relatif du fichier sauvegardé (par rapport au target_dir)
    ou None en cas d'erreur.
    """
    if uploaded_file is not None:
        os.makedirs(target_dir, exist_ok=True)
        
        filename = os.path.basename(uploaded_file.name)
        clean_filename = "".join(c for c in filename if c.isalnum() or c in ('.', '_', '-')).strip()
        
        base, ext = os.path.splitext(clean_filename)
        unique_filename = f"{base}_{datetime.now().strftime('%H%M%S%f')}{ext}"

        file_path = os.path.join(target_dir, unique_filename)
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Fichier sauvegardé: {unique_filename}")
            # CORRECTION ICI : Retourne seulement le nom de fichier unique, pas le chemin relatif au dossier parent
            return unique_filename 
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde du fichier {unique_filename}: {e}")
            return None
    return None

def format_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formate un DataFrame pour un affichage plus lisible dans Streamlit,
    gérant les dates et les listes d'IDs.
    """
    df_display = df.copy()
    for col in df_display.columns:
        # Formatage des dates
        if 'Date' in col and not df_display[col].empty and pd.api.types.is_object_dtype(df_display[col]):
            try:
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
            except:
                pass # Laisse tel quel si la conversion échoue

        # Gérer les listes d'IDs (par exemple, ID_Morceaux_Affectes)
        if 'ID_' in col and 's' in col: # Heuristic for plural IDs like 'ID_Morceaux_Lies'
            df_display[col] = df_display[col].apply(lambda x: x.replace(',', ', ') if isinstance(x, str) else x)

    return df_display

def parse_boolean_string(value):
    """Convertit une chaîne de caractères en booléen."""
    if isinstance(value, str):
        return value.strip().upper() == 'VRAI'
    # Gérer aussi les cas où la valeur est déjà un booléen ou un type numérique
    return bool(value)

def safe_cast_to_int(value):
    """Tente de convertir une valeur en int, retourne None si échec."""
    try:
        # Tente d'abord une conversion directe, puis via float si c'est une chaîne float.
        if isinstance(value, str):
            value = value.replace(',', '.') # Gère les virgules pour les décimaux
        return int(float(value))
    except (ValueError, TypeError):
        return None

def safe_cast_to_float(value):
    """Tente de convertir une valeur en float, retourne None si échec."""
    try:
        # Remplace la virgule par un point pour la conversion en float si format français
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value)
    except (ValueError, TypeError):
        return None