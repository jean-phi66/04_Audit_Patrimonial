# pages/2_💸_Flux.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.calculs import calculer_mensualite_pret

st.title("💸 Suivi des Flux Financiers du Foyer")
st.subheader("Saisie des Dépenses Courantes Annuelles (hors prêts)")
st.session_state.df_depenses = st.data_editor(st.session_state.df_depenses, num_rows="dynamic", key="editor_depenses", use_container_width=True, column_config={"Montant Annuel": st.column_config.NumberColumn(format="%d €")})
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Saisie des Revenus Annuels")
    st.session_state.df_revenus = st.data_editor(st.session_state.df_revenus, num_rows="dynamic", key="editor_revenus", use_container_width=True, column_config={"Montant Annuel": st.column_config.NumberColumn(format="%d €")})
with col2:
    st.subheader("Récapitulatif Complet des Dépenses")
    total_mensualites_prets_actuelles = sum(calculer_mensualite_pret(p['Montant Initial'], p['Taux Annuel %'], p['Durée Initiale (ans)']) * 12 for _, p in st.session_state.df_prets.iterrows() if pd.to_datetime(p['Date Début']) < datetime.now())
    df_depenses_courantes = st.session_state.df_depenses.copy()
    df_depenses_affiches = pd.DataFrame()
    if total_mensualites_prets_actuelles > 0:
        df_pret_affiche = pd.DataFrame([{'Poste': 'Mensualités Prêts (calculé)', 'Montant Annuel': total_mensualites_prets_actuelles}])
        df_depenses_affiches = pd.concat([df_depenses_affiches, df_pret_affiche], ignore_index=True)
    df_depenses_affiches = pd.concat([df_depenses_affiches, df_depenses_courantes], ignore_index=True)
    st.dataframe(df_depenses_affiches.style.format({"Montant Annuel": "{:,.0f} €"}), use_container_width=True, hide_index=True)
st.divider()
total_revenus = st.session_state.df_revenus['Montant Annuel'].sum()
total_depenses_courantes = st.session_state.df_depenses['Montant Annuel'].sum()
total_depenses_globales = total_depenses_courantes + total_mensualites_prets_actuelles
reste_a_vivre_annuel = total_revenus - total_depenses_globales
st.subheader("Bilan Annuel Actuel")
col_met1, col_met2, col_met3 = st.columns(3)
col_met1.metric("Total Revenus", f"{total_revenus:,.0f} €")
col_met2.metric("Total Dépenses", f"{total_depenses_globales:,.0f} €", help=f"Dépenses courantes: {total_depenses_courantes:,.0f} € | Mensualités prêts: {total_mensualites_prets_actuelles:,.0f} €")
col_met3.metric("Reste à Vivre", f"{reste_a_vivre_annuel:,.0f} €")
st.subheader("Répartition Graphique des Dépenses et du Reste à Vivre")
treemap_data = df_depenses_affiches.copy()
treemap_data['Montant Annuel'] = treemap_data['Montant Annuel'].abs()
if reste_a_vivre_annuel > 0:
    treemap_data = pd.concat([treemap_data, pd.DataFrame([{'Poste': 'Reste à Vivre', 'Montant Annuel': reste_a_vivre_annuel}])], ignore_index=True)
if not treemap_data.empty:
    fig_treemap = px.treemap(treemap_data, path=['Poste'], values='Montant Annuel', color='Poste', title="Répartition des Dépenses Annuelles et du Reste à Vivre")
    fig_treemap.update_layout(margin=dict(t=30, l=10, r=10, b=10))
    fig_treemap.update_traces(textinfo='label+value+percent root')
    st.plotly_chart(fig_treemap, use_container_width=True)