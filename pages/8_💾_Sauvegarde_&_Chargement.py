# pages/8_💾_Sauvegarde_&_Chargement.py
import streamlit as st
import os
from utils.state_manager import (
    save_state_to_file, 
    load_state_from_file, 
    reset_state, 
    initialize_session
)

# Configuration de la page
st.set_page_config(page_title="Sauvegarde & Chargement", layout="wide")
st.title("💾 Sauvegarde & Chargement")

# Initialisation de l'état (important au début de chaque page)
initialize_session()

# --- Section Sauvegarde ---
st.header("Sauvegarder l'état de la session")
save_path = "session_state.json" # Fichier temporaire sur le serveur

if st.button("Préparer le fichier de sauvegarde"):
    save_state_to_file(save_path)

# Le bouton de téléchargement apparaît si le fichier de sauvegarde a été créé
if os.path.exists(save_path):
    with open(save_path, "rb") as fp:
        st.download_button(
            label="Télécharger le fichier de sauvegarde",
            data=fp,
            file_name="audit_patrimonial_sauvegarde.json",
            mime="application/json"
        )
    # On peut optionnellement supprimer le fichier temporaire après préparation
    # os.remove(save_path)

# --- Section Chargement ---
st.header("Charger l'état de la session depuis un fichier")
uploaded_file = st.file_uploader(
    "Choisissez un fichier de sauvegarde (.json)", 
    type="json"
)

if uploaded_file is not None:
    # Le chargement se fait via la fonction du state_manager qui gère aussi le st.rerun()
    load_state_from_file(uploaded_file)
    # Il n'est plus nécessaire d'avoir un bouton "Charger" car le simple fait
    # de téléverser un fichier suffit à le rendre disponible. On pourrait
    # garder un bouton pour une confirmation explicite si souhaité.

# --- Section Réinitialisation ---
st.header("Réinitialiser l'état")
if st.button("Réinitialiser la session"):
    reset_state()
    st.rerun()

