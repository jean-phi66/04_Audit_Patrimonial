# pages/4_📈_Projection.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # <-- LIGNE AJOUTÉE
from utils.calculs_projection import generer_projection_complete

st.title("📈 Projection de l'Évolution des Flux et du Patrimoine")
duree_simulation = st.slider("Durée de la simulation (années)", 1, 50, 25)

if st.button("🚀 Lancer la Projection Complète", type="primary", use_container_width=True):
    with st.spinner("Calcul de la projection en cours..."):
        tableau_financier, logs = generer_projection_complete(
            duree_simulation, 
            st.session_state.df_stocks, 
            st.session_state.df_revenus, 
            st.session_state.df_depenses, 
            st.session_state.df_prets, 
            st.session_state.df_adultes, 
            st.session_state.df_enfants, 
            st.session_state.hyp_retraite, 
            st.session_state.hyp_economiques,
            st.session_state.parent_isole, 
            st.session_state.df_ventes
        )
        st.session_state.tableau_financier = tableau_financier
        st.session_state.logs_evenements = logs

if 'tableau_financier' in st.session_state and st.session_state.tableau_financier is not None:
    dfp = st.session_state.tableau_financier
    if 'logs_evenements' in st.session_state and st.session_state.logs_evenements:
        st.subheader("Journal des Événements de la Simulation")
        for log in st.session_state.logs_evenements:
            st.markdown(f"- {log}")
    
    st.subheader("Tableau de Projection")
    st.dataframe(dfp.style.format(precision=0), use_container_width=True, hide_index=True)
    
    st.subheader("Analyse des Flux Annuels")
    df_plot_flux = dfp.copy()
    fig_stacked_flux = px.bar(df_plot_flux, x="Année", y=["Charges (hors prêts)", "Mensualités Prêts", "Impôt sur le Revenu", "Reste à Vivre"], title="Répartition du Revenu Annuel", labels={"value": "Montant Annuel (€)", "variable": "Poste"}, color_discrete_map={"Charges (hors prêts)": "indianred", "Mensualités Prêts": "orangered", "Impôt sur le Revenu": "gold", "Reste à Vivre": "mediumseagreen"})
    st.plotly_chart(fig_stacked_flux, use_container_width=True)
    
    st.subheader("Analyse du Patrimoine")
    
    # Graphique de la composition du patrimoine BRUT
    fig_pat_composition = px.area(
        dfp, 
        x='Année', 
        y=['Patrimoine Financier', 'Immobilier Jouissance', 'Immobilier Productif'],
        title="Composition et Évolution du Patrimoine Brut",
        labels={"value": "Valeur (€)", "variable": "Type d'Actif"},
        color_discrete_map={
            "Patrimoine Financier": "#ff7f0e",
            "Immobilier Jouissance": "#1f77b4",
            "Immobilier Productif": "#636EFA"
        }
    )
    st.plotly_chart(fig_pat_composition, use_container_width=True)

    # Graphique Actifs vs Passifs pour voir le NET
    df_plot_bilan = pd.DataFrame({'Année': dfp['Année'], 'Actifs': dfp['Actifs Totaux'], 'Passifs': -dfp['Passifs Totaux']})
    fig_bilan = px.bar(
        df_plot_bilan.melt(id_vars='Année', var_name='Type', value_name='Valeur'), 
        x='Année', y='Valeur', color='Type', 
        title="Évolution des Actifs et Passifs (Bilan)", 
        labels={'Valeur': 'Montant (€)'}, 
        color_discrete_map={'Actifs': 'mediumseagreen', 'Passifs': 'indianred'}
    )
    # Ajout d'une ligne pour le patrimoine net
    fig_bilan.add_trace(go.Scatter(x=dfp['Année'], y=dfp['Patrimoine Net'], mode='lines', name='Patrimoine Net', line=dict(color='royalblue', width=3)))
    st.plotly_chart(fig_bilan, use_container_width=True)