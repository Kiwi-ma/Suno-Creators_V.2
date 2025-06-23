import streamlit as st
import os
import pandas as pd
from datetime import datetime
import base64

# Importation de nos modules personnalisés
# Assurez-vous que config.py, firestore_connector.py, gemini_oracle.py, utils.py sont dans le même dossier
from config import (
    # SHEET_NAME, # Non utilisé avec Firestore
    WORKSHEET_NAMES, ASSETS_DIR, AUDIO_CLIPS_DIR, SONG_COVERS_DIR, ALBUM_COVERS_DIR, GENERATED_TEXTS_DIR, GEMINI_API_KEY_NAME
)
# CHANGEMENT MAJEUR ICI : Remplacer sheets_connector par firestore_connector
import firestore_connector as fsc # Renommage en 'fsc' pour la concision
import gemini_oracle as go
import utils as ut

# --- Configuration Générale de l'Application Streamlit ---
st.set_page_config(
    page_title="L'ARCHITECTE Ω - Micro-Empire Musical IA (Firestore Edition)", # Nouveau titre pour marquer le changement
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialisation de st.session_state ---
if 'app_initialized' not in st.session_state:
    st.session_state['app_initialized'] = True
    st.session_state['current_page'] = 'Accueil'
    st.session_state['user_id'] = 'Gardien' # Peut être étendu pour des profils utilisateur
    st.session_state['theme_mode'] = 'light' # Ou 'dark', si tu veux un toggle plus tard

    # Initialisation des états pour les confirmations de suppression
    st.session_state['confirm_delete_morceau_id'] = None
    st.session_state['confirm_delete_morceau_name'] = None
    st.session_state['confirm_delete_album_id'] = None
    st.session_state['confirm_delete_album_name'] = None
    st.session_state['confirm_delete_artiste_id'] = None
    st.session_state['confirm_delete_artiste_name'] = None
    st.session_state['confirm_delete_style_id'] = None
    st.session_state['confirm_delete_style_name'] = None
    st.session_state['confirm_delete_style_lyrique_id'] = None
    st.session_state['confirm_delete_style_lyrique_name'] = None
    st.session_state['confirm_delete_theme_id'] = None
    st.session_state['confirm_delete_theme_name'] = None
    st.session_state['confirm_delete_mood_id'] = None
    st.session_state['confirm_delete_mood_name'] = None
    st.session_state['confirm_delete_inst_id'] = None
    st.session_state['confirm_delete_inst_name'] = None
    st.session_state['confirm_delete_vocal_id'] = None
    st.session_state['confirm_delete_vocal_name'] = None
    st.session_state['confirm_delete_structure_id'] = None
    st.session_state['confirm_delete_structure_name'] = None
    st.session_state['confirm_delete_regle_id'] = None
    st.session_state['confirm_delete_regle_name'] = None
    st.session_state['confirm_delete_projet_id'] = None
    st.session_state['confirm_delete_projet_name'] = None
    st.session_state['confirm_delete_outil_id'] = None
    st.session_state['confirm_delete_outil_name'] = None
    st.session_state['confirm_delete_event_id'] = None
    st.session_state['confirm_delete_event_name'] = None
    st.session_state['confirm_delete_paroles_id'] = None
    st.session_state['confirm_delete_paroles_name'] = None
    st.session_state['confirm_delete_stat_simulee_id'] = None # Nouveau pour les stats
    st.session_state['confirm_delete_stat_simulee_name'] = None # Nouveau pour les stats
    st.session_state['confirm_delete_conseil_id'] = None # Nouveau pour les conseils
    st.session_state['confirm_delete_conseil_name'] = None # Nouveau pour les conseils
    st.session_state['confirm_delete_public_id'] = None # Nouveau pour le public cible
    st.session_state['confirm_delete_public_name'] = None # Nouveau pour le public cible
    st.session_state['confirm_delete_prompt_type_id'] = None # Nouveau pour les prompts types
    st.session_state['confirm_delete_prompt_type_name'] = None # Nouveau pour les prompts types
    st.session_state['confirm_delete_ref_sonore_id'] = None # Nouveau pour les références sonores
    st.session_state['confirm_delete_ref_sonore_name'] = None # Nouveau pour les références sonores


# --- Vérification et Création des Dossiers d'Assets ---
for directory in [ASSETS_DIR, AUDIO_CLIPS_DIR, SONG_COVERS_DIR, ALBUM_COVERS_DIR, GENERATED_TEXTS_DIR]:
    os.makedirs(directory, exist_ok=True)


# --- Fonctions Utilitaires d'Affichage pour l'UI ---
def display_dataframe(df: pd.DataFrame, title: str = "", key: str = ""):
    """Affiche un DataFrame avec un titre et un key unique pour Streamlit."""
    if title:
        st.subheader(title)
    if not df.empty:
        st.dataframe(df, use_container_width=True, key=key)
    else:
        st.info("Aucune donnée à afficher pour le moment.")

def get_base64_image(image_path: str):
    """Encode une image en base64 pour l'intégration directe dans Streamlit (si besoin) ou CSS."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def set_background_image(image_path: str):
    """Définit une image de fond pour l'application Streamlit."""
    bin_img = get_base64_image(image_path)
    if bin_img:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_img}");
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# Tu peux choisir une image de fond par défaut ici si tu en as une dans le dossier assets.
# set_background_image(os.path.join(ASSETS_DIR, "background_default.jpg")) # Décommenter et adapter

# --- Menu de Navigation Latéral ---
st.sidebar.title("ARCHITECTE Ω - Menu")

# Structure du menu mise à jour
menu_options = {
    "Accueil": "🏠 Vue d'ensemble de l'empire",
    "Création Musicale IA": { # Catégorie (sera un expander)
        "Générateur de Contenu": "✍️ Paroles, Prompts Audio, Titres...",
        "Co-pilote Créatif": "💡 Idées en temps réel (Beta)",
        "Création Multimodale": "🎬 Audio, Visuel, Paroles (Synchronisé)",
        "Générateur d'Harmonies": "🎵 Structures Harmoniques"
    },
    "Gestion du Sanctuaire": { # Catégorie (sera un expander)
        "Mes Morceaux": "🎶 Gérer les créations musicales",
        "Lecteur Audios": "▶️ Écouter et gérer mes audios", # NOUVEAU : Ajoute cette ligne !
        "Mes Albums": "💿 Gérer les collections",
        "Mes Artistes IA": "🤖 Gérer les identités IA",
        "Paroles Existantes": "📜 Consulter mes paroles manuelles"
    },
    "Analyse & Stratégie": { # Catégorie (sera un expander)
        "Stats & Tendances Sim.": "📊 Analyser les performances virtuelles",
        "Directives Stratégiques": "🎯 Conseils de l'Oracle",
        "Potentiel Viral & Niches": "📈 Détecter les opportunités"
    },
    "Bibliothèques de l'Oracle": { # Catégorie (sera un expander)
        "Styles Musicaux": "🎸 Explorer les genres",
        "Styles Lyriques": "📝 Définir les écritures",
        "Thèmes & Concepts": "🌌 Naviguer les idées",
        "Moods & Émotions": "❤️ Préciser les ressentis",
        "Instruments & Voix": "🎤 Palette sonore",
        "Structures de Chanson": "🏛️ Modèles de composition",
        "Règles de Génération": "⚖️ Contrôler l'IA",
        "Public Cible": "👥 Définir les audiences",
        "Prompts Types": "💡 Modèles de prompts",
        "Références Sonores": "🔊 Catalogue de sons"
    },
    "Outils & Projets": { # Catégorie (sera un expander)
        "Projets en Cours": "🚧 Suivi de production",
        "Outils IA Référencés": "🛠️ Boîte à outils IA",
        "Timeline Événements": "🗓️ Planification des lancements"
    },
    "Historique de l'Oracle": "📚 Traces de nos interactions" # Page directe (sera un bouton)
}

# NOUVELLE FONCTION D'AFFICHAGE DU MENU (NON-RÉCURSIVE POUR LE TOP NIVEAU)
# Remplace l'ancienne fonction display_menu et son appel.
def render_sidebar_menu(options_dict):
    for key, value in options_dict.items():
        # Si la valeur est un dictionnaire, c'est une catégorie -> Expander
        if isinstance(value, dict):
            with st.sidebar.expander(key, expanded=False): # Le 'key' devient le titre de l'expander
                # Parcours les sous-éléments (pages) de cette catégorie
                for sub_key, sub_value in value.items():
                    # sub_value contient déjà l'icône et le texte, ex: "✍️ Paroles..."
                    if st.button(f"{sub_value}", key=f"menu_button_{key}_{sub_key}"):
                        st.session_state['current_page'] = sub_key
                        # Réinitialiser les états de confirmation de suppression
                        for k in list(st.session_state.keys()):
                            if k.startswith('confirm_delete_') and k.endswith('_id'):
                                st.session_state[k] = None
                        st.rerun() # Rafraîchit l'application pour changer de page
        # Si la valeur est une chaîne de caractères, c'est une page directe -> Bouton
        else:
            # value contient l'icône et le texte, ex: "🏠 Vue d'ensemble..."
            if st.sidebar.button(f"{value}", key=f"menu_button_{key}"):
                st.session_state['current_page'] = key
                # Réinitialiser les états de confirmation de suppression
                for k in list(st.session_state.keys()):
                    if k.startswith('confirm_delete_') and k.endswith('_id'):
                        st.session_state[k] = None
                st.rerun() # Rafraîchit l'application pour changer de page

# Appel de la nouvelle fonction d'affichage du menu
render_sidebar_menu(menu_options)

# --- Contenu principal de la page (le reste de ton app.py commence ici) ---
st.title(f"Page : {st.session_state['current_page']}")

# Page d'Accueil
if st.session_state['current_page'] == 'Accueil':
    st.write("Bienvenue dans votre Quartier Général de Micro-Empire Numérique Musical IA. Utilisez le menu latéral pour naviguer.")
    st.info("Pensez à bien configurer vos dossiers d'assets et vos secrets dans les paramètres de votre application Streamlit Cloud!")
    st.markdown("---")
    st.subheader("État de l'Oracle")
    if st.session_state.get('gemini_initialized'):
        st.success("L'Oracle Architecte (Gemini) est initialisé et prêt à servir.")
    else:
        st.error("L'Oracle Architecte (Gemini) n'a pas pu être initialisé. Vérifiez vos secrets API.")
    st.subheader("État des Connexions Base de Données")
    try:
        # Tente de récupérer une petite collection pour tester la connexion Firestore
        fsc.get_all_styles_musicaux()
        st.success(f"Connexion à Firestore réussie pour le projet '{st.secrets['GCP_PROJECT_ID']}'.")
    except Exception as e:
        st.error(f"Échec de la connexion à Firestore : {e}. Vérifiez vos secrets GCP et les permissions de votre compte de service.")

# --- Page : Générateur de Contenu (Création Musicale IA) ---
if st.session_state['current_page'] == 'Générateur de Contenu':
    st.header("✍️ Générateur de Contenu Musical par l'Oracle")
    st.write("Utilisez cette interface pour demander à l'Oracle de générer des paroles, des prompts audio, des titres, des descriptions marketing et des prompts visuels pour vos pochettes d'album.")

    content_type = st.radio(
        "Quel type de contenu souhaitez-vous générer ?",
        ["Paroles de Chanson", "Prompt Audio (pour SUNO)", "Idées de Titres", "Description Marketing", "Prompt Pochette d'Album"],
        key="content_type_radio"
    )

    st.markdown("---") # Séparateur visuel

    # --- Formulaire de Génération de Paroles ---
    if content_type == "Paroles de Chanson":
        st.subheader("Générer des Paroles de Chanson")
        
        # Récupération des données pour les selectbox (MAJ : Utilise fsc.)
        genres_musicaux = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
        themes = [''] + fsc.get_all_themes()['ID_Theme'].tolist()
        styles_lyriques = [''] + fsc.get_all_styles_lyriques()['ID_Style_Lyrique'].tolist()
        structures_song = [''] + fsc.get_all_structures_song()['ID_Structure'].tolist()
        
        with st.form("lyrics_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Genre Musical", genres_musicaux, key="lyrics_genre_musical")
                st.selectbox("Mood Principal", moods, key="lyrics_mood_principal")
                st.selectbox("Thème Principal Lyrique", themes, key="lyrics_theme_lyrique_principal")
                st.selectbox("Style Lyrique", styles_lyriques, key="lyrics_style_lyrique")
                st.text_input("Mots-clés de Génération (séparés par des virgules)", key="lyrics_mots_cles_generation")
            with col2:
                st.selectbox("Structure de Chanson", structures_song, key="lyrics_structure_chanson")
                st.selectbox("Langue des Paroles", ["Français", "Anglais", "Espagnol"], key="lyrics_langue_paroles")
                st.selectbox("Niveau de Langage", ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], key="lyrics_niveau_langage_paroles")
                st.selectbox("Imagerie Texte", ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], key="lyrics_imagerie_texte")
                
            submit_lyrics_button = st.form_submit_button("Générer les Paroles")

        # --- Intégration de Modèles "Empathiques" (pour les Moods) ---
        if st.session_state.get('lyrics_mood_principal') and st.session_state.lyrics_mood_principal != '':
            st.markdown("---")
            st.subheader("Affiner le Mood de vos Paroles avec l'Oracle")
            if st.button("Affiner le Mood avec l'Oracle 🧠", key="refine_mood_button_outside_form"):
                with st.spinner("L'Oracle affine le mood..."):
                    mood_questions = go.refine_mood_with_questions(st.session_state.lyrics_mood_principal)
                    st.session_state['mood_refinement_questions'] = mood_questions
            
            if 'mood_refinement_questions' in st.session_state and st.session_state.mood_refinement_questions:
                st.info("Voici les questions de l'Oracle pour affiner votre mood :\n" + st.session_state.mood_refinement_questions)
                st.text_area("Vos réponses / Affinement du mood (optionnel)", key="lyrics_mood_refinement_response_outside_form")


        if submit_lyrics_button:
            if all([st.session_state.lyrics_genre_musical, st.session_state.lyrics_mood_principal,
                    st.session_state.lyrics_theme_lyrique_principal, st.session_state.lyrics_style_lyrique,
                    st.session_state.lyrics_structure_chanson]):
                with st.spinner("L'Oracle compose les paroles..."):
                    generated_lyrics = go.generate_song_lyrics(
                        genre_musical=st.session_state.lyrics_genre_musical,
                        mood_principal=st.session_state.lyrics_mood_principal,
                        theme_lyrique_principal=st.session_state.lyrics_theme_lyrique_principal,
                        style_lyrique=st.session_state.lyrics_style_lyrique,
                        mots_cles_generation=st.session_state.lyrics_mots_cles_generation,
                        structure_chanSONG=st.session_state.lyrics_structure_chanson,
                        langue_paroles=st.session_state.lyrics_langue_paroles,
                        niveau_langage_paroles=st.session_state.lyrics_niveau_langage_paroles,
                        imagerie_texte=st.session_state.lyrics_imagerie_texte
                    )
                    st.session_state['generated_lyrics'] = generated_lyrics
                    st.success("Paroles générées avec succès !")
            else:
                st.warning("Veuillez remplir tous les champs obligatoires pour générer les paroles.")

        if 'generated_lyrics' in st.session_state and st.session_state.generated_lyrics:
            st.markdown("---")
            st.subheader("Paroles Générées")
            st.text_area("Copiez les paroles ici :", st.session_state.generated_lyrics, height=400, key="displayed_generated_lyrics")
            
            save_lyrics_option = st.radio(
                "Où souhaitez-vous sauvegarder ces paroles ?",
                ["Ne pas sauvegarder", "Dans un nouveau Morceau (Base de Données)", "Dans un Morceau Existant (Base de Données)", "Dans un fichier local"],
                key="save_lyrics_option"
            )

            if save_lyrics_option == "Dans un nouveau Morceau (Base de Données)":
                with st.form("save_new_morceau_lyrics_form"):
                    st.info("Ces paroles seront ajoutées à un nouveau morceau dans la collection `MORCEAUX_GENERES`.")
                    # MAJ : Utilise fsc.
                    artistes_ia_list = [''] + fsc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()
                    new_morceau_title = st.text_input("Titre du nouveau morceau", value=f"Nouveau Morceau - {st.session_state.lyrics_genre_musical}", key="new_morceau_lyrics_title")
                    new_morceau_artist_ia = st.selectbox("Artiste IA Associé", artistes_ia_list, key="new_morceau_lyrics_artist_ia")
                    
                    save_button = st.form_submit_button("Sauvegarder le nouveau Morceau")
                    if save_button:
                        morceau_data = {
                            'Titre_Morceau': new_morceau_title,
                            'Statut_Production': 'Paroles Générées',
                            'Prompt_Generation_Paroles': st.session_state.generated_lyrics,
                            'ID_Style_Musical_Principal': st.session_state.lyrics_genre_musical,
                            'ID_Style_Lyrique_Principal': st.session_state.lyrics_style_lyrique,
                            'Theme_Principal_Lyrique': st.session_state.lyrics_theme_lyrique_principal,
                            'Mots_Cles_Generation': st.session_state.lyrics_mots_cles_generation,
                            'Langue_Paroles': st.session_state.lyrics_langue_paroles,
                            'Niveau_Langage_Paroles': st.session_state.lyrics_niveau_langage_paroles,
                            'Imagerie_Texte': st.session_state.lyrics_imagerie_texte,
                            'Structure_Chanson_Specifique': st.session_state.lyrics_structure_chanson,
                            'ID_Artiste_IA': new_morceau_artist_ia,
                            'Ambiance_Sonore_Specifique': st.session_state.lyrics_mood_principal,
                            # Remplir les colonnes restantes avec des valeurs par défaut pour éviter les erreurs
                            'Effets_Production_Dominants': '', 'Type_Voix_Desiree': '', 'Style_Vocal_Desire': '', 'Caractere_Voix_Desire': '',
                            'Durée_Estimee': '', 'URL_Audio_Local': '', 'URL_Cover_Album': '', 'URL_Video_Clip_Associe': '', 'Mots_Cles_SEO': '', 'Description_Courte_Marketing': '',
                            'ID_Album_Associe': ''
                        }
                        if fsc.add_morceau_generes(morceau_data): # MAJ : Utilise fsc.
                            st.success(f"Paroles sauvegardées comme nouveau morceau '{new_morceau_title}' dans la base de données !")
                            st.session_state['generated_lyrics'] = "" # Effacer après sauvegarde
                            st.rerun()
                        else:
                            st.error("Échec de la sauvegarde des paroles.")
            
            elif save_lyrics_option == "Dans un Morceau Existant (Base de Données)":
                # MAJ : Utilise fsc.
                morceaux_df_all = fsc.get_all_morceaux()
                if not morceaux_df_all.empty:
                    morceau_to_update_id = st.selectbox(
                        "Sélectionnez le morceau à mettre à jour",
                        morceaux_df_all['ID_Morceau'].tolist(),
                        format_func=lambda x: f"{x} - {morceaux_df_all[morceaux_df_all['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
                        key="update_existing_morceau_lyrics_id"
                    )
                    if st.button("Mettre à jour les Paroles du Morceau Existant", key="update_lyrics_existing_btn"):
                        morceau_data_update = {
                            'Prompt_Generation_Paroles': st.session_state.generated_lyrics,
                            'Statut_Production': 'Paroles Générées'
                        }
                        if fsc.update_morceau_generes(morceau_to_update_id, morceau_data_update): # MAJ : Utilise fsc.
                            st.success(f"Paroles mises à jour pour le morceau '{morceau_to_update_id}' dans la base de données !")
                            st.session_state['generated_lyrics'] = ""
                            st.rerun()
                        else:
                            st.error("Échec de la mise à jour des paroles.")
                else:
                    st.info("Aucun morceau existant dans votre base de données.")

            elif save_lyrics_option == "Dans un fichier local":
                filename = st.text_input("Nom du fichier local (.txt)", value=f"paroles_{st.session_state.lyrics_genre_musical}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", key="local_lyrics_filename")
                if st.button("Sauvegarder les Paroles en local", key="save_lyrics_local_btn"):
                    file_path = os.path.join(GENERATED_TEXTS_DIR, filename)
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(st.session_state.generated_lyrics)
                        st.success(f"Paroles sauvegardées localement: {file_path}")
                        st.session_state['generated_lyrics'] = ""
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde locale des paroles: {e}")

    st.markdown("---")

    # --- Formulaire de Génération de Prompt Audio ---
    if content_type == "Prompt Audio (pour SUNO)":
        st.subheader("Générer un Prompt Audio Détaillé (pour SUNO)")
        
        # MAJ : Utilise fsc.
        styles_musicaux = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
        structures_song = ['N/A'] + fsc.get_all_structures_song()['ID_Structure'].tolist()
        types_voix = ['N/A'] + fsc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist()

        with st.form("audio_prompt_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Genre Musical", styles_musicaux, key="audio_genre_musical_input")
                st.selectbox("Mood Principal", moods, key="audio_mood_principal_input")
                st.text_input("Durée Estimée (ex: 03:30)", key="audio_duree_estimee_input")
                st.text_input("Instrumentation Principale (ex: Piano, Violoncelle, Pads)", key="audio_instrumentation_principale_input")
            with col2:
                st.text_input("Ambiance Sonore Spécifique", key="audio_ambiance_sonore_specifique_input")
                st.text_input("Effets de Production Dominants (ex: Réverbération luxuriante)", key="audio_effets_production_dominants_input")
                st.selectbox("Type de Voix Désirée", types_voix, key="audio_type_voix_desiree_input")
                st.text_input("Style Vocal Désiré (ex: Lyrique, Râpeux)", key="audio_style_vocal_desire_input")
                st.text_input("Caractère de la Voix (ex: Puissant, Doux)", key="audio_caractere_voix_desire_input")
                st.selectbox("Structure de Chanson", structures_song, key="audio_structure_song_input")

            submit_audio_prompt_button = st.form_submit_button("Générer le Prompt Audio")

        if submit_audio_prompt_button:
            if st.session_state.audio_genre_musical_input and st.session_state.audio_mood_principal_input:
                with st.spinner("L'Oracle génère le prompt audio..."):
                    generated_audio_prompt = go.generate_audio_prompt(
                        genre_musical=st.session_state.audio_genre_musical_input,
                        mood_principal=st.session_state.audio_mood_principal_input,
                        duree_estimee=st.session_state.audio_duree_estimee_input,
                        instrumentation_principale=st.session_state.audio_instrumentation_principale_input,
                        ambiance_sonore_specifique=st.session_state.audio_ambiance_sonore_specifique_input,
                        effets_production_dominants=st.session_state.audio_effets_production_dominants_input,
                        type_voix_desiree=st.session_state.audio_type_voix_desiree_input,
                        style_vocal_desire=st.session_state.audio_style_vocal_desire_input,
                        caractere_voix_desire=st.session_state.audio_caractere_voix_desire_input,
                        structure_song=st.session_state.audio_structure_song_input
                    )
                    st.session_state['generated_audio_prompt'] = generated_audio_prompt
                    st.success("Prompt Audio généré avec succès !")
            else:
                st.warning("Veuillez remplir les champs obligatoires (Genre Musical, Mood Principal).")

        if 'generated_audio_prompt' in st.session_state and st.session_state.generated_audio_prompt:
            st.markdown("---")
            st.subheader("Prompt Audio Généré (pour SUNO ou autre)")
            st.text_area("Copiez ce prompt pour votre générateur audio :", st.session_state.generated_audio_prompt, height=200, key="displayed_generated_audio_prompt")

            # MAJ : Utilise fsc.
            morceaux_df_all = fsc.get_all_morceaux()
            if not morceaux_df_all.empty:
                morceau_to_update_audio_id = st.selectbox(
                    "Liez ce prompt à un morceau existant (Base de Données) :",
                    morceaux_df_all['ID_Morceau'].tolist(),
                    format_func=lambda x: f"{x} - {morceaux_df_all[morceaux_df_all['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
                    key="update_existing_morceau_audio_prompt_id"
                )
                if st.button("Mettre à jour le Prompt Audio du Morceau Existant", key="update_audio_prompt_existing_btn"):
                    morceau_data_update = {
                        'Prompt_Generation_Audio': st.session_state.generated_audio_prompt,
                        'Statut_Production': 'Prompt Audio Généré'
                    }
                    if fsc.update_morceau_generes(morceau_to_update_audio_id, morceau_data_update): # MAJ : Utilise fsc.
                        st.success(f"Prompt Audio mis à jour pour le morceau '{morceau_to_update_audio_id}' !")
                        st.session_state['generated_audio_prompt'] = ""
                        st.rerun()
                    else:
                        st.error("Échec de la mise à jour du prompt audio.")
            else:
                st.info("Aucun morceau existant pour lier le prompt audio.")

    st.markdown("---")

    # --- Formulaire de Génération d'Idées de Titres ---
    if content_type == "Idées de Titres":
        st.subheader("Générer des Idées de Titres de Chansons")
        # MAJ : Utilise fsc.
        themes_list = [''] + fsc.get_all_themes()['ID_Theme'].tolist()
        genres_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

        with st.form("title_generator_form"):
            st.selectbox("Thème Principal", themes_list, key="title_theme_principal")
            st.selectbox("Genre Musical", genres_list, key="title_genre_musical")
            st.text_area("Extrait de paroles (optionnel, pour inspiration)", key="title_paroles_extrait")
            submit_title_button = st.form_submit_button("Générer les Titres")

        if submit_title_button:
            if st.session_state.title_theme_principal and st.session_state.title_genre_musical:
                with st.spinner("L'Oracle brainstorme des titres..."):
                    generated_titles = go.generate_title_ideas(
                        theme_principal=st.session_state.title_theme_principal,
                        genre_musical=st.session_state.title_genre_musical,
                        paroles_extrait=st.session_state.title_paroles_extrait
                    )
                    st.session_state['generated_titles'] = generated_titles
                    st.success("Idées de titres générées avec succès !")
            else:
                st.warning("Veuillez remplir les champs obligatoires (Thème Principal, Genre Musical).")
        
        if 'generated_titles' in st.session_state and st.session_state.generated_titles:
            st.markdown("---")
            st.subheader("Idées de Titres Générées")
            st.text_area("Copiez les titres ici :", st.session_state.generated_titles, height=250, key="displayed_generated_titles")

    st.markdown("---")

    # --- Formulaire de Génération de Description Marketing ---
    if content_type == "Description Marketing":
        st.subheader("Générer une Description Marketing")
        # MAJ : Utilise fsc.
        styles_musicaux_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods_list = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
        public_cible_list = [''] + fsc.get_all_public_cible()['ID_Public'].tolist()

        with st.form("marketing_copy_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Titre du Morceau/Album", key="marketing_titre_morceau")
                st.selectbox("Genre Musical", styles_musicaux_list, key="marketing_genre_musical")
            with col2:
                st.selectbox("Mood Principal", moods_list, key="marketing_mood_principal")
                st.selectbox("Public Cible", public_cible_list, key="marketing_marketing_public_cible") # Changed key
            st.text_input("Point Fort Principal (ex: 'son unique', 'message profond')", key="marketing_point_fort")
            submit_marketing_button = st.form_submit_button("Générer la Description Marketing")

            if submit_marketing_button:
                if all([st.session_state.marketing_titre_morceau, st.session_state.marketing_genre_musical,
                        st.session_state.marketing_mood_principal, st.session_state.marketing_marketing_public_cible,
                        st.session_state.marketing_point_fort]): # Check changed key
                    with st.spinner("L'Oracle rédige la description..."):
                        generated_marketing_copy = go.generate_marketing_copy(
                            titre_morceau=st.session_state.marketing_titre_morceau,
                            genre_musical=st.session_state.marketing_genre_musical,
                            mood_principal=st.session_state.marketing_mood_principal,
                            public_cible=st.session_state.marketing_marketing_public_cible, # Check changed key
                            point_fort_principal=st.session_state.marketing_point_fort
                        )
                        st.session_state['generated_marketing_copy'] = generated_marketing_copy
                        st.success("Description marketing générée avec succès !")
                else:
                    st.warning("Veuillez remplir tous les champs pour générer la description marketing.")
        
        if 'generated_marketing_copy' in st.session_state and st.session_state.generated_marketing_copy:
            st.markdown("---")
            st.subheader("Description Marketing Générée")
            st.text_area("Copiez la description ici :", st.session_state.generated_marketing_copy, height=150, key="displayed_generated_marketing_copy")

    st.markdown("---")

    # --- Formulaire de Génération de Prompt Pochette d'Album ---
    if content_type == "Prompt Pochette d'Album":
        st.subheader("Générer un Prompt pour Pochette d'Album (Midjourney/DALL-E)")
        # MAJ : Utilise fsc.
        styles_musicaux_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods_list = [''] + fsc.get_all_moods()['ID_Mood'].tolist()

        with st.form("album_art_prompt_form"):
            st.text_input("Nom de l'Album", key="album_art_nom_album")
            st.selectbox("Genre Dominant de l'Album", styles_musicaux_list, key="album_art_genre_dominant")
            st.text_area("Description du Concept de l'Album", key="album_art_description_concept")
            st.selectbox("Mood Principal Visuel", moods_list, key="album_art_mood_principal")
            st.text_input("Mots-clés Visuels Supplémentaires (ex: 'couleurs vives', 'style néon', 'minimaliste')", key="album_art_mots_cles_visuels")
            submit_album_art_button = st.form_submit_button("Générer le Prompt Visuel")

            if submit_album_art_button:
                if all([st.session_state.album_art_nom_album, st.session_state.album_art_genre_dominant,
                        st.session_state.album_art_description_concept, st.session_state.album_art_mood_principal]):
                    with st.spinner("L'Oracle imagine la pochette..."):
                        generated_album_art_prompt = go.generate_album_art_prompt(
                            nom_album=st.session_state.album_art_nom_album,
                            genre_dominant_album=st.session_state.album_art_genre_dominant,
                            description_concept_album=st.session_state.album_art_description_concept,
                            mood_principal=st.session_state.album_art_mood_principal,
                            mots_cles_visuels_suppl=st.session_state.album_art_mots_cles_visuels
                        )
                        st.session_state['generated_album_art_prompt'] = generated_album_art_prompt
                        st.success("Prompt de pochette d'album généré avec succès !")
                else:
                    st.warning("Veuillez remplir les champs obligatoires pour générer le prompt visuel.")
        
        if 'generated_album_art_prompt' in st.session_state and st.session_state.generated_album_art_prompt:
            st.markdown("---")
            st.subheader("Prompt de Pochette d'Album Généré")
            st.text_area("Copiez ce prompt pour votre générateur d'images :", st.session_state.generated_album_art_prompt, height=300, key="displayed_generated_album_art_prompt")

# --- Page : Générateur d'Harmonies (Création Musicale IA) ---
if st.session_state['current_page'] == 'Générateur d\'Harmonies':
    st.header("🎵 Générateur de Structures Harmoniques Complexes")
    st.write("Demandez à l'Oracle de générer des progressions d'accords, des voicings et des modulations.")

    # MAJ : Utilise fsc.
    genres_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
    moods_list = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
    instruments_list = [''] + fsc.get_all_instruments()['Nom_Instrument'].tolist()

    with st.form("harmonic_structure_form"):
        st.selectbox("Genre Musical", genres_list, key="harmony_genre_musical")
        st.selectbox("Mood Principal", moods_list, key="harmony_mood_principal")
        st.multiselect("Instrumentation Principale (sélectionnez plusieurs)", instruments_list, key="harmony_instrumentation")
        st.text_input("Tonalité de base (ex: C Majeur, Am)", key="harmony_tonalite_input")
        
        submit_harmony_button = st.form_submit_button("Générer la Structure Harmonique")

    if submit_harmony_button:
        if all([st.session_state.harmony_genre_musical, st.session_state.harmony_mood_principal, st.session_state.harmony_instrumentation]):
            with st.spinner("L'Oracle compose la structure harmonique..."):
                generated_harmony = go.generate_complex_harmonic_structure(
                    genre_musical=st.session_state.harmony_genre_musical,
                    mood_principal=st.session_state.harmony_mood_principal,
                    instrumentation=", ".join(st.session_state.harmony_instrumentation),
                    tonalite=st.session_state.harmony_tonalite_input
                )
                st.session_state['generated_harmony'] = generated_harmony
                st.success("Structure harmonique générée avec succès !")
        else:
            st.warning("Veuillez remplir tous les champs obligatoires.")

    if 'generated_harmony' in st.session_state and st.session_state.generated_harmony:
        st.markdown("---")
        st.subheader("Structure Harmonique Générée")
        st.text_area("Voici la structure harmonique proposée :", st.session_state.generated_harmony, height=500, key="displayed_generated_harmony")


# --- Page : Co-pilote Créatif (Création Musicale IA) ---
if st.session_state['current_page'] == 'Co-pilote Créatif':
    st.header("💡 Co-pilote Créatif de l'Oracle (Beta)")
    st.write("Laissez l'Oracle vous accompagner en temps réel pour l'écriture de paroles, la composition harmonique ou rythmique.")
    st.info("Cette fonctionnalité est en version Beta. Les suggestions sont basées sur votre input et le contexte défini.")

    co_pilot_type = st.radio(
        "Quel type de suggestion souhaitez-vous ?",
        ["Suite Lyrique", "Ligne de Basse", "Prochain Accord", "Idée Rythmique"],
        key="co_pilot_type_radio"
    )

    st.markdown("---")

    # Contexte global pour le co-pilote
    st.subheader("Contexte du Morceau")
    col_ctx1, col_ctx2 = st.columns(2)
    with col_ctx1:
        # MAJ : Utilise fsc.
        st.selectbox("Genre Musical du morceau", [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="copilot_genre_musical")
        st.selectbox("Mood du morceau", [''] + fsc.get_all_moods()['ID_Mood'].tolist(), key="copilot_mood_principal")
    with col_ctx2:
        # MAJ : Utilise fsc.
        st.selectbox("Thème Principal du morceau", [''] + fsc.get_all_themes()['ID_Theme'].tolist(), key="copilot_theme_principal")
        st.text_input("Mots-clés contextuels (ex: 'solitude urbaine', 'rythme entraînant')", key="copilot_context_keywords")
        
    # Construction du contexte pour l'IA
    full_context = f"Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}, Thème: {st.session_state.copilot_theme_principal}, Mots-clés: {st.session_state.copilot_context_keywords}"

    st.markdown("---")

    # --- Formulaire pour Suite Lyrique ---
    if co_pilot_type == "Suite Lyrique":
        st.subheader("Suggérer la Suite des Paroles")
        with st.form("copilot_lyrics_form"):
            st.text_area("Commencez à écrire vos paroles ici :", key="copilot_current_lyrics_input", height=100)
            submit_copilot_lyrics = st.form_submit_button("Suggérer la suite")

            if submit_copilot_lyrics:
                if st.session_state.copilot_current_lyrics_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
                    with st.spinner("L'Oracle brainstorme la suite des paroles..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_lyrics_input,
                            context=full_context,
                            type_suggestion="suite_lyrique"
                        )
                        st.session_state['copilot_lyrics_suggestion'] = suggestion
                        st.success("Suggestion de paroles prête !")
                else:
                    st.warning("Veuillez entrer du texte et définir le contexte musical pour obtenir une suggestion.")

        if 'copilot_lyrics_suggestion' in st.session_state and st.session_state.copilot_lyrics_suggestion:
            st.markdown("---")
            st.subheader("Suggestion de Paroles")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_lyrics_suggestion, height=200)
            if st.button("Utiliser cette suggestion", key="use_lyrics_suggestion"):
                st.session_state.copilot_current_lyrics_input += "\n" + st.session_state.copilot_lyrics_suggestion
                st.rerun()


    # --- Formulaire pour Ligne de Basse ---
    elif co_pilot_type == "Ligne de Basse":
        st.subheader("Suggérer une Ligne de Basse")
        with st.form("copilot_bass_form"):
            st.text_input("Décrivez le groove ou la progression d'accords actuelle (ex: 'groove funk sur Am - G - C - F')", key="copilot_current_bass_input")
            submit_copilot_bass = st.form_submit_button("Suggérer une ligne de basse")

            if submit_copilot_bass:
                if st.session_state.copilot_current_bass_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
                    with st.spinner("L'Oracle imagine la ligne de basse..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_bass_input,
                            context=full_context,
                            type_suggestion="ligne_basse"
                        )
                        st.session_state['copilot_bass_suggestion'] = suggestion
                        st.success("Suggestion de ligne de basse prête !")
                else:
                    st.warning("Veuillez décrire le contexte musical pour la ligne de basse.")

        if 'copilot_bass_suggestion' in st.session_state and st.session_state.copilot_bass_suggestion:
            st.markdown("---")
            st.subheader("Suggestion de Ligne de Basse")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_bass_suggestion, height=150)


    # --- Formulaire pour Prochain Accord ---
    elif co_pilot_type == "Prochain Accord":
        st.subheader("Suggérer le Prochain Accord")
        with st.form("copilot_chord_form"):
            st.text_input("Entrez l'accord actuel (ex: 'Cmaj7', 'Am')", key="copilot_current_chord_input")
            st.text_input("Tonalité du morceau (ex: 'C Majeur', 'A mineur')", key="copilot_tonalite_input")
            submit_copilot_chord = st.form_submit_button("Suggérer le prochain accord")

            if submit_copilot_chord:
                if all([st.session_state.copilot_current_chord_input, st.session_state.copilot_tonalite_input,
                        st.session_state.copilot_genre_musical, st.session_state.copilot_mood_principal]):
                    chord_context = f"Tonalité: {st.session_state.copilot_tonalite_input}, Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}"
                    with st.spinner("L'Oracle réfléchit aux harmonies..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_chord_input,
                            context=chord_context,
                            type_suggestion="prochain_accord"
                        )
                        st.session_state['copilot_chord_suggestion'] = suggestion
                        st.success("Suggestion d'accords prête !")
                else:
                    st.warning("Veuillez entrer l'accord actuel, la tonalité et le contexte.")

        if 'copilot_chord_suggestion' in st.session_state and st.session_state.copilot_chord_suggestion:
            st.markdown("---")
            st.subheader("Suggestions de Prochains Accords")
            st.text_area("Voici les options du Co-pilote :", st.session_state.copilot_chord_suggestion, height=200)

    # --- Formulaire pour Idée Rythmique ---
    elif co_pilot_type == "Idée Rythmique":
        st.subheader("Suggérer une Idée Rythmique")
        with st.form("copilot_rhythm_form"):
            st.text_input("Décrivez le feeling rythmique désiré (ex: 'un groove entraînant', 'un rythme brisé')", key="copilot_current_rhythm_input")
            submit_copilot_rhythm = st.form_submit_button("Suggérer un rythme")

            if submit_copilot_rhythm:
                if st.session_state.copilot_current_rhythm_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
                    rhythm_context = f"Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}"
                    with st.spinner("L'Oracle imagine un rythme..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_rhythm_input,
                            context=rhythm_context,
                            type_suggestion="idee_rythmique"
                        )
                        st.session_state['copilot_rhythm_suggestion'] = suggestion
                        st.success("Suggestion rythmique prête !")
                else:
                    st.warning("Veuillez décrire le feeling rythmique et le contexte musical.")

        if 'copilot_rhythm_suggestion' in st.session_state and st.session_state.copilot_rhythm_suggestion:
            st.markdown("---")
            st.subheader("Suggestion Rythmique")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_rhythm_suggestion, height=150)


# --- Page : Création Multimodale (Création Musicale IA) ---
if st.session_state['current_page'] == 'Création Multimodale':
    st.header("🎬 Création Multimodale Synchronisée")
    st.write("L'Oracle génère des prompts cohérents pour vos paroles, votre audio (pour SUNO) et vos visuels (pour Midjourney/DALL-E), assurant une harmonie parfaite de votre œuvre.")

    # MAJ : Utilise fsc.
    themes_list = [''] + fsc.get_all_themes()['ID_Theme'].tolist()
    genres_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
    moods_list = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
    artistes_ia_list = [''] + fsc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()

    with st.form("multimodal_creation_form"):
        col_multi1, col_multi2 = st.columns(2)
        with col_multi1:
            st.selectbox("Thème Principal", themes_list, key="multi_main_theme")
            st.selectbox("Genre Musical Général", genres_list, key="multi_main_genre")
        with col_multi2:
            st.selectbox("Mood Général", moods_list, key="multi_main_mood")
            st.selectbox("Artiste IA Associé", artistes_ia_list, key="multi_artiste_ia_name")
            
        st.text_input("Longueur Estimée du Morceau (ex: '03:45')", key="multi_longueur_morceau")

        submit_multimodal_button = st.form_submit_button("Générer les Prompts Multimodaux")

        if submit_multimodal_button:
            if all([st.session_state.multi_main_theme, st.session_state.multi_main_genre,
                    st.session_state.multi_main_mood, st.session_state.multi_artiste_ia_name,
                    st.session_state.multi_longueur_morceau]):
                with st.spinner("L'Oracle orchestre votre création multimodale..."):
                    multimodal_prompts = go.generate_multimodal_content_prompts(
                        main_theme=st.session_state.multi_main_theme,
                        main_genre=st.session_state.multi_main_genre,
                        main_mood=st.session_state.multi_main_mood,
                        longueur_morceau=st.session_state.multi_longueur_morceau,
                        artiste_ia_name=st.session_state.multi_artiste_ia_name
                    )
                    st.session_state['multimodal_prompts'] = multimodal_prompts
                    st.success("Prompts multimodaux générés avec succès !")
            else:
                st.warning("Veuillez remplir tous les champs obligatoires pour la création multimodale.")

    if 'multimodal_prompts' in st.session_state and st.session_state.multimodal_prompts:
        st.markdown("---")
        st.subheader("Prompts Multimodaux Générés")
        
        st.write("### Prompt pour les Paroles de Chanson :")
        st.text_area("Copiez pour votre parolier ou pour affiner :", st.session_state.multimodal_prompts.get("paroles_prompt", ""), height=300, key="multi_lyrics_output")

        st.write("### Prompt pour la Génération Audio (pour SUNO) :")
        st.text_area("Copiez pour SUNO ou votre générateur audio :", st.session_state.multimodal_prompts.get("audio_suno_prompt", ""), height=200, key="multi_audio_output")

        st.write("### Prompt pour l'Image de Pochette (Midjourney/DALL-E) :")
        st.text_area("Copiez pour votre générateur d'images :", st.session_state.multimodal_prompts.get("image_prompt", ""), height=250, key="multi_image_output")


# --- Page : Mes Morceaux (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Mes Morceaux':
    st.header("🎶 Mes Morceaux Générés")
    st.write("Gérez et consultez toutes vos créations musicales, qu'elles soient entièrement générées par l'IA ou co-créées.")

    morceaux_df = fsc.get_all_morceaux() # MAJ : Utilise fsc.
    
    tab1, tab2, tab3 = st.tabs(["Voir/Rechercher Morceaux", "Ajouter un Nouveau Morceau", "Mettre à Jour/Supprimer Morceau"])

    with tab1:
        st.subheader("Voir et Rechercher des Morceaux")
        if not morceaux_df.empty:
            # Recherche simple
            search_query = st.text_input("Rechercher par titre, genre ou mots-clés", key="search_morceaux")
            if search_query:
                filtered_df = morceaux_df[morceaux_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_df = morceaux_df

            # Affichage avec formatage
            display_dataframe(ut.format_dataframe_for_display(filtered_df), key="morceaux_display")
        else:
            st.info("Aucun morceau enregistré pour le moment.")

    with tab2:
        st.subheader("Ajouter un Nouveau Morceau")
        
        # Récupération des données pour les selectbox (MAJ : Utilise fsc.)
        artistes_ia_list = [''] + fsc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()
        albums_list = [''] + fsc.get_all_albums()['ID_Album'].tolist()
        genres_musicaux = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
        themes = [''] + fsc.get_all_themes()['ID_Theme'].tolist()
        styles_lyriques = [''] + fsc.get_all_styles_lyriques()['ID_Style_Lyrique'].tolist()
        structures_song = [''] + fsc.get_all_structures_song()['ID_Structure'].tolist()
        types_voix = [''] + fsc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist()

        with st.form("add_morceau_form"):
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                new_titre = st.text_input("Titre du Morceau", key="add_morceau_titre")
                new_statut = st.selectbox("Statut de Production", ["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"], key="add_morceau_statut")
                new_duree = st.text_input("Durée Estimée (ex: 03:45)", key="add_morceau_duree")
                
                st.selectbox("Style Musical Principal", genres_musicaux, key="add_morceau_style_musical")
                st.selectbox("Mood Principal", moods, key="add_morceau_mood_principal")
                st.selectbox("Thème Principal Lyrique", themes, key="add_morceau_theme_lyrique")
                st.selectbox("Style Lyrique", styles_lyriques, key="add_morceau_style_lyrique_selection")
                st.selectbox("Structure de Chanson", structures_song, key="add_morceau_structure_chanson")
                st.text_area("Mots-clés de Génération (séparés par des virgules)", key="add_morceau_mots_cles_gen")
                st.selectbox("Langue des Paroles", [''] + ["Français", "Anglais", "Espagnol"], key="add_morceau_langue_paroles")
                st.selectbox("Niveau de Langage Paroles", [''] + ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], key="add_morceau_niveau_langage")
                st.selectbox("Imagerie Texte", [''] + ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], key="add_morceau_imagerie_texte")
                
            with col_add2:
                new_artiste_ia = st.selectbox("Artiste IA Associé", artistes_ia_list, key="add_morceau_artiste_ia")
                new_album_associe = st.selectbox("Album Associé", albums_list, key="add_morceau_album_associe")
                
                st.text_area("Prompt Génération Audio (pour SUNO)", key="add_morceau_prompt_audio", height=150)
                st.text_area("Prompt Génération Paroles", key="add_morceau_prompt_paroles", height=150)
                st.text_input("Instrumentation Principale", key="add_morceau_instrumentation")
                st.text_input("Ambiance Sonore Spécifique", key="add_morceau_ambiance_sonore")
                st.text_input("Effets Production Dominants", key="add_morceau_effets_prod")
                st.selectbox("Type de Voix Désirée", types_voix, key="add_morceau_type_voix")
                st.text_input("Style Vocal Désiré (ex: Lyrique, Râpeux)", key="add_morceau_style_vocal")
                st.text_input("Caractère Voix Désiré (ex: Puissant, Doux)", key="add_morceau_caractere_voix")
                st.text_input("Mots-clés SEO", key="add_morceau_mots_cles_seo")
                st.text_area("Description Courte Marketing", key="add_morceau_desc_marketing", height=100)
                
                # --- Téléchargement de Fichiers ---
                st.markdown("##### Téléchargement de Fichiers Locaux")
                uploaded_audio_file = st.file_uploader("Uploader Fichier Audio (.mp3, .wav)", type=["mp3", "wav"], key="upload_audio_morceau")
                uploaded_cover_file = st.file_uploader("Uploader Image de Cover (.jpg, .png)", type=["jpg", "png"], key="upload_cover_morceau")

            submit_new_morceau = st.form_submit_button("Ajouter le Morceau")

            if submit_new_morceau:
                if not new_titre:
                    st.error("Le titre du morceau est obligatoire.")
                elif new_artiste_ia == '':
                    st.error("Veuillez sélectionner un Artiste IA associé.")
                else:
                    # Sauvegarder les fichiers uploadés
                    audio_path = ut.save_uploaded_file(uploaded_audio_file, AUDIO_CLIPS_DIR)
                    cover_path = ut.save_uploaded_file(uploaded_cover_file, SONG_COVERS_DIR)

                    new_morceau_data = {
                        'Titre_Morceau': st.session_state.add_morceau_titre,
                        'Statut_Production': st.session_state.add_morceau_statut,
                        'Durée_Estimee': st.session_state.add_morceau_duree,
                        'ID_Album_Associe': st.session_state.add_morceau_album_associe,
                        'ID_Artiste_IA': st.session_state.add_morceau_artiste_ia,
                        'Prompt_Generation_Audio': st.session_state.add_morceau_prompt_audio,
                        'Prompt_Generation_Paroles': st.session_state.add_morceau_prompt_paroles,
                        'ID_Style_Musical_Principal': st.session_state.add_morceau_style_musical,
                        'ID_Style_Lyrique_Principal': st.session_state.add_morceau_style_lyrique_selection,
                        'Theme_Principal_Lyrique': st.session_state.add_morceau_theme_lyrique,
                        'Mots_Cles_Generation': st.session_state.add_morceau_mots_cles_gen,
                        'Langue_Paroles': st.session_state.add_morceau_langue_paroles,
                        'Niveau_Langage_Paroles': st.session_state.add_morceau_niveau_langage,
                        'Imagerie_Texte': st.session_state.add_morceau_imagerie_texte,
                        'Structure_Chanson_Specifique': st.session_state.add_morceau_structure_chanson,
                        'Instrumentation_Principale': st.session_state.add_morceau_instrumentation,
                        'Ambiance_Sonore_Specifique': st.session_state.add_morceau_ambiance_sonore,
                        'Effets_Production_Dominants': st.session_state.add_morceau_effets_prod,
                        'Type_Voix_Desiree': st.session_state.add_morceau_type_voix,
                        'Style_Vocal_Desire': st.session_state.add_morceau_style_vocal,
                        'Caractere_Voix_Desire': st.session_state.add_morceau_caractere_voix,
                        'URL_Audio_Local': audio_path if audio_path else '',
                        'URL_Cover_Album': cover_path if cover_path else '',
                        'URL_Video_Clip_Associe': '',
                        'Mots_Cles_SEO': st.session_state.add_morceau_mots_cles_seo,
                        'Description_Courte_Marketing': st.session_state.add_morceau_desc_marketing
                    }
                    
                    if fsc.add_morceau_generes(new_morceau_data): # MAJ : Utilise fsc.
                        st.success(f"Morceau '{new_titre}' ajouté avec succès à la base de données !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du morceau.")

    with tab3:
        st.subheader("Mettre à Jour ou Supprimer un Morceau")
        if not morceaux_df.empty:
            morceau_options_display = morceaux_df.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}", axis=1).tolist()
            morceau_to_select_display = st.selectbox(
                "Sélectionnez le Morceau à modifier/supprimer",
                morceau_options_display,
                key="select_morceau_to_edit"
            )
            morceau_to_select = morceaux_df[morceaux_df.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}" == morceau_to_select_display, axis=1)]['ID_Morceau'].iloc[0]
            
            if morceau_to_select:
                selected_morceau = morceaux_df[morceaux_df['ID_Morceau'] == morceau_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_morceau['Titre_Morceau']}")

                # Récupération des données pour les selectbox (MAJ : Utilise fsc.)
                artistes_ia_list_upd = [''] + fsc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()
                albums_list_upd = [''] + fsc.get_all_albums()['ID_Album'].tolist()
                genres_musicaux_upd = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
                moods_upd = [''] + fsc.get_all_moods()['ID_Mood'].tolist()
                themes_upd = [''] + fsc.get_all_themes()['ID_Theme'].tolist()
                styles_lyriques_upd = [''] + fsc.get_all_styles_lyriques()['ID_Style_Lyrique'].tolist()
                structures_song_upd = [''] + fsc.get_all_structures_song()['ID_Structure'].tolist()
                types_voix_upd = [''] + fsc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist()

                with st.form("update_delete_morceau_form"):
                    col_upd1, col_upd2 = st.columns(2)
                    with col_upd1:
                        upd_titre = st.text_input("Titre du Morceau", value=selected_morceau['Titre_Morceau'], key="upd_morceau_titre")
                        upd_statut = st.selectbox("Statut de Production", ["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"], index=["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"].index(selected_morceau['Statut_Production']), key="upd_morceau_statut")
                        upd_duree = st.text_input("Durée Estimée (ex: 03:45)", value=selected_morceau['Durée_Estimee'], key="upd_morceau_duree")

                        upd_style_musical = st.selectbox("Style Musical Principal", genres_musicaux_upd, index=genres_musicaux_upd.index(selected_morceau['ID_Style_Musical_Principal']) if selected_morceau['ID_Style_Musical_Principal'] in genres_musicaux_upd else 0, key="upd_morceau_style_musical")
                        upd_mood_principal = st.selectbox("Mood Principal", moods_upd, index=moods_upd.index(selected_morceau['Ambiance_Sonore_Specifique']) if selected_morceau['Ambiance_Sonore_Specifique'] in moods_upd else 0, key="upd_morceau_mood_principal")
                        upd_theme_lyrique = st.selectbox("Thème Principal Lyrique", themes_upd, index=themes_upd.index(selected_morceau['Theme_Principal_Lyrique']) if selected_morceau['Theme_Principal_Lyrique'] in themes_upd else 0, key="upd_morceau_theme_lyrique")
                        upd_style_lyrique_selection = st.selectbox("Style Lyrique", styles_lyriques_upd, index=styles_lyriques_upd.index(selected_morceau['ID_Style_Lyrique_Principal']) if selected_morceau['ID_Style_Lyrique_Principal'] in styles_lyriques_upd else 0, key="upd_morceau_style_lyrique_selection")
                        upd_structure_chanson = st.selectbox("Structure de Chanson", structures_song_upd, index=structures_song_upd.index(selected_morceau['Structure_Chanson_Specifique']) if selected_morceau['Structure_Chanson_Specifique'] in structures_song_upd else 0, key="upd_morceau_structure_chanson")
                        upd_mots_cles_gen = st.text_area("Mots-clés de Génération (séparés par des virgules)", value=selected_morceau['Mots_Cles_Generation'], key="upd_morceau_mots_cles_gen")
                        upd_langue_paroles = st.selectbox("Langue des Paroles", ["Français", "Anglais", "Espagnol"], index=["Français", "Anglais", "Espagnol"].index(selected_morceau['Langue_Paroles']) if selected_morceau['Langue_Paroles'] in ["Français", "Anglais", "Espagnol"] else 0, key="upd_morceau_langue_paroles")
                        upd_niveau_langage = st.selectbox("Niveau de Langage Paroles", ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], index=["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"].index(selected_morceau['Niveau_Langage_Paroles']) if selected_morceau['Niveau_Langage_Paroles'] in ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"] else 0, key="upd_morceau_niveau_langage")
                        upd_imagerie_texte = st.selectbox("Imagerie Texte", ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], index=["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"].index(selected_morceau['Imagerie_Texte']) if selected_morceau['Imagerie_Texte'] in ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"] else 0, key="upd_morceau_imagerie_texte")
                        
                    with col_upd2:
                        upd_artiste_ia = st.selectbox("Artiste IA Associé", artistes_ia_list_upd, index=artistes_ia_list_upd.index(selected_morceau['ID_Artiste_IA']) if selected_morceau['ID_Artiste_IA'] in artistes_ia_list_upd else 0, key="upd_morceau_artiste_ia")
                        upd_album_associe = st.selectbox("Album Associé", albums_list_upd, index=albums_list_upd.index(selected_morceau['ID_Album_Associe']) if selected_morceau['ID_Album_Associe'] in albums_list_upd else 0, key="upd_morceau_album_associe")
                        
                        upd_prompt_audio = st.text_area("Prompt Génération Audio (pour SUNO)", value=selected_morceau['Prompt_Generation_Audio'], height=150, key="upd_morceau_prompt_audio")
                        upd_prompt_paroles = st.text_area("Prompt Génération Paroles", value=selected_morceau['Prompt_Generation_Paroles'], height=150, key="upd_morceau_prompt_paroles")
                        upd_instrumentation = st.text_input("Instrumentation Principale", value=selected_morceau['Instrumentation_Principale'], key="upd_morceau_instrumentation")
                        upd_ambiance_sonore = st.text_input("Ambiance Sonore Spécifique", value=selected_morceau['Ambiance_Sonore_Specifique'], key="upd_morceau_ambiance_sonore")
                        upd_effets_prod = st.text_input("Effets Production Dominants", value=selected_morceau['Effets_Production_Dominants'], key="upd_morceau_effets_prod")
                        upd_type_voix = st.selectbox("Type de Voix Désirée", types_voix_upd, index=types_voix_upd.index(selected_morceau['Type_Voix_Desiree']) if selected_morceau['Type_Voix_Desiree'] in types_voix_upd else 0, key="upd_morceau_type_voix")
                        upd_style_vocal = st.text_input("Style Vocal Désiré", value=selected_morceau['Style_Vocal_Desire'], key="upd_morceau_style_vocal")
                        upd_caractere_voix = st.text_input("Caractère Voix Désiré", value=selected_morceau['Caractere_Voix_Desire'], key="upd_morceau_caractere_voix")
                        upd_mots_cles_seo = st.text_input("Mots-clés SEO", value=selected_morceau['Mots_Cles_SEO'], key="upd_morceau_mots_cles_seo")
                        upd_desc_marketing = st.text_area("Description Courte Marketing", value=selected_morceau['Description_Courte_Marketing'], height=100, key="upd_morceau_desc_marketing")
                        
                        # Affichage des chemins de fichiers existants et upload pour mise à jour
                        st.markdown("##### Fichiers Locaux Existants")
                        if selected_morceau['URL_Audio_Local'] and os.path.exists(os.path.join(AUDIO_CLIPS_DIR, selected_morceau['URL_Audio_Local'])):
                            st.text_input("Chemin Audio Local Actuel", value=selected_morceau['URL_Audio_Local'], disabled=True, key="current_audio_path")
                            st.audio(os.path.join(AUDIO_CLIPS_DIR, selected_morceau['URL_Audio_Local']), format="audio/mp3", start_time=0)
                        if selected_morceau['URL_Cover_Album'] and os.path.exists(os.path.join(SONG_COVERS_DIR, selected_morceau['URL_Cover_Album'])):
                            st.text_input("Chemin Cover Album Actuel", value=selected_morceau['URL_Cover_Album'], disabled=True, key="current_cover_path")
                            st.image(os.path.join(SONG_COVERS_DIR, selected_morceau['URL_Cover_Album']), width=150)

                        uploaded_audio_file_upd = st.file_uploader("Uploader Nouveau Fichier Audio (.mp3, .wav)", type=["mp3", "wav"], key="upload_audio_morceau_upd")
                        uploaded_cover_file_upd = st.file_uploader("Uploader Nouvelle Image de Cover (.jpg, .png)", type=["jpg", "png"], key="upload_cover_morceau_upd")


                    col_form_buttons = st.columns(2)
                    with col_form_buttons[0]:
                        submit_update_morceau = st.form_submit_button("Mettre à Jour le Morceau")
                    with col_form_buttons[1]:
                        submit_delete_morceau_trigger = st.form_submit_button("Supprimer le Morceau", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_morceau:
                        audio_path_upd = selected_morceau['URL_Audio_Local']
                        if uploaded_audio_file_upd:
                            new_audio_path = ut.save_uploaded_file(uploaded_audio_file_upd, AUDIO_CLIPS_DIR)
                            if new_audio_path: audio_path_upd = new_audio_path

                        cover_path_upd = selected_morceau['URL_Cover_Album']
                        if uploaded_cover_file_upd:
                            new_cover_path = ut.save_uploaded_file(uploaded_cover_file_upd, SONG_COVERS_DIR)
                            if new_cover_path: cover_path_upd = new_cover_path

                        morceau_data_update = {
                            'Titre_Morceau': upd_titre,
                            'Statut_Production': upd_statut,
                            'Durée_Estimee': upd_duree,
                            'ID_Album_Associe': upd_album_associe,
                            'ID_Artiste_IA': upd_artiste_ia,
                            'Prompt_Generation_Audio': upd_prompt_audio,
                            'Prompt_Generation_Paroles': upd_prompt_paroles,
                            'ID_Style_Musical_Principal': upd_style_musical,
                            'ID_Style_Lyrique_Principal': upd_style_lyrique_selection,
                            'Theme_Principal_Lyrique': upd_theme_lyrique,
                            'Mots_Cles_Generation': upd_mots_cles_gen,
                            'Langue_Paroles': upd_langue_paroles,
                            'Niveau_Langage_Paroles': upd_niveau_langage,
                            'Imagerie_Texte': upd_imagerie_texte,
                            'Structure_Chanson_Specifique': upd_structure_chanson,
                            'Instrumentation_Principale': upd_instrumentation,
                            'Ambiance_Sonore_Specifique': upd_ambiance_sonore,
                            'Effets_Production_Dominants': upd_effets_prod,
                            'Type_Voix_Desiree': upd_type_voix,
                            'Style_Vocal_Desire': upd_style_vocal,
                            'Caractere_Voix_Desire': upd_caractere_voix,
                            'URL_Audio_Local': audio_path_upd,
                            'URL_Cover_Album': cover_path_upd,
                            'Mots_Cles_SEO': upd_mots_cles_seo,
                            'Description_Courte_Marketing': upd_desc_marketing
                        }
                        if fsc.update_morceau_generes(morceau_to_select, morceau_data_update): # MAJ : Utilise fsc.
                            st.success(f"Morceau '{upd_titre}' mis à jour avec succès !")
                            st.rerun()
                        else:
                            st.error("Échec de la mise à jour du morceau.")
                    
                    if submit_delete_morceau_trigger:
                        st.session_state['confirm_delete_morceau_id'] = morceau_to_select
                        st.session_state['confirm_delete_morceau_name'] = selected_morceau['Titre_Morceau']
                        st.rerun()
        else:
            st.info("Aucun morceau à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_morceau_id']:
        st.error(f"Confirmez-vous la suppression définitive du morceau '{st.session_state.confirm_delete_morceau_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement", key="final_confirm_delete_morceau"):
                if fsc.delete_morceau_generes(st.session_state.confirm_delete_morceau_id): # MAJ : Utilise fsc.
                    st.success(f"Morceau '{st.session_state.confirm_delete_morceau_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_morceau_id'] = None # Nettoyer l'état
                    st.rerun()
                else:
                    st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler", key="cancel_delete_morceau"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_morceau_id'] = None # Nettoyer l'état
                st.rerun()


# --- Page : Lecteur Audios (Expérience Musicale Interactive) ---
if st.session_state['current_page'] == 'Lecteur Audios':
    st.header("🎵 Lecteur Audios de l'Architecte Ω")
    st.write("Écoutez vos morceaux générés par l'IA, visualisez leurs paroles et marquez vos favoris. Une expérience immersive pour vos créations.")

    morceaux_df_player = fsc.get_all_morceaux() # MAJ : Utilise fsc.
    paroles_existantes_df_player = fsc.get_all_paroles_existantes() # MAJ : Utilise fsc.

    if not morceaux_df_player.empty:
        # Filtrage et sélection du morceau
        col_select_track, col_filter_track = st.columns([0.7, 0.3])
        
        with col_filter_track:
            st.subheader("Filtres")
            filter_genre = st.selectbox("Filtrer par Genre", ['Tous'] + morceaux_df_player['ID_Style_Musical_Principal'].unique().tolist(), key="player_filter_genre")
            filter_artist = st.selectbox("Filtrer par Artiste IA", ['Tous'] + morceaux_df_player['ID_Artiste_IA'].unique().tolist(), key="player_filter_artist")
            filter_status = st.selectbox("Filtrer par Statut", ['Tous'] + morceaux_df_player['Statut_Production'].unique().tolist(), key="player_filter_status")

        filtered_morceaux_player = morceaux_df_player.copy()
        if filter_genre != 'Tous':
            filtered_morceaux_player = filtered_morceaux_player[filtered_morceaux_player['ID_Style_Musical_Principal'] == filter_genre]
        if filter_artist != 'Tous':
            filtered_morceaux_player = filtered_morceaux_player[filtered_morceaux_player['ID_Artiste_IA'] == filter_artist]
        if filter_status != 'Tous':
            filtered_morceaux_player = filtered_morceaux_player[filtered_morceaux_player['Statut_Production'] == filter_status]

        with col_select_track:
            st.subheader("Sélection du Morceau")
            if not filtered_morceaux_player.empty:
                track_options = filtered_morceaux_player.apply(lambda row: f"{row['Titre_Morceau']} ({row['ID_Morceau']}) - {row['ID_Artiste_IA']}", axis=1).tolist()
                selected_track_display = st.selectbox("Choisissez un morceau à écouter", track_options, key="player_select_track")

                selected_morceau_id = selected_track_display.split('(')[1].split(')')[0] if selected_track_display else None
                st.session_state['selected_morceau_id'] = selected_morceau_id
                
                current_morceau = filtered_morceaux_player[filtered_morceaux_player['ID_Morceau'] == st.session_state.selected_morceau_id].iloc[0] if st.session_state.selected_morceau_id else None
            else:
                st.info("Aucun morceau ne correspond à vos filtres.")
                current_morceau = None
                st.session_state['selected_morceau_id'] = None

        if current_morceau is not None:
            st.markdown("---")
            st.subheader(f"En cours de lecture : {current_morceau['Titre_Morceau']}")
            
            audio_file_path = os.path.join(AUDIO_CLIPS_DIR, current_morceau['URL_Audio_Local'])
            cover_image_path = os.path.join(SONG_COVERS_DIR, current_morceau['URL_Cover_Album'])

            col_player_info, col_player_audio = st.columns([0.3, 0.7])

            with col_player_info:
                if current_morceau['URL_Cover_Album'] and os.path.exists(cover_image_path):
                    st.image(cover_image_path, caption=current_morceau['Titre_Morceau'], use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/200?text=Pas+de+Cover", caption="Aucune image de cover", use_container_width=True)
                
                st.markdown(f"**Artiste IA :** {current_morceau['ID_Artiste_IA']}")
                st.markdown(f"**Genre :** {current_morceau['ID_Style_Musical_Principal']}")
                st.markdown(f"**Durée Estimée :** {current_morceau['Durée_Estimee']}")
                st.markdown(f"**Statut :** {current_morceau['Statut_Production']}")

                # --- Fonctionnalité "Favori" ---
                # Vérifier si la colonne 'Favori' existe dans le DataFrame chargé
                # Note: Firestore ne force pas les schémas, donc 'Favori' peut manquer si aucun document ne l'a.
                if 'Favori' in morceaux_df_player.columns:
                    current_favorite_status = current_morceau.get('Favori', 'FAUX')
                    is_favorite_bool = ut.parse_boolean_string(str(current_favorite_status))

                    if is_favorite_bool:
                        if st.button("💔 Retirer des Favoris", key="remove_from_favorite_button"):
                            fsc.update_morceau_generes(current_morceau['ID_Morceau'], {'Favori': 'FAUX'}) # MAJ : Utilise fsc.
                            st.success("Retiré des favoris.")
                            st.rerun()
                    else:
                        if st.button("❤️ Ajouter aux Favoris", key="add_to_favorite_button_persistant"):
                            fsc.update_morceau_generes(current_morceau['ID_Morceau'], {'Favori': 'VRAI'}) # MAJ : Utilise fsc.
                            st.success("Ajouté aux favoris !")
                            st.rerun()
                else:
                    st.info("Ajoutez un champ 'Favori' (VRAI/FAUX) aux documents de votre collection 'MORCEAUX_GENERES' pour activer la persistance des favoris.")
                    st.button("❤️ Ajouter aux Favoris (non persistant)", key="add_to_favorite_button_no_persist") # Bouton non persistant si champ manquant
                
            with col_player_audio:
                if current_morceau['URL_Audio_Local'] and os.path.exists(audio_file_path):

                    st.audio(audio_file_path, start_time=0) 
                else:
                    st.warning("Fichier audio non trouvé localement ou URL non renseignée.")
                    if current_morceau['Prompt_Generation_Audio']:
                        st.info("Vous pouvez utiliser le prompt audio ci-dessous avec SUNO ou un autre générateur :")
                        st.text_area("Prompt Génération Audio", value=current_morceau['Prompt_Generation_Audio'], height=150, disabled=True)

                # --- Affichage des Paroles Associées ---
                st.markdown("---")
                st.subheader("Paroles")
                
                lyrics_from_morceau = current_morceau.get('Prompt_Generation_Paroles', '')
                
                lyrics_from_existing = ''
                if not paroles_existantes_df_player.empty:
                    matching_paroles = paroles_existantes_df_player[paroles_existantes_df_player['ID_Morceau'] == current_morceau['ID_Morceau']]
                    if not matching_paroles.empty:
                        lyrics_from_existing = matching_paroles['Paroles_Existantes'].iloc[0]

                displayed_lyrics = lyrics_from_morceau if lyrics_from_morceau else lyrics_from_existing

                if displayed_lyrics:
                    st.text_area("Paroles du Morceau :", value=displayed_lyrics, height=400, key="player_displayed_lyrics")
                else:
                    st.info("Aucune parole disponible pour ce morceau.")
                    st.markdown("Vous pouvez générer des paroles via la page 'Générateur de Contenu' et les lier à ce morceau.")

                # --- Visualiseur Audio Réactif (Conceptuel) ---
                st.markdown("---")
                st.subheader("Visualiseur Audio (Conceptuel)")
                st.info("Un visualiseur audio réactif pourrait être implémenté ici pour ajouter une dimension visuelle à l'écoute. Pour l'instant, c'est une idée à développer (nécessite des librairies complexes ou intégrations JS).")
                st.markdown("![Visualiseur conceptuel](https://via.placeholder.com/600x150?text=Visualiseur+Audio+Conceptuel)", unsafe_allow_html=True)


    else:
        st.info("Votre collection de morceaux est vide. Allez dans 'Mes Morceaux' pour ajouter vos premières créations !")

# --- Page : Mes Albums (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Mes Albums':
    st.header("💿 Mes Albums")
    st.write("Gérez vos albums, leurs pochettes, leurs descriptions et leurs dates de sortie.")

    albums_df = fsc.get_all_albums() # MAJ : Utilise fsc.

    tab_albums_view, tab_albums_add, tab_albums_edit = st.tabs(["Voir/Rechercher Albums", "Ajouter un Nouvel Album", "Mettre à Jour/Supprimer Album"])

    with tab_albums_view:
        st.subheader("Voir et Rechercher des Albums")
        if not albums_df.empty:
            search_album_query = st.text_input("Rechercher par nom d'album ou artiste", key="search_albums")
            if search_album_query:
                filtered_albums_df = albums_df[albums_df.apply(lambda row: search_album_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_albums_df = albums_df
            display_dataframe(ut.format_dataframe_for_display(filtered_albums_df), key="albums_display")
        else:
            st.info("Aucun album enregistré pour le moment.")

    with tab_albums_add:
        st.subheader("Ajouter un Nouvel Album")
        
        # MAJ : Utilise fsc.
        artistes_ia_list = [''] + fsc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()
        genres_musicaux = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

        with st.form("add_album_form"):
            new_album_nom = st.text_input("Nom de l'Album", key="add_album_nom")
            new_album_date_sortie = st.date_input("Date de Sortie", value=datetime.now(), key="add_album_date_sortie")
            new_album_artiste_ia = st.selectbox("Artiste IA Principal", artistes_ia_list, key="add_album_artiste_ia")
            new_album_genre = st.selectbox("Genre Dominant de l'Album", genres_musicaux, key="add_album_genre")
            new_album_description = st.text_area("Description Thématique de l'Album", key="add_album_description")
            
            # --- Téléchargement de la Pochette ---
            uploaded_album_cover = st.file_uploader("Uploader Image de Pochette (.jpg, .png)", type=["jpg", "png"], key="upload_album_cover")
            new_album_mots_cles_seo = st.text_input("Mots-clés SEO de l'Album", key="add_album_mots_cles_seo")

            submit_new_album = st.form_submit_button("Ajouter l'Album")

            if submit_new_album:
                if not new_album_nom:
                    st.error("Le nom de l'album est obligatoire.")
                elif new_album_artiste_ia == '':
                    st.error("Veuillez sélectionner un Artiste IA principal.")
                else:
                    cover_path_album = ut.save_uploaded_file(uploaded_album_cover, ALBUM_COVERS_DIR)

                    new_album_data = {
                        'Nom_Album': new_album_nom,
                        'Date_Sortie_Prevue': new_album_date_sortie.strftime('%Y-%m-%d'),
                        'Statut_Album': 'En Production', # Default status
                        'Description_Concept_Album': new_album_description,
                        'ID_Artiste_IA_Principal': new_album_artiste_ia,
                        'Genre_Dominant_Album': new_album_genre,
                        'URL_Cover_Principale': cover_path_album if cover_path_album else '',
                        'Mots_Cles_Album_SEO': new_album_mots_cles_seo
                    }
                    if fsc.add_album(new_album_data): # MAJ : Utilise fsc.
                        st.success(f"Album '{new_album_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de l'album.")

    with tab_albums_edit:
        st.subheader("Mettre à Jour ou Supprimer un Album")
        if not albums_df.empty:
            album_options_display = albums_df.apply(lambda row: f"{row['ID_Album']} - {row['Nom_Album']}", axis=1).tolist()
            album_to_select_display = st.selectbox(
                "Sélectionnez l'Album à modifier/supprimer",
                album_options_display,
                key="select_album_to_edit"
            )
            album_to_select = albums_df[albums_df.apply(lambda row: f"{row['ID_Album']} - {row['Nom_Album']}" == album_to_select_display, axis=1)]['ID_Album'].iloc[0]
            
            if album_to_select:
                selected_album = albums_df[albums_df['ID_Album'] == album_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_album['Nom_Album']}")

                # MAJ : Utilise fsc.
                artistes_ia_list_upd = [''] + fsc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()
                genres_musicaux_upd = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

                with st.form("update_delete_album_form"):
                    upd_album_nom = st.text_input("Nom de l'Album", value=selected_album['Nom_Album'], key="upd_album_nom")
                    upd_album_date_sortie = st.date_input("Date de Sortie", value=pd.to_datetime(selected_album['Date_Sortie_Prevue']), key="upd_album_date_sortie")
                    upd_album_statut = st.selectbox("Statut de l'Album", ["En Production", "En Idée", "Mix/Master", "Publié", "Archivé"], index=["En Production", "En Idée", "Mix/Master", "Publié", "Archivé"].index(selected_album['Statut_Album']) if selected_album['Statut_Album'] in ["En Production", "En Idée", "Mix/Master", "Publié", "Archivé"] else 0, key="upd_album_statut")
                    upd_album_artiste_ia = st.selectbox("Artiste IA Principal", artistes_ia_list_upd, index=artistes_ia_list_upd.index(selected_album['ID_Artiste_IA_Principal']) if selected_album['ID_Artiste_IA_Principal'] in artistes_ia_list_upd else 0, key="upd_album_artiste_ia")
                    upd_album_genre = st.selectbox("Genre Dominant de l'Album", genres_musicaux_upd, index=genres_musicaux_upd.index(selected_album['Genre_Dominant_Album']) if selected_album['Genre_Dominant_Album'] in genres_musicaux_upd else 0, key="upd_album_genre")
                    upd_album_description = st.text_area("Description Thématique de l'Album", value=selected_album['Description_Concept_Album'], key="upd_album_description")
                    upd_album_mots_cles_seo = st.text_input("Mots-clés SEO de l'Album", value=selected_album['Mots_Cles_Album_SEO'], key="upd_album_mots_cles_seo")
                    
                    # Affichage de la pochette actuelle et upload pour mise à jour
                    st.markdown("##### Pochette Actuelle")
                    if selected_album['URL_Cover_Principale'] and os.path.exists(os.path.join(ALBUM_COVERS_DIR, selected_album['URL_Cover_Principale'])):
                        st.image(os.path.join(ALBUM_COVERS_DIR, selected_album['URL_Cover_Principale']), width=150)
                    else:
                        st.info("Aucune pochette enregistrée.")
                    uploaded_album_cover_upd = st.file_uploader("Uploader Nouvelle Image de Pochette (.jpg, .png)", type=["jpg", "png"], key="upload_album_cover_upd")

                    col_album_form_buttons = st.columns(2)
                    with col_album_form_buttons[0]:
                        submit_update_album = st.form_submit_button("Mettre à Jour l'Album")
                    with col_album_form_buttons[1]:
                        submit_delete_album_trigger = st.form_submit_button("Supprimer l'Album", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_album:
                        cover_path_album_upd = selected_album['URL_Cover_Principale']
                        if uploaded_album_cover_upd:
                            new_cover_path_album = ut.save_uploaded_file(uploaded_album_cover_upd, ALBUM_COVERS_DIR)
                            if new_cover_path_album: cover_path_album_upd = new_cover_path_album

                        album_data_update = {
                            'Nom_Album': upd_album_nom,
                            'Date_Sortie_Prevue': upd_album_date_sortie.strftime('%Y-%m-%d'),
                            'Statut_Album': upd_album_statut,
                            'Description_Concept_Album': upd_album_description,
                            'ID_Artiste_IA_Principal': upd_album_artiste_ia,
                            'Genre_Dominant_Album': upd_album_genre,
                            'URL_Cover_Principale': cover_path_album_upd,
                            'Mots_Cles_Album_SEO': upd_album_mots_cles_seo
                        }
                        if fsc.update_album(album_to_select, album_data_update): # MAJ : Utilise fsc.
                            st.success(f"Album '{upd_album_nom}' mis à jour avec succès !")
                            st.rerun()
                        else:
                            st.error("Échec de la mise à jour de l'album.")

                    if submit_delete_album_trigger:
                        st.session_state['confirm_delete_album_id'] = album_to_select
                        st.session_state['confirm_delete_album_name'] = selected_album['Nom_Album']
                        st.rerun()
        else:
            st.info("Aucun album à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_album_id']:
        st.error(f"Confirmez-vous la suppression définitive de l'album '{st.session_state.confirm_delete_album_name}' ?")
        col_confirm_buttons_album = st.columns(2)
        with col_confirm_buttons_album[0]:
            if st.button("Oui, Supprimer Définitivement Album", key="final_confirm_delete_album"):
                if fsc.delete_album(st.session_state.confirm_delete_album_id): # MAJ : Utilise fsc.
                    st.success(f"Album '{st.session_state.confirm_delete_album_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_album_id'] = None
                    st.rerun()
                else:
                    st.error("Échec de la suppression.")
        with col_confirm_buttons_album[1]:
            if st.button("Annuler Suppression Album", key="cancel_delete_album"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_album_id'] = None
                st.rerun()

# --- Page : Mes Artistes IA (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Mes Artistes IA':
    st.header("🤖 Mes Artistes IA")
    st.write("Gérez les profils de vos artistes IA, leurs styles, leurs apparences et leurs métadonnées.")

    artistes_ia_df = fsc.get_all_artistes_ia() # MAJ : Utilise fsc.

    tab_artistes_view, tab_artistes_add, tab_artistes_edit = st.tabs(["Voir/Rechercher Artistes IA", "Ajouter un Nouvel Artiste IA", "Mettre à Jour/Supprimer Artiste IA"])

    with tab_artistes_view:
        st.subheader("Voir et Rechercher des Artistes IA")
        if not artistes_ia_df.empty:
            search_artiste_query = st.text_input("Rechercher par nom d'artiste ou style", key="search_artistes")
            if search_artiste_query:
                filtered_artistes_ia_df = artistes_ia_df[artistes_ia_df.apply(lambda row: search_artiste_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_artistes_ia_df = artistes_ia_df
            display_dataframe(ut.format_dataframe_for_display(filtered_artistes_ia_df), key="artistes_display")
        else:
            st.info("Aucun artiste IA enregistré pour le moment.")

    with tab_artistes_add:
        st.subheader("Ajouter un Nouvel Artiste IA")
        # MAJ : Utilise fsc.
        genres_musicaux_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

        with st.form("add_artiste_ia_form"):
            new_artiste_nom = st.text_input("Nom de l'Artiste IA", key="add_artiste_nom")
            new_artiste_description = st.text_area("Description de l'Artiste (Biographie/Concept)", key="add_artiste_description_bio")
            new_artiste_genres = st.multiselect("Genres de Prédilection (IDs)", fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="add_artiste_genres")
            
            uploaded_artiste_profile_img = st.file_uploader("Uploader Image de Profil (.jpg, .png)", type=["jpg", "png"], key="upload_artiste_img")

            submit_new_artiste = st.form_submit_button("Ajouter l'Artiste IA")

            if submit_new_artiste:
                if not new_artiste_nom:
                    st.error("Le nom de l'artiste IA est obligatoire.")
                else:
                    img_path_artiste = ut.save_uploaded_file(uploaded_artiste_profile_img, ALBUM_COVERS_DIR)

                    new_artiste_data = {
                        'Nom_Artiste_IA': new_artiste_nom,
                        'Description_Artiste': new_artiste_description,
                        'Genres_Predilection': ', '.join(new_artiste_genres),
                        'URL_Image_Profil': img_path_artiste if img_path_artiste else ''
                    }
                    if fsc.add_artiste_ia(new_artiste_data): # MAJ : Utilise fsc.
                        st.success(f"Artiste IA '{new_artiste_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de l'artiste IA.")

    with tab_artistes_edit:
        st.subheader("Mettre à Jour ou Supprimer un Artiste IA")
        if not artistes_ia_df.empty:
            artiste_options_display = artistes_ia_df.apply(lambda row: f"{row['ID_Artiste_IA']} - {row['Nom_Artiste_IA']}", axis=1).tolist()
            artiste_to_select_display = st.selectbox(
                "Sélectionnez l'Artiste IA à modifier/supprimer",
                artiste_options_display,
                key="select_artiste_to_edit"
            )
            artiste_to_select = artistes_ia_df[artistes_ia_df.apply(lambda row: f"{row['ID_Artiste_IA']} - {row['Nom_Artiste_IA']}" == artiste_to_select_display, axis=1)]['ID_Artiste_IA'].iloc[0]
            
            if artiste_to_select:
                selected_artiste = artistes_ia_df[artistes_ia_df['ID_Artiste_IA'] == artiste_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_artiste['Nom_Artiste_IA']}")

                # MAJ : Utilise fsc.
                genres_musicaux_list_upd = fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

                with st.form("update_delete_artiste_form"):
                    upd_artiste_nom = st.text_input("Nom de l'Artiste IA", value=selected_artiste['Nom_Artiste_IA'], key="upd_artiste_nom")
                    upd_artiste_description = st.text_area("Description de l'Artiste (Biographie/Concept)", value=selected_artiste['Description_Artiste'], key="upd_artiste_description_bio")
                    
                    # Convertir la chaîne de genres en liste pour le multiselect
                    current_genres = [g.strip() for g in selected_artiste['Genres_Predilection'].split(',')] if selected_artiste['Genres_Predilection'] else []
                    upd_artiste_genres = st.multiselect("Genres de Prédilection (IDs)", genres_musicaux_list_upd, default=current_genres, key="upd_artiste_genres")
                    
                    # Affichage image actuelle et upload
                    st.markdown("##### Image de Profil Actuelle")
                    if selected_artiste['URL_Image_Profil'] and os.path.exists(os.path.join(ALBUM_COVERS_DIR, selected_artiste['URL_Image_Profil'])):
                        st.image(os.path.join(ALBUM_COVERS_DIR, selected_artiste['URL_Image_Profil']), width=100)
                    else:
                        st.info("Aucune image de profil enregistrée.")
                    uploaded_artiste_profile_img_upd = st.file_uploader("Uploader Nouvelle Image de Profil (.jpg, .png)", type=["jpg", "png"], key="upload_artiste_img_upd")

                    col_artiste_form_buttons = st.columns(2)
                    with col_artiste_form_buttons[0]:
                        submit_update_artiste = st.form_submit_button("Mettre à Jour l'Artiste IA")
                    with col_artiste_form_buttons[1]:
                        submit_delete_artiste_trigger = st.form_submit_button("Supprimer l'Artiste IA", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_artiste:
                        img_path_artiste_upd = selected_artiste['URL_Image_Profil']
                        if uploaded_artiste_profile_img_upd:
                            new_img_path_artiste = ut.save_uploaded_file(uploaded_artiste_profile_img_upd, ALBUM_COVERS_DIR)
                            if new_img_path_artiste: img_path_artiste_upd = new_img_path_artiste

                        artiste_data_update = {
                            'Nom_Artiste_IA': upd_artiste_nom,
                            'Description_Artiste': upd_artiste_description,
                            'Genres_Predilection': ', '.join(upd_artiste_genres),
                            'URL_Image_Profil': img_path_artiste_upd
                        }
                        if fsc.update_artiste_ia(artiste_to_select, artiste_data_update): # MAJ : Utilise fsc.
                            st.success(f"Artiste IA '{upd_artiste_nom}' mis à jour avec succès !")
                            st.rerun()
                        else:
                            st.error("Échec de la mise à jour de l'artiste IA.")

                    if submit_delete_artiste_trigger:
                        st.session_state['confirm_delete_artiste_id'] = artiste_to_select
                        st.session_state['confirm_delete_artiste_name'] = selected_artiste['Nom_Artiste_IA']
                        st.rerun()
        else:
            st.info("Aucun artiste IA à modifier ou supprimer pour le moment.")
    
    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_artiste_id']:
        st.error(f"Confirmez-vous la suppression définitive de l'artiste IA '{st.session_state.confirm_delete_artiste_name}' ?")
        col_confirm_buttons_artiste = st.columns(2)
        with col_confirm_buttons_artiste[0]:
            if st.button("Oui, Supprimer Définitivement Artiste", key="final_confirm_delete_artiste"):
                if fsc.delete_artiste_ia(st.session_state.confirm_delete_artiste_id): # MAJ : Utilise fsc.
                    st.success(f"Artiste IA '{st.session_state.confirm_delete_artiste_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_artiste_id'] = None
                    st.rerun()
                else:
                    st.error("Échec de la suppression.")
        with col_confirm_buttons_artiste[1]:
            if st.button("Annuler Suppression Artiste", key="cancel_delete_artiste"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_artiste_id'] = None
                st.rerun()


# --- Page : Paroles Existantes (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Paroles Existantes':
    st.header("📜 Paroles Existantes (Manuelles)")
    st.write("Consultez et gérez vos propres paroles de chansons que l'Oracle peut utiliser comme référence.")

    paroles_existantes_df = fsc.get_all_paroles_existantes() # MAJ : Utilise fsc.

    tab_paroles_view, tab_paroles_add, tab_paroles_edit = st.tabs(["Voir/Rechercher Paroles", "Ajouter de Nouvelles Paroles", "Mettre à Jour/Supprimer Paroles"])

    with tab_paroles_view:
        st.subheader("Voir et Rechercher des Paroles Existantes")
        if not paroles_existantes_df.empty:
            search_paroles_query = st.text_input("Rechercher par titre ou contenu", key="search_paroles_existantes")
            if search_paroles_query:
                filtered_paroles_df = paroles_existantes_df[paroles_existantes_df.apply(lambda row: search_paroles_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_paroles_df = paroles_existantes_df
            display_dataframe(ut.format_dataframe_for_display(filtered_paroles_df), key="paroles_existantes_display")
        else:
            st.info("Aucune parole existante enregistrée pour le moment.")

    with tab_paroles_add:
        st.subheader("Ajouter de Nouvelles Paroles Manuelles")
        with st.form("add_paroles_form"):
            new_paroles_titre_morceau = st.text_input("Titre du Morceau (pour ces paroles)", key="add_paroles_titre_morceau")
            new_paroles_artiste = st.text_input("Artiste Principal (ex: Le Gardien)", key="add_paroles_artiste")
            new_paroles_genre = st.text_input("Genre Musical (pour référence)", key="add_paroles_genre")
            new_paroles_texte = st.text_area("Collez les Paroles ici", height=300, key="add_paroles_texte")
            new_paroles_notes = st.text_area("Notes (ex: A retravailler, version finale)", key="add_paroles_notes")
            submit_new_paroles = st.form_submit_button("Ajouter les Paroles")

            if submit_new_paroles:
                if not new_paroles_titre_morceau or not new_paroles_texte:
                    st.error("Le titre du morceau et les paroles sont obligatoires.")
                else:
                    new_paroles_data = {
                        'Titre_Morceau': new_paroles_titre_morceau,
                        'Artiste_Principal': new_paroles_artiste,
                        'Genre_Musical': new_paroles_genre,
                        'Paroles_Existantes': new_paroles_texte,
                        'Notes': new_paroles_notes
                    }
                    if fsc.add_paroles_existantes(new_paroles_data): # MAJ : Utilise fsc.
                        st.success(f"Paroles pour '{new_paroles_titre_morceau}' ajoutées avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout des paroles.")

    with tab_paroles_edit:
        st.subheader("Mettre à Jour ou Supprimer des Paroles Existantes")
        if not paroles_existantes_df.empty:
            paroles_options_display = paroles_existantes_df.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}", axis=1).tolist()
            paroles_to_select_display = st.selectbox(
                "Sélectionnez les Paroles à modifier/supprimer",
                paroles_options_display,
                key="select_paroles_to_edit"
            )
            paroles_to_select = paroles_existantes_df[paroles_existantes_df.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}" == paroles_to_select_display, axis=1)]['ID_Morceau'].iloc[0]

            if paroles_to_select:
                selected_paroles = paroles_existantes_df[paroles_existantes_df['ID_Morceau'] == paroles_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_paroles['Titre_Morceau']}")

                with st.form("update_delete_paroles_form"):
                    upd_paroles_titre_morceau = st.text_input("Titre du Morceau", value=selected_paroles['Titre_Morceau'], key="upd_paroles_titre_morceau")
                    upd_paroles_artiste = st.text_input("Artiste Principal", value=selected_paroles['Artiste_Principal'], key="upd_paroles_artiste")
                    upd_paroles_genre = st.text_input("Genre Musical", value=selected_paroles['Genre_Musical'], key="upd_paroles_genre")
                    upd_paroles_texte = st.text_area("Paroles", value=selected_paroles['Paroles_Existantes'], height=300, key="upd_paroles_texte")
                    upd_paroles_notes = st.text_area("Notes", value=selected_paroles['Notes'], key="upd_paroles_notes")

                    col_paroles_form_buttons = st.columns(2)
                    with col_paroles_form_buttons[0]:
                        submit_update_paroles = st.form_submit_button("Mettre à Jour les Paroles")
                    with col_paroles_form_buttons[1]:
                        submit_delete_paroles_trigger = st.form_submit_button("Supprimer les Paroles", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_paroles:
                        if not upd_paroles_titre_morceau or not upd_paroles_texte:
                            st.error("Le titre du morceau et les paroles sont obligatoires.")
                        else:
                            paroles_data_update = {
                                'Titre_Morceau': upd_paroles_titre_morceau,
                                'Artiste_Principal': upd_paroles_artiste,
                                'Genre_Musical': upd_paroles_genre,
                                'Paroles_Existantes': upd_paroles_texte,
                                'Notes': upd_paroles_notes
                            }
                            if fsc.update_paroles_existantes(paroles_to_select, paroles_data_update): # MAJ : Utilise fsc.
                                st.success(f"Paroles pour '{upd_paroles_titre_morceau}' mises à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour des paroles.")

                    if submit_delete_paroles_trigger:
                        st.session_state['confirm_delete_paroles_id'] = paroles_to_select
                        st.session_state['confirm_delete_paroles_name'] = selected_paroles['Titre_Morceau']
                        st.rerun()
        else:
            st.info("Aucune parole existante à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_paroles_id']:
        st.error(f"Confirmez-vous la suppression définitive des paroles pour '{st.session_state.confirm_delete_paroles_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Paroles", key="final_confirm_delete_paroles"):
                if fsc.delete_paroles_existantes(st.session_state.confirm_delete_paroles_id): # MAJ : Utilise fsc.
                    st.success(f"Paroles '{st.session_state.confirm_delete_paroles_name}' supprimées avec succès !")
                    st.session_state['confirm_delete_paroles_id'] = None
                    st.rerun()
                else:
                    st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Paroles", key="cancel_delete_paroles"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_paroles_id'] = None
                st.rerun()

# --- Page : Stats & Tendances Sim. (Analyse & Stratégie) ---
if st.session_state['current_page'] == 'Stats & Tendances Sim.':
    st.header("📊 Stats & Tendances d'Écoute Simulées")
    st.write("Visualisez des statistiques d'écoute simulées pour vos morceaux, identifiez les tendances et suivez les performances virtuelles.")

    morceaux_pour_stats_df = fsc.get_all_morceaux() # MAJ : Utilise fsc.
    
    with st.form("stats_simulation_form"):
        st.subheader("Paramètres de Simulation")
        morceaux_options_stats = morceaux_pour_stats_df.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}", axis=1).tolist() if not morceaux_pour_stats_df.empty else []
        morceaux_pour_stats = st.multiselect(
            "Sélectionnez les Morceaux à Simuler",
            morceaux_options_stats,
            key="stats_morceaux_a_simuler"
        )
        nombre_mois_simulation = st.number_input("Nombre de Mois à Simuler", min_value=1, max_value=36, value=12, step=1, key="stats_nombre_mois")
        submit_stats_simulation = st.form_submit_button("Simuler les Statistiques")

        if submit_stats_simulation:
            if morceaux_pour_stats:
                # Extraire les IDs des morceaux sélectionnés
                selected_morceau_ids = [s.split(' - ')[0] for s in morceaux_pour_stats]
                with st.spinner("L'Oracle simule les tendances d'écoute..."):
                    stats_df = go.simulate_streaming_stats(selected_morceau_ids, nombre_mois_simulation)
                    st.session_state['simulated_stats_df'] = stats_df
                    st.success("Statistiques simulées avec succès !")
            else:
                st.warning("Veuillez sélectionner au moins un morceau.")

    if 'simulated_stats_df' in st.session_state and not st.session_state.simulated_stats_df.empty:
        st.markdown("---")
        st.subheader("Statistiques d'Écoute Simulées")
        display_dataframe(ut.format_dataframe_for_display(st.session_state.simulated_stats_df), key="simulated_stats_display")

        # --- Visualisations (Exemple : Graphique des écoutes par mois) ---
        st.markdown("---")
        st.subheader("Visualisations (Exemple)")
        if 'Mois_Annee_Stat' in st.session_state.simulated_stats_df.columns and 'Ecoutes_Totales' in st.session_state.simulated_stats_df.columns:
            try:
                plot_df = st.session_state.simulated_stats_df.pivot_table(
                    index='Mois_Annee_Stat',
                    columns='ID_Morceau',
                    values='Ecoutes_Totales',
                    aggfunc='sum'
                ).reset_index()
                
                plot_df['Mois_Annee_Stat_dt'] = pd.to_datetime(plot_df['Mois_Annee_Stat'], format='%m-%Y')
                plot_df = plot_df.sort_values('Mois_Annee_Stat_dt')
                plot_df = plot_df.drop(columns=['Mois_Annee_Stat_dt'])

                st.line_chart(plot_df.set_index('Mois_Annee_Stat'))
                st.info("Ce graphique montre l'évolution des écoutes simulées par mois pour les morceaux sélectionnés. Des visualisations plus avancées sont possibles avec `Plotly` ou `Altair`.")
            except Exception as e:
                st.error(f"Erreur lors de la création du graphique: {e}")
                st.info("Assurez-vous que vos données simulées sont numériques et que le format de date est correct.")
        else:
            st.info("Données insuffisantes ou format incorrect pour la visualisation.")

    # --- Section pour la gestion des STATISTIQUES_ORBITALES_SIMULEES (AJOUTER/METTRE A JOUR/SUPPRIMER) ---
    st.markdown("---")
    st.subheader("Gestion des Statistiques Simulées")
    stats_simulees_df = fsc.get_all_stats_simulees() # MAJ : Utilise fsc.

    tab_stats_sim_view, tab_stats_sim_add, tab_stats_sim_edit = st.tabs(["Voir/Rechercher Stats", "Ajouter une Statistique", "Mettre à Jour/Supprimer Statistique"])

    with tab_stats_sim_view:
        st.subheader("Voir et Rechercher des Statistiques Simulées")
        if not stats_simulees_df.empty:
            search_stats_sim_query = st.text_input("Rechercher par Morceau ID ou Mois/Année", key="search_stats_simulees")
            if search_stats_sim_query:
                filtered_stats_sim_df = stats_simulees_df[stats_simulees_df.apply(lambda row: search_stats_sim_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_stats_sim_df = stats_simulees_df
            display_dataframe(ut.format_dataframe_for_display(filtered_stats_sim_df), key="stats_simulees_display_tab")
        else:
            st.info("Aucune statistique simulée enregistrée pour le moment.")

    with tab_stats_sim_add:
        st.subheader("Ajouter une Nouvelle Statistique Simulée")
        morceaux_list_for_stats = [''] + fsc.get_all_morceaux()['ID_Morceau'].tolist() # MAJ : Utilise fsc.
        with st.form("add_stat_sim_form"):
            new_stat_morceau_id = st.selectbox("Morceau Associé", morceaux_list_for_stats, key="add_stat_morceau_id")
            new_stat_mois_annee = st.text_input("Mois-Année (MM-AAAA)", value=datetime.now().strftime('%m-%Y'), key="add_stat_mois_annee")
            new_stat_plateforme = st.text_input("Plateforme Simulée", value="Manuelle", key="add_stat_plateforme")
            new_stat_ecoutes = st.number_input("Ecoutes Totales", min_value=0, value=0, step=100, key="add_stat_ecoutes")
            new_stat_likes = st.number_input("J'aimes Reçus", min_value=0, value=0, step=10, key="add_stat_likes")
            new_stat_shares = st.number_input("Partages Simulés", min_value=0, value=0, step=1, key="add_stat_shares")
            new_stat_revenus = st.number_input("Revenus Simulés Streaming (€)", min_value=0.0, value=0.0, step=0.01, key="add_stat_revenus")
            new_stat_audience = st.text_input("Audience Cible Démographique", value="Mixte", key="add_stat_audience")
            submit_new_stat = st.form_submit_button("Ajouter la Statistique")
            if submit_new_stat:
                if new_stat_morceau_id and new_stat_mois_annee:
                    new_stat_data = {
                        'ID_Morceau': new_stat_morceau_id,
                        'Mois_Annee_Stat': new_stat_mois_annee,
                        'Plateforme_Simulee': new_stat_plateforme,
                        'Ecoutes_Totales': new_stat_ecoutes,
                        'J_aimes_Recus': new_stat_likes,
                        'Partages_Simules': new_stat_shares,
                        'Revenus_Simules_Streaming': new_stat_revenus,
                        'Audience_Cible_Demographique': new_stat_audience
                    }
                    if fsc.add_stat_simulee(new_stat_data): # MAJ : Utilise fsc.
                        st.success(f"Statistique pour '{new_stat_morceau_id}' ajoutée.")
                        st.rerun()
                    else: st.error("Erreur ajout statistique.")
                else: st.error("Le morceau et la période sont obligatoires.")

    with tab_stats_sim_edit:
        st.subheader("Mettre à Jour ou Supprimer une Statistique Simulée")
        if not stats_simulees_df.empty:
            stat_options_display = stats_simulees_df.apply(lambda row: f"{row['ID_Stat_Simulee']} - {row['ID_Morceau']} ({row['Mois_Annee_Stat']})", axis=1).tolist()
            stat_to_select_display = st.selectbox("Sélectionnez la Statistique", stat_options_display, key="select_stat_sim_edit")
            stat_to_select_id = stats_simulees_df[stats_simulees_df.apply(lambda row: f"{row['ID_Stat_Simulee']} - {row['ID_Morceau']} ({row['Mois_Annee_Stat']})" == stat_to_select_display, axis=1)]['ID_Stat_Simulee'].iloc[0]

            if stat_to_select_id:
                selected_stat = stats_simulees_df[stats_simulees_df['ID_Stat_Simulee'] == stat_to_select_id].iloc[0]
                with st.form("update_delete_stat_sim_form"):
                    upd_stat_morceau_id = st.text_input("Morceau Associé (ID)", value=selected_stat['ID_Morceau'], disabled=True, key="upd_stat_morceau_id")
                    upd_stat_mois_annee = st.text_input("Mois-Année (MM-AAAA)", value=selected_stat['Mois_Annee_Stat'], key="upd_stat_mois_annee")
                    upd_stat_plateforme = st.text_input("Plateforme Simulée", value=selected_stat['Plateforme_Simulee'], key="upd_stat_plateforme")
                    upd_stat_ecoutes = st.number_input("Ecoutes Totales", min_value=0, value=ut.safe_cast_to_int(selected_stat['Ecoutes_Totales']) if ut.safe_cast_to_int(selected_stat['Ecoutes_Totales']) is not None else 0, step=100, key="upd_stat_ecoutes")
                    upd_stat_likes = st.number_input("J'aimes Reçus", min_value=0, value=ut.safe_cast_to_int(selected_stat['J_aimes_Recus']) if ut.safe_cast_to_int(selected_stat['J_aimes_Recus']) is not None else 0, step=10, key="upd_stat_likes")
                    upd_stat_shares = st.number_input("Partages Simulés", min_value=0, value=ut.safe_cast_to_int(selected_stat['Partages_Simules']) if ut.safe_cast_to_int(selected_stat['Partages_Simules']) is not None else 0, step=1, key="upd_stat_shares")
                    upd_stat_revenus = st.number_input("Revenus Simulés Streaming (€)", min_value=0.0, value=ut.safe_cast_to_float(selected_stat['Revenus_Simules_Streaming']) if ut.safe_cast_to_float(selected_stat['Revenus_Simules_Streaming']) is not None else 0.0, step=0.01, key="upd_stat_revenus")
                    upd_stat_audience = st.text_input("Audience Cible Démographique", value=selected_stat['Audience_Cible_Demographique'], key="upd_stat_audience")
                    
                    col_stats_buttons = st.columns(2)
                    with col_stats_buttons[0]: submit_upd_stat = st.form_submit_button("Mettre à Jour")
                    with col_stats_buttons[1]: submit_del_stat_trigger = st.form_submit_button("Supprimer", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_upd_stat:
                        if upd_stat_morceau_id and upd_stat_mois_annee:
                            upd_stat_data = {
                                'ID_Morceau': upd_stat_morceau_id,
                                'Mois_Annee_Stat': upd_stat_mois_annee,
                                'Plateforme_Simulee': upd_stat_plateforme,
                                'Ecoutes_Totales': upd_stat_ecoutes,
                                'J_aimes_Recus': upd_stat_likes,
                                'Partages_Simules': upd_stat_shares,
                                'Revenus_Simules_Streaming': upd_stat_revenus,
                                'Audience_Cible_Demographique': upd_stat_audience
                            }
                            if fsc.update_stat_simulee(stat_to_select_id, upd_stat_data): # MAJ : Utilise fsc.
                                st.success("Statistique mise à jour."); st.rerun()
                            else: st.error("Erreur mise à jour.")
                        else: st.error("Le morceau et la période sont obligatoires.")
                    
                    if submit_del_stat_trigger:
                        st.session_state['confirm_delete_stat_simulee_id'] = stat_to_select_id
                        st.session_state['confirm_delete_stat_simulee_name'] = f"{selected_stat['ID_Morceau']} ({selected_stat['Mois_Annee_Stat']})"
                        st.rerun()
        else: st.info("Aucune statistique à modifier.")
    
    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_stat_simulee_id']:
        st.error(f"Confirmez-vous la suppression définitive de la statistique '{st.session_state.confirm_delete_stat_simulee_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Statistique", key="final_confirm_delete_stat"):
                if fsc.delete_stat_simulee(st.session_state.confirm_delete_stat_simulee_id): # MAJ : Utilise fsc.
                    st.success(f"Statistique '{st.session_state.confirm_delete_stat_simulee_name}' supprimée avec succès !")
                    st.session_state['confirm_delete_stat_simulee_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Statistique", key="cancel_delete_stat"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_stat_simulee_id'] = None
                st.rerun()


# --- Page : Directives Stratégiques (Analyse & Stratégie) ---
if st.session_state['current_page'] == 'Directives Stratégiques':
    st.header("🎯 Directives Stratégiques de l'Oracle")
    st.write("Recevez des conseils stratégiques de l'Oracle pour optimiser vos créations et votre présence musicale.")

    # MAJ : Utilise fsc.
    artistes_ia_list = [''] + fsc.get_all_artistes_ia()['Nom_Artiste_IA'].tolist()
    genres_musicaux_list = [''] + fsc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
    morceaux_all = fsc.get_all_morceaux() # MAJ : Utilise fsc.
    morceaux_options_directive = morceaux_all.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}", axis=1).tolist() if not morceaux_all.empty else []

    with st.form("strategic_directive_form"):
        st.subheader("Paramètres de la Directive")
        objectif_artiste = st.text_area("Quel est votre objectif principal pour cet artiste/morceau/album ? (ex: 'Maximiser les écoutes sur les plateformes', 'Développer une communauté de fans')", key="directive_objectif")
        nom_artiste_ia_directive = st.selectbox("Artiste IA concerné", artistes_ia_list, key="directive_artiste_ia")
        genre_dominant_directive = st.selectbox("Genre dominant de l'artiste/projet", genres_musicaux_list, key="directive_genre_dominant")
        
        st.info("Les données simulées peuvent influencer la directive. Effectuez une simulation de stats pour les morceaux pertinents avant de générer la directive.")
        st.text_area("Résumé des données et performances actuelles (optionnel, ex: '5k écoutes en 1 mois sur Spotify')", key="directive_donnees_resume")
        st.text_area("Tendances actuelles du marché à prendre en compte (optionnel, ex: 'TikTok est clé pour les artistes émergents')", key="directive_tendances_actuelles")
        
        submit_directive = st.form_submit_button("Obtenir la Directive Stratégique")

        if submit_directive:
            if objectif_artiste and nom_artiste_ia_directive and genre_dominant_directive:
                with st.spinner("L'Oracle élabore une stratégie..."):
                    directive = go.generate_strategic_directive(
                        objectif_strategique=objectif_artiste,
                        nom_artiste_ia=nom_artiste_ia_directive,
                        genre_dominant=genre_dominant_directive,
                        donnees_simulees_resume=st.session_state.directive_donnees_resume,
                        tendances_actuelles=st.session_state.directive_tendances_actuelles
                    )
                    st.session_state['strategic_directive'] = directive
                    st.success("Directive stratégique générée !")
            else:
                st.warning("Veuillez définir votre objectif, l'artiste IA et son genre dominant.")

    if 'strategic_directive' in st.session_state and st.session_state.strategic_directive:
        st.markdown("---")
        st.subheader("Directive Stratégique de l'Oracle")
        st.text_area("Voici les recommandations de l'Oracle :", value=st.session_state.strategic_directive, height=300, key="directive_output")

    # --- Section pour la gestion des CONSEILS_STRATEGIQUES_ORACLE (AJOUTER/METTRE A JOUR/SUPPRIMER) ---
    st.markdown("---")
    st.subheader("Gestion des Conseils Stratégiques de l'Oracle")
    conseils_df = fsc.get_all_conseils_strategiques() # MAJ : Utilise fsc.

    tab_conseils_view, tab_conseils_add, tab_conseils_edit = st.tabs(["Voir/Rechercher Conseils", "Ajouter un Conseil", "Mettre à Jour/Supprimer Conseil"])

    with tab_conseils_view:
        st.subheader("Voir et Rechercher des Conseils Stratégiques")
        if not conseils_df.empty:
            search_conseil_query = st.text_input("Rechercher par type de conseil ou directive", key="search_conseils")
            if search_conseil_query:
                filtered_conseils_df = conseils_df[conseils_df.apply(lambda row: search_conseil_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_conseils_df = conseils_df
            display_dataframe(ut.format_dataframe_for_display(filtered_conseils_df), key="conseils_display_tab")
        else:
            st.info("Aucun conseil stratégique enregistré pour le moment.")

    with tab_conseils_add:
        st.subheader("Ajouter un Nouveau Conseil Stratégique")
        with st.form("add_conseil_form"):
            new_conseil_type = st.text_input("Type de Conseil", key="add_conseil_type")
            new_conseil_prompt_demande = st.text_area("Prompt ou Demande à l'Oracle", key="add_conseil_prompt_demande")
            new_conseil_directive_oracle = st.text_area("Directive de l'Oracle", key="add_conseil_directive_oracle")
            new_conseil_donnees_source = st.text_area("Données Source Utilisées", key="add_conseil_donnees_source")
            submit_new_conseil = st.form_submit_button("Ajouter le Conseil")
            if submit_new_conseil:
                if new_conseil_type and new_conseil_directive_oracle:
                    new_conseil_data = {
                        'Date_Conseil': datetime.now().strftime('%Y-%m-%d'),
                        'Type_Conseil': new_conseil_type,
                        'Prompt_Demande': new_conseil_prompt_demande,
                        'Directive_Oracle': new_conseil_directive_oracle,
                        'Donnees_Source_Utilisees': new_conseil_donnees_source
                    }
                    if fsc.add_conseil_strategique(new_conseil_data): # MAJ : Utilise fsc.
                        st.success(f"Conseil '{new_conseil_type}' ajouté.")
                        st.rerun()
                    else: st.error("Erreur ajout conseil.")
                else: st.error("Le type et la directive sont obligatoires.")

    with tab_conseils_edit:
        st.subheader("Mettre à Jour ou Supprimer un Conseil Stratégique")
        if not conseils_df.empty:
            conseil_options_display = conseils_df.apply(lambda row: f"{row['ID_Conseil']} - {row['Type_Conseil']}", axis=1).tolist()
            conseil_to_select_display = st.selectbox("Sélectionnez le Conseil", conseil_options_display, key="select_conseil_edit")
            conseil_to_select_id = conseils_df[conseils_df.apply(lambda row: f"{row['ID_Conseil']} - {row['Type_Conseil']}" == conseil_to_select_display, axis=1)]['ID_Conseil'].iloc[0]

            if conseil_to_select_id:
                selected_conseil = conseils_df[conseils_df['ID_Conseil'] == conseil_to_select_id].iloc[0]
                with st.form("update_delete_conseil_form"):
                    upd_conseil_type = st.text_input("Type de Conseil", value=selected_conseil['Type_Conseil'], key="upd_conseil_type")
                    upd_conseil_prompt_demande = st.text_area("Prompt ou Demande à l'Oracle", value=selected_conseil['Prompt_Demande'], key="upd_conseil_prompt_demande")
                    upd_conseil_directive_oracle = st.text_area("Directive de l'Oracle", value=selected_conseil['Directive_Oracle'], key="upd_conseil_directive_oracle")
                    upd_conseil_donnees_source = st.text_area("Données Source Utilisées", value=selected_conseil['Donnees_Source_Utilisees'], key="upd_conseil_donnees_source")
                    
                    col_conseil_buttons = st.columns(2)
                    with col_conseil_buttons[0]: submit_upd_conseil = st.form_submit_button("Mettre à Jour")
                    with col_conseil_buttons[1]: submit_del_conseil_trigger = st.form_submit_button("Supprimer", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_upd_conseil:
                        if upd_conseil_type and upd_conseil_directive_oracle:
                            upd_conseil_data = {
                                'Type_Conseil': upd_conseil_type,
                                'Prompt_Demande': upd_conseil_prompt_demande,
                                'Directive_Oracle': upd_conseil_directive_oracle,
                                'Donnees_Source_Utilisees': upd_conseil_donnees_source
                            }
                            if fsc.update_conseil_strategique(conseil_to_select_id, upd_conseil_data): # MAJ : Utilise fsc.
                                st.success("Conseil mis à jour."); st.rerun()
                            else: st.error("Erreur mise à jour.")
                        else: st.error("Le type et la directive sont obligatoires.")
                    
                    if submit_del_conseil_trigger:
                        st.session_state['confirm_delete_conseil_id'] = conseil_to_select_id
                        st.session_state['confirm_delete_conseil_name'] = selected_conseil['Type_Conseil']
                        st.rerun()
        else: st.info("Aucun conseil à modifier.")
    
    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_conseil_id']:
        st.error(f"Confirmez-vous la suppression définitive du conseil '{st.session_state.confirm_delete_conseil_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Conseil", key="final_confirm_delete_conseil"):
                if fsc.delete_conseil_strategique(st.session_state.confirm_delete_conseil_id): # MAJ : Utilise fsc.
                    st.success(f"Conseil '{st.session_state.confirm_delete_conseil_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_conseil_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Conseil", key="cancel_delete_conseil"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_conseil_id'] = None
                st.rerun()

# --- Page : Potentiel Viral & Niches (Analyse & Stratégie) ---
if st.session_state['current_page'] == 'Potentiel Viral & Niches':
    st.header("📈 Analyse du Potentiel Viral et des Niches")
    st.write("Identifiez les éléments de vos morceaux qui pourraient attirer un large public et explorez les niches musicales potentielles.")
    
    morceaux_all_viral = fsc.get_all_morceaux() # MAJ : Utilise fsc.
    public_cible_list = [''] + fsc.get_all_public_cible()['ID_Public'].tolist() # MAJ : Utilise fsc.

    with st.form("viral_potential_form"):
        st.subheader("Paramètres d'Analyse")
        morceau_to_analyze_display = st.selectbox(
            "Sélectionnez le Morceau à Analyser",
            morceaux_all_viral.apply(lambda row: f"{row['ID_Morceau']} - {row['Titre_Morceau']}", axis=1).tolist() if not morceaux_all_viral.empty else [],
            key="viral_morceau_a_analyser"
        )
        morceau_to_analyze_id = morceau_to_analyze_display.split(' - ')[0] if morceau_to_analyze_display else None

        st.selectbox("Public Cible Principal de ce morceau", public_cible_list, key="viral_public_cible_selected") # Changed key
        st.text_area("Tendances actuelles du marché général à considérer (ex: 'Popularité croissante des vidéos courtes sur TikTok')", key="viral_current_trends")
        
        submit_viral_analysis = st.form_submit_button("Analyser le Potentiel Viral")

        if submit_viral_analysis:
            if morceau_to_analyze_id and st.session_state.viral_public_cible_selected: # Check changed key
                selected_morceau_data = morceaux_all_viral[morceaux_all_viral['ID_Morceau'] == morceau_to_analyze_id].iloc[0].to_dict()
                with st.spinner("L'Oracle analyse le potentiel viral..."):
                    viral_analysis_result = go.analyze_viral_potential_and_niche_recommendations(
                        morceau_data=selected_morceau_data,
                        public_cible_id=st.session_state.viral_public_cible_selected, # Check changed key
                        current_trends=st.session_state.viral_current_trends
                    )
                    st.session_state['viral_analysis_result'] = viral_analysis_result
                    st.success("Analyse du potentiel viral terminée !")
            else:
                st.warning("Veuillez sélectionner un morceau et un public cible.")

    if 'viral_analysis_result' in st.session_state and st.session_state.viral_analysis_result:
        st.markdown("---")
        st.subheader("Analyse du Potentiel Viral et Recommandations de Niche")
        st.text_area("Analyse de l'Oracle :", value=st.session_state.viral_analysis_result, height=400, key="viral_analysis_output")


# --- Page : Styles Musicaux (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Styles Musicaux':
    st.header("🎸 Styles Musicaux")
    st.write("Gérez les styles musicaux reconnus par l'Oracle.")

    styles_musicaux_df = fsc.get_all_styles_musicaux() # MAJ : Utilise fsc.

    tab_styles_view, tab_styles_add, tab_styles_edit = st.tabs(["Voir/Rechercher Styles", "Ajouter un Nouveau Style", "Mettre à Jour/Supprimer Style"])

    with tab_styles_view:
        st.subheader("Voir et Rechercher des Styles Musicaux")
        if not styles_musicaux_df.empty:
            search_style_query = st.text_input("Rechercher par nom ou description", key="search_styles_musicaux")
            if search_style_query:
                filtered_styles_df = styles_musicaux_df[styles_musicaux_df.apply(lambda row: search_style_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_styles_df = styles_musicaux_df
            display_dataframe(ut.format_dataframe_for_display(filtered_styles_df), key="styles_musicaux_display")
        else:
            st.info("Aucun style musical enregistré pour le moment.")

    with tab_styles_add:
        st.subheader("Ajouter un Nouveau Style Musical")
        with st.form("add_style_musical_form"):
            new_style_musical_nom = st.text_input("Nom du Style Musical", key="add_style_musical_nom")
            new_style_musical_description = st.text_area("Description Détaillée", key="add_style_musical_description")
            new_style_musical_artistes = st.text_input("Artistes de Référence (séparés par des virgules)", key="add_style_musical_artistes")
            new_style_musical_exemples = st.text_area("Exemples Sonores (URL ou description)", key="add_style_musical_exemples")
            submit_new_style_musical = st.form_submit_button("Ajouter le Style Musical")

            if submit_new_style_musical:
                if new_style_musical_nom and new_style_musical_description:
                    new_style_musical_data = {
                        'Nom_Style_Musical': new_style_musical_nom,
                        'Description_Detaillee': new_style_musical_description,
                        'Artistes_References': new_style_musical_artistes,
                        'Exemples_Sonores': new_style_musical_exemples
                    }
                    if fsc.add_style_musical(new_style_musical_data): # MAJ : Utilise fsc.
                        st.success(f"Style musical '{new_style_musical_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du style musical.")
                else: st.error("Le nom et la description du style sont obligatoires.")

    with tab_styles_edit:
        st.subheader("Mettre à Jour ou Supprimer un Style Musical")
        if not styles_musicaux_df.empty:
            style_options_display = styles_musicaux_df.apply(lambda row: f"{row['ID_Style_Musical']} - {row['Nom_Style_Musical']}", axis=1).tolist()
            style_to_select_display = st.selectbox("Sélectionnez le Style Musical", style_options_display, key="select_style_musical_to_edit")
            style_to_select = styles_musicaux_df[styles_musicaux_df.apply(lambda row: f"{row['ID_Style_Musical']} - {row['Nom_Style_Musical']}" == style_to_select_display, axis=1)]['ID_Style_Musical'].iloc[0]

            if style_to_select:
                selected_style = styles_musicaux_df[styles_musicaux_df['ID_Style_Musical'] == style_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_style['Nom_Style_Musical']}")

                with st.form("update_delete_style_musical_form"):
                    upd_style_musical_nom = st.text_input("Nom du Style Musical", value=selected_style['Nom_Style_Musical'], key="upd_style_musical_nom")
                    upd_style_musical_description = st.text_area("Description Détaillée", value=selected_style['Description_Detaillee'], key="upd_style_musical_description")
                    upd_style_musical_artistes = st.text_input("Artistes de Référence", value=selected_style['Artistes_References'], key="upd_style_musical_artistes")
                    upd_style_musical_exemples = st.text_area("Exemples Sonores", value=selected_style['Exemples_Sonores'], key="upd_style_musical_exemples")

                    col_style_buttons = st.columns(2)
                    with col_style_buttons[0]:
                        submit_update_style = st.form_submit_button("Mettre à Jour le Style Musical")
                    with col_style_buttons[1]:
                        submit_delete_style_trigger = st.form_submit_button("Supprimer le Style Musical", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_style:
                        if upd_style_musical_nom and upd_style_musical_description:
                            style_data_update = {
                                'Nom_Style_Musical': upd_style_musical_nom,
                                'Description_Detaillee': upd_style_musical_description,
                                'Artistes_References': upd_style_musical_artistes,
                                'Exemples_Sonores': upd_style_musical_exemples
                            }
                            if fsc.update_style_musical(style_to_select, style_data_update): # MAJ : Utilise fsc.
                                st.success(f"Style musical '{upd_style_musical_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du style musical.")
                        else: st.error("Le nom et la description du style sont obligatoires.")

                    if submit_delete_style_trigger:
                        st.session_state['confirm_delete_style_id'] = style_to_select
                        st.session_state['confirm_delete_style_name'] = selected_style['Nom_Style_Musical']
                        st.rerun()
        else:
            st.info("Aucun style musical à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_style_id']:
        st.error(f"Confirmez-vous la suppression définitive du style musical '{st.session_state.confirm_delete_style_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Style", key="final_confirm_delete_style"):
                if fsc.delete_style_musical(st.session_state.confirm_delete_style_id): # MAJ : Utilise fsc.
                    st.success(f"Style musical '{st.session_state.confirm_delete_style_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_style_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Style", key="cancel_delete_style"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_style_id'] = None
                st.rerun()


# --- Page : Styles Lyriques (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Styles Lyriques':
    st.header("📝 Styles Lyriques")
    st.write("Gérez les styles lyriques reconnus par l'Oracle.")

    styles_lyriques_df = fsc.get_all_styles_lyriques() # MAJ : Utilise fsc.

    tab_styles_lyriques_view, tab_styles_lyriques_add, tab_styles_lyriques_edit = st.tabs(["Voir/Rechercher Styles Lyriques", "Ajouter un Nouveau Style Lyrique", "Mettre à Jour/Supprimer Style Lyrique"])

    with tab_styles_lyriques_view:
        st.subheader("Voir et Rechercher des Styles Lyriques")
        if not styles_lyriques_df.empty:
            search_style_lyrique_query = st.text_input("Rechercher par nom ou description", key="search_styles_lyriques")
            if search_style_lyrique_query:
                filtered_styles_lyriques_df = styles_lyriques_df[styles_lyriques_df.apply(lambda row: search_style_lyrique_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_styles_lyriques_df = styles_lyriques_df
            display_dataframe(ut.format_dataframe_for_display(filtered_styles_lyriques_df), key="styles_lyriques_display")
        else:
            st.info("Aucun style lyrique enregistré pour le moment.")

    with tab_styles_lyriques_add:
        st.subheader("Ajouter un Nouveau Style Lyrique")
        with st.form("add_style_lyrique_form"):
            new_style_lyrique_nom = st.text_input("Nom du Style Lyrique", key="add_style_lyrique_nom")
            new_style_lyrique_description = st.text_area("Description Détaillée", key="add_style_lyrique_description")
            new_style_lyrique_auteurs = st.text_input("Auteurs de Référence (séparés par des virgules)", key="add_style_lyrique_auteurs")
            new_style_lyrique_exemples = st.text_area("Exemples Textuels Courts", key="add_style_lyrique_exemples")
            submit_new_style_lyrique = st.form_submit_button("Ajouter le Style Lyrique")

            if submit_new_style_lyrique:
                if new_style_lyrique_nom and new_style_lyrique_description:
                    new_style_lyrique_data = {
                        'Nom_Style_Lyrique': new_style_lyrique_nom,
                        'Description_Detaillee': new_style_lyrique_description,
                        'Auteurs_References': new_style_lyrique_auteurs,
                        'Exemples_Textuels_Courts': new_style_lyrique_exemples
                    }
                    if fsc.add_style_lyrique(new_style_lyrique_data): # MAJ : Utilise fsc.
                        st.success(f"Style lyrique '{new_style_lyrique_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du style lyrique.")
                else: st.error("Le nom et la description du style lyrique sont obligatoires.")

    with tab_styles_lyriques_edit:
        st.subheader("Mettre à Jour ou Supprimer un Style Lyrique")
        if not styles_lyriques_df.empty:
            style_lyrique_options_display = styles_lyriques_df.apply(lambda row: f"{row['ID_Style_Lyrique']} - {row['Nom_Style_Lyrique']}", axis=1).tolist()
            style_lyrique_to_select_display = st.selectbox("Sélectionnez le Style Lyrique", style_lyrique_options_display, key="select_style_lyrique_to_edit")
            style_lyrique_to_select = styles_lyriques_df[styles_lyriques_df.apply(lambda row: f"{row['ID_Style_Lyrique']} - {row['Nom_Style_Lyrique']}" == style_lyrique_to_select_display, axis=1)]['ID_Style_Lyrique'].iloc[0]

            if style_lyrique_to_select:
                selected_style_lyrique = styles_lyriques_df[styles_lyriques_df['ID_Style_Lyrique'] == style_lyrique_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_style_lyrique['Nom_Style_Lyrique']}")

                with st.form("update_delete_style_lyrique_form"):
                    upd_style_lyrique_nom = st.text_input("Nom du Style Lyrique", value=selected_style_lyrique['Nom_Style_Lyrique'], key="upd_style_lyrique_nom")
                    upd_style_lyrique_description = st.text_area("Description Détaillée", value=selected_style_lyrique['Description_Detaillee'], key="upd_style_lyrique_description")
                    upd_style_lyrique_auteurs = st.text_input("Auteurs de Référence", value=selected_style_lyrique['Auteurs_References'], key="upd_style_lyrique_auteurs")
                    upd_style_lyrique_exemples = st.text_area("Exemples Textuels Courts", value=selected_style_lyrique['Exemples_Textuels_Courts'], key="upd_style_lyrique_exemples")

                    col_style_lyrique_buttons = st.columns(2)
                    with col_style_lyrique_buttons[0]:
                        submit_update_style_lyrique = st.form_submit_button("Mettre à Jour le Style Lyrique")
                    with col_style_lyrique_buttons[1]:
                        submit_delete_style_lyrique_trigger = st.form_submit_button("Supprimer le Style Lyrique", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_style_lyrique:
                        if upd_style_lyrique_nom and upd_style_lyrique_description:
                            style_lyrique_data_update = {
                                'Nom_Style_Lyrique': upd_style_lyrique_nom,
                                'Description_Detaillee': upd_style_lyrique_description,
                                'Auteurs_References': upd_style_lyrique_auteurs,
                                'Exemples_Textuels_Courts': upd_style_lyrique_exemples
                            }
                            if fsc.update_style_lyrique(style_lyrique_to_select, style_lyrique_data_update): # MAJ : Utilise fsc.
                                st.success(f"Style lyrique '{upd_style_lyrique_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du style lyrique.")
                        else: st.error("Le nom et la description du style lyrique sont obligatoires.")

                    if submit_delete_style_lyrique_trigger:
                        st.session_state['confirm_delete_style_lyrique_id'] = style_lyrique_to_select
                        st.session_state['confirm_delete_style_lyrique_name'] = selected_style_lyrique['Nom_Style_Lyrique']
                        st.rerun()
        else:
            st.info("Aucun style lyrique à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_style_lyrique_id']:
        st.error(f"Confirmez-vous la suppression définitive du style lyrique '{st.session_state.confirm_delete_style_lyrique_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Style Lyrique", key="final_confirm_delete_style_lyrique"):
                if fsc.delete_style_lyrique(st.session_state.confirm_delete_style_lyrique_id): # MAJ : Utilise fsc.
                    st.success(f"Style lyrique '{st.session_state.confirm_delete_style_lyrique_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_style_lyrique_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Style Lyrique", key="cancel_delete_style_lyrique"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_style_lyrique_id'] = None
                st.rerun()


# --- Page : Thèmes & Concepts (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Thèmes & Concepts':
    st.header("🌌 Thèmes & Concepts")
    st.write("Gérez les thèmes et concepts que l'Oracle peut utiliser.")

    themes_df = fsc.get_all_themes() # MAJ : Utilise fsc.

    tab_themes_view, tab_themes_add, tab_themes_edit = st.tabs(["Voir/Rechercher Thèmes", "Ajouter un Nouveau Thème", "Mettre à Jour/Supprimer Thème"])

    with tab_themes_view:
        st.subheader("Voir et Rechercher des Thèmes")
        if not themes_df.empty:
            search_theme_query = st.text_input("Rechercher par nom ou description", key="search_themes")
            if search_theme_query:
                filtered_themes_df = themes_df[themes_df.apply(lambda row: search_theme_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_themes_df = themes_df
            display_dataframe(ut.format_dataframe_for_display(filtered_themes_df), key="themes_display")
        else:
            st.info("Aucun thème enregistré pour le moment.")

    with tab_themes_add:
        st.subheader("Ajouter un Nouveau Thème")
        with st.form("add_theme_form"):
            new_theme_nom = st.text_input("Nom du Thème", key="add_theme_nom")
            new_theme_description = st.text_area("Description Conceptuelle", key="add_theme_description")
            new_theme_mots_cles = st.text_input("Mots-clés Associés (séparés par des virgules)", key="add_theme_mots_cles")
            submit_new_theme = st.form_submit_button("Ajouter le Thème")

            if submit_new_theme:
                if new_theme_nom and new_theme_description:
                    new_theme_data = {
                        'Nom_Theme': new_theme_nom,
                        'Description_Conceptuelle': new_theme_description,
                        'Mots_Cles_Associes': new_theme_mots_cles
                    }
                    if fsc.add_theme(new_theme_data): # MAJ : Utilise fsc.
                        st.success(f"Thème '{new_theme_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du thème.")
                else: st.error("Le nom et la description du thème sont obligatoires.")

    with tab_themes_edit:
        st.subheader("Mettre à Jour ou Supprimer un Thème")
        if not themes_df.empty:
            theme_options_display = themes_df.apply(lambda row: f"{row['ID_Theme']} - {row['Nom_Theme']}", axis=1).tolist()
            theme_to_select_display = st.selectbox("Sélectionnez le Thème", theme_options_display, key="select_theme_to_edit")
            theme_to_select = themes_df[themes_df.apply(lambda row: f"{row['ID_Theme']} - {row['Nom_Theme']}" == theme_to_select_display, axis=1)]['ID_Theme'].iloc[0]

            if theme_to_select:
                selected_theme = themes_df[themes_df['ID_Theme'] == theme_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_theme['Nom_Theme']}")

                with st.form("update_delete_theme_form"):
                    upd_theme_nom = st.text_input("Nom du Thème", value=selected_theme['Nom_Theme'], key="upd_theme_nom")
                    upd_theme_description = st.text_area("Description Conceptuelle", value=selected_theme['Description_Conceptuelle'], key="upd_theme_description")
                    upd_theme_mots_cles = st.text_input("Mots-clés Associés", value=selected_theme['Mots_Cles_Associes'], key="upd_theme_mots_cles")

                    col_theme_buttons = st.columns(2)
                    with col_theme_buttons[0]:
                        submit_update_theme = st.form_submit_button("Mettre à Jour le Thème")
                    with col_theme_buttons[1]:
                        submit_delete_theme_trigger = st.form_submit_button("Supprimer le Thème", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_theme:
                        if upd_theme_nom and upd_theme_description:
                            theme_data_update = {
                                'Nom_Theme': upd_theme_nom,
                                'Description_Conceptuelle': upd_theme_description,
                                'Mots_Cles_Associes': upd_theme_mots_cles
                            }
                            if fsc.update_theme(theme_to_select, theme_data_update): # MAJ : Utilise fsc.
                                st.success(f"Thème '{upd_theme_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du thème.")
                        else: st.error("Le nom et la description du thème sont obligatoires.")

                    if submit_delete_theme_trigger:
                        st.session_state['confirm_delete_theme_id'] = theme_to_select
                        st.session_state['confirm_delete_theme_name'] = selected_theme['Nom_Theme']
                        st.rerun()
        else:
            st.info("Aucun thème à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_theme_id']:
        st.error(f"Confirmez-vous la suppression définitive du thème '{st.session_state.confirm_delete_theme_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Thème", key="final_confirm_delete_theme"):
                if fsc.delete_theme(st.session_state.confirm_delete_theme_id): # MAJ : Utilise fsc.
                    st.success(f"Thème '{st.session_state.confirm_delete_theme_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_theme_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Thème", key="cancel_delete_theme"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_theme_id'] = None
                st.rerun()


# --- Page : Moods & Émotions (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Moods & Émotions':
    st.header("❤️ Moods & Émotions")
    st.write("Gérez les moods et émotions que l'Oracle peut utiliser.")

    moods_df = fsc.get_all_moods() # MAJ : Utilise fsc.

    tab_moods_view, tab_moods_add, tab_moods_edit = st.tabs(["Voir/Rechercher Moods", "Ajouter un Nouveau Mood", "Mettre à Jour/Supprimer Mood"])

    with tab_moods_view:
        st.subheader("Voir et Rechercher des Moods")
        if not moods_df.empty:
            search_mood_query = st.text_input("Rechercher par nom ou description", key="search_moods")
            if search_mood_query:
                filtered_moods_df = moods_df[moods_df.apply(lambda row: search_mood_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_moods_df = moods_df
            display_dataframe(ut.format_dataframe_for_display(filtered_moods_df), key="moods_display")
        else:
            st.info("Aucun mood enregistré pour le moment.")

    with tab_moods_add:
        st.subheader("Ajouter un Nouveau Mood")
        with st.form("add_mood_form"):
            new_mood_nom = st.text_input("Nom du Mood", key="add_mood_nom")
            new_mood_description = st.text_area("Description Nuancée", key="add_mood_description")
            new_mood_intensite = st.slider("Niveau d'Intensité (1-5)", min_value=1, max_value=5, value=3, step=1, key="add_mood_intensite")
            new_mood_mots_cles = st.text_input("Mots-clés Associés (séparés par des virgules)", key="add_mood_mots_cles")
            new_mood_couleur = st.color_picker("Couleur Associée", '#FFFFFF', key="add_mood_couleur")
            new_mood_tempo = st.text_input("Tempo Range Suggérer (ex: 80-120 BPM)", key="add_mood_tempo")
            submit_new_mood = st.form_submit_button("Ajouter le Mood")

            if submit_new_mood:
                if new_mood_nom and new_mood_description:
                    new_mood_data = {
                        'Nom_Mood': new_mood_nom,
                        'Description_Nuance': new_mood_description,
                        'Niveau_Intensite': new_mood_intensite,
                        'Mots_Cles_Associes': new_mood_mots_cles,
                        'Couleur_Associee': new_mood_couleur,
                        'Tempo_Range_Suggerer': new_mood_tempo
                    }
                    if fsc.add_mood(new_mood_data): # MAJ : Utilise fsc.
                        st.success(f"Mood '{new_mood_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du mood.")
                else: st.error("Le nom et la description du mood sont obligatoires.")

    with tab_moods_edit:
        st.subheader("Mettre à Jour ou Supprimer un Mood")
        if not moods_df.empty:
            mood_options_display = moods_df.apply(lambda row: f"{row['ID_Mood']} - {row['Nom_Mood']}", axis=1).tolist()
            mood_to_select_display = st.selectbox("Sélectionnez le Mood", mood_options_display, key="select_mood_to_edit")
            mood_to_select = moods_df[moods_df.apply(lambda row: f"{row['ID_Mood']} - {row['Nom_Mood']}" == mood_to_select_display, axis=1)]['ID_Mood'].iloc[0]

            if mood_to_select:
                selected_mood = moods_df[moods_df['ID_Mood'] == mood_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_mood['Nom_Mood']}")

                with st.form("update_delete_mood_form"):
                    upd_mood_nom = st.text_input("Nom du Mood", value=selected_mood['Nom_Mood'], key="upd_mood_nom")
                    upd_mood_description = st.text_area("Description Nuancée", value=selected_mood['Description_Nuance'], key="upd_mood_description")
                    upd_mood_intensite = st.slider("Niveau d'Intensité (1-5)", min_value=1, max_value=5, value=ut.safe_cast_to_int(selected_mood['Niveau_Intensite']) if ut.safe_cast_to_int(selected_mood['Niveau_Intensite']) is not None else 3, step=1, key="upd_mood_intensite")
                    upd_mood_mots_cles = st.text_input("Mots-clés Associés", value=selected_mood['Mots_Cles_Associes'], key="upd_mood_mots_cles")
                    upd_mood_couleur = st.color_picker("Couleur Associée", value=selected_mood['Couleur_Associee'], key="upd_mood_couleur")
                    upd_mood_tempo = st.text_input("Tempo Range Suggérer", value=selected_mood['Tempo_Range_Suggerer'], key="upd_mood_tempo")

                    col_mood_buttons = st.columns(2)
                    with col_mood_buttons[0]:
                        submit_update_mood = st.form_submit_button("Mettre à Jour le Mood")
                    with col_mood_buttons[1]:
                        submit_delete_mood_trigger = st.form_submit_button("Supprimer le Mood", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_mood:
                        if upd_mood_nom and upd_mood_description:
                            mood_data_update = {
                                'Nom_Mood': upd_mood_nom,
                                'Description_Nuance': upd_mood_description,
                                'Niveau_Intensite': upd_mood_intensite,
                                'Mots_Cles_Associes': upd_mood_mots_cles,
                                'Couleur_Associee': upd_mood_couleur,
                                'Tempo_Range_Suggerer': upd_mood_tempo
                            }
                            if fsc.update_mood(mood_to_select, mood_data_update): # MAJ : Utilise fsc.
                                st.success(f"Mood '{upd_mood_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du mood.")
                        else: st.error("Le nom et la description du mood sont obligatoires.")

                    if submit_delete_mood_trigger:
                        st.session_state['confirm_delete_mood_id'] = mood_to_select
                        st.session_state['confirm_delete_mood_name'] = selected_mood['Nom_Mood']
                        st.rerun()
        else:
            st.info("Aucun mood à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_mood_id']:
        st.error(f"Confirmez-vous la suppression définitive du mood '{st.session_state.confirm_delete_mood_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Mood", key="final_confirm_delete_mood"):
                if fsc.delete_mood(st.session_state.confirm_delete_mood_id): # MAJ : Utilise fsc.
                    st.success(f"Mood '{st.session_state.confirm_delete_mood_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_mood_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Mood", key="cancel_delete_mood"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_mood_id'] = None
                st.rerun()


# --- Page : Instruments & Voix (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Instruments & Voix':
    st.header("🎤 Instruments & Voix")
    st.write("Gérez les instruments orchestraux et les styles vocaux utilisés par l'Oracle.")

    instruments_df = fsc.get_all_instruments() # MAJ : Utilise fsc.
    voix_styles_df = fsc.get_all_voix_styles() # MAJ : Utilise fsc.

    tab_instruments, tab_voix_styles = st.tabs(["Instruments Orchestraux", "Styles Vocaux"])

    with tab_instruments:
        st.subheader("Instruments Orchestraux")
        if not instruments_df.empty:
            display_dataframe(ut.format_dataframe_for_display(instruments_df), key="instruments_display")
        else:
            st.info("Aucun instrument enregistré pour le moment.")
        
        st.markdown("##### Ajouter un Instrument")
        with st.form("add_instrument_form"):
            new_inst_nom = st.text_input("Nom de l'Instrument", key="add_inst_nom")
            new_inst_type = st.text_input("Type d'Instrument", key="add_inst_type")
            new_inst_sonorite = st.text_area("Sonorité Caractéristique", key="add_inst_sonorite")
            new_inst_utilisation = st.text_area("Utilisation Prévalente", key="add_inst_utilisation")
            new_inst_famille = st.text_input("Famille Sonore", key="add_inst_famille")
            submit_new_inst = st.form_submit_button("Ajouter l'Instrument")
            if submit_new_inst:
                if new_inst_nom and new_inst_type:
                    new_inst_data = {
                        'Nom_Instrument': new_inst_nom, 'Type_Instrument': new_inst_type,
                        'Sonorité_Caractéristique': new_inst_sonorite, 'Utilisation_Prevalente': new_inst_utilisation,
                        'Famille_Sonore': new_inst_famille
                    }
                    if fsc.add_instrument(new_inst_data): # MAJ : Utilise fsc.
                        st.success(f"Instrument '{new_inst_nom}' ajouté.")
                        st.rerun()
                    else: st.error("Erreur ajout instrument.")
                else: st.error("Le nom et le type de l'instrument sont obligatoires.")

        st.markdown("##### Mettre à Jour/Supprimer un Instrument")
        if not instruments_df.empty:
            inst_options_display = instruments_df.apply(lambda row: f"{row['ID_Instrument']} - {row['Nom_Instrument']}", axis=1).tolist()
            inst_to_select_display = st.selectbox("Sélectionnez l'Instrument", inst_options_display, key="select_inst_edit")
            inst_to_select = instruments_df[instruments_df.apply(lambda row: f"{row['ID_Instrument']} - {row['Nom_Instrument']}" == inst_to_select_display, axis=1)]['ID_Instrument'].iloc[0]

            if inst_to_select:
                selected_inst = instruments_df[instruments_df['ID_Instrument'] == inst_to_select].iloc[0]
                with st.form("update_delete_instrument_form"):
                    upd_inst_nom = st.text_input("Nom", value=selected_inst['Nom_Instrument'], key="upd_inst_nom")
                    upd_inst_type = st.text_input("Type", value=selected_inst['Type_Instrument'], key="upd_inst_type")
                    upd_inst_sonorite = st.text_area("Sonorité", value=selected_inst['Sonorité_Caractéristique'], key="upd_inst_sonorite")
                    upd_inst_utilisation = st.text_area("Utilisation", value=selected_inst['Utilisation_Prevalente'], key="upd_inst_utilisation")
                    upd_inst_famille = st.text_input("Famille", value=selected_inst['Famille_Sonore'], key="upd_inst_famille")
                    col_inst_buttons = st.columns(2)
                    with col_inst_buttons[0]: submit_upd_inst = st.form_submit_button("Mettre à Jour")
                    with col_inst_buttons[1]: submit_del_inst_trigger = st.form_submit_button("Supprimer", help="Cliquez pour lancer la confirmation de suppression.")
                    if submit_upd_inst:
                        if upd_inst_nom and upd_inst_type:
                            upd_inst_data = {'Nom_Instrument': upd_inst_nom, 'Type_Instrument': upd_inst_type, 'Sonorité_Caractéristique': upd_inst_sonorite, 'Utilisation_Prevalente': upd_inst_utilisation, 'Famille_Sonore': upd_inst_famille}
                            if fsc.update_instrument(inst_to_select, upd_inst_data): st.success("Instrument mis à jour."); st.rerun() # MAJ : Utilise fsc.
                            else: st.error("Erreur mise à jour.")
                        else: st.error("Le nom et le type de l'instrument sont obligatoires.")
                    if submit_del_inst_trigger:
                        st.session_state['confirm_delete_inst_id'] = inst_to_select
                        st.session_state['confirm_delete_inst_name'] = selected_inst['Nom_Instrument']
                        st.rerun()
        else: st.info("Aucun instrument à modifier.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_inst_id']:
        st.error(f"Confirmez-vous la suppression définitive de l'instrument '{st.session_state.confirm_delete_inst_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Instrument", key="final_confirm_delete_inst"):
                if fsc.delete_instrument(st.session_state.confirm_delete_inst_id): # MAJ : Utilise fsc.
                    st.success(f"Instrument '{st.session_state.confirm_delete_inst_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_inst_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Instrument", key="cancel_delete_inst"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_inst_id'] = None
                st.rerun()

    with tab_voix_styles:
        st.subheader("Styles Vocaux")
        if not voix_styles_df.empty:
            display_dataframe(ut.format_dataframe_for_display(voix_styles_df), key="voix_styles_display")
        else:
            st.info("Aucun style vocal enregistré pour le moment.")
        
        st.markdown("##### Ajouter un Style Vocal")
        with st.form("add_vocal_style_form"):
            new_vocal_type = st.text_input("Type Vocal Général", key="add_vocal_type")
            new_vocal_tessiture = st.text_input("Tessiture Spécifique (ex: Soprano, N/A)", key="add_vocal_tessiture")
            new_vocal_style_detaille = st.text_area("Style Vocal Détaillé", key="add_vocal_style_detaille")
            new_vocal_caractere = st.text_input("Caractère Expressif", key="add_vocal_caractere")
            new_vocal_effets = st.text_area("Effets Voix Souhaités", key="add_vocal_effets")
            submit_new_vocal = st.form_submit_button("Ajouter le Style Vocal")
            if submit_new_vocal:
                if new_vocal_type and new_vocal_style_detaille:
                    new_vocal_data = {
                        'Type_Vocal_General': new_vocal_type, 'Tessiture_Specifique': new_vocal_tessiture,
                        'Style_Vocal_Detaille': new_vocal_style_detaille, 'Caractere_Expressif': new_vocal_caractere,
                        'Effets_Voix_Souhaites': new_vocal_effets
                    }
                    if fsc.add_voix_style(new_vocal_data): # MAJ : Utilise fsc.
                        st.success(f"Style vocal '{new_vocal_style_detaille}' ajouté.")
                        st.rerun()
                    else: st.error("Erreur ajout style vocal.")
                else: st.error("Le type vocal et le style détaillé sont obligatoires.")
        
        st.markdown("##### Mettre à Jour/Supprimer un Style Vocal")
        if not voix_styles_df.empty:
            vocal_options_display = voix_styles_df.apply(lambda row: f"{row['ID_Vocal']} - {row['Style_Vocal_Detaille']}", axis=1).tolist()
            vocal_to_select_display = st.selectbox("Sélectionnez le Style Vocal", vocal_options_display, key="select_vocal_edit")
            vocal_to_select = voix_styles_df[voix_styles_df.apply(lambda row: f"{row['ID_Vocal']} - {row['Style_Vocal_Detaille']}" == vocal_to_select_display, axis=1)]['ID_Vocal'].iloc[0]

            if vocal_to_select:
                selected_vocal = voix_styles_df[voix_styles_df['ID_Vocal'] == vocal_to_select].iloc[0]
                with st.form("update_delete_vocal_style_form"):
                    upd_vocal_type = st.text_input("Type", value=selected_vocal['Type_Vocal_General'], key="upd_vocal_type")
                    upd_vocal_tessiture = st.text_input("Tessiture", value=selected_vocal['Tessiture_Specifique'], key="upd_vocal_tessiture")
                    upd_vocal_style_detaille = st.text_area("Style Détaillé", value=selected_vocal['Style_Vocal_Detaille'], key="upd_vocal_style_detaille")
                    upd_vocal_caractere = st.text_input("Caractère", value=selected_vocal['Caractere_Expressif'], key="upd_vocal_caractere")
                    upd_vocal_effets = st.text_area("Effets", value=selected_vocal['Effets_Voix_Souhaites'], key="upd_vocal_effets")
                    col_vocal_buttons = st.columns(2)
                    with col_vocal_buttons[0]: submit_upd_vocal = st.form_submit_button("Mettre à Jour")
                    with col_vocal_buttons[1]: submit_del_vocal_trigger = st.form_submit_button("Supprimer", help="Cliquez pour lancer la confirmation de suppression.")
                    if submit_upd_vocal:
                        if upd_vocal_type and upd_vocal_style_detaille:
                            upd_vocal_data = {'Type_Vocal_General': upd_vocal_type, 'Tessiture_Specifique': upd_vocal_tessiture, 'Style_Vocal_Detaille': upd_vocal_style_detaille, 'Caractere_Expressif': upd_vocal_caractere, 'Effets_Voix_Souhaites': upd_vocal_effets}
                            if fsc.update_voix_style(vocal_to_select, upd_vocal_data): st.success("Style vocal mis à jour."); st.rerun() # MAJ : Utilise fsc.
                            else: st.error("Erreur mise à jour.")
                        else: st.error("Le type vocal et le style détaillé sont obligatoires.")
                    if submit_del_vocal_trigger:
                        st.session_state['confirm_delete_vocal_id'] = vocal_to_select
                        st.session_state['confirm_delete_vocal_name'] = selected_vocal['Style_Vocal_Detaille']
                        st.rerun()
        else: st.info("Aucun style vocal à modifier.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_vocal_id']:
        st.error(f"Confirmez-vous la suppression définitive du style vocal '{st.session_state.confirm_delete_vocal_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Vocal", key="final_confirm_delete_vocal"):
                if fsc.delete_voix_style(st.session_state.confirm_delete_vocal_id): # MAJ : Utilise fsc.
                    st.success(f"Style vocal '{st.session_state.confirm_delete_vocal_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_vocal_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Vocal", key="cancel_delete_vocal"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_vocal_id'] = None
                st.rerun()


# --- Page : Structures de Chanson (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Structures de Chanson':
    st.header("🏛️ Structures de Chanson")
    st.write("Gérez les modèles de structure de chanson que l'Oracle peut utiliser.")

    structures_df = fsc.get_all_structures_song() # MAJ : Utilise fsc.

    tab_structures_view, tab_structures_add, tab_structures_edit = st.tabs(["Voir/Rechercher Structures", "Ajouter une Nouvelle Structure", "Mettre à Jour/Supprimer Structure"])

    with tab_structures_view:
        st.subheader("Voir et Rechercher des Structures de Chanson")
        if not structures_df.empty:
            search_structure_query = st.text_input("Rechercher par nom de structure ou schéma", key="search_structures")
            if search_structure_query:
                filtered_structures_df = structures_df[structures_df.apply(lambda row: search_structure_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_structures_df = structures_df
            display_dataframe(ut.format_dataframe_for_display(filtered_structures_df), key="structures_display")
        else:
            st.info("Aucune structure de chanson enregistrée pour le moment.")

    with tab_structures_add:
        st.subheader("Ajouter une Nouvelle Structure de Chanson")
        with st.form("add_structure_form"):
            new_structure_nom = st.text_input("Nom de la Structure", key="add_structure_nom")
            new_structure_schema = st.text_area("Schéma Détaillé (ex: Intro > Couplet > Refrain)", key="add_structure_schema")
            new_structure_notes_ia = st.text_area("Notes d'Application pour l'IA", key="add_structure_notes_ia")
            submit_new_structure = st.form_submit_button("Ajouter la Structure")

            if submit_new_structure:
                if new_structure_nom and new_structure_schema:
                    new_structure_data = {
                        'Nom_Structure': new_structure_nom,
                        'Schema_Detaille': new_structure_schema,
                        'Notes_Application_IA': new_structure_notes_ia
                    }
                    if fsc.add_structure_song(new_structure_data): # MAJ : Utilise fsc.
                        st.success(f"Structure '{new_structure_nom}' ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de la structure.")
                else: st.error("Le nom et le schéma de la structure sont obligatoires.")

    with tab_structures_edit:
        st.subheader("Mettre à Jour ou Supprimer une Structure de Chanson")
        if not structures_df.empty:
            structure_options_display = structures_df.apply(lambda row: f"{row['ID_Structure']} - {row['Nom_Structure']}", axis=1).tolist()
            structure_to_select_display = st.selectbox("Sélectionnez la Structure", structure_options_display, key="select_structure_to_edit")
            structure_to_select = structures_df[structures_df.apply(lambda row: f"{row['ID_Structure']} - {row['Nom_Structure']}" == structure_to_select_display, axis=1)]['ID_Structure'].iloc[0]

            if structure_to_select:
                selected_structure = structures_df[structures_df['ID_Structure'] == structure_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_structure['Nom_Structure']}")

                with st.form("update_delete_structure_form"):
                    upd_structure_nom = st.text_input("Nom de la Structure", value=selected_structure['Nom_Structure'], key="upd_structure_nom")
                    upd_structure_schema = st.text_area("Schéma Détaillé", value=selected_structure['Schema_Detaille'], key="upd_structure_schema")
                    upd_structure_notes_ia = st.text_area("Notes d'Application pour l'IA", value=selected_structure['Notes_Application_IA'], key="upd_structure_notes_ia")

                    col_structure_form_buttons = st.columns(2)
                    with col_structure_form_buttons[0]:
                        submit_update_structure = st.form_submit_button("Mettre à Jour la Structure")
                    with col_structure_form_buttons[1]:
                        submit_delete_structure_trigger = st.form_submit_button("Supprimer la Structure", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_structure:
                        if upd_structure_nom and upd_structure_schema:
                            structure_data_update = {
                                'Nom_Structure': upd_structure_nom,
                                'Schema_Detaille': upd_structure_schema,
                                'Notes_Application_IA': upd_structure_notes_ia
                            }
                            if fsc.update_structure_song(structure_to_select, structure_data_update): # MAJ : Utilise fsc.
                                st.success(f"Structure '{upd_structure_nom}' mise à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour de la structure.")
                        else: st.error("Le nom et le schéma de la structure sont obligatoires.")

                    if submit_delete_structure_trigger:
                        st.session_state['confirm_delete_structure_id'] = structure_to_select
                        st.session_state['confirm_delete_structure_name'] = selected_structure['Nom_Structure']
                        st.rerun()
        else:
            st.info("Aucune structure de chanson à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_structure_id']:
        st.error(f"Confirmez-vous la suppression définitive de la structure '{st.session_state.confirm_delete_structure_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Structure", key="final_confirm_delete_structure"):
                if fsc.delete_structure_song(st.session_state.confirm_delete_structure_id): # MAJ : Utilise fsc.
                    st.success(f"Structure '{st.session_state.confirm_delete_structure_name}' supprimée avec succès !")
                    st.session_state['confirm_delete_structure_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Structure", key="cancel_delete_structure"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_structure_id'] = None
                st.rerun()


# --- Page : Règles de Génération (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Règles de Génération':
    st.header("⚖️ Règles de Génération de l'Oracle")
    st.write("Gérez les règles qui guident le comportement de l'Oracle lors de la génération de contenu.")

    regles_df = fsc.get_all_regles_generation() # MAJ : Utilise fsc.

    tab_regles_view, tab_regles_add, tab_regles_edit = st.tabs(["Voir/Rechercher Règles", "Ajouter une Nouvelle Règle", "Mettre à Jour/Supprimer Règle"])

    with tab_regles_view:
        st.subheader("Voir et Rechercher des Règles de Génération")
        if not regles_df.empty:
            search_regle_query = st.text_input("Rechercher par nom de règle ou description", key="search_regles")
            if search_regle_query:
                filtered_regles_df = regles_df[regles_df.apply(lambda row: search_regle_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_regles_df = regles_df
            display_dataframe(ut.format_dataframe_for_display(filtered_regles_df), key="regles_display")
        else:
            st.info("Aucune règle de génération enregistrée pour le moment.")

    with tab_regles_add:
        st.subheader("Ajouter une Nouvelle Règle de Génération")
        with st.form("add_regle_form"):
            new_regle_type = st.text_input("Type de Règle (ex: Contrainte de Langage)", key="add_regle_type")
            new_regle_description = st.text_area("Description de la Règle", key="add_regle_description")
            new_regle_impact = st.text_input("Impact sur Génération (ex: Directive Pré-Génération)", key="add_regle_impact")
            new_regle_statut_actif = st.checkbox("Statut Actif", value=True, key="add_regle_statut_actif")
            submit_new_regle = st.form_submit_button("Ajouter la Règle")

            if submit_new_regle:
                if new_regle_type and new_regle_description:
                    new_regle_data = {
                        'Type_Regle': new_regle_type,
                        'Description_Regle': new_regle_description,
                        'Impact_Sur_Generation': new_regle_impact,
                        'Statut_Actif': 'VRAI' if new_regle_statut_actif else 'FAUX'
                    }
                    if fsc.add_regle_generation(new_regle_data): # MAJ : Utilise fsc.
                        st.success(f"Règle '{new_regle_type}' ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de la règle.")
                else: st.error("Le type et la description de la règle sont obligatoires.")

    with tab_regles_edit:
        st.subheader("Mettre à Jour ou Supprimer une Règle de Génération")
        if not regles_df.empty:
            regle_options_display = regles_df.apply(lambda row: f"{row['ID_Regle']} - {row['Type_Regle']}", axis=1).tolist()
            regle_to_select_display = st.selectbox("Sélectionnez la Règle", regle_options_display, key="select_regle_to_edit")
            regle_to_select = regles_df[regles_df.apply(lambda row: f"{row['ID_Regle']} - {row['Type_Regle']}" == regle_to_select_display, axis=1)]['ID_Regle'].iloc[0]

            if regle_to_select:
                selected_regle = regles_df[regles_df['ID_Regle'] == regle_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_regle['Type_Regle']}")

                with st.form("update_delete_regle_form"):
                    upd_regle_type = st.text_input("Type de Règle", value=selected_regle['Type_Regle'], key="upd_regle_type")
                    upd_regle_description = st.text_area("Description de la Règle", value=selected_regle['Description_Regle'], key="upd_regle_description")
                    upd_regle_impact = st.text_input("Impact sur Génération", value=selected_regle['Impact_Sur_Generation'], key="upd_regle_impact")
                    upd_regle_statut_actif = st.checkbox("Statut Actif", value=ut.parse_boolean_string(selected_regle['Statut_Actif']), key="upd_regle_statut_actif")

                    col_regle_form_buttons = st.columns(2)
                    with col_regle_form_buttons[0]:
                        submit_update_regle = st.form_submit_button("Mettre à Jour la Règle")
                    with col_regle_form_buttons[1]:
                        submit_delete_regle_trigger = st.form_submit_button("Supprimer la Règle", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_regle:
                        if upd_regle_type and upd_regle_description:
                            regle_data_update = {
                                'Type_Regle': upd_regle_type,
                                'Description_Regle': upd_regle_description,
                                'Impact_Sur_Generation': upd_regle_impact,
                                'Statut_Actif': 'VRAI' if upd_regle_statut_actif else 'FAUX'
                            }
                            if fsc.update_regle_generation(regle_to_select, regle_data_update): # MAJ : Utilise fsc.
                                st.success(f"Règle '{upd_regle_type}' mise à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour de la règle.")
                        else: st.error("Le type et la description de la règle sont obligatoires.")

                    if submit_delete_regle_trigger:
                        st.session_state['confirm_delete_regle_id'] = regle_to_select
                        st.session_state['confirm_delete_regle_name'] = selected_regle['Type_Regle']
                        st.rerun()
        else:
            st.info("Aucune règle de génération à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_regle_id']:
        st.error(f"Confirmez-vous la suppression définitive de la règle '{st.session_state.confirm_delete_regle_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Règle", key="final_confirm_delete_regle"):
                if fsc.delete_regle_generation(st.session_state.confirm_delete_regle_id): # MAJ : Utilise fsc.
                    st.success(f"Règle '{st.session_state.confirm_delete_regle_name}' supprimée avec succès !")
                    st.session_state['confirm_delete_regle_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Règle", key="cancel_delete_regle"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_regle_id'] = None
                st.rerun()


# --- Page : Public Cible (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Public Cible':
    st.header("👥 Public Cible Démographique")
    st.write("Gérez les profils d'audience que l'Oracle peut cibler.")

    public_cible_df = fsc.get_all_public_cible() # MAJ : Utilise fsc.

    tab_public_view, tab_public_add, tab_public_edit = st.tabs(["Voir/Rechercher Public", "Ajouter un Nouveau Public", "Mettre à Jour/Supprimer Public"])

    with tab_public_view:
        st.subheader("Voir et Rechercher des Publics Cibles")
        if not public_cible_df.empty:
            search_public_query = st.text_input("Rechercher par nom ou intérêts", key="search_public_cible")
            if search_public_query:
                filtered_public_df = public_cible_df[public_cible_df.apply(lambda row: search_public_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_public_df = public_cible_df
            display_dataframe(ut.format_dataframe_for_display(filtered_public_df), key="public_cible_display")
        else:
            st.info("Aucun public cible enregistré pour le moment.")

    with tab_public_add:
        st.subheader("Ajouter un Nouveau Public Cible")
        with st.form("add_public_cible_form"):
            new_public_nom = st.text_input("Nom du Public (ex: Adolescents Rock)", key="add_public_nom")
            new_public_tranche_age = st.text_input("Tranche d'Age (ex: 13-18, 25-34)", key="add_public_tranche_age")
            new_public_interets = st.text_area("Intérêts Démographiques (séparés par des virgules)", key="add_public_interets")
            new_public_plateformes = st.text_input("Plateformes d'Écoute Préférées (ex: Spotify, TikTok)", key="add_public_plateformes")
            new_public_tone_marketing = st.text_input("Tone Marketing Suggérer (ex: direct, inspirant)", key="add_public_tone_marketing")
            new_public_notes = st.text_area("Notes de Comportement (habitudes d'écoute, etc.)", key="add_public_notes")
            submit_new_public = st.form_submit_button("Ajouter le Public Cible")

            if submit_new_public:
                if new_public_nom and new_public_tranche_age:
                    new_public_data = {
                        'Nom_Public': new_public_nom,
                        'Tranche_Age': new_public_tranche_age,
                        'Interets_Demographiques': new_public_interets,
                        'Plateformes_Ecoute_Preferees': new_public_plateformes,
                        'Tone_Marketing_Suggerer': new_public_tone_marketing,
                        'Notes_Comportement': new_public_notes
                    }
                    if fsc.add_public_cible(new_public_data): # MAJ : Utilise fsc.
                        st.success(f"Public cible '{new_public_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du public cible.")
                else: st.error("Le nom et la tranche d'âge du public sont obligatoires.")

    with tab_public_edit:
        st.subheader("Mettre à Jour ou Supprimer un Public Cible")
        if not public_cible_df.empty:
            public_options_display = public_cible_df.apply(lambda row: f"{row['ID_Public']} - {row['Nom_Public']}", axis=1).tolist()
            public_to_select_display = st.selectbox("Sélectionnez le Public", public_options_display, key="select_public_to_edit")
            public_to_select = public_cible_df[public_cible_df.apply(lambda row: f"{row['ID_Public']} - {row['Nom_Public']}" == public_to_select_display, axis=1)]['ID_Public'].iloc[0]

            if public_to_select:
                selected_public = public_cible_df[public_cible_df['ID_Public'] == public_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_public['Nom_Public']}")

                with st.form("update_delete_public_form"):
                    upd_public_nom = st.text_input("Nom du Public", value=selected_public['Nom_Public'], key="upd_public_nom")
                    upd_public_tranche_age = st.text_input("Tranche d'Age", value=selected_public['Tranche_Age'], key="upd_public_tranche_age")
                    upd_public_interets = st.text_area("Intérêts Démographiques", value=selected_public['Interets_Demographiques'], key="upd_public_interets")
                    upd_public_plateformes = st.text_input("Plateformes d'Écoute Préférées", value=selected_public['Plateformes_Ecoute_Preferees'], key="upd_public_plateformes")
                    upd_public_tone_marketing = st.text_input("Tone Marketing Suggérer", value=selected_public['Tone_Marketing_Suggerer'], key="upd_public_tone_marketing")
                    upd_public_notes = st.text_area("Notes de Comportement", value=selected_public['Notes_Comportement'], key="upd_public_notes")

                    col_public_buttons = st.columns(2)
                    with col_public_buttons[0]:
                        submit_update_public = st.form_submit_button("Mettre à Jour le Public")
                    with col_public_buttons[1]:
                        submit_delete_public_trigger = st.form_submit_button("Supprimer le Public", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_public:
                        if upd_public_nom and upd_public_tranche_age:
                            public_data_update = {
                                'Nom_Public': upd_public_nom,
                                'Tranche_Age': upd_public_tranche_age,
                                'Interets_Demographiques': upd_public_interets,
                                'Plateformes_Ecoute_Preferees': upd_public_plateformes,
                                'Tone_Marketing_Suggerer': upd_public_tone_marketing,
                                'Notes_Comportement': upd_public_notes
                            }
                            if fsc.update_public_cible(public_to_select, public_data_update): # MAJ : Utilise fsc.
                                st.success(f"Public cible '{upd_public_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du public cible.")
                        else: st.error("Le nom et la tranche d'âge du public sont obligatoires.")

                    if submit_delete_public_trigger:
                        st.session_state['confirm_delete_public_id'] = public_to_select
                        st.session_state['confirm_delete_public_name'] = selected_public['Nom_Public']
                        st.rerun()
        else:
            st.info("Aucun public cible à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_public_id']:
        st.error(f"Confirmez-vous la suppression définitive du public '{st.session_state.confirm_delete_public_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Public", key="final_confirm_delete_public"):
                if fsc.delete_public_cible(st.session_state.confirm_delete_public_id): # MAJ : Utilise fsc.
                    st.success(f"Public '{st.session_state.confirm_delete_public_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_public_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Public", key="cancel_delete_public"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_public_id'] = None
                st.rerun()


# --- Page : Prompts Types (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Prompts Types':
    st.header("💡 Prompts Types et Guides")
    st.write("Gérez les modèles de prompts et les guides pour l'Oracle.")

    prompts_types_df = fsc.get_all_prompts_types() # MAJ : Utilise fsc.

    tab_prompts_view, tab_prompts_add, tab_prompts_edit = st.tabs(["Voir/Rechercher Prompts", "Ajouter un Nouveau Prompt Type", "Mettre à Jour/Supprimer Prompt Type"])

    with tab_prompts_view:
        st.subheader("Voir et Rechercher des Prompts Types")
        if not prompts_types_df.empty:
            search_prompt_type_query = st.text_input("Rechercher par nom ou objectif", key="search_prompts_types")
            if search_prompt_type_query:
                filtered_prompts_df = prompts_types_df[prompts_types_df.apply(lambda row: search_prompt_type_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_prompts_df = prompts_types_df
            display_dataframe(ut.format_dataframe_for_display(filtered_prompts_df), key="prompts_types_display")
        else:
            st.info("Aucun prompt type enregistré pour le moment.")

    with tab_prompts_add:
        st.subheader("Ajouter un Nouveau Prompt Type")
        with st.form("add_prompt_type_form"):
            new_prompt_type_nom = st.text_input("Nom du Prompt Type", key="add_prompt_type_nom")
            new_prompt_type_description = st.text_area("Description de l'Objectif", key="add_prompt_type_description")
            new_prompt_type_structure = st.text_area("Structure du Prompt Modèle", key="add_prompt_type_structure")
            new_prompt_type_variables = st.text_input("Variables Attendues (séparées par des virgules)", key="add_prompt_type_variables")
            new_prompt_type_instructions = st.text_area("Instructions pour l'IA", key="add_prompt_type_instructions")
            submit_new_prompt_type = st.form_submit_button("Ajouter le Prompt Type")

            if submit_new_prompt_type:
                if new_prompt_type_nom and new_prompt_type_description:
                    new_prompt_type_data = {
                        'Nom_PromptType': new_prompt_type_nom,
                        'Description_Objectif': new_prompt_type_description,
                        'Structure_Prompt_Modele': new_prompt_type_structure,
                        'Variables_Attendues': new_prompt_type_variables,
                        'Instructions_IA': new_prompt_type_instructions
                    }
                    if fsc.add_prompt_type(new_prompt_type_data): # MAJ : Utilise fsc.
                        st.success(f"Prompt type '{new_prompt_type_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du prompt type.")
                else: st.error("Le nom et la description du prompt type sont obligatoires.")

    with tab_prompts_edit:
        st.subheader("Mettre à Jour ou Supprimer un Prompt Type")
        if not prompts_types_df.empty:
            prompt_type_options_display = prompts_types_df.apply(lambda row: f"{row['ID_PromptType']} - {row['Nom_PromptType']}", axis=1).tolist()
            prompt_type_to_select_display = st.selectbox("Sélectionnez le Prompt Type", prompt_type_options_display, key="select_prompt_type_to_edit")
            prompt_type_to_select = prompts_types_df[prompts_types_df.apply(lambda row: f"{row['ID_PromptType']} - {row['Nom_PromptType']}" == prompt_type_to_select_display, axis=1)]['ID_PromptType'].iloc[0]

            if prompt_type_to_select:
                selected_prompt_type = prompts_types_df[prompts_types_df['ID_PromptType'] == prompt_type_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_prompt_type['Nom_PromptType']}")

                with st.form("update_delete_prompt_type_form"):
                    upd_prompt_type_nom = st.text_input("Nom du Prompt Type", value=selected_prompt_type['Nom_PromptType'], key="upd_prompt_type_nom")
                    upd_prompt_type_description = st.text_area("Description de l'Objectif", value=selected_prompt_type['Description_Objectif'], key="upd_prompt_type_description")
                    upd_prompt_type_structure = st.text_area("Structure du Prompt Modèle", value=selected_prompt_type['Structure_Prompt_Modele'], key="upd_prompt_type_structure")
                    upd_prompt_type_variables = st.text_input("Variables Attendues", value=selected_prompt_type['Variables_Attendues'], key="upd_prompt_type_variables")
                    upd_prompt_type_instructions = st.text_area("Instructions pour l'IA", value=selected_prompt_type['Instructions_IA'], key="upd_prompt_type_instructions")

                    col_prompt_type_buttons = st.columns(2)
                    with col_prompt_type_buttons[0]:
                        submit_update_prompt_type = st.form_submit_button("Mettre à Jour le Prompt Type")
                    with col_prompt_type_buttons[1]:
                        submit_delete_prompt_type_trigger = st.form_submit_button("Supprimer le Prompt Type", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_prompt_type:
                        if upd_prompt_type_nom and upd_prompt_type_description:
                            prompt_type_data_update = {
                                'Nom_PromptType': upd_prompt_type_nom,
                                'Description_Objectif': upd_prompt_type_description,
                                'Structure_Prompt_Modele': upd_prompt_type_structure,
                                'Variables_Attendues': upd_prompt_type_variables,
                                'Instructions_IA': upd_prompt_type_instructions
                            }
                            if fsc.update_prompt_type(prompt_type_to_select, prompt_type_data_update): # MAJ : Utilise fsc.
                                st.success(f"Prompt type '{upd_prompt_type_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du prompt type.")
                        else: st.error("Le nom et la description du prompt type sont obligatoires.")

                    if submit_delete_prompt_type_trigger:
                        st.session_state['confirm_delete_prompt_type_id'] = prompt_type_to_select
                        st.session_state['confirm_delete_prompt_type_name'] = selected_prompt_type['Nom_PromptType']
                        st.rerun()
        else:
            st.info("Aucun prompt type à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_prompt_type_id']:
        st.error(f"Confirmez-vous la suppression définitive du prompt type '{st.session_state.confirm_delete_prompt_type_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Prompt Type", key="final_confirm_delete_prompt_type"):
                if fsc.delete_prompt_type(st.session_state.confirm_delete_prompt_type_id): # MAJ : Utilise fsc.
                    st.success(f"Prompt type '{st.session_state.confirm_delete_prompt_type_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_prompt_type_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Prompt Type", key="cancel_delete_prompt_type"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_prompt_type_id'] = None
                st.rerun()


# --- Page : Références Sonores (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Références Sonores':
    st.header("🔊 Références Sonores Détaillées")
    st.write("Gérez les références sonores que l'Oracle peut utiliser pour affiner les ambiances.")

    references_sonores_df = fsc.get_all_references_sonores() # MAJ : Utilise fsc.

    tab_refs_view, tab_refs_add, tab_refs_edit = st.tabs(["Voir/Rechercher Références", "Ajouter une Nouvelle Référence", "Mettre à Jour/Supprimer Référence"])

    with tab_refs_view:
        st.subheader("Voir et Rechercher des Références Sonores")
        if not references_sonores_df.empty:
            search_ref_sonore_query = st.text_input("Rechercher par nom ou description", key="search_references_sonores")
            if search_ref_sonore_query:
                filtered_refs_df = references_sonores_df[references_sonores_df.apply(lambda row: search_ref_sonore_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_refs_df = references_sonores_df
            display_dataframe(ut.format_dataframe_for_display(filtered_refs_df), key="references_sonores_display")
        else:
            st.info("Aucune référence sonore enregistrée pour le moment.")

    with tab_refs_add:
        st.subheader("Ajouter une Nouvelle Référence Sonore")
        with st.form("add_ref_sonore_form"):
            new_ref_sonore_nom = st.text_input("Nom de la Référence Sonore (ex: Bruit de Pluie Apaisante)", key="add_ref_sonore_nom")
            new_ref_sonore_type = st.text_input("Type de Son (ex: Ambiance, FX, Instrument)", key="add_ref_sonore_type")
            new_ref_sonore_artiste_album = st.text_input("Artiste/Album de Référence (si applicable)", key="add_ref_sonore_artiste_album")
            new_ref_sonore_description = st.text_area("Description Sonore Détaillée", key="add_ref_sonore_description")
            new_ref_sonore_impact = st.text_area("Impact Audio Désiré (ex: crée une atmosphère mélancolique)", key="add_ref_sonore_impact")
            submit_new_ref_sonore = st.form_submit_button("Ajouter la Référence Sonore")

            if submit_new_ref_sonore:
                if new_ref_sonore_nom and new_ref_sonore_type:
                    new_ref_sonore_data = {
                        'Nom_RefSonore': new_ref_sonore_nom,
                        'Type_Son': new_ref_sonore_type,
                        'Artiste_Album_Ref': new_ref_sonore_artiste_album,
                        'Description_Sonore': new_ref_sonore_description,
                        'Impact_Audio_Desire': new_ref_sonore_impact
                    }
                    if fsc.add_reference_sonore(new_ref_sonore_data): # MAJ : Utilise fsc.
                        st.success(f"Référence sonore '{new_ref_sonore_nom}' ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de la référence sonore.")
                else: st.error("Le nom et le type de la référence sonore sont obligatoires.")

    with tab_refs_edit:
        st.subheader("Mettre à Jour ou Supprimer une Référence Sonore")
        if not references_sonores_df.empty:
            ref_sonore_options_display = references_sonores_df.apply(lambda row: f"{row['ID_RefSonore']} - {row['Nom_RefSonore']}", axis=1).tolist()
            ref_sonore_to_select_display = st.selectbox("Sélectionnez la Référence Sonore", ref_sonore_options_display, key="select_ref_sonore_to_edit")
            ref_sonore_to_select = references_sonores_df[references_sonores_df.apply(lambda row: f"{row['ID_RefSonore']} - {row['Nom_RefSonore']}" == ref_sonore_to_select_display, axis=1)]['ID_RefSonore'].iloc[0]

            if ref_sonore_to_select:
                selected_ref_sonore = references_sonores_df[references_sonores_df['ID_RefSonore'] == ref_sonore_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_ref_sonore['Nom_RefSonore']}")

                with st.form("update_delete_ref_sonore_form"):
                    upd_ref_sonore_nom = st.text_input("Nom de la Référence Sonore", value=selected_ref_sonore['Nom_RefSonore'], key="upd_ref_sonore_nom")
                    upd_ref_sonore_type = st.text_input("Type de Son", value=selected_ref_sonore['Type_Son'], key="upd_ref_sonore_type")
                    upd_ref_sonore_artiste_album = st.text_input("Artiste/Album de Référence", value=selected_ref_sonore['Artiste_Album_Ref'], key="upd_ref_sonore_artiste_album")
                    upd_ref_sonore_description = st.text_area("Description Sonore Détaillée", value=selected_ref_sonore['Description_Sonore'], key="upd_ref_sonore_description")
                    upd_ref_sonore_impact = st.text_area("Impact Audio Désiré", value=selected_ref_sonore['Impact_Audio_Desire'], key="upd_ref_sonore_impact")

                    col_ref_sonore_buttons = st.columns(2)
                    with col_ref_sonore_buttons[0]:
                        submit_update_ref_sonore = st.form_submit_button("Mettre à Jour la Référence Sonore")
                    with col_ref_sonore_buttons[1]:
                        submit_delete_ref_sonore_trigger = st.form_submit_button("Supprimer la Référence Sonore", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_ref_sonore:
                        if upd_ref_sonore_nom and upd_ref_sonore_type:
                            ref_sonore_data_update = {
                                'Nom_RefSonore': upd_ref_sonore_nom,
                                'Type_Son': upd_ref_sonore_type,
                                'Artiste_Album_Ref': upd_ref_sonore_artiste_album,
                                'Description_Sonore': upd_ref_sonore_description,
                                'Impact_Audio_Desire': upd_ref_sonore_impact
                            }
                            if fsc.update_reference_sonore(ref_sonore_to_select, ref_sonore_data_update): # MAJ : Utilise fsc.
                                st.success(f"Référence sonore '{upd_ref_sonore_nom}' mise à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour de la référence sonore.")
                        else: st.error("Le nom et le type de la référence sonore sont obligatoires.")

                    if submit_delete_ref_sonore_trigger:
                        st.session_state['confirm_delete_ref_sonore_id'] = ref_sonore_to_select
                        st.session_state['confirm_delete_ref_sonore_name'] = selected_ref_sonore['Nom_RefSonore']
                        st.rerun()
        else:
            st.info("Aucune référence sonore à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_ref_sonore_id']:
        st.error(f"Confirmez-vous la suppression définitive de la référence sonore '{st.session_state.confirm_delete_ref_sonore_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Référence", key="final_confirm_delete_ref_sonore"):
                if fsc.delete_reference_sonore(st.session_state.confirm_delete_ref_sonore_id): # MAJ : Utilise fsc.
                    st.success(f"Référence sonore '{st.session_state.confirm_delete_ref_sonore_name}' supprimée avec succès !")
                    st.session_state['confirm_delete_ref_sonore_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Référence", key="cancel_delete_ref_sonore"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_ref_sonore_id'] = None
                st.rerun()

# Continuer à partir du code précédent dans app.py

# --- Page : Projets en Cours (Outils & Projets) ---
if st.session_state['current_page'] == 'Projets en Cours':
    st.header("🚧 Projets en Cours")
    st.write("Suivez l'avancement de vos projets musicaux, de l'idée à la publication.")

    projets_df = fsc.get_all_projets_en_cours() # MAJ : Utilise fsc.

    tab_projets_view, tab_projets_add, tab_projets_edit = st.tabs(["Voir/Rechercher Projets", "Ajouter un Nouveau Projet", "Mettre à Jour/Supprimer Projet"])

    with tab_projets_view:
        st.subheader("Voir et Rechercher des Projets")
        if not projets_df.empty:
            search_projet_query = st.text_input("Rechercher par nom de projet ou statut", key="search_projets")
            if search_projet_query:
                filtered_projets_df = projets_df[projets_df.apply(lambda row: search_projet_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_projets_df = projets_df
            display_dataframe(ut.format_dataframe_for_display(filtered_projets_df), key="projets_display")
        else:
            st.info("Aucun projet enregistré pour le moment.")

    with tab_projets_add:
        st.subheader("Ajouter un Nouveau Projet")
        with st.form("add_projet_form"):
            new_projet_nom = st.text_input("Nom du Projet", key="add_projet_nom")
            new_projet_type = st.selectbox("Type de Projet", ["Single", "EP", "Album"], key="add_projet_type")
            new_projet_statut = st.selectbox("Statut du Projet", ["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"], key="add_projet_statut")
            new_projet_date_debut = st.date_input("Date de Début", value=datetime.now(), key="add_projet_date_debut")
            new_projet_date_cible_fin = st.date_input("Date Cible de Fin", value=datetime.now() + pd.DateOffset(months=3), key="add_projet_date_cible_fin")
            new_projet_morceaux_lies = st.text_input("IDs Morceaux Liés (séparés par des virgules)", key="add_projet_morceaux_lies")
            new_projet_notes = st.text_area("Notes de Production", key="add_projet_notes")
            new_projet_budget = st.number_input("Budget Estimé (€)", min_value=0.0, value=0.0, step=10.0, key="add_projet_budget")
            submit_new_projet = st.form_submit_button("Ajouter le Projet")

            if submit_new_projet:
                if new_projet_nom and new_projet_type and new_projet_statut:
                    new_projet_data = {
                        'Nom_Projet': new_projet_nom,
                        'Type_Projet': new_projet_type,
                        'Statut_Projet': new_projet_statut,
                        'Date_Debut': new_projet_date_debut.strftime('%Y-%m-%d'),
                        'Date_Cible_Fin': new_projet_date_cible_fin.strftime('%Y-%m-%d'),
                        'ID_Morceaux_Lies': new_projet_morceaux_lies,
                        'Notes_Production': new_projet_notes,
                        'Budget_Estime': new_projet_budget
                    }
                    if fsc.add_projet_en_cours(new_projet_data): # MAJ : Utilise fsc.
                        st.success(f"Projet '{new_projet_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout du projet.")
                else: st.error("Le nom, le type et le statut du projet sont obligatoires.")

    with tab_projets_edit:
        st.subheader("Mettre à Jour ou Supprimer un Projet")
        if not projets_df.empty:
            projet_options_display = projets_df.apply(lambda row: f"{row['ID_Projet']} - {row['Nom_Projet']}", axis=1).tolist()
            projet_to_select_display = st.selectbox("Sélectionnez le Projet", projet_options_display, key="select_projet_to_edit")
            projet_to_select = projets_df[projets_df.apply(lambda row: f"{row['ID_Projet']} - {row['Nom_Projet']}" == projet_to_select_display, axis=1)]['ID_Projet'].iloc[0]

            if projet_to_select:
                selected_projet = projets_df[projets_df['ID_Projet'] == projet_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_projet['Nom_Projet']}")

                with st.form("update_delete_projet_form"):
                    upd_projet_nom = st.text_input("Nom du Projet", value=selected_projet['Nom_Projet'], key="upd_projet_nom")
                    upd_projet_type = st.selectbox("Type de Projet", ["Single", "EP", "Album"], index=["Single", "EP", "Album"].index(selected_projet['Type_Projet']), key="upd_projet_type")
                    upd_projet_statut = st.selectbox("Statut du Projet", ["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"], index=["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"].index(selected_projet['Statut_Projet']), key="upd_projet_statut")
                    upd_projet_date_debut = st.date_input("Date de Début", value=pd.to_datetime(selected_projet['Date_Debut']), key="upd_projet_date_debut")
                    upd_projet_date_cible_fin = st.date_input("Date Cible de Fin", value=pd.to_datetime(selected_projet['Date_Cible_Fin']), key="upd_projet_date_cible_fin")
                    upd_projet_morceaux_lies = st.text_input("IDs Morceaux Liés (séparés par des virgules)", value=selected_projet['ID_Morceaux_Lies'], key="upd_projet_morceaux_lies")
                    upd_projet_notes = st.text_area("Notes de Production", value=selected_projet['Notes_Production'], key="upd_projet_notes")
                    upd_projet_budget = st.number_input("Budget Estimé (€)", min_value=0.0, value=ut.safe_cast_to_float(selected_projet['Budget_Estime']) if ut.safe_cast_to_float(selected_projet['Budget_Estime']) is not None else 0.0, step=10.0, key="upd_projet_budget")

                    col_projet_form_buttons = st.columns(2)
                    with col_projet_form_buttons[0]:
                        submit_update_projet = st.form_submit_button("Mettre à Jour le Projet")
                    with col_projet_form_buttons[1]:
                        submit_delete_projet_trigger = st.form_submit_button("Supprimer le Projet", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_projet:
                        if upd_projet_nom and upd_projet_type and upd_projet_statut:
                            projet_data_update = {
                                'Nom_Projet': upd_projet_nom,
                                'Type_Projet': upd_projet_type,
                                'Statut_Projet': upd_projet_statut,
                                'Date_Debut': upd_projet_date_debut.strftime('%Y-%m-%d'),
                                'Date_Cible_Fin': upd_projet_date_cible_fin.strftime('%Y-%m-%d'),
                                'ID_Morceaux_Lies': upd_projet_morceaux_lies,
                                'Notes_Production': upd_projet_notes,
                                'Budget_Estime': upd_projet_budget
                            }
                            if fsc.update_projet_en_cours(projet_to_select, projet_data_update): # MAJ : Utilise fsc.
                                st.success(f"Projet '{upd_projet_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour du projet.")
                        else: st.error("Le nom, le type et le statut du projet sont obligatoires.")

                    if submit_delete_projet_trigger:
                        st.session_state['confirm_delete_projet_id'] = projet_to_select
                        st.session_state['confirm_delete_projet_name'] = selected_projet['Nom_Projet']
                        st.rerun()
        else:
            st.info("Aucun projet à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_projet_id']:
        st.error(f"Confirmez-vous la suppression définitive du projet '{st.session_state.confirm_delete_projet_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Projet", key="final_confirm_delete_projet"):
                if fsc.delete_projet_en_cours(st.session_state.confirm_delete_projet_id): # MAJ : Utilise fsc.
                    st.success(f"Projet '{st.session_state.confirm_delete_projet_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_projet_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Projet", key="cancel_delete_projet"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_projet_id'] = None
                st.rerun()


# --- Page : Outils IA Référencés (Outils & Projets) ---
if st.session_state['current_page'] == 'Outils IA Référencés':
    st.header("🛠️ Outils IA Référencés")
    st.write("Consultez les outils IA externes référencés qui peuvent compléter les capacités de l'Architecte Ω.")

    outils_ia_df = fsc.get_all_outils_ia() # MAJ : Utilise fsc.

    tab_outils_view, tab_outils_add, tab_outils_edit = st.tabs(["Voir/Rechercher Outils", "Ajouter un Nouvel Outil", "Mettre à Jour/Supprimer Outil"])

    with tab_outils_view:
        st.subheader("Voir et Rechercher des Outils IA")
        if not outils_ia_df.empty:
            search_outil_query = st.text_input("Rechercher par nom d'outil ou fonction", key="search_outils")
            if search_outil_query:
                filtered_outils_df = outils_ia_df[outils_ia_df.apply(lambda row: search_outil_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_outils_df = outils_ia_df
            display_dataframe(ut.format_dataframe_for_display(filtered_outils_df), key="outils_display")
            
            st.markdown("---")
            st.subheader("Liens Directs vers les Outils")
            for index, row in filtered_outils_df.iterrows():
                if row['URL_Outil']:
                    st.markdown(f"**[{row['Nom_Outil']}]({row['URL_Outil']})** : {row['Description_Fonctionnalite']}")
        else:
            st.info("Aucun outil IA enregistré pour le moment.")

    with tab_outils_add:
        st.subheader("Ajouter un Nouvel Outil IA")
        with st.form("add_outil_ia_form"):
            new_outil_nom = st.text_input("Nom de l'Outil", key="add_outil_nom")
            new_outil_description = st.text_area("Description de la Fonctionnalité", key="add_outil_description")
            new_outil_type = st.text_input("Type de Fonction (ex: Génération audio, Mastering)", key="add_outil_type")
            new_outil_url = st.text_input("URL de l'Outil", key="add_outil_url")
            new_outil_compat = st.checkbox("Compatibilité API (Oui/Non)", key="add_outil_compat")
            new_outil_prix = st.text_input("Prix Approximatif", key="add_outil_prix")
            new_outil_eval = st.number_input("Évaluation Gardien (1-5)", min_value=1, max_value=5, value=3, step=1, key="add_outil_eval")
            new_outil_notes = st.text_area("Notes d'Utilisation", key="add_outil_notes")
            submit_new_outil = st.form_submit_button("Ajouter l'Outil")

            if submit_new_outil:
                if new_outil_nom and new_outil_description and new_outil_type:
                    new_outil_data = {
                        'Nom_Outil': new_outil_nom,
                        'Description_Fonctionnalite': new_outil_description,
                        'Type_Fonction': new_outil_type,
                        'URL_Outil': new_outil_url,
                        'Compatibilite_API': 'OUI' if new_outil_compat else 'NON',
                        'Prix_Approximatif': new_outil_prix,
                        'Evaluation_Gardien': new_outil_eval,
                        'Notes_Utilisation': new_outil_notes
                    }
                    if fsc.add_outil_ia(new_outil_data): # MAJ : Utilise fsc.
                        st.success(f"Outil '{new_outil_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de l'outil.")
                else: st.error("Le nom, la description et le type de fonction sont obligatoires.")

    with tab_outils_edit:
        st.subheader("Mettre à Jour ou Supprimer un Outil IA")
        if not outils_ia_df.empty:
            outil_options_display = outils_ia_df.apply(lambda row: f"{row['ID_Outil']} - {row['Nom_Outil']}", axis=1).tolist()
            outil_to_select_display = st.selectbox("Sélectionnez l'Outil IA", outil_options_display, key="select_outil_to_edit")
            outil_to_select = outils_ia_df[outils_ia_df.apply(lambda row: f"{row['ID_Outil']} - {row['Nom_Outil']}" == outil_to_select_display, axis=1)]['ID_Outil'].iloc[0]

            if outil_to_select:
                selected_outil = outils_ia_df[outils_ia_df['ID_Outil'] == outil_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_outil['Nom_Outil']}")

                with st.form("update_delete_outil_form"):
                    upd_outil_nom = st.text_input("Nom de l'Outil", value=selected_outil['Nom_Outil'], key="upd_outil_nom")
                    upd_outil_description = st.text_area("Description de la Fonctionnalité", value=selected_outil['Description_Fonctionnalite'], key="upd_outil_description")
                    upd_outil_type = st.text_input("Type de Fonction", value=selected_outil['Type_Fonction'], key="upd_outil_type")
                    upd_outil_url = st.text_input("URL de l'Outil", value=selected_outil['URL_Outil'], key="upd_outil_url")
                    upd_outil_compat = st.checkbox("Compatibilité API (Oui/Non)", value=ut.parse_boolean_string(selected_outil['Compatibilite_API']), key="upd_outil_compat")
                    upd_outil_prix = st.text_input("Prix Approximatif", value=selected_outil['Prix_Approximatif'], key="upd_outil_prix")
                    upd_outil_eval = st.number_input("Évaluation Gardien (1-5)", min_value=1, max_value=5, value=int(selected_outil['Evaluation_Gardien']), step=1, key="upd_outil_eval")
                    upd_outil_notes = st.text_area("Notes d'Utilisation", value=selected_outil['Notes_Utilisation'], key="upd_outil_notes")

                    col_outil_form_buttons = st.columns(2)
                    with col_outil_form_buttons[0]:
                        submit_update_outil = st.form_submit_button("Mettre à Jour l'Outil")
                    with col_outil_form_buttons[1]:
                        submit_delete_outil_trigger = st.form_submit_button("Supprimer l'Outil", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_outil:
                        if upd_outil_nom and upd_outil_description and upd_outil_type:
                            outil_data_update = {
                                'Nom_Outil': upd_outil_nom,
                                'Description_Fonctionnalite': upd_outil_description,
                                'Type_Fonction': upd_outil_type,
                                'URL_Outil': upd_outil_url,
                                'Compatibilite_API': 'OUI' if upd_outil_compat else 'NON',
                                'Prix_Approximatif': upd_outil_prix,
                                'Evaluation_Gardien': upd_outil_eval,
                                'Notes_Utilisation': upd_outil_notes
                            }
                            if fsc.update_outil_ia(outil_to_select, outil_data_update): # MAJ : Utilise fsc.
                                st.success(f"Outil '{upd_outil_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour de l'outil.")
                        else: st.error("Le nom, la description et le type de fonction sont obligatoires.")

                    if submit_delete_outil_trigger:
                        st.session_state['confirm_delete_outil_id'] = outil_to_select
                        st.session_state['confirm_delete_outil_name'] = selected_outil['Nom_Outil']
                        st.rerun()
        else:
            st.info("Aucun outil IA à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_outil_id']:
        st.error(f"Confirmez-vous la suppression définitive de l'outil '{st.session_state.confirm_delete_outil_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Outil", key="final_confirm_delete_outil"):
                if fsc.delete_outil_ia(st.session_state.confirm_delete_outil_id): # MAJ : Utilise fsc.
                    st.success(f"Outil '{st.session_state.confirm_delete_outil_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_outil_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Outil", key="cancel_delete_outil"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_outil_id'] = None
                st.rerun()


# --- Page : Timeline Événements (Outils & Projets) ---
if st.session_state['current_page'] == 'Timeline Événements':
    st.header("🗓️ Timeline des Événements Culturels")
    st.write("Consultez et gérez les événements majeurs pour planifier vos lancements musicaux et campagnes promotionnelles.")

    timeline_df = fsc.get_all_timeline_evenements() # MAJ : Utilise fsc.

    tab_timeline_view, tab_timeline_add, tab_timeline_edit = st.tabs(["Voir/Rechercher Événements", "Ajouter un Nouvel Événement", "Mettre à Jour/Supprimer Événement"])

    with tab_timeline_view:
        st.subheader("Voir et Rechercher des Événements")
        if not timeline_df.empty:
            search_timeline_query = st.text_input("Rechercher par nom d'événement ou genre", key="search_timeline")
            if search_timeline_query:
                filtered_timeline_df = timeline_df[timeline_df.apply(lambda row: search_timeline_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_timeline_df = timeline_df
            display_dataframe(ut.format_dataframe_for_display(filtered_timeline_df), key="timeline_display")
        else:
            st.info("Aucun événement enregistré pour le moment.")

    with tab_timeline_add:
        st.subheader("Ajouter un Nouvel Événement")
        with st.form("add_timeline_event_form"):
            new_event_nom = st.text_input("Nom de l'Événement", key="add_event_nom")
            new_event_date_debut = st.date_input("Date de Début", value=datetime.now(), key="add_event_date_debut")
            new_event_date_fin = st.date_input("Date de Fin", value=datetime.now(), key="add_event_date_fin")
            new_event_type = st.selectbox("Type d'Événement", ["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"], key="add_event_type")
            new_event_genre = st.text_input("Genre(s) Associé(s) (séparés par des virgules)", key="add_event_genre")
            new_event_public = st.text_input("Public(s) Associé(s) (IDs séparés par virgules)", key="add_event_public")
            new_event_notes = st.text_area("Notes Stratégiques", key="add_event_notes")
            submit_new_event = st.form_submit_button("Ajouter l'Événement")

            if submit_new_event:
                if new_event_nom and new_event_type:
                    new_event_data = {
                        'Nom_Evenement': new_event_nom,
                        'Date_Debut': new_event_date_debut.strftime('%Y-%m-%d'),
                        'Date_Fin': new_event_date_fin.strftime('%Y-%m-%d'),
                        'Type_Evenement': new_event_type,
                        'Genre_Associe': new_event_genre,
                        'Public_Associe': new_event_public,
                        'Notes_Strategiques': new_event_notes
                    }
                    if fsc.add_timeline_event(new_event_data): # MAJ : Utilise fsc.
                        st.success(f"Événement '{new_event_nom}' ajouté avec succès !")
                        st.rerun()
                    else:
                        st.error("Échec de l'ajout de l'événement.")
                else: st.error("Le nom et le type d'événement sont obligatoires.")

    with tab_timeline_edit:
        st.subheader("Mettre à Jour ou Supprimer un Événement")
        if not timeline_df.empty:
            event_options_display = timeline_df.apply(lambda row: f"{row['ID_Evenement']} - {row['Nom_Evenement']}", axis=1).tolist()
            event_to_select_display = st.selectbox("Sélectionnez l'Événement", event_options_display, key="select_event_to_edit")
            event_to_select = timeline_df[timeline_df.apply(lambda row: f"{row['ID_Evenement']} - {row['Nom_Evenement']}" == event_to_select_display, axis=1)]['ID_Evenement'].iloc[0]

            if event_to_select:
                selected_event = timeline_df[timeline_df['ID_Evenement'] == event_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_event['Nom_Evenement']}")

                with st.form("update_delete_event_form"):
                    upd_event_nom = st.text_input("Nom de l'Événement", value=selected_event['Nom_Evenement'], key="upd_event_nom")
                    upd_event_date_debut = st.date_input("Date de Début", value=pd.to_datetime(selected_event['Date_Debut']), key="upd_event_date_debut")
                    upd_event_date_fin = st.date_input("Date de Fin", value=pd.to_datetime(selected_event['Date_Fin']), key="upd_event_date_fin")
                    upd_event_type = st.selectbox("Type d'Événement", ["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"], index=["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"].index(selected_event['Type_Evenement']), key="upd_event_type")
                    upd_event_genre = st.text_input("Genre(s) Associé(s)", value=selected_event['Genre_Associe'], key="upd_event_genre")
                    upd_event_public = st.text_input("Public(s) Associé(s)", value=selected_event['Public_Associe'], key="upd_event_public")
                    upd_event_notes = st.text_area("Notes Stratégiques", value=selected_event['Notes_Strategiques'], key="upd_event_notes")

                    col_event_form_buttons = st.columns(2)
                    with col_event_form_buttons[0]:
                        submit_update_event = st.form_submit_button("Mettre à Jour l'Événement")
                    with col_event_form_buttons[1]:
                        submit_delete_event_trigger = st.form_submit_button("Supprimer l'Événement", help="Cliquez pour lancer la confirmation de suppression.")

                    if submit_update_event:
                        if upd_event_nom and upd_event_type:
                            event_data_update = {
                                'Nom_Evenement': upd_event_nom,
                                'Date_Debut': upd_event_date_debut.strftime('%Y-%m-%d'),
                                'Date_Fin': upd_event_date_fin.strftime('%Y-%m-%d'),
                                'Type_Evenement': upd_event_type,
                                'Genre_Associe': upd_event_genre,
                                'Public_Associe': upd_event_public,
                                'Notes_Strategiques': upd_event_notes
                            }
                            if fsc.update_timeline_event(event_to_select, event_data_update): # MAJ : Utilise fsc.
                                st.success(f"Événement '{upd_event_nom}' mis à jour avec succès !")
                                st.rerun()
                            else:
                                st.error("Échec de la mise à jour de l'événement.")
                        else: st.error("Le nom et le type d'événement sont obligatoires.")

                    if submit_delete_event_trigger:
                        st.session_state['confirm_delete_event_id'] = event_to_select
                        st.session_state['confirm_delete_event_name'] = selected_event['Nom_Evenement']
                        st.rerun()
        else:
            st.info("Aucun événement à modifier ou supprimer pour le moment.")

    # --- Bloc de confirmation de suppression (EN DEHORS DU FORMULAIRE) ---
    if st.session_state['confirm_delete_event_id']:
        st.error(f"Confirmez-vous la suppression définitive de l'événement '{st.session_state.confirm_delete_event_name}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement Événement", key="final_confirm_delete_event"):
                if fsc.delete_timeline_event(st.session_state.confirm_delete_event_id): # MAJ : Utilise fsc.
                    st.success(f"Événement '{st.session_state.confirm_delete_event_name}' supprimé avec succès !")
                    st.session_state['confirm_delete_event_id'] = None
                    st.rerun()
                else: st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler Suppression Événement", key="cancel_delete_event"):
                st.info("Suppression annulée.")
                st.session_state['confirm_delete_event_id'] = None
                st.rerun()


# --- Page : Historique de l'Oracle (Logging) ---
if st.session_state['current_page'] == "Historique de l'Oracle":
    st.header("📚 Historique de l'Oracle")
    st.write("Consultez l'historique de toutes vos interactions avec l'Oracle Architecte et évaluez ses générations.")

    historique_df = fsc.get_all_historique_generations() # MAJ : Utilise fsc.

    tab_historique_view, tab_historique_feedback = st.tabs(["Voir Historique", "Donner du Feedback"])

    with tab_historique_view:
        st.subheader("Historique des Générations")
        if not historique_df.empty:
            search_hist_query = st.text_input("Rechercher dans l'historique", key="search_historique")
            if search_hist_query:
                filtered_hist_df = historique_df[historique_df.apply(lambda row: search_hist_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_hist_df = historique_df
            display_dataframe(ut.format_dataframe_for_display(filtered_hist_df), key="historique_display")
        else:
            st.info("Aucun historique de génération pour le moment.")

    with tab_historique_feedback:
        st.subheader("Donner du Feedback à l'Oracle")
        if not historique_df.empty:
            # Filtrer les entrées sans évaluation
            unrated_generations = historique_df[historique_df['Evaluation_Manuelle'] == '']
            if not unrated_generations.empty:
                gen_options_feedback = unrated_generations.apply(lambda row: f"{row['ID_GenLog']} - {row['Type_Generation']} ({row['Date_Heure']})", axis=1).tolist()
                gen_to_feedback_id_display = st.selectbox(
                    "Sélectionnez une génération à évaluer",
                    gen_options_feedback,
                    key="select_gen_to_feedback"
                )
                gen_to_feedback_id = unrated_generations[unrated_generations.apply(lambda row: f"{row['ID_GenLog']} - {row['Type_Generation']} ({row['Date_Heure']})" == gen_to_feedback_id_display, axis=1)]['ID_GenLog'].iloc[0]

                if gen_to_feedback_id:
                    selected_gen = unrated_generations[unrated_generations['ID_GenLog'] == gen_to_feedback_id].iloc[0]

                    st.markdown("---")
                    st.write(f"**Génération sélectionnée :** {selected_gen['Type_Generation']} du {selected_gen['Date_Heure']}")
                    st.text_area("Prompt envoyé :", value=selected_gen['Prompt_Envoye_Full'], height=150, disabled=True)
                    st.text_area("Réponse reçue :", value=selected_gen['Reponse_Recue_Full'], height=200, disabled=True)

                    with st.form("feedback_form"):
                        evaluation = st.slider("Évaluation de la qualité (1: Faible, 5: Excellente)", min_value=1, max_value=5, value=3, step=1, key="feedback_evaluation")
                        commentaire = st.text_area("Commentaire ou suggestion d'amélioration", key="feedback_commentaire")
                        tags_feedback = st.text_input("Tags de feedback (ex: 'trop long', 'mélodie parfaite', 'style non respecté')", key="feedback_tags")
                        
                        submit_feedback = st.form_submit_button("Soumettre le Feedback")

                        if submit_feedback:
                            feedback_data = {
                                'Evaluation_Manuelle': str(evaluation), # Convertir en string pour la base de données
                                'Commentaire_Qualitatif': commentaire,
                                'Tags_Feedback': tags_feedback
                            }
                            if fsc.update_historique_generation(gen_to_feedback_id, feedback_data): # MAJ : Utilise fsc.
                                st.success("Feedback soumis avec succès ! L'Oracle vous remercie pour votre contribution.")
                                st.rerun()
                            else:
                                st.error("Échec de la soumission du feedback.")
            else:
                st.info("Toutes les générations ont été évaluées, ou il n'y a pas encore d'historique.")
        else:
            st.info("Aucun historique de génération pour le moment.")