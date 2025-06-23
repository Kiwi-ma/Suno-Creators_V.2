# firestore_connector.py

import streamlit as st
import pandas as pd
from datetime import datetime
import google.cloud.firestore
import base64
import json

# Importation des configurations. Assure-toi que ces noms d'onglets correspondent à tes FUTURES collections Firestore
# Pour la conversion, nous allons "mapper" les noms d'onglets aux noms de collection.
# Par convention Firestore, les noms de collections sont souvent en minuscules_snake_case.
# Nous allons donc utiliser les mêmes noms que tes onglets pour le moment, mais sois conscient
# que dans Firestore, ces noms peuvent être "morceaux_generes", "albums_planetaires", etc.
# Pour l'instant, on garde les noms d'origine du config.py pour faciliter le mapping.
# CORRECTION ICI : WORKSHEET_NAMES au lieu de FIRESTORE_COLLECTIONS
from config import WORKSHEET_NAMES, EXPECTED_COLUMNS 
from utils import generate_unique_id, parse_boolean_string, safe_cast_to_int, safe_cast_to_float

# --- Initialisation de la Connexion à Firestore ---
@st.cache_resource(ttl=3600) # Mise en cache de la connexion pendant 1 heure
def get_firestore_client():
    """
    Initialise et retourne un client Firestore authentifié.
    Utilise les secrets Streamlit pour l'authentification du compte de service (clé JSON encodée en Base64).
    """
    try:
        service_account_info_b64 = st.secrets["GCP_SERVICE_ACCOUNT_B64"]
        project_id = st.secrets["GCP_PROJECT_ID"]
        
        service_account_info_json_str = base64.b64decode(service_account_info_b64).decode('utf-8')
        creds = json.loads(service_account_info_json_str)
        
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(creds)
        db = google.cloud.firestore.Client(project=project_id, credentials=credentials)

        st.session_state['firestore_initialized'] = True
        st.session_state['firestore_error'] = None
        return db
    except KeyError:
        st.error("Les clés 'GCP_SERVICE_ACCOUNT_B64' ou 'GCP_PROJECT_ID' sont manquantes dans votre fichier .streamlit/secrets.toml. Veuillez les configurer.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur d'authentification Firestore. Assurez-vous que la clé GCP_SERVICE_ACCOUNT_B64 est correctement encodée et configurée, et que le Project ID est correct: {e}")
        st.stop()

db = get_firestore_client()

# --- Fonctions d'interaction avec Firestore ---

@st.cache_data(ttl=600) # Mise en cache des données lues pendant 10 minutes
def get_dataframe_from_collection(collection_name: str) -> pd.DataFrame:
    """
    Lit une collection Firestore et la retourne sous forme de DataFrame Pandas.
    Vérifie la présence des colonnes attendues (qui sont maintenant des champs de document).
    """
    try:
        docs = db.collection(collection_name).stream()
        data = []
        for doc in docs:
            doc_dict = doc.to_dict()
            # Ajoute l'ID du document comme une colonne 'ID_Doc' (ou similaire) si besoin
            # Pour l'instant, on suppose que l'ID unique est déjà un champ dans le document
            # ou que nous le générerons et l'ajouterons lors de l'écriture.
            # L'ID réel du document Firestore est accessible via doc.id, mais pour la compatibilité
            # avec la structure GSheet, nous utilisons les IDs contenus dans les documents eux-mêmes.
            data.append(doc_dict)
        
        df = pd.DataFrame(data)

        # Vérifier si les "colonnes" (champs) attendues sont présentes
        # et ajouter les manquantes pour assurer la compatibilité du DataFrame
        if collection_name in EXPECTED_COLUMNS:
            missing_cols = [col for col in EXPECTED_COLUMNS[collection_name] if col not in df.columns]
            if missing_cols:
                st.warning(f"Attention: Les champs suivants sont manquants dans la collection '{collection_name}': {', '.join(missing_cols)}. Ils seront ajoutés avec des valeurs vides.")
                for col in missing_cols:
                    df[col] = ''
            # Réordonner les colonnes selon EXPECTED_COLUMNS
            for col in EXPECTED_COLUMNS[collection_name]:
                if col not in df.columns:
                    df[col] = '' # Ajoutez-les si manquantes avec une valeur par défaut
            df = df[EXPECTED_COLUMNS[collection_name]] # Réordonner
        
        # Gérer les types de données spécifiques
        if collection_name == WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"]:
            if 'Statut_Actif' in df.columns:
                df['Statut_Actif'] = df['Statut_Actif'].apply(parse_boolean_string)
        
        numeric_cols_to_check = {
            WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"]: ['Ecoutes_Totales', 'J_aimes_Recus', 'Partages_Simules', 'Revenus_Simules_Streaming'],
            WORKSHEET_NAMES["MOODS_ET_EMOTIONS"]: ['Niveau_Intensite'],
            WORKSHEET_NAMES["PROJETS_EN_COURS"]: ['Budget_Estime'],
            WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"]: ['Evaluation_Gardien']
        }
        if collection_name in numeric_cols_to_check:
            for col in numeric_cols_to_check[collection_name]:
                if col in df.columns:
                    if 'Revenus' in col or 'Budget' in col:
                        df[col] = df[col].apply(safe_cast_to_float)
                    else:
                        df[col] = df[col].apply(safe_cast_to_int)

        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture de la collection '{collection_name}': {e}")
        return pd.DataFrame() # Retourne un DataFrame vide en cas d'erreur grave


def add_document_to_collection(collection_name: str, document_data: dict, doc_id: str = None) -> bool:
    """
    Ajoute un nouveau document à la collection spécifiée.
    Si doc_id est fourni, il sera utilisé comme ID du document, sinon Firestore en générera un.
    """
    try:
        col_ref = db.collection(collection_name)
        if doc_id:
            col_ref.document(doc_id).set(document_data)
        else:
            col_ref.add(document_data)
        st.cache_data.clear() # Invalider le cache après une écriture
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'ajout du document à la collection '{collection_name}': {e}")
        return False

def update_document_in_collection(collection_name: str, doc_id: str, updates: dict) -> bool:
    """
    Met à jour un document existant dans la collection spécifiée.
    doc_id: L'ID du document à mettre à jour.
    updates: Dictionnaire des champs à mettre à jour.
    """
    try:
        db.collection(collection_name).document(doc_id).update(updates)
        st.cache_data.clear() # Invalider le cache après une écriture
        return True
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour du document dans la collection '{collection_name}': {e}")
        return False

def delete_document_from_collection(collection_name: str, doc_id: str) -> bool:
    """
    Supprime un document de la collection spécifiée.
    doc_id: L'ID du document à supprimer.
    """
    try:
        db.collection(collection_name).document(doc_id).delete()
        st.cache_data.clear() # Invalider le cache après une suppression
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression du document dans la collection '{collection_name}': {e}")
        return False

# --- Fonctions spécifiques pour chaque collection (adaptées de sheets_connector) ---

# Note : Pour Firestore, il est souvent préférable que l'ID unique soit le DOC_ID de Firestore.
# Cependant, pour maintenir la compatibilité avec la structure existante de tes IDs (ex: ID_Morceau),
# nous allons continuer à générer ces IDs et les stocker comme des champs dans le document.
# Lors de la mise à jour/suppression, nous devrons rechercher le document par ce champ ID.
# Pour une implémentation plus "native" Firestore, on utiliserait le doc.id de Firestore directement.
# Pour l'instant, on maintient la logique actuelle pour minimiser les changements.

def add_morceau_generes(data: dict) -> bool:
    if 'ID_Morceau' not in data or not data['ID_Morceau']:
        data['ID_Morceau'] = generate_unique_id('M')
    data['Date_Creation'] = datetime.now().strftime('%Y-%m-%d')
    data['Date_Mise_A_Jour'] = datetime.now().strftime('%Y-%m-%d')
    # Pour l'ajout, on peut utiliser l'ID_Morceau comme ID du document pour faciliter la recherche future
    return add_document_to_collection(WORKSHEET_NAMES["MORCEAUX_GENERES"], data, doc_id=data['ID_Morceau'])

def update_morceau_generes(morceau_id: str, data: dict) -> bool:
    data['Date_Mise_A_Jour'] = datetime.now().strftime('%Y-%m-%d')
    # Supposons que morceau_id est bien l'ID du document Firestore
    return update_document_in_collection(WORKSHEET_NAMES["MORCEAUX_GENERES"], morceau_id, data)

def delete_morceau_generes(morceau_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["MORCEAUX_GENERES"], morceau_id)

def add_historique_generation(data: dict) -> bool:
    if 'ID_GenLog' not in data or not data['ID_GenLog']:
        data['ID_GenLog'] = generate_unique_id('LOG')
    data['Date_Heure'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['ID_Utilisateur'] = st.session_state.get('user_id', 'Gardien')
    return add_document_to_collection(WORKSHEET_NAMES["HISTORIQUE_GENERATIONS"], data, doc_id=data['ID_GenLog'])

def update_historique_generation(gen_log_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["HISTORIQUE_GENERATIONS"], gen_log_id, data)

def delete_historique_generation(gen_log_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["HISTORIQUE_GENERATIONS"], gen_log_id)

# Répéter pour toutes les autres entités, en mappant les fonctions
# vers add_document_to_collection, update_document_in_collection, delete_document_from_collection
# en utilisant leur ID_XXX respectif comme doc_id pour les opérations (add/update/delete)

def add_album(data: dict) -> bool:
    if 'ID_Album' not in data or not data['ID_Album']:
        data['ID_Album'] = generate_unique_id('A')
    if 'Date_Sortie_Prevue' not in data or not data['Date_Sortie_Prevue']:
        data['Date_Sortie_Prevue'] = datetime.now().strftime('%Y-%m-%d')
    return add_document_to_collection(WORKSHEET_NAMES["ALBUMS_PLANETAIRES"], data, doc_id=data['ID_Album'])

def update_album(album_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["ALBUMS_PLANETAIRES"], album_id, data)

def delete_album(album_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["ALBUMS_PLANETAIRES"], album_id)

def add_artiste_ia(data: dict) -> bool:
    if 'ID_Artiste_IA' not in data or not data['ID_Artiste_IA']:
        data['ID_Artiste_IA'] = generate_unique_id('AI')
    return add_document_to_collection(WORKSHEET_NAMES["ARTISTES_IA_COSMIQUES"], data, doc_id=data['ID_Artiste_IA'])

def update_artiste_ia(artiste_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["ARTISTES_IA_COSMIQUES"], artiste_id, data)

def delete_artiste_ia(artiste_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["ARTISTES_IA_COSMIQUES"], artiste_id)

def add_paroles_existantes(data: dict) -> bool:
    if 'ID_Morceau' not in data or not data['ID_Morceau']:
        data['ID_Morceau'] = generate_unique_id('M') 
    return add_document_to_collection(WORKSHEET_NAMES["PAROLES_EXISTANTES"], data, doc_id=data['ID_Morceau'])

def update_paroles_existantes(morceau_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["PAROLES_EXISTANTES"], morceau_id, data)

def delete_paroles_existantes(morceau_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["PAROLES_EXISTANTES"], morceau_id)

def add_style_musical(data: dict) -> bool:
    if 'ID_Style_Musical' not in data or not data['ID_Style_Musical']:
        data['ID_Style_Musical'] = generate_unique_id('SM')
    return add_document_to_collection(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"], data, doc_id=data['ID_Style_Musical'])

def update_style_musical(style_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"], style_id, data)

def delete_style_musical(style_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"], style_id)

def add_style_lyrique(data: dict) -> bool:
    if 'ID_Style_Lyrique' not in data or not data['ID_Style_Lyrique']:
        data['ID_Style_Lyrique'] = generate_unique_id('SL')
    return add_document_to_collection(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"], data, doc_id=data['ID_Style_Lyrique'])

def update_style_lyrique(style_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"], style_id, data)

def delete_style_lyrique(style_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"], style_id)

def add_theme(data: dict) -> bool:
    if 'ID_Theme' not in data or not data['ID_Theme']:
        data['ID_Theme'] = generate_unique_id('TH')
    return add_document_to_collection(WORKSHEET_NAMES["THEMES_CONSTELLES"], data, doc_id=data['ID_Theme'])

def update_theme(theme_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["THEMES_CONSTELLES"], theme_id, data)

def delete_theme(theme_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["THEMES_CONSTELLES"], theme_id)

def add_mood(data: dict) -> bool:
    if 'ID_Mood' not in data or not data['ID_Mood']:
        data['ID_Mood'] = generate_unique_id('MOOD')
    return add_document_to_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"], data, doc_id=data['ID_Mood'])

def update_mood(mood_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"], mood_id, data)

def delete_mood(mood_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"], mood_id)

def add_instrument(data: dict) -> bool:
    if 'ID_Instrument' not in data or not data['ID_Instrument']:
        data['ID_Instrument'] = generate_unique_id('INST')
    return add_document_to_collection(WORKSHEET_NAMES["INSTRUMENTS_ORCHESTRAUX"], data, doc_id=data['ID_Instrument'])

def update_instrument(instrument_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["INSTRUMENTS_ORCHESTRAUX"], instrument_id, data)

def delete_instrument(instrument_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["INSTRUMENTS_ORCHESTRAUX"], instrument_id)

def add_voix_style(data: dict) -> bool:
    if 'ID_Vocal' not in data or not data['ID_Vocal']:
        data['ID_Vocal'] = generate_unique_id('VOC')
    return add_document_to_collection(WORKSHEET_NAMES["VOIX_ET_STYLES_VOCAUX"], data, doc_id=data['ID_Vocal'])

def update_voix_style(vocal_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["VOIX_ET_STYLES_VOCAUX"], vocal_id, data)

def delete_voix_style(vocal_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["VOIX_ET_STYLES_VOCAUX"], vocal_id)

def add_structure_song(data: dict) -> bool:
    if 'ID_Structure' not in data or not data['ID_Structure']:
        data['ID_Structure'] = generate_unique_id('STR')
    return add_document_to_collection(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"], data, doc_id=data['ID_Structure'])

def update_structure_song(structure_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"], structure_id, data)

def delete_structure_song(structure_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"], structure_id)

def add_regle_generation(data: dict) -> bool:
    if 'ID_Regle' not in data or not data['ID_Regle']:
        data['ID_Regle'] = generate_unique_id('REGLE')
    return add_document_to_collection(WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"], data, doc_id=data['ID_Regle'])

def update_regle_generation(regle_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"], regle_id, data)

def delete_regle_generation(regle_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"], regle_id)

def add_projet_en_cours(data: dict) -> bool:
    if 'ID_Projet' not in data or not data['ID_Projet']:
        data['ID_Projet'] = generate_unique_id('PROJ')
    return add_document_to_collection(WORKSHEET_NAMES["PROJETS_EN_COURS"], data, doc_id=data['ID_Projet'])

def update_projet_en_cours(projet_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["PROJETS_EN_COURS"], projet_id, data)

def delete_projet_en_cours(projet_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["PROJETS_EN_COURS"], projet_id)

def add_outil_ia(data: dict) -> bool:
    if 'ID_Outil' not in data or not data['ID_Outil']:
        data['ID_Outil'] = generate_unique_id('IA')
    return add_document_to_collection(WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"], data, doc_id=data['ID_Outil'])

def update_outil_ia(outil_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"], outil_id, data)

def delete_outil_ia(outil_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"], outil_id)

def add_timeline_event(data: dict) -> bool:
    if 'ID_Evenement' not in data or not data['ID_Evenement']:
        data['ID_Evenement'] = generate_unique_id('EV')
    return add_document_to_collection(WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"], data, doc_id=data['ID_Evenement'])

def update_timeline_event(event_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"], event_id, data)

def delete_timeline_event(event_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"], event_id)

def add_stat_simulee(data: dict) -> bool:
    if 'ID_Stat_Simulee' not in data or not data['ID_Stat_Simulee']:
        data['ID_Stat_Simulee'] = generate_unique_id('SS')
    return add_document_to_collection(WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"], data, doc_id=data['ID_Stat_Simulee'])

def update_stat_simulee(stat_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"], stat_id, data)

def delete_stat_simulee(stat_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"], stat_id)

def add_conseil_strategique(data: dict) -> bool:
    if 'ID_Conseil' not in data or not data['ID_Conseil']:
        data['ID_Conseil'] = generate_unique_id('CS')
    return add_document_to_collection(WORKSHEET_NAMES["CONSEILS_STRATEGIQUES_ORACLE"], data, doc_id=data['ID_Conseil'])

def update_conseil_strategique(conseil_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["CONSEILS_STRATEGIQUES_ORACLE"], conseil_id, data)

def delete_conseil_strategique(conseil_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["CONSEILS_STRATEGIQUES_ORACLE"], conseil_id)

def add_public_cible(data: dict) -> bool:
    if 'ID_Public' not in data or not data['ID_Public']:
        data['ID_Public'] = generate_unique_id('PC')
    return add_document_to_collection(WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"], data, doc_id=data['ID_Public'])

def update_public_cible(public_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"], public_id, data)

def delete_public_cible(public_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"], public_id)

def add_prompt_type(data: dict) -> bool:
    if 'ID_PromptType' not in data or not data['ID_PromptType']:
        data['ID_PromptType'] = generate_unique_id('PT')
    return add_document_to_collection(WORKSHEET_NAMES["PROMPTS_TYPES_ET_GUIDES"], data, doc_id=data['ID_PromptType'])

def update_prompt_type(prompt_type_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["PROMPTS_TYPES_ET_GUIDES"], prompt_type_id, data)

def delete_prompt_type(prompt_type_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["PROMPTS_TYPES_ET_GUIDES"], prompt_type_id)

def add_reference_sonore(data: dict) -> bool:
    if 'ID_RefSonore' not in data or not data['ID_RefSonore']:
        data['ID_RefSonore'] = generate_unique_id('RS')
    return add_document_to_collection(WORKSHEET_NAMES["REFERENCES_SONORES_DETAILLES"], data, doc_id=data['ID_RefSonore'])

def update_reference_sonore(ref_sonore_id: str, data: dict) -> bool:
    return update_document_in_collection(WORKSHEET_NAMES["REFERENCES_SONORES_DETAILLES"], ref_sonore_id, data)

def delete_reference_sonore(ref_sonore_id: str) -> bool:
    return delete_document_from_collection(WORKSHEET_NAMES["REFERENCES_SONORES_DETAILLES"], ref_sonore_id)


# Fonctions génériques pour obtenir toutes les données d'une collection
# Elles appellent toutes get_dataframe_from_collection avec le nom de collection approprié.
def get_all_morceaux():
    return get_dataframe_from_collection(WORKSHEET_NAMES["MORCEAUX_GENERES"])

def get_all_albums():
    return get_dataframe_from_collection(WORKSHEET_NAMES["ALBUMS_PLANETAIRES"])

def get_all_sessions_creatives():
    return get_dataframe_from_collection(WORKSHEET_NAMES["SESSIONS_CREATIVES_ORACLE"])

def get_all_artistes_ia():
    return get_dataframe_from_collection(WORKSHEET_NAMES["ARTISTES_IA_COSMIQUES"])

def get_all_styles_musicaux():
    return get_dataframe_from_collection(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"])

def get_all_styles_lyriques():
    return get_dataframe_from_collection(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"])

def get_all_themes():
    return get_dataframe_from_collection(WORKSHEET_NAMES["THEMES_CONSTELLES"])

def get_all_stats_simulees():
    return get_dataframe_from_collection(WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"])

def get_all_conseils_strategiques():
    return get_dataframe_from_collection(WORKSHEET_NAMES["CONSEILS_STRATEGIQUES_ORACLE"])

def get_all_instruments():
    return get_dataframe_from_collection(WORKSHEET_NAMES["INSTRUMENTS_ORCHESTRAUX"])

def get_all_structures_song():
    return get_dataframe_from_collection(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"])

def get_all_voix_styles():
    return get_dataframe_from_collection(WORKSHEET_NAMES["VOIX_ET_STYLES_VOCAUX"])

def get_all_regles_generation():
    return get_dataframe_from_collection(WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"])

def get_all_moods():
    return get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])

def get_all_references_sonores():
    return get_dataframe_from_collection(WORKSHEET_NAMES["REFERENCES_SONORES_DETAILLES"])

def get_all_public_cible():
    return get_dataframe_from_collection(WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"])

def get_all_prompts_types():
    return get_dataframe_from_collection(WORKSHEET_NAMES["PROMPTS_TYPES_ET_GUIDES"])

def get_all_projets_en_cours():
    return get_dataframe_from_collection(WORKSHEET_NAMES["PROJETS_EN_COURS"])

def get_all_outils_ia():
    return get_dataframe_from_collection(WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"])

def get_all_timeline_evenements():
    return get_dataframe_from_collection(WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"])

def get_all_paroles_existantes():
    return get_dataframe_from_collection(WORKSHEET_NAMES["PAROLES_EXISTANTES"])

def get_all_historique_generations():
    return get_dataframe_from_collection(WORKSHEET_NAMES["HISTORIQUE_GENERATIONS"])