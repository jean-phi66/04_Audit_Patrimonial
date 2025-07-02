import streamlit as st

st.set_page_config(
    page_title="Accueil | Optimiseur Patrimonial",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Bienvenue sur l'Outil d'Optimisation et de Simulation")
st.write("""
Utilisez le menu de navigation sur la gauche pour accéder aux différentes fonctionnalités de cet outil.

- **🚀 Optimisation**: Laissez l'algorithme trouver la meilleure allocation d'actifs pour atteindre vos objectifs financiers en fonction de vos paramètres.

- **Manuelle Simulation**: Testez vous-même une stratégie d'investissement en définissant manuellement la répartition de votre épargne.

Toutes les hypothèses (situation initiale, fiscalité, options d'investissement) peuvent être configurées dans la barre latérale qui est commune aux deux modules.
""")

st.info("👈 Commencez par sélectionner une page dans le menu de navigation.")