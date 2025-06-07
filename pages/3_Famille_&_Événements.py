# pages/3_👨‍👩‍👧‍👦_Famille_&_Événements.py
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("👨‍👩‍👧‍👦 Famille & Événements")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Adultes")
    st.session_state.df_adultes = st.data_editor(st.session_state.df_adultes, num_rows="dynamic", key="editor_adultes", use_container_width=True)
    if len(st.session_state.df_adultes) == 1:
        st.session_state.parent_isole = st.checkbox("Parent isolé (coche la case T de la déclaration)", value=st.session_state.get('parent_isole', False))
    else:
        st.session_state.parent_isole = False
with col2:
    st.subheader("Enfants")
    st.session_state.df_enfants = st.data_editor(st.session_state.df_enfants, num_rows="dynamic", key="editor_enfants", use_container_width=True, column_config={"Coût Annuel Études (€)": st.column_config.NumberColumn(format="%d €")})
st.divider()
st.subheader("Hypothèses Générales de Projection")
col_hyp_1, col_hyp_2 = st.columns(2)
with col_hyp_1:
    st.write("**Hypothèses Économiques**")
    st.session_state.hyp_economiques['inflation'] = st.slider("Taux d'inflation annuel moyen (%)", 0.0, 5.0, st.session_state.hyp_economiques.get('inflation', 2.0), 0.1, help="Impacte les dépenses courantes.")
    st.session_state.hyp_economiques['revalo_salaire'] = st.slider("Taux de revalorisation des salaires (%)", 0.0, 5.0, st.session_state.hyp_economiques.get('revalo_salaire', 1.5), 0.1, help="Impacte les revenus salariaux avant la retraite.")
with col_hyp_2:
    st.write("**Hypothèses de Retraite**")
    st.session_state.hyp_retraite['taux_remplacement'] = st.slider("Taux de remplacement du revenu à la retraite (%)", 30.0, 100.0, st.session_state.hyp_retraite['taux_remplacement'])
st.divider()
st.subheader("Événements Immobiliers (optionnel)")
st.write("Planifiez ici la revente d'un bien au cours de la projection.")
df_immobilier = st.session_state.df_stocks[st.session_state.df_stocks['Type'].str.contains('Immobilier', na=False)]
liste_biens_immobiliers = df_immobilier['Actif'].tolist()
if not liste_biens_immobiliers:
    st.info("Aucun bien de type 'Immobilier' n'a été saisi dans l'onglet 'Patrimoine & Dettes'.")
else:
    st.session_state.df_ventes = st.data_editor(st.session_state.df_ventes, num_rows="dynamic", key="editor_ventes", use_container_width=True, column_config={'Année de Vente': st.column_config.NumberColumn(min_value=datetime.now().year, format="%d"),'Bien à Vendre': st.column_config.SelectboxColumn("Bien à Vendre", options=liste_biens_immobiliers, required=True)})