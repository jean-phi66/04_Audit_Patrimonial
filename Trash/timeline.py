import streamlit as st
import pandas as pd
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Test Graphique Timeline", layout="wide")

st.title("Test Graphique Timeline (Données Bidons)")

# Données bidons pour la chronologie
dummy_timeline_data = [
    dict(Task="Personne A", Start='2024-01-01', Finish='2026-12-31', Resource="Actif", Label="Actif"),
    dict(Task="Personne A", Start='2026-01-01', Finish='2028-12-31', Resource="Étudiant", Label="Étudiant"),
    dict(Task="Personne B", Start='2024-01-01', Finish='2025-12-31', Resource="Scolarisé", Label="Scolarisé"),
    dict(Task="Personne B", Start='2025-01-01', Finish='2028-12-31', Resource="Actif", Label="Actif"),
    dict(Task="Personne C", Start='2024-01-01', Finish='2028-12-31', Resource="Retraité", Label="Retraité")
]

#dummy_timeline_data = pd.DataFrame([
#    dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28'),
#    dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15'),
#    dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30')
#])

fig = px.timeline(dummy_timeline_data, x_start="Start", x_end="Finish", y="Task", 
                  color="Resource",
                  text="Label")
fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
#fig.show()

st.plotly_chart(fig, use_container_width=True)
    

df_dummy_timeline = pd.DataFrame(dummy_timeline_data)

# Affichage et vérification du DataFrame bidon
st.write("DataFrame pour la timeline BIDON (df_dummy_timeline):")
st.dataframe(df_dummy_timeline)
if not df_dummy_timeline.empty:
    st.write("Types de données (dtypes) de df_dummy_timeline:")
    st.write(df_dummy_timeline.dtypes)

# Définir un ordre pour les statuts pour un affichage logique sur l'axe Y et la légende
ordre_statuts = ["Scolarisé", "Étudiant", "Actif", "Retraité"]
# Définir des couleurs pour chaque statut pour la cohérence
couleurs_statuts = {
    "Scolarisé": "skyblue",
    "Étudiant": "lightgreen",
    "Actif": "royalblue",
    "Retraité": "silver"
}
# Noms des membres pour ordonner l'axe Y
noms_membres = ["Personne A", "Personne B", "Personne C"]


try:
    fig_dummy_timeline = px.timeline(
        df_dummy_timeline,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        text="Label",
        title="Exemple de Chronologie avec Données Bidons (Test)",
        labels={"Task": "Membre", "Resource": "Statut"},
        category_orders={"Resource": ordre_statuts},
        color_discrete_map=couleurs_statuts
    )
    #fig_dummy_timeline.update_yaxes(categoryorder="array", categoryarray=noms_membres)
    #fig_dummy_timeline.update_layout(xaxis_title="Année")
    st.plotly_chart(fig_dummy_timeline, use_container_width=True)
    st.success("Graphique bidon généré et tentative d'affichage.")
except Exception as e:
    st.error(f"Erreur lors de la création ou de l'affichage du graphique bidon : {e}")
    st.exception(e) # Affiche la trace complète de l'erreur

