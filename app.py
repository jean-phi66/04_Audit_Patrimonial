# app.py
import streamlit as st
from utils.state_manager import initialize_session

# Configuration de la page doit être la première commande Streamlit
st.set_page_config(
    page_title="Audit Patrimonial Dynamique",
    page_icon="📊",
    layout="wide"
)

# Initialise toutes les variables de session au premier lancement
initialize_session()

# Page d'accueil
st.title("📊 Outil d'Audit et de Projection Patrimoniale")
st.write("""
Bienvenue sur votre outil d'audit patrimonial.
Utilisez le menu de navigation sur la gauche pour vous déplacer entre les différentes sections :

- **Patrimoine & Dettes**: Saisissez l'ensemble de vos actifs et de vos prêts.
- **Budget (Flux)**: Renseignez vos revenus et vos dépenses courantes.
- **Famille & Événements**: Décrivez la composition de votre foyer et planifiez des événements futurs comme la revente d'un bien.
- **Projection**: Lancez la simulation pour visualiser l'évolution de votre patrimoine et de vos flux financiers sur le long terme.
- **Sauvegarde & Chargement**: Enregistrez votre session ou chargez une session précédente.
""")

st.info("Toutes les données que vous saisissez sont conservées au sein de votre session de navigation.")