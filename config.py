# config.py

import os

# --- Configuration Générale du Projet ---
# Nom de ton Google Sheet principal (ceci est conservé pour le moment pour la compatibilité des noms de collection)
# Dans Firestore, ces noms seront utilisés comme noms de collection.
# RENOMMÉ DE FIRESTORE_COLLECTIONS À WORKSHEET_NAMES POUR LA COMPATIBILITÉ
WORKSHEET_NAMES = {
    "MORCEAUX_GENERES": "MORCEAUX_GENERES",
    "ALBUMS_PLANETAIRES": "ALBUMS_PLANETAIRES",
    "SESSIONS_CREATIVES_ORACLE": "SESSIONS_CREATIVES_ORACLE",
    "ARTISTES_IA_COSMIQUES": "ARTISTES_IA_COSMIQUES",
    "STYLES_MUSICAUX_GALACTIQUES": "STYLES_MUSICAUX_GALACTIQUES",
    "STYLES_LYRIQUES_UNIVERS": "STYLES_LYRIQUES_UNIVERS",
    "THEMES_CONSTELLES": "THEMES_CONSTELLES",
    "STATISTIQUES_ORBITALES_SIMULEES": "STATISTIQUES_ORBITALES_SIMULEES",
    "CONSEILS_STRATEGIQUES_ORACLE": "CONSEILS_STRATEGIQUES_ORACLE",
    "INSTRUMENTS_ORCHESTRAUX": "INSTRUMENTS_ORCHESTRAUX",
    "STRUCTURES_SONG_UNIVERSELLES": "STRUCTURES_SONG_UNIVERSELLES",
    "VOIX_ET_STYLES_VOCAUX": "VOIX_ET_STYLES_VOCAUX",
    "REGLES_DE_GENERATION_ORACLE": "REGLES_DE_GENERATION_ORACLE",
    "MOODS_ET_EMOTIONS": "MOODS_ET_EMOTIONS",
    "REFERENCES_SONORES_DETAILLES": "REFERENCES_SONORES_DETAILLES",
    "PUBLIC_CIBLE_DEMOGRAPHIQUE": "PUBLIC_CIBLE_DEMOGRAPHIQUE",
    "PROMPTS_TYPES_ET_GUIDES": "PROMPTS_TYPES_ET_GUIDES",
    "PROJETS_EN_COURS": "PROJETS_EN_COURS",
    "OUTILS_IA_REFERENCEMENT": "OUTILS_IA_REFERENCEMENT",
    "TIMELINE_EVENEMENTS_CULTURELS": "TIMELINE_EVENEMENTS_CULTURELS",
    "PAROLES_EXISTANTES": "PAROLES_EXISTANTES",
    "HISTORIQUE_GENERATIONS": "HISTORIQUE_GENERATIONS"
}

# Dossier local pour les assets (covers, audios, textes générés)
# Assure-toi que ces dossiers existent dans le répertoire de ton application Streamlit
ASSETS_DIR = "assets"
AUDIO_CLIPS_DIR = os.path.join(ASSETS_DIR, "audio_clips")
SONG_COVERS_DIR = os.path.join(ASSETS_DIR, "song_covers")
ALBUM_COVERS_DIR = os.path.join(ASSETS_DIR, "album_covers")
GENERATED_TEXTS_DIR = os.path.join(ASSETS_DIR, "texts_generated") # Pour les paroles sauvegardées localement

# Clé API Gemini (nom de la variable dans secrets.toml)
GEMINI_API_KEY_NAME = "GEMINI_API_KEY"

# --- Colonnes attendues pour chaque collection Firestore (pour la validation des données) ---
# Ceci est crucial pour firestore_connector.py pour s'assurer que les données sont bien structurées
EXPECTED_COLUMNS = {
    WORKSHEET_NAMES["MORCEAUX_GENERES"]: [
        'ID_Morceau', 'Titre_Morceau', 'Statut_Production', 'Date_Creation', 'Date_Mise_A_Jour',
        'ID_Album_Associe', 'ID_Artiste_IA', 'Durée_Estimee', 'Prompt_Generation_Audio',
        'Prompt_Generation_Paroles', 'ID_Style_Musical_Principal', 'ID_Style_Lyrique_Principal',
        'Theme_Principal_Lyrique', 'Mots_Cles_Generation', 'Langue_Paroles',
        'Niveau_Langage_Paroles', 'Imagerie_Texte', 'Structure_Chanson_Specifique',
        'Instrumentation_Principale', 'Ambiance_Sonore_Specifique', 'Effets_Production_Dominants',
        'Type_Voix_Desiree', 'Style_Vocal_Desire', 'Caractere_Voix_Desire',
        'URL_Audio_Local', 'URL_Cover_Album', 'URL_Video_Clip_Associe', 'Mots_Cles_SEO',
        'Description_Courte_Marketing', 'Favori'
    ],
    WORKSHEET_NAMES["ALBUMS_PLANETAIRES"]: [
        'ID_Album', 'Nom_Album', 'Date_Sortie_Prevue', 'Statut_Album',
        'Description_Concept_Album', 'ID_Artiste_IA_Principal',
        'Genre_Dominant_Album', 'URL_Cover_Principale', 'Mots_Cles_Album_SEO'
    ],
    WORKSHEET_NAMES["SESSIONS_CREATIVES_ORACLE"]: [
        'ID_Session', 'Date_Session', 'Heure_Debut', 'Heure_Fin', 'Objectif_Session',
        'Oracle_Prompt_Utilise', 'Resultats_Clefs_Session', 'Notes_Gardien',
        'ID_Morceaux_Affectes'
    ],
    WORKSHEET_NAMES["ARTISTES_IA_COSMIQUES"]: [
        'ID_Artiste_IA', 'Nom_Artiste_IA', 'Description_Artiste', 'Genres_Predilection',
        'URL_Image_Profil'
    ],
    WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"]: [
        'ID_Style_Musical', 'Nom_Style_Musical', 'Description_Detaillee',
        'Artistes_References', 'Exemples_Sonores'
    ],
    WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"]: [
        'ID_Style_Lyrique', 'Nom_Style_Lyrique', 'Description_Detaillee',
        'Auteurs_References', 'Exemples_Textuels_Courts'
    ],
    WORKSHEET_NAMES["THEMES_CONSTELLES"]: [
        'ID_Theme', 'Nom_Theme', 'Description_Conceptuelle', 'Mots_Cles_Associes'
    ],
    WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"]: [
        'ID_Stat_Simulee', 'ID_Morceau', 'Mois_Annee_Stat', 'Plateforme_Simulee',
        'Ecoutes_Totales', 'J_aimes_Recus', 'Partages_Simules',
        'Revenus_Simules_Streaming', 'Audience_Cible_Demographique'
    ],
    WORKSHEET_NAMES["CONSEILS_STRATEGIQUES_ORACLE"]: [
        'ID_Conseil', 'Date_Conseil', 'Type_Conseil', 'Prompt_Demande',
        'Directive_Oracle', 'Donnees_Source_Utilisees'
    ],
    WORKSHEET_NAMES["INSTRUMENTS_ORCHESTRAUX"]: [
        'ID_Instrument', 'Nom_Instrument', 'Type_Instrument',
        'Sonorité_Caractéristique', 'Utilisation_Prevalente', 'Famille_Sonore'
    ],
    WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"]: [
        'ID_Structure', 'Nom_Structure', 'Schema_Detaille', 'Notes_Application_IA'
    ],
    WORKSHEET_NAMES["VOIX_ET_STYLES_VOCAUX"]: [
        'ID_Vocal', 'Type_Vocal_General', 'Tessiture_Specifique',
        'Style_Vocal_Detaille', 'Caractere_Expressif', 'Effets_Voix_Souhaites'
    ],
    WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"]: [
        'ID_Regle', 'Type_Regle', 'Description_Regle',
        'Impact_Sur_Generation', 'Statut_Actif'
    ],
    WORKSHEET_NAMES["MOODS_ET_EMOTIONS"]: [
        'ID_Mood', 'Nom_Mood', 'Description_Nuance', 'Niveau_Intensite',
        'Mots_Cles_Associes', 'Couleur_Associee', 'Tempo_Range_Suggerer'
    ],
    WORKSHEET_NAMES["REFERENCES_SONORES_DETAILLES"]: [
        'ID_RefSonore', 'Nom_RefSonore', 'Type_Son', 'Artiste_Album_Ref',
        'Description_Sonore', 'Impact_Audio_Desire'
    ],
    WORKSHEET_NAMES["PUBLIC_CIBLE_DEMOGRAPHIQUE"]: [
        'ID_Public', 'Nom_Public', 'Tranche_Age', 'Interets_Demographiques',
        'Plateformes_Ecoute_Preferees', 'Tone_Marketing_Suggerer', 'Notes_Comportement'
    ],
    WORKSHEET_NAMES["PROMPTS_TYPES_ET_GUIDES"]: [
        'ID_PromptType', 'Nom_PromptType', 'Description_Objectif',
        'Structure_Prompt_Modele', 'Variables_Attendues', 'Instructions_IA'
    ],
    WORKSHEET_NAMES["PROJETS_EN_COURS"]: [
        'ID_Projet', 'Nom_Projet', 'Type_Projet', 'Statut_Projet',
        'Date_Debut', 'Date_Cible_Fin', 'ID_Morceaux_Lies',
        'Notes_Production', 'Budget_Estime'
    ],
    WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"]: [
        'ID_Outil', 'Nom_Outil', 'Description_Fonctionnalite', 'Type_Fonction',
        'URL_Outil', 'Compatibilite_API', 'Prix_Approximatif',
        'Evaluation_Gardien', 'Notes_Utilisation'
    ],
    WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"]: [
        'ID_Evenement', 'Nom_Evenement', 'Date_Debut', 'Date_Fin',
        'Type_Evenement', 'Genre_Associe', 'Public_Associe', 'Notes_Strategiques'
    ],
    WORKSHEET_NAMES["PAROLES_EXISTANTES"]: [
        'ID_Morceau', 'Titre_Morceau', 'Artiste_Principal', 'Genre_Musical',
        'Paroles_Existantes', 'Notes'
    ],
    WORKSHEET_NAMES["HISTORIQUE_GENERATIONS"]: [
        'ID_GenLog', 'Date_Heure', 'ID_Utilisateur', 'Type_Generation',
        'Prompt_Envoye_Full', 'Reponse_Recue_Full', 'ID_Morceau_Associe',
        'Evaluation_Manuelle', 'Commentaire_Qualitatif', 'Tags_Feedback',
        'ID_Regle_Appliquee_Auto'
    ]
}