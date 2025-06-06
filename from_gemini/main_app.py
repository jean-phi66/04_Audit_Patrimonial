# main_app.py
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Développement Audit Patrimonial"
)

# Définition des pages de l'application
pages = {
    "Bilan Actuel": st.Page("views/01_bilan_actuel.py", title="Bilan Patrimonial", icon="🏠"),
    "Budget Actuel": st.Page("views/02_budget_actuel.py", title="Budget & Flux", icon="💶"),
    "Hypothèses": st.Page("views/03_hypotheses.py", title="Hypothèses", icon="⚙️"),
    "Projection": st.Page("views/04_projection.py", title="Résultats Projection", icon="📈")
}

# Barre de navigation
pg = st.navigation(pages)
pg.run()