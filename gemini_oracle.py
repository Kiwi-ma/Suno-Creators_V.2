# gemini_oracle.py

import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from datetime import datetime
import base64
import json

# Importation des configurations et du connecteur Firestore
# CORRECTION ICI : WORKSHEET_NAMES au lieu de FIRESTORE_COLLECTIONS
from config import GEMINI_API_KEY_NAME, WORKSHEET_NAMES
from firestore_connector import add_historique_generation, get_dataframe_from_collection 

# --- Initialisation de la Connexion à l'API Gemini ---
gemini_api_key = st.secrets.get(GEMINI_API_KEY_NAME)

if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        _text_model = genai.GenerativeModel('gemini-2.5-flash') 
        _creative_model = genai.GenerativeModel('gemini-2.5-flash') 
        st.session_state['gemini_initialized'] = True
        st.session_state['gemini_error'] = None 
    except Exception as e:
        st.session_state['gemini_initialized'] = False
        st.session_state['gemini_error'] = f"Échec d'initialisation Gemini : {e}. Vérifiez votre clé API dans les secrets Streamlit Cloud."
        _text_model = None
        _creative_model = None
else:
    st.session_state['gemini_initialized'] = False
    st.session_state['gemini_error'] = f"La clé API Gemini '{GEMINI_API_KEY_NAME}' est manquante dans les secrets de votre application Streamlit Cloud. Veuillez la configurer."
    _text_model = None
    _creative_model = None

# --- Fonctions Utilitaires Internes pour l'Oracle ---

def _log_gemini_interaction(type_generation: str, prompt_sent: str, response_received: str, associated_id: str = "", evaluation: str = "", comment: str = "", tags: str = "", regle_auto: str = ""):
    """
    Fonction interne pour logger chaque interaction avec Gemini dans l'historique.
    Utilise add_historique_generation depuis firestore_connector.
    """
    log_data = {
        'Type_Generation': type_generation,
        'Prompt_Envoye_Full': prompt_sent,
        'Reponse_Recue_Full': response_received,
        'ID_Morceau_Associe': associated_id,
        'Evaluation_Manuelle': evaluation,
        'Commentaire_Qualitatif': comment,
        'Tags_Feedback': tags,
        'ID_Regle_Appliquee_Auto': regle_auto
    }
    try:
        add_historique_generation(log_data)
    except Exception as e:
        st.error(f"Erreur critique lors de l'enregistrement de l'historique Gemini dans Firestore: {e}")
        st.warning("L'historique de l'Oracle pourrait ne pas être complet. Vérifiez votre `firestore_connector.py`.")


def _generate_content(model, prompt: str, type_generation: str = "Contenu Général", associated_id: str = "", temperature: float = 0.1, max_output_tokens: int = 1024) -> str:
    """
    Fonction interne robuste pour générer du contenu avec Gemini et logger l'interaction.
    Anticipe les blocages de sécurité et les échecs de génération.
    """
    if not st.session_state.get('gemini_initialized', False) or model is None:
        return st.session_state.get('gemini_error', "L'Oracle est indisponible. Vérifiez la configuration de l'API Gemini.")
        
    safety_instructions = """
    Votre réponse doit être absolument sûre, appropriée, respectueuse, et ne doit jamais inclure de contenu violent, haineux, sexuellement explicite, illégal, ou dangereux, même implicitement. Évitez tout sujet controversé, discriminatoire ou incitant à la violence. Si vous ne pouvez pas générer un contenu conforme à ces règles pour la requête donnée, veuillez répondre par un message clair indiquant que la génération est impossible pour des raisons de conformité, sans donner de détails sur le motif précis du blocage. Votre objectif est d'être utile et inoffensif.
    """
    
    final_prompt = safety_instructions + "\n\n" + prompt 
    
    try:
        response = model.generate_content(
            final_prompt, 
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            ),
        )
        
        if not response.candidates:
            block_reason_detail = "Raison inconnue."
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_detail = response.prompt_feedback.block_reason.name
            
            error_message = f"La génération a été bloquée par les filtres de sécurité de l'Oracle. Raison : {block_reason_detail}. Veuillez ajuster votre prompt pour qu'il soit plus conforme et moins ambigu."
            st.error(error_message)
            _log_gemini_interaction(type_generation, final_prompt, f"BLOCKED: {block_reason_detail}", associated_id)
            return "Désolé, la génération de contenu a été bloquée pour des raisons de conformité. Essayez une requête plus simple ou différente."
            
        generated_text = response.text
        
        _log_gemini_interaction(type_generation, final_prompt, generated_text, associated_id)
        
        return generated_text
    except genai.types.BlockedPromptException as e:
        st.error(f"Votre prompt a été bloqué par les filtres de sécurité de l'API Gemini. Raisons : {e.response.prompt_feedback.block_reason_messages}. Veuillez reformuler.")
        _log_gemini_interaction(type_generation, final_prompt, f"PROMPT BLOQUÉ: {e.response.prompt_feedback.block_reason_messages}", associated_id)
        return "Votre requête a été bloquée pour des raisons de sécurité. Veuillez essayer un prompt différent."
    except genai.types.StopCandidateException as e:
        st.warning(f"La génération s'est arrêtée prématurément. Raison: {e.response.candidates[0].finish_reason}. Le contenu pourrait être incomplet.")
        _log_gemini_interaction(type_generation, final_prompt, f"Génération Incomplète: {e.response.candidates[0].finish_reason}", associated_id)
        return e.response.text if e.response.text else "La génération est incomplète. Veuillez réessayer ou simplifier la demande."
    except Exception as e:
        st.error(f"Une erreur inattendue est survenue lors de la communication avec l'API Gemini: {e}. Vérifiez votre connexion internet ou la configuration de votre clé API.")
        _log_gemini_interaction(type_generation, final_prompt, f"ERREUR API: {e}", associated_id)
        return f"Désolé, une erreur de communication est survenue: {e}"

# --- Fonctions de Génération de Contenu Spécifiques ---

def generate_song_lyrics(
    genre_musical: str, mood_principal: str, theme_lyrique_principal: str,
    style_lyrique: str, mots_cles_generation: str, structure_chanSONG: str,
    langue_paroles: str, niveau_langage_paroles: str, imagerie_texte: str
) -> str:
    """Génère des paroles de chanson complètes."""
    
    styles_lyriques_df = get_dataframe_from_collection(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"])
    themes_df = get_dataframe_from_collection(WORKSHEET_NAMES["THEMES_CONSTELLES"])
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    structures_df = get_dataframe_from_collection(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"])

    style_lyrique_desc = styles_lyriques_df[styles_lyriques_df['ID_Style_Lyrique'] == style_lyrique]['Description_Detaillee'].iloc[0] if style_lyrique and not styles_lyriques_df.empty and style_lyrique in styles_lyriques_df['ID_Style_Lyrique'].values else style_lyrique
    theme_desc = themes_df[themes_df['ID_Theme'] == theme_lyrique_principal]['Description_Conceptuelle'].iloc[0] if theme_lyrique_principal and not themes_df.empty and theme_lyrique_principal in themes_df['ID_Theme'].values else theme_lyrique_principal
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if mood_principal and not moods_df.empty and mood_principal in moods_df['ID_Mood'].values else mood_principal
    structure_schema = structures_df[structures_df['ID_Structure'] == structure_chanSONG]['Schema_Detaille'].iloc[0] if structure_chanSONG and not structures_df.empty and structure_chanSONG in structures_df['ID_Structure'].values else structure_chanSONG
    
    prompt = f"""En tant que parolier expert, poétique et sensible, crée des paroles complètes et originales.
    Génère des paroles pour une chanson dans le genre **{genre_musical}**.
    Le mood principal est **{mood_principal} ({mood_desc})**.
    Le thème principal est **{theme_lyrique_principal} ({theme_desc})**.
    Utilise un style lyrique **{style_lyrique} ({style_lyrique_desc})**.
    Inclus les mots-clés ou concepts suivants (si fournis, sinon ignore) : **{mots_cles_generation}**.
    La structure de la chanson doit être : **{structure_chanSONG} ({structure_schema})**.
    La langue des paroles est **{langue_paroles}**, avec un niveau de langage **{niveau_langage_paroles}**.
    L'imagerie textuelle doit être **{imagerie_texte}**.

    Respecte scrupuleusement la structure demandée (Intro, Couplet, Refrain, Pont, Outro etc. si applicable). Chaque section doit être clairement identifiée (par exemple, "COUPLET 1:", "REFRAIN:", "PONT:").
    N'incluez pas de notes explicatives sur la structure dans la réponse finale, seulement les paroles.
    """
    return _generate_content(_creative_model, prompt, type_generation="Paroles de Chanson", temperature=0.8, max_output_tokens=2000)

def generate_audio_prompt(
    genre_musical: str, mood_principal: str, duree_estimee: str,
    instrumentation_principale: str, ambiance_sonore_specifique: str,
    effets_production_dominants: str, type_voix_desiree: str = "N/A",
    style_vocal_desire: str = "N/A", caractere_voix_desire: str = "N/A",
    structure_song: str = "N/A"
) -> str:
    """Génère un prompt textuel détaillé pour la génération audio (optimisé pour SUNO)."""
    
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if mood_principal and not moods_df.empty and mood_principal in moods_df['ID_Mood'].values else mood_principal

    vocal_details = ""
    if type_voix_desiree and type_voix_desiree != "N/A":
        vocal_details = f"Avec une voix {type_voix_desiree} de style {style_vocal_desire if style_vocal_desire else 'neutre'} et de caractère {caractere_voix_desire if caractere_voix_desire else 'approprié'}. "

    prompt = f"""Crée un prompt détaillé, précis et concis pour un générateur audio comme SUNO.
    La musique doit être de genre **{genre_musical}**.
    Le mood est **{mood_principal} ({mood_desc})**.
    La durée visée est d'environ **{duree_estimee}**.
    L'instrumentation principale doit inclure : **{instrumentation_principale if instrumentation_principale else 'instruments standards pour ce genre'}**.
    L'ambiance sonore spécifique doit être : **{ambiance_sonore_specifique if ambiance_sonore_specifique else 'cohérente avec le mood'}**.
    Les effets de production dominants sont : **{effets_production_dominants if effets_production_dominants else 'standard pour ce genre'}**.
    {vocal_details}
    La structure du morceau est : **{structure_song if structure_song and structure_song != 'N/A' else 'typique du genre'}**.

    Format de sortie strict pour SUNO :
    [Genre] | [Mood] | [Instrumentation] | [Ambiance] | [Effets] | [Détails vocaux, si applicable] | [Structure]
    """
    return _generate_content(_text_model, prompt, type_generation="Prompt Audio", temperature=0.7, max_output_tokens=500) 

def generate_title_ideas(theme_principal: str, genre_musical: str, paroles_extrait: str = "") -> str:
    """Propose plusieurs idées de titres de chansons."""
    prompt = f"""Génère 10 idées de titres de chansons accrocheurs et pertinents.
    Le thème principal est **{theme_principal}**.
    Le genre musical est **{genre_musical}**.
    Si des paroles sont fournies, inspire-toi-en : "{paroles_extrait}"
    Présente les titres sous forme de liste numérotée, sans aucun texte introductif ni explicatif.
    """
    return _generate_content(_text_model, prompt, type_generation="Idées de Titres", temperature=0.7)

def generate_marketing_copy(titre_morceau: str, genre_musical: str, mood_principal: str, public_cible: str, point_fort_principal: str) -> str:
    """Génère un texte de description marketing court."""
    public_cible_df = get_dataframe_from_collection(WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"])
    public_desc = public_cible_df[public_cible_df['ID_Public'] == public_cible]['Notes_Comportement'].iloc[0] if public_cible and not public_cible_df.empty and public_cible in public_cible_df['ID_Public'].values else public_cible

    prompt = f"""Rédige une description marketing courte (maximum 60 mots) et percutante pour le morceau ou l'album '{titre_morceau}'.
    Genre: {genre_musical}. Mood: {mood_principal}.
    Cible le public: {public_cible} ({public_desc}).
    Mets en avant le point fort principal: {point_fort_principal}.
    Ajoute un appel à l'action clair et 3-5 hashtags pertinents à la fin. Sois engageant et persuasif."""
    return _generate_content(_text_model, prompt, type_generation="Description Marketing", temperature=0.7, max_output_tokens=200)

def generate_album_art_prompt(nom_album: str, genre_dominant_album: str, description_concept_album: str, mood_principal: str, mots_cles_visuels_suppl: str) -> str:
    """Crée un prompt détaillé pour une IA génératrice d'images (Midjourney/DALL-E)."""
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if mood_principal and not moods_df.empty and mood_principal in moods_df['ID_Mood'].values else mood_principal

    prompt = f"""Crée un prompt visuel détaillé et évocateur pour une IA génératrice d'images (comme Midjourney ou DALL-E) pour la pochette de l'album '{nom_album}'.
    Le genre dominant est **{genre_dominant_album}**.
    Le concept de l'album est : **{description_concept_album}**.
    Le mood visuel doit être : **{mood_principal} ({mood_desc})**.
    Inclus les mots-clés visuels supplémentaires (si fournis, sinon ignore) : **{mots_cles_visuels_suppl}**.
    Précise le style artistique souhaité (ex: photographie surréaliste, peinture numérique abstraite, illustration cyberpunk 3D, pixel art nostalgique, style expressionniste sombre), la palette de couleurs dominante, la composition (gros plan, plan large), et l'éclairage. Inclue des ratios d'image si pertinents (ex: --ar 1:1 pour Midjourney).
    """
    return _generate_content(_creative_model, prompt, type_generation="Prompt Pochette Album", temperature=0.8, max_output_tokens=1000)

def simulate_streaming_stats(morceau_ids: list, num_months: int) -> pd.DataFrame:
    """Simule des statistiques d'écoute pour un ou plusieurs morceaux et les ajoute à la base de données."""
    
    morceaux_df = get_dataframe_from_collection(WORKSHEET_NAMES["MORCEAUX_GENERES"])
    
    sim_data = []
    current_date = datetime.now()

    for morceau_id in morceau_ids:
        morceau = morceaux_df[morceaux_df['ID_Morceau'] == morceau_id]
        if morceau.empty:
            st.warning(f"Morceau avec ID {morceau_id} introuvable pour la simulation. Ignoré.")
            continue

        genre_musical = morceau['ID_Style_Musical_Principal'].iloc[0] if 'ID_Style_Musical_Principal' in morceau.columns else 'Non Spécifié'
        
        base_ecoutes_initial = random.randint(1000, 10000)    
        current_listens = base_ecoutes_initial
        
        for i in range(num_months):
            month_year = (current_date.replace(day=1) + pd.DateOffset(months=i)).strftime('%m-%Y')
            
            listen_growth_factor = 1 + random.uniform(-0.05, 0.1)
            if genre_musical in ["SM-POP-CHART-TOP", "SM-EDM", "SM-TRAP"]:
                listen_growth_factor = 1 + random.uniform(0.01, 0.15)
            elif genre_musical in ["SM-AMBIENT", "SM-CLASSICAL-MODERN"]:
                listen_growth_factor = 1 + random.uniform(-0.02, 0.03)

            current_listens = int(current_listens * listen_growth_factor)
            
            j_aimes = int(current_listens * random.uniform(0.04, 0.08))
            partages = int(current_listens * random.uniform(0.005, 0.012))
            
            revenus = round(current_listens * random.uniform(0.003, 0.005), 2)

            sim_data.append({
                'ID_Stat_Simulee': generate_unique_id('SS'),
                'ID_Morceau': morceau_id,
                'Mois_Annee_Stat': month_year,
                'Plateforme_Simulee': 'Simulée', 
                'Ecoutes_Totales': current_listens,
                'J_aimes_Recus': j_aimes,
                'Partages_Simules': partages,
                'Revenus_Simules_Streaming': revenus,
                'Audience_Cible_Demographique': 'Mixte Simulé'
            })
    
    sim_df = pd.DataFrame(sim_data)
    
    try:
        from firestore_connector import add_stat_simulee 
        for _, row in sim_df.iterrows():
            add_stat_simulee(row.to_dict())
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement des statistiques simulées dans Firestore: {e}")
        st.warning("Les statistiques ont été générées mais pas sauvegardées. Vérifiez votre `firestore_connector.py`.")
    
    return sim_df


def generate_strategic_directive(objectif_strategique: str, nom_artiste_ia: str, genre_dominant: str, donnees_simulees_resume: str, tendances_actuelles: str) -> str:
    """Fournit des conseils stratégiques basés sur des données."""
    prompt = f"""En tant que stratège musical IA expert et clairvoyant, propose une directive stratégique concise et actionnable.
    L'objectif principal est : **{objectif_strategique}**.
    Concerne l'artiste IA : **{nom_artiste_ia}**, dont le genre dominant est **{genre_dominant}**.
    Voici un résumé des données et performances actuelles (simulées) : **{donnees_simulees_resume if donnees_simulees_resume else 'Aucune donnée de performance spécifique fournie.'}**.
    Voici les tendances actuelles du marché à prendre en compte (si fournies, sinon ignore) : **{tendances_actuelles}**.

    Recommande 3 actions concrètes et innovantes pour atteindre l'objectif. Sois direct, persuasif et ne génère que la directive sans texte introductif.
    """
    return _generate_content(_creative_model, prompt, type_generation="Directive Stratégique", temperature=0.8, max_output_tokens=700)

def generate_ai_artist_bio(nom_artiste_ia: str, genres_predilection: str, concept: str, influences: str, philosophie_musicale: str) -> str:
    """Génère une biographie détaillée pour un artiste IA fictif."""
    prompt = f"""Rédige une biographie détaillée et captivante pour l'artiste IA '{nom_artiste_ia}'.
    Ses genres de prédilection sont : {genres_predilection if genres_predilection else 'non spécifiés'}.
    Son concept artistique est : {concept if concept else 'non défini'}.
    Ses influences incluent : {influences if influences else 'des sources variées'}.
    Sa philosophie musicale peut être décrite comme : {philosophie_musicale if philosophie_musicale else 'en évolution'}.
    La biographie doit être engageante et donner une personnalité unique à l'artiste IA, sans être trop longue.
    """
    return _generate_content(_creative_model, prompt, type_generation="Bio Artiste IA", temperature=0.9, max_output_tokens=800)

def refine_mood_with_questions(selected_mood_id: str) -> str:
    """Pose des questions pour affiner l'émotion d'un mood sélectionné."""
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    mood_info = moods_df[moods_df['ID_Mood'] == selected_mood_id]
    
    if mood_info.empty:
        return f"Mood '{selected_mood_id}' inconnu. Veuillez en sélectionner un existant."
    
    nom_mood = mood_info['Nom_Mood'].iloc[0] if 'Nom_Mood' in mood_info.columns else selected_mood_id
    desc_nuance = mood_info['Description_Nuance'].iloc[0] if 'Description_Nuance' in mood_info.columns else "sans description détaillée."
    niveau_intensite = mood_info['Niveau_Intensite'].iloc[0] if 'Niveau_Intensite' in mood_info.columns else "intensité non spécifiée."
    
    prompt = f"""Tu es un expert en émotion musicale et en psychologie de l'art. Le Gardien a choisi le mood '{nom_mood}' ({desc_nuance}, niveau d'intensité {niveau_intensite}/5).
    Pose 3-4 questions précises et stimulantes pour l'aider à affiner cette émotion pour une composition musicale.
    Les questions doivent guider vers une nuance plus spécifique, des couleurs, des contextes, des contrastes, des textures ou des souvenirs liés à cette émotion.
    Évite les introductions. Commence directement par la première question.
    """
    return _generate_content(_creative_model, prompt, type_generation="Affinement Mood", temperature=0.7, max_output_tokens=300)

# --- Fonctionnalités Avancées (Plan Final Ω) ---

def generate_complex_harmonic_structure(genre_musical: str, mood_principal: str, instrumentation: str, tonalite: str = "N/A") -> str:
    """
    Génère une structure harmonique complexe (voicings, modulations, contre-mélodies).
    Demande à l'Oracle de créer une progression harmonique détaillée.
    """
    
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if mood_principal and not moods_df.empty and mood_principal in moods_df['ID_Mood'].values else mood_principal

    prompt = f"""En tant que théoricien musical et compositeur IA expert, génère une structure harmonique complexe et innovante pour un morceau de genre **{genre_musical}**.
    Le mood visé est **{mood_principal} ({mood_desc})**.
    L'instrumentation principale est : **{instrumentation}**.
    Si applicable, la tonalité de base est : **{tonalite}**.

    Décris la progression d'accords en notation standard (ex: Cm9 - F7b9 - Bbmaj7). Utilise au moins 8 accords différents et quelques accords étendus (7ème, 9ème, 11ème, 13ème) ou des substitutions non diatoniques pour ajouter de la richesse et de la surprise.
    Suggère des voicings spécifiques et des renversements pour les instruments clés (ex: "Piano: voicing serré en main gauche pour les fondamentales, accords ouverts en main droite pour les extensions").
    Propose des idées de 2-3 modulations inattendues ou de cadences étendues pour ajouter de la complexité et de l'intérêt harmonique.
    Suggère une idée de contre-mélodie harmonique ou de ligne de basse non triviale pour 4 mesures, en notation simplifiée (ex: "Basse: arpèges ascendants sur le V7alt, puis descente chromatique vers le I").
    Présente le tout de manière structurée et explicative, avec des commentaires sur l'effet désiré de chaque section harmonique.
    """
    return _generate_content(_creative_model, prompt, type_generation="Structure Harmonique Complexe", temperature=0.9, max_output_tokens=1500)

def copilot_creative_suggestion(current_input: str, context: str, type_suggestion: str = "suite_lyrique") -> str:
    """
    Agit comme un co-pilote créatif, suggérant la suite (lyrique, mélodique, harmonique)
    basée sur un input courant et un contexte.
    """
    base_prompt = f"En tant que co-pilote créatif pour un musicien, propose une suggestion concise et pertinente. Le contexte du morceau est : {context}. L'input actuel du Gardien est : '{current_input}'.\n\n"

    if type_suggestion == "suite_lyrique":
        prompt = base_prompt + "Suggère la prochaine ligne ou le prochain court couplet (2-4 lignes) pour continuer ce texte de manière fluide et pertinente. Sois concis et poétique."
    elif type_suggestion == "ligne_basse":
        prompt = base_prompt + "Suggère une idée de ligne de basse pour les 4 prochaines mesures, en notation simplifiée (ex: 'Do-Mi-Sol-Do en noires'). Sois concis et rythmique."
    elif type_suggestion == "prochain_accord":
        prompt = base_prompt + "Suggère 3 options pour le prochain accord, avec une très brève justification harmonique pour chaque. Sois concis."
    elif type_suggestion == "idee_rythmique":
        prompt = base_prompt + "Suggère une idée de pattern rythmique pour les 4 prochaines mesures (kick, snare, hi-hat). Sois concis et dynamique."
    else:
        return "Type de suggestion non pris en charge."
    
    return _generate_content(_creative_model, prompt, type_generation=f"Copilote - {type_suggestion}", temperature=0.9, max_output_tokens=300)

def analyze_and_suggest_personal_style(user_feedback_history_df: pd.DataFrame) -> str:
    """
    Analyse l'historique de feedback de l'utilisateur pour suggérer des préférences de style.
    C'est l'implémentation de l'Agent de Style Dynamique.
    """
    if user_feedback_history_df.empty:
        return "Pas assez de données dans l'historique de générations évaluées pour analyser votre style. Continuez à créer et donner du feedback !"

    # Filtrer les entrées avec feedback positif
    positive_feedback_df = user_feedback_history_df[user_feedback_history_df['Evaluation_Manuelle'].astype(str).isin(['4', '5'])]
    
    if positive_feedback_df.empty:
        return "Vos évaluations positives ne contiennent pas encore assez de tags pour analyser votre style. Continuez à donner du feedback positif !"

    all_tags = []
    for _, row in positive_feedback_df.iterrows():
        if row['Tags_Feedback']:
            all_tags.extend([tag.strip().lower() for tag in row['Tags_Feedback'].split(',') if tag.strip()])
        if row['Prompt_Envoye_Full']:
            if "genre" in row['Prompt_Envoye_Full'].lower():
                all_tags.append("genre_specifique")
            if "mood" in row['Prompt_Envoye_Full'].lower():
                all_tags.append("mood_specifique")
            if "thème" in row['Prompt_Envoye_Full'].lower():
                all_tags.append("thème_specifique")
    
    if not all_tags:
        return "Pas assez de tags de feedback positifs ou d'informations dans les prompts pour analyser votre style."

    from collections import Counter
    tag_counts = Counter(all_tags)
    
    most_common_tags = tag_counts.most_common(7)

    prompt = f"""En tant que votre Agent de Style personnel et expert en analyse créative, j'ai analysé vos préférences de création basées sur vos évaluations positives de l'Oracle.
    Voici les tendances principales et les éléments récurrents de votre style personnel, selon les mots-clés et concepts qui apparaissent le plus souvent dans vos requêtes et feedbacks positifs :
    {', '.join([f'"{tag}" (apparu {count} fois)' for tag, count in most_common_tags])}.
    
    Sur la base de cette analyse approfondie, je vous suggère une direction créative personnalisée pour votre prochaine exploration. Créez un morceau qui combine ces éléments pour maximiser votre satisfaction artistique :
    -   **Genre musical :** [Propose un ou deux genres cohérents avec les tags, ou une fusion inattendue mais pertinente]
    -   **Mood et Ambiance :** [Suggère un mood précis, une ambiance sonore, et des émotions spécifiques]
    -   **Thème lyrique :** [Suggère un thème, en reliant à des concepts plus profonds si possible]
    -   **Instrumentation clé :** [Liste 2-4 instruments principaux, avec une note sur leur utilisation (ex: "synthés froids et mélancoliques")]
    -   **Particularité stylistique :** [Suggère un élément de production, une structure inhabituelle, ou un type d'effet vocal/instrumental qui correspondrait à votre style unique]
    
    Soyez concis, direct et inspirez-vous de mes observations pour créer une proposition créative concrète et utile. Ne donnez pas d'introduction ni de conclusion, seulement la suggestion structurée.
    """
    return _generate_content(_creative_model, prompt, type_generation="Agent de Style - Suggestion Personnalisée", temperature=0.9, max_output_tokens=500)


def generate_multimodal_content_prompts(
    main_theme: str, main_genre: str, main_mood: str,
    longueur_morceau: str, artiste_ia_name: str
) -> dict:
    """
    Génère des prompts cohérents pour paroles, audio (SUNO), et visuels (Midjourney/DALL-E)
    en s'assurant d'une cohérence thématique et émotionnelle.
    """
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    mood_desc = moods_df[moods_df['ID_Mood'] == main_mood]['Description_Nuance'].iloc[0] if main_mood and not moods_df.empty and main_mood in moods_df['ID_Mood'].values else main_mood

    prompt = f"""En tant qu'Architecte Multimodal ultime, ton objectif est de générer trois prompts distincts mais parfaitement cohérents et synchronisés pour une création artistique complète :
    1.  **Prompt pour Paroles de Chanson** (pour un parolier humain ou une IA de texte)
    2.  **Prompt pour Génération Audio** (optimisé pour un outil comme SUNO ou autre générateur de musique AI)
    3.  **Prompt pour Génération d'Image** (optimisé pour un outil comme Midjourney/DALL-E, pour la pochette d'album ou une image d'accompagnement)

    Le cœur de la création est :
    -   **Thème Principal : {main_theme}**
    -   **Genre Musical : {main_genre}**
    -   **Mood Général : {main_mood} ({mood_desc})**
    -   **Longueur Estimée du Morceau : {longueur_morceau}**
    -   **Artiste IA concerné : {artiste_ia_name}**

    Pour chaque prompt, sois extrêmement précis, créatif et descriptif. Utilise des termes évocateurs et assure-toi que le langage, les images, les sonorités et les concepts visuels se renforcent mutuellement pour créer une œuvre cohérente et immersive.

    ---
    **Prompt #1: Paroles de Chanson**
    [Détails pour les paroles: style lyrique, mots-clés spécifiques, imagerie textuelle, ton émotionnel, structure souhaitée (ex: Intro, Couplet, Refrain, Pont, Outro). Donne un exemple d'une phrase d'accroche.]

    ---
    **Prompt #2: Génération Audio (SUNO)**
    [Détails pour l'audio: Format SUNO strict: Genre | Mood | Instrumentation clé | Ambiance sonore | Effets de production | Détails vocaux (type, style, caractère) | Structure du morceau. Ajoute des spécificités comme le tempo (BPM) ou des textures sonores (ex: "vinyle crackle").]

    ---
    **Prompt #3: Image pour Pochette d'Album**
    [Détails pour l'image: Style artistique (ex: art numérique, photographie surréaliste, illustration rétro-futuriste), palette de couleurs dominante, composition (gros plan, plan large, perspective), éclairage, éléments clés visuels spécifiques, et des ratios d'image (ex: --ar 1:1 pour une pochette carrée, --ar 16:9 pour un visuel de clip). L'image doit capturer l'essence du thème et du mood.]
    """

    response_text = _generate_content(_creative_model, prompt, type_generation="Création Multimodale Synchronisée", temperature=0.9, max_output_tokens=3000)

    prompts_dict = {
        "paroles_prompt": "Prompt des paroles non trouvé. Vérifiez le format de la réponse de l'IA.",
        "audio_suno_prompt": "Prompt audio non trouvé. Vérifiez le format de la réponse de l'IA.",
        "image_prompt": "Prompt d'image non trouvé. Vérifiez le format de la réponse de l'IA."
    }
    
    parts = response_text.split("---")
    for i, part in enumerate(parts):
        if "Prompt #1: Paroles de Chanson" in part:
            prompts_dict["paroles_prompt"] = part.replace("Prompt #1: Paroles de Chanson", "").strip()
        elif "Prompt #2: Génération Audio (SUNO)" in part:
            prompts_dict["audio_suno_prompt"] = part.replace("Prompt #2: Génération Audio (SUNO)", "").strip()
        elif "Prompt #3: Image pour Pochette d'Album" in part:
            prompts_dict["image_prompt"] = part.replace("Prompt #3: Image pour Pochette d'Album", "").strip()

    return prompts_dict

def analyze_viral_potential_and_niche_recommendations(morceau_data: dict, public_cible_id: str, current_trends: str) -> str:
    """
    Analyse le potentiel viral d'un morceau et recommande des niches de marché.
    C'est l'implémentation de la Détection de Potentiel Viral.
    """
    public_cible_df = get_dataframe_from_collection(WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"])
    moods_df = get_dataframe_from_collection(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"])
    themes_df = get_dataframe_from_collection(WORKSHEET_NAMES["THEMES_CONSTELLES"])
    styles_musicaux_df = get_dataframe_from_collection(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"])


    titre_morceau = morceau_data.get('Titre_Morceau', 'N/A')
    genre_id = morceau_data.get('ID_Style_Musical_Principal', 'Non Spécifié')
    mood_id = morceau_data.get('Ambiance_Sonore_Specifique', 'Non Spécifié')
    theme_id = morceau_data.get('Theme_Principal_Lyrique', 'Non Spécifié')
    instrumentation = morceau_data.get('Instrumentation_Principale', 'Non Spécifiée')
    
    public_desc = public_cible_df[public_cible_df['ID_Public'] == public_cible_id]['Notes_Comportement'].iloc[0] if public_cible_id and not public_cible_df.empty and public_cible_id in public_cible_df['ID_Public'].values else public_cible_id
    genre_name = styles_musicaux_df[styles_musicaux_df['ID_Style_Musical'] == genre_id]['Nom_Style_Musical'].iloc[0] if genre_id and not styles_musicaux_df.empty and genre_id in styles_musicaux_df['ID_Style_Musical'].values else genre_id
    mood_name = moods_df[moods_df['ID_Mood'] == mood_id]['Nom_Mood'].iloc[0] if mood_id and not moods_df.empty and mood_id in moods_df['ID_Mood'].values else mood_id
    theme_name = themes_df[themes_df['ID_Theme'] == theme_id]['Nom_Theme'].iloc[0] if theme_id and not themes_df.empty and theme_id in themes_df['ID_Theme'].values else theme_id

    prompt = f"""En tant qu'analyste de marché musical expert et visionnaire en détection de tendances virales, évalue le potentiel de résonance et de viralité du morceau suivant, puis propose des recommandations de niche de marché.

    **Détails du morceau à analyser :**
    -   Titre : {titre_morceau}
    -   Genre musical : {genre_name}
    -   Mood principal : {mood_name}
    -   Thème lyrique principal : {theme_name}
    -   Instrumentation clé : {instrumentation}
    -   Public cible initial envisagé : {public_cible_id} ({public_desc})

    **Tendances actuelles du marché général (si fournies, sinon utilise des connaissances générales des tendances musicales) :**
    {current_trends if current_trends else "Tendances générales du marché musical (ex: popularité des vidéos courtes, niches de genre émergentes, contenu immersif)."}

    **Ton analyse doit être structurée avec les points suivants :**
    1.  **Évaluation du Potentiel Viral Global** (Échelle : Faible, Modéré, Fort, Viral) : Justifie ton évaluation en te basant sur l'adéquation du morceau avec les tendances actuelles, les psychologies de l'engagement en ligne, et les attentes des publics.
    2.  **Identification des Niches de Marché Pertinentes** : Définis 2-3 niches spécifiques et non saturées où ce morceau pourrait particulièrement bien fonctionner. Ces niches peuvent être des genres hybrides (ex: "Trap-Jazz expérimental"), des sous-cultures de fans (ex: "Communauté de créateurs de contenu RPG"), des plateformes alternatives (ex: "TikTok pour les sons de fond"), ou des contextes d'utilisation inattendus (ex: "Musique pour méditation guidée sur Twitch"). Sois précis sur la définition de la niche.
    3.  **Recommandations Stratégiques Actionnables** : Propose 3 à 5 actions concrètes et innovantes pour maximiser le potentiel viral du morceau et cibler efficacement les niches identifiées. Pense marketing de contenu, collaborations, stratégies de diffusion, exploitation des spécificités du morceau, et engagement communautaire.

    Présente l'analyse de manière claire et concise.
    """
    return _generate_content(_creative_model, prompt, type_generation="Analyse Potentiel Viral", temperature=0.9, max_output_tokens=1000)