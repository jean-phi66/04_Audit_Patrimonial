# pages/1_💰_Patrimoine.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.calculs import generer_tableau_amortissement

st.title("💰 Patrimoine et Dettes")
st.write("Les valeurs sont mises à jour automatiquement après chaque modification.")

st.header("Actifs")
# MODIFICATION: Ajout des nouvelles options pour le type d'actif
types_actifs_options = ["Immobilier de jouissance", "Immobilier productif", "Financier"]
edited_stocks = st.data_editor(
    st.session_state.df_stocks, 
    num_rows="dynamic", 
    key="editor_stocks", 
    use_container_width=True, 
    column_config={
        "Actif": st.column_config.TextColumn("Actif", required=True),
        "Type": st.column_config.SelectboxColumn("Type d'Actif", options=types_actifs_options, required=True),
        "Valeur Brute": st.column_config.NumberColumn("Valeur Brute", format="%d €"),
        "Valeur Nette": st.column_config.NumberColumn("Valeur Nette", format="%d €", help="Calculé automatiquement.", disabled=True),
        "Rendement %": st.column_config.NumberColumn(format="%.2f %%"),
        "Prix Achat Initial": st.column_config.NumberColumn(format="%d €"),
        "Date Achat": st.column_config.DateColumn(format="DD/MM/YYYY")
    },
    column_order=["Actif", "Type", "Valeur Brute", "Valeur Nette", "Rendement %", "Prix Achat Initial", "Date Achat"]
)

st.header("Passifs (Prêts Immobiliers)")
# MODIFICATION: Filtrage pour ne lister que les actifs immobiliers
df_immobilier_only = edited_stocks[edited_stocks['Type'].str.contains('Immobilier', na=False)]
actifs_immobiliers_options = df_immobilier_only['Actif'].tolist()

if not actifs_immobiliers_options:
    st.info("Aucun actif de type 'Immobilier' n'a été saisi. Vous ne pouvez pas encore ajouter de prêt associé.")
    # On affiche l'éditeur de prêts mais on le désactive
    edited_prets = st.data_editor(st.session_state.df_prets, num_rows="dynamic", key="editor_prets_disabled", use_container_width=True, disabled=True)
else:
    edited_prets = st.data_editor(
        st.session_state.df_prets, 
        num_rows="dynamic", 
        key="editor_prets", 
        use_container_width=True, 
        column_config={
            "Actif Associé": st.column_config.SelectboxColumn("Actif Associé", options=actifs_immobiliers_options, required=True),
            "Montant Initial": st.column_config.NumberColumn(format="%d €"),
            "Taux Annuel %": st.column_config.NumberColumn(format="%.2f %%"),
            "Durée Initiale (ans)": st.column_config.NumberColumn(format="%d ans"),
            "Date Début": st.column_config.DateColumn("Date de Début", format="DD/MM/YYYY")
        }
    )
st.session_state.df_prets = edited_prets

# Logique de mise à jour automatique
crd_par_actif = {}
for _, pret in st.session_state.df_prets.iterrows():
    actif_associe = pret['Actif Associé']
    if actif_associe:
        echeancier = generer_tableau_amortissement(pret['Montant Initial'], pret['Taux Annuel %'], pret['Durée Initiale (ans)'], pd.to_datetime(pret['Date Début']))
        crd_actuel = pret['Montant Initial']
        if not echeancier.empty:
            echeances_passees = echeancier[echeancier.index < datetime.now().year]
            if not echeances_passees.empty:
                crd_actuel = echeances_passees.iloc[-1]['CRD']
            elif echeancier.index[0] > datetime.now().year:
                crd_actuel = pret['Montant Initial']
            else:
                lignes_annee_en_cours = echeancier[echeancier.index == datetime.now().year]
                if not lignes_annee_en_cours.empty:
                    crd_actuel = lignes_annee_en_cours.iloc[0]['CRD']
        crd_par_actif[actif_associe] = crd_par_actif.get(actif_associe, 0) + crd_actuel

for i, row in edited_stocks.iterrows():
    crd = crd_par_actif.get(row['Actif'], 0)
    edited_stocks.loc[i, 'Valeur Nette'] = row['Valeur Brute'] - crd

st.session_state.df_stocks = edited_stocks

st.divider()
st.header("Analyse Visuelle du Patrimoine Actuel")

df_graph = st.session_state.df_stocks.copy()
# MODIFICATION: On renomme la colonne 'Type' pour les graphiques
df_graph.rename(columns={"Type": "Type de Patrimoine"}, inplace=True)
total_valeur_nette = df_graph["Valeur Nette"].sum()

if total_valeur_nette > 0:
    repartition_type = df_graph.groupby("Type de Patrimoine")["Valeur Nette"].sum().reset_index()
    # MODIFICATION: Couleurs pour les 3 types
    couleurs_patrimoine = {"Immobilier de jouissance": "#1f77b4", "Immobilier productif": "#636EFA", "Financier": "#ff7f0e"}
    
    fig_treemap_detail = px.treemap(df_graph[df_graph['Valeur Nette'] > 0], 
                                    path=['Type de Patrimoine', 'Actif'], 
                                    values='Valeur Nette', 
                                    color='Type de Patrimoine', 
                                    color_discrete_map=couleurs_patrimoine, 
                                    title='Répartition Détaillée du Patrimoine Net')
    fig_treemap_detail.update_traces(textinfo='label+value')
    st.plotly_chart(fig_treemap_detail, use_container_width=True)

    fig_treemap_agrege = px.treemap(repartition_type[repartition_type['Valeur Nette'] > 0], 
                                    path=['Type de Patrimoine'], 
                                    values='Valeur Nette', 
                                    color='Type de Patrimoine',
                                    color_discrete_map=couleurs_patrimoine, 
                                    title='Répartition Globale du Patrimoine Net')
    fig_treemap_agrege.update_traces(textinfo='label+percent root+value')
    st.plotly_chart(fig_treemap_agrege, use_container_width=True)