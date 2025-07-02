# pages/2_💸_Flux.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from utils.calculs import calculer_mensualite_pret

st.title("💸 Suivi des Flux Financiers du Foyer")

col_depenses_input, col_revenus_input = st.columns(2)

with col_depenses_input:
    st.subheader("Saisie des Dépenses Annuelles (hors prêts)")

    # --- NOUVELLE LOGIQUE DE WIDGETS POUR LES DÉPENSES ---
    updated_depenses_data = []
    indices_to_delete_depenses = []
    df_depenses_copy = st.session_state.df_depenses.copy()

    for i, row in df_depenses_copy.iterrows():
        expander_title = row.get('Poste') if row.get('Poste') else f"Nouvelle Dépense #{i+1}"
        with st.expander(expander_title, expanded=not row.get('Poste')):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                poste = st.text_input("Poste de dépense", value=row.get('Poste', ''), key=f"depense_poste_{i}")
            with col2:
                montant = st.number_input("Montant Annuel (€)", value=float(row.get('Montant Annuel', 0.0)), min_value=0.0, step=100.0, key=f"depense_montant_{i}", format="%.0f")
            with col3:
                st.write("") # Espace pour aligner le bouton
                st.write("")
                if st.button("🗑️ Supprimer", key=f"delete_depense_{i}", use_container_width=True):
                    indices_to_delete_depenses.append(i)
            
            updated_depenses_data.append({'Poste': poste, 'Montant Annuel': montant})

    if indices_to_delete_depenses:
        st.session_state.df_depenses = st.session_state.df_depenses.drop(indices_to_delete_depenses).reset_index(drop=True)
        st.rerun()

    st.session_state.df_depenses = pd.DataFrame(updated_depenses_data)

    if st.button("➕ Ajouter une Dépense", key="add_depense", use_container_width=True):
        new_row = pd.DataFrame([{'Poste': '', 'Montant Annuel': 0.0}])
        st.session_state.df_depenses = pd.concat([st.session_state.df_depenses, new_row], ignore_index=True)
        st.rerun()

with col_revenus_input:
    st.subheader("Saisie des Revenus Annuels")
    # --- NOUVELLE LOGIQUE DE WIDGETS POUR LES REVENUS ---
    updated_revenus_data = []
    indices_to_delete_revenus = []
    df_revenus_copy = st.session_state.df_revenus.copy()

    for i, row in df_revenus_copy.iterrows():
        expander_title = row.get('Poste') if row.get('Poste') else f"Nouveau Revenu #{i+1}"
        with st.expander(expander_title, expanded=not row.get('Poste')):
            r_col1, r_col2, r_col3 = st.columns([3, 2, 1])
            with r_col1:
                poste = st.text_input("Poste de revenu", value=row.get('Poste', ''), key=f"revenu_poste_{i}")
            with r_col2:
                montant = st.number_input("Montant Annuel (€)", value=float(row.get('Montant Annuel', 0.0)), min_value=0.0, step=100.0, key=f"revenu_montant_{i}", format="%.0f")
            with r_col3:
                st.write("") # Espace pour aligner le bouton
                st.write("")
                if st.button("🗑️ Supprimer", key=f"delete_revenu_{i}", use_container_width=True):
                    indices_to_delete_revenus.append(i)
            
            updated_revenus_data.append({'Poste': poste, 'Montant Annuel': montant})

    if indices_to_delete_revenus:
        st.session_state.df_revenus = st.session_state.df_revenus.drop(indices_to_delete_revenus).reset_index(drop=True)
        st.rerun()

    st.session_state.df_revenus = pd.DataFrame(updated_revenus_data)

    if st.button("➕ Ajouter un Revenu", key="add_revenu", use_container_width=True):
        new_row = pd.DataFrame([{'Poste': '', 'Montant Annuel': 0.0}])
        st.session_state.df_revenus = pd.concat([st.session_state.df_revenus, new_row], ignore_index=True)
        st.rerun()

st.divider()

# --- Calculs préparatoires pour les récapitulatifs ---

# Dépenses
df_prets_pour_calcul = st.session_state.df_prets.copy()
if 'Assurance Emprunteur %' not in df_prets_pour_calcul.columns:
    df_prets_pour_calcul['Assurance Emprunteur %'] = 0

total_mensualites_prets_actuelles = sum(
    calculer_mensualite_pret(p['Montant Initial'], p['Taux Annuel %'], p['Durée Initiale (ans)'], p.get('Assurance Emprunteur %', 0)) * 12 
    for _, p in df_prets_pour_calcul.iterrows() 
    if pd.to_datetime(p['Date Début'], errors='coerce') < datetime.now() and pd.notna(p['Montant Initial']) and p['Montant Initial'] > 0
)
df_depenses_courantes = st.session_state.df_depenses.copy()
total_charges_annuelles_immo = 0
total_taxe_fonciere_annuelle_immo = 0
df_depenses_affiches = pd.DataFrame()
if total_mensualites_prets_actuelles > 0:
    df_pret_affiche = pd.DataFrame([{'Poste': 'Mensualités Prêts (calculé)', 'Montant Annuel': total_mensualites_prets_actuelles}])
    df_depenses_affiches = pd.concat([df_depenses_affiches, df_pret_affiche], ignore_index=True)
if 'df_stocks' in st.session_state and not st.session_state.df_stocks.empty:
    df_immobilier_charges = st.session_state.df_stocks[
        (st.session_state.df_stocks['Type'] == 'Immobilier de jouissance') |
        (st.session_state.df_stocks['Type'] == 'Immobilier productif')
    ].copy()
    if 'Charges Annuelles (€)' in df_immobilier_charges.columns:
        total_charges_annuelles_immo = pd.to_numeric(df_immobilier_charges['Charges Annuelles (€)'], errors='coerce').fillna(0).sum()
    if 'Taxe Foncière Annuelle (€)' in df_immobilier_charges.columns:
        total_taxe_fonciere_annuelle_immo = pd.to_numeric(df_immobilier_charges['Taxe Foncière Annuelle (€)'], errors='coerce').fillna(0).sum()
    if total_charges_annuelles_immo > 0:
        df_depenses_affiches = pd.concat([df_depenses_affiches, pd.DataFrame([{'Poste': 'Charges Immobilières (calculé)', 'Montant Annuel': total_charges_annuelles_immo}])], ignore_index=True)
    if total_taxe_fonciere_annuelle_immo > 0:
        df_depenses_affiches = pd.concat([df_depenses_affiches, pd.DataFrame([{'Poste': 'Taxe Foncière (calculé)', 'Montant Annuel': total_taxe_fonciere_annuelle_immo}])], ignore_index=True)
df_depenses_affiches = pd.concat([df_depenses_affiches, df_depenses_courantes], ignore_index=True)

# Revenus
df_revenus_courants = st.session_state.df_revenus.copy()
df_revenus_affiches = pd.DataFrame()
total_loyers_annuels = 0
if 'df_stocks' in st.session_state and not st.session_state.df_stocks.empty:
    df_immobilier_productif = st.session_state.df_stocks[st.session_state.df_stocks['Type'] == 'Immobilier productif'].copy()
    if 'Loyer Mensuel Brut (€)' in df_immobilier_productif.columns:
        df_immobilier_productif['Loyer Mensuel Brut (€)'] = pd.to_numeric(df_immobilier_productif['Loyer Mensuel Brut (€)'], errors='coerce').fillna(0)
        total_loyers_annuels = (df_immobilier_productif['Loyer Mensuel Brut (€)'] * 12).sum()
    if total_loyers_annuels > 0:
        df_loyers_affiche = pd.DataFrame([{'Poste': 'Revenus Locatifs (calculé)', 'Montant Annuel': total_loyers_annuels}])
        df_revenus_affiches = pd.concat([df_revenus_affiches, df_loyers_affiche], ignore_index=True)
df_revenus_affiches = pd.concat([df_revenus_affiches, df_revenus_courants], ignore_index=True)

st.divider()

total_revenus = df_revenus_affiches['Montant Annuel'].sum()
total_depenses_courantes_saisies = st.session_state.df_depenses['Montant Annuel'].sum() # Renommé pour clarté
total_depenses_globales = total_depenses_courantes_saisies + total_mensualites_prets_actuelles + total_charges_annuelles_immo + total_taxe_fonciere_annuelle_immo

reste_a_vivre_annuel = total_revenus - total_depenses_globales


with st.expander("Bilan Annuel et Répartition", expanded=True):
    st.subheader("Bilan Annuel Actuel")
    col_met1, col_met2, col_met3 = st.columns(3)
    col_met1.metric("Total Revenus", f"{total_revenus:,.0f} €")
    col_met2.metric("Total Dépenses", f"{total_depenses_globales:,.0f} €", help=f"Dépenses saisies: {total_depenses_courantes_saisies:,.0f} € | Prêts: {total_mensualites_prets_actuelles:,.0f} € | Charges Immo: {total_charges_annuelles_immo:,.0f} € | Taxe Foncière: {total_taxe_fonciere_annuelle_immo:,.0f} €")
    col_met3.metric("Reste à Vivre Annuel", f"{reste_a_vivre_annuel:,.0f} €")

    # Déplacé ici pour être dans le même expander
    col_recap_dep_annuel, col_recap_rev_annuel = st.columns(2)
    with col_recap_dep_annuel:
        st.subheader("Récapitulatif Complet des Dépenses")
        st.dataframe(df_depenses_affiches.style.format({"Montant Annuel": "{:,.0f} €"}), use_container_width=True, hide_index=True)
    with col_recap_rev_annuel:
        st.subheader("Récapitulatif Complet des Revenus")
        st.dataframe(df_revenus_affiches.style.format({"Montant Annuel": "{:,.0f} €"}), use_container_width=True, hide_index=True)

    st.subheader("Répartition Graphique des Dépenses et du Reste à Vivre (Annuel)")
    treemap_data = df_depenses_affiches.copy()
    treemap_data['Montant Annuel'] = treemap_data['Montant Annuel'].abs()
    if reste_a_vivre_annuel > 0:
        treemap_data = pd.concat([treemap_data, pd.DataFrame([{'Poste': 'Reste à Vivre', 'Montant Annuel': reste_a_vivre_annuel}])], ignore_index=True)
    if not treemap_data.empty:
        fig_treemap = px.treemap(treemap_data, path=['Poste'], values='Montant Annuel', color='Poste', title="Répartition des Dépenses Annuelles et du Reste à Vivre")
        fig_treemap.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        fig_treemap.update_traces(texttemplate='%{label}<br>%{value:,.0f} €<br>%{percentRoot:.0%}')
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher pour la répartition annuelle.")

with st.expander("Bilan Mensuel et Répartition", expanded=False):
    col_recap_dep_mensuel, col_recap_rev_mensuel = st.columns(2)
    with col_recap_dep_mensuel:
        st.subheader("Récapitulatif Complet des Dépenses (Mensuel)")
        df_depenses_affiches_mensuel = df_depenses_affiches.copy()
        df_depenses_affiches_mensuel['Montant Annuel'] = np.ceil(df_depenses_affiches_mensuel['Montant Annuel'] / 12).astype(int)
        st.dataframe(df_depenses_affiches_mensuel.style.format({"Montant Annuel": "{:,.0f} €"}), use_container_width=True, hide_index=True)

    with col_recap_rev_mensuel:
        st.subheader("Récapitulatif Complet des Revenus (Mensuel)")
        df_revenus_affiches_mensuel = df_revenus_affiches.copy()
        df_revenus_affiches_mensuel['Montant Annuel'] = np.ceil(df_revenus_affiches_mensuel['Montant Annuel'] / 12).astype(int)
        st.dataframe(df_revenus_affiches_mensuel.style.format({"Montant Annuel": "{:,.0f} €"}), use_container_width=True, hide_index=True)

    st.subheader("Bilan Mensuel (estimé)")
    total_revenus_mensuel = np.ceil(total_revenus / 12)
    total_depenses_globales_mensuel = np.ceil(total_depenses_globales / 12)
    reste_a_vivre_mensuel = np.ceil(reste_a_vivre_annuel / 12)

    col_met_m1, col_met_m2, col_met_m3 = st.columns(3)
    col_met_m1.metric("Total Revenus Mensuels", f"{total_revenus_mensuel:,.0f} €")
    col_met_m2.metric("Total Dépenses Mensuelles", f"{total_depenses_globales_mensuel:,.0f} €")
    col_met_m3.metric("Reste à Vivre Mensuel", f"{reste_a_vivre_mensuel:,.0f} €")

    st.subheader("Répartition Graphique Mensualisée")
    if not treemap_data.empty: # treemap_data est déjà calculé pour l'annuel
        treemap_data_mensuel = treemap_data.copy()
        treemap_data_mensuel['Montant Mensuel'] = np.ceil(treemap_data_mensuel['Montant Annuel'] / 12).astype(int)

        fig_treemap_mensuel = px.treemap(
            treemap_data_mensuel,
            path=['Poste'],
            values='Montant Mensuel',
            color='Poste',
            title="Répartition des Dépenses Mensuelles et du Reste à Vivre"
        )
        fig_treemap_mensuel.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        fig_treemap_mensuel.update_traces(texttemplate='%{label}<br>%{value:,.0f} € / mois<br>%{percentRoot:.0%}')
        st.plotly_chart(fig_treemap_mensuel, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher pour la répartition mensualisée.")