import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- MODIFICATION : Vérification de la présence d'OpenFisca ---
try:
    from openfisca_core.simulation import Simulation
    from openfisca_france import FranceTaxBenefitSystem
    OPENFISCA_READY = True
except ImportError:
    OPENFISCA_READY = False

# ==============================================================================
# INITIALISATION DE L'ÉTAT DE LA SESSION (inchangé)
# ==============================================================================
if 'df_stocks' not in st.session_state:
    st.session_state.df_stocks = pd.DataFrame([
        {'Actif': 'Résidence Principale', 'Valeur Nette': 200000, 'Valeur Brute': 300000},
        {'Actif': 'Livret bancaire', 'Valeur Nette': 25000, 'Valeur Brute': 25000},
        {'Actif': 'Assurance Vie', 'Valeur Nette': 50000, 'Valeur Brute': 50000},
    ])
if 'df_revenus' not in st.session_state:
    st.session_state.df_revenus = pd.DataFrame({'Poste': ['Salaire Adulte 1', 'Salaire Adulte 2'], 'Montant Annuel': [45000, 35000]})
if 'df_depenses' not in st.session_state:
    st.session_state.df_depenses = pd.DataFrame({'Poste': ['Prêt immobilier', 'Dépenses courantes'], 'Montant Annuel': [15000, 20000]})
if 'df_adultes' not in st.session_state:
    st.session_state.df_adultes = pd.DataFrame([
        {'Prénom': 'Jean', 'Âge': 40, 'Année Départ Retraite': 2049},
        {'Prénom': 'Marie', 'Âge': 38, 'Année Départ Retraite': 2051}
    ])
if 'df_enfants' not in st.session_state:
    st.session_state.df_enfants = pd.DataFrame([
        {'Prénom': 'Léo', 'Âge': 12, 'Âge Début Études': 18, 'Durée Études (ans)': 5, 'Coût Annuel Études (€)': 8000},
    ])
if 'hyp_retraite' not in st.session_state:
    st.session_state.hyp_retraite = {'taux_remplacement': 60.0}

# ==============================================================================
# DÉFINITION DES PAGES DE L'APPLICATION (inchangées)
# ==============================================================================

def page_stocks():
    st.title("💰 Représentation du Patrimoine du Foyer (Stocks)")
    # (Code inchangé)
    edited_df = st.data_editor(st.session_state.df_stocks, num_rows="dynamic", use_container_width=True, column_config={"Valeur Nette": st.column_config.NumberColumn(format="%d €"), "Valeur Brute": st.column_config.NumberColumn(format="%d €")})
    st.session_state.df_stocks = edited_df
    def get_type_patrimoine(actif):
        return "Immobilier" if "immo" in actif.lower() or "résidence" in actif.lower() else "Financier"
    df = st.session_state.df_stocks
    df["Type de Patrimoine"] = df["Actif"].apply(get_type_patrimoine)
    total_valeur_nette = df["Valeur Nette"].sum()
    if total_valeur_nette > 0:
        fig = px.treemap(df, path=['Type de Patrimoine', 'Actif'], values='Valeur Nette', color='Type de Patrimoine', color_discrete_map={"Immobilier": "#1f77b4", "Financier": "#ff7f0e"}, title='Répartition du Patrimoine Net')
        fig.update_traces(textinfo='label+percent parent+value')
        st.plotly_chart(fig, use_container_width=True)

def page_flux():
    st.title("💸 Suivi des Flux Financiers du Foyer")
    # (Code inchangé)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenus Annuels")
        edited_revenus = st.data_editor(st.session_state.df_revenus, num_rows="dynamic", key="editor_revenus", use_container_width=True, column_config={"Montant Annuel": st.column_config.NumberColumn(format="%d €")})
        st.session_state.df_revenus = edited_revenus
    with col2:
        st.subheader("Dépenses Annuelles")
        edited_depenses = st.data_editor(st.session_state.df_depenses, num_rows="dynamic", key="editor_depenses", use_container_width=True, column_config={"Montant Annuel": st.column_config.NumberColumn(format="%d €")})
        st.session_state.df_depenses = edited_depenses
    total_revenus = st.session_state.df_revenus['Montant Annuel'].sum()
    total_depenses = st.session_state.df_depenses['Montant Annuel'].sum()
    reste_a_vivre_annuel = total_revenus - total_depenses
    st.subheader("Bilan Annuel")
    col1_met, col2_met, col3_met = st.columns(3)
    col1_met.metric("Total Revenus", f"{total_revenus:,.0f} €")
    col2_met.metric("Total Dépenses", f"{total_depenses:,.0f} €")
    col3_met.metric("Capacité d'Épargne", f"{reste_a_vivre_annuel:,.0f} €", delta_color="off" if reste_a_vivre_annuel == 0 else "normal")
    st.subheader("Répartition des Dépenses et de l'Épargne")
    treemap_data = st.session_state.df_depenses.copy()
    treemap_data['Montant Annuel'] = treemap_data['Montant Annuel'].abs()
    if reste_a_vivre_annuel > 0:
        new_row = pd.DataFrame([{'Poste': 'Capacité d\'Épargne', 'Montant Annuel': reste_a_vivre_annuel}])
        treemap_data = pd.concat([treemap_data, new_row], ignore_index=True)
    if not treemap_data.empty:
        fig_treemap = px.treemap(treemap_data, path=['Poste'], values='Montant Annuel', color='Poste', title="Répartition des Dépenses Annuelles et de l'Épargne")
        fig_treemap.update_traces(textinfo='label+value+percent root')
        st.plotly_chart(fig_treemap, use_container_width=True)

def page_famille():
    st.title("👨‍👩‍👧‍👦 Composition de la Famille et Événements de Vie")
    # (Code inchangé)
    st.subheader("Adultes")
    st.session_state.df_adultes = st.data_editor(st.session_state.df_adultes, num_rows="dynamic", key="editor_adultes", use_container_width=True)
    st.subheader("Enfants")
    st.session_state.df_enfants = st.data_editor(st.session_state.df_enfants, num_rows="dynamic", key="editor_enfants", use_container_width=True, column_config={"Coût Annuel Études (€)": st.column_config.NumberColumn(format="%d €")})
    st.subheader("Hypothèses pour la retraite")
    st.session_state.hyp_retraite['taux_remplacement'] = st.slider("Taux de remplacement du revenu à la retraite (%)", min_value=30.0, max_value=100.0, value=st.session_state.hyp_retraite['taux_remplacement'])

def page_projection():
    st.title("📈 Projection de l'Évolution des Flux")

    # --- MODIFICATION : Définition de la fonction de calcul OpenFisca ---
    @st.cache_data
    def calculer_impot_openfisca(annee, revenus_imposables, foyer_parts):
        """Calcule l'impôt en utilisant OpenFisca."""
        if not OPENFISCA_READY:
            # Fallback vers le calcul simplifié
            tranches = [
                (0, 11294, 0), (11295, 28797, 0.11), (28798, 82341, 0.30),
                (82342, 171330, 0.41), (171331, float('inf'), 0.45)
            ]
            if foyer_parts['nb_parts'] <= 0: return 0
            qf = revenus_imposables / foyer_parts['nb_parts']
            impot = 0
            for tr_min, tr_max, taux in tranches:
                if qf > tr_min:
                    impot += (min(qf, tr_max) - tr_min) * taux
            return impot * foyer_parts['nb_parts']

        # Construction de la situation pour OpenFisca
        tax_benefit_system = FranceTaxBenefitSystem()
        
        personnes = []
        ids_personnes = []

        # On répartit le revenu sur les adultes actifs
        revenu_par_adulte_actif = revenus_imposables / foyer_parts['adultes_actifs'] if foyer_parts['adultes_actifs'] > 0 else 0
        
        for i, adulte in enumerate(foyer_parts['adultes_details']):
            person_id = f"adulte_{i+1}"
            ids_personnes.append(person_id)
            personnes.append({
                'id': person_id,
                'date_de_naissance': pd.to_datetime(f"{adulte['annee_naissance']}-01-01"),
                'salaire_imposable': revenu_par_adulte_actif if not adulte['est_retraite'] else 0,
                'pensions_retraites_imposables': revenu_par_adulte_actif if adulte['est_retraite'] else 0
            })
        
        for i, enfant in enumerate(foyer_parts['enfants_details']):
             person_id = f"enfant_{i+1}"
             ids_personnes.append(person_id)
             personnes.append({'id': person_id, 'date_de_naissance': pd.to_datetime(f"{enfant['annee_naissance']}-01-01")})

        situation = {
            'personnes': personnes,
            'foyers_fiscaux': [{'id': 'foyer1', 'declarateur_principal': 'adulte_1', 'personnes': ids_personnes}],
            'menages': [{'id': 'menage1', 'personne_de_reference': 'adulte_1', 'personnes': ids_personnes}]
        }
        
        simulation = Simulation(tax_benefit_system, start_date=f"{annee}-01-01")
        resultat = simulation.run(situation)
        
        return float(resultat['impot_sur_le_revenu_net_a_payer'].sum())

    def generer_tableau_financier(duree, revenus_df, depenses_df, adultes_df, enfants_df, hyp_retraite):
        annee_actuelle = datetime.now().year
        annees_projection = range(annee_actuelle, annee_actuelle + duree)
        
        sim_revenus = revenus_df.copy()
        sim_depenses = depenses_df.copy()
        salaires_de_base = sim_revenus.copy()
        
        adultes_df_sim = adultes_df.copy()
        adultes_df_sim['Année Naissance'] = annee_actuelle - adultes_df_sim['Âge']
        
        enfants_df_sim = enfants_df.copy()
        if not enfants_df_sim.empty:
            enfants_df_sim['Année Naissance'] = annee_actuelle - enfants_df_sim['Âge']
            enfants_df_sim['Année Fin Études'] = enfants_df_sim['Année Naissance'] + enfants_df_sim['Âge Début Études'] + enfants_df_sim['Durée Études (ans)']

        data = []
        for annee in annees_projection:
            # GESTION DES ÉVÉNEMENTS
            nb_enfants_a_charge = 0
            depenses_etudes_annuelles = 0
            adultes_actifs_count = 0
            adultes_details_list = []
            enfants_details_list = []

            for idx, adulte in adultes_df_sim.iterrows():
                est_retraite = annee >= adulte['Année Départ Retraite']
                if not est_retraite:
                    adultes_actifs_count += 1
                adultes_details_list.append({'annee_naissance': adulte['Année Naissance'], 'est_retraite': est_retraite})
                if est_retraite and idx < len(sim_revenus):
                   salaire_avant = salaires_de_base.loc[idx, 'Montant Annuel']
                   sim_revenus.loc[idx, 'Montant Annuel'] = salaire_avant * (hyp_retraite['taux_remplacement'] / 100)

            if not enfants_df_sim.empty:
                for _, enfant in enfants_df_sim.iterrows():
                    age_enfant = annee - enfant['Année Naissance']
                    if enfant['Âge Début Études'] <= age_enfant < (enfant['Âge Début Études'] + enfant['Durée Études (ans)']):
                        depenses_etudes_annuelles += enfant['Coût Annuel Études (€)']
                    if annee < enfant['Année Fin Études']:
                        nb_enfants_a_charge += 1
                        enfants_details_list.append({'annee_naissance': enfant['Année Naissance']})

            # CALCULS ANNUELS
            revenus_courants = sim_revenus['Montant Annuel'].sum()
            depenses_courantes = sim_depenses['Montant Annuel'].sum() + depenses_etudes_annuelles
            
            nb_parts = len(adultes_df) + nb_enfants_a_charge * 0.5
            foyer_pour_impot = {
                'nb_parts': nb_parts,
                'adultes_actifs': adultes_actifs_count,
                'adultes_details': adultes_details_list,
                'enfants_details': enfants_details_list
            }
            # --- MODIFICATION : Appel à la fonction OpenFisca ---
            impot_annuel = calculer_impot_openfisca(annee, revenus_courants, foyer_pour_impot)
            
            capacite_epargne = revenus_courants - depenses_courantes - impot_annuel

            data.append({"Année": annee, "Nb Parts": nb_parts, "Revenu Annuel": revenus_courants, "Charges Fixes": depenses_courantes, "Impôt sur le Revenu": impot_annuel, "Capacité d'Épargne": capacite_epargne})

            # Évolution pour l'année suivante
            sim_depenses['Montant Annuel'] *= 1.02
            for idx, adulte in adultes_df_sim.iterrows():
                 if annee < adulte['Année Départ Retraite'] and idx < len(sim_revenus):
                    sim_revenus.loc[idx, 'Montant Annuel'] *= 1.015

        return pd.DataFrame(data)

    # --- Interface Utilisateur ---
    duree_simulation = st.slider("Durée de la simulation (années)", 1, 50, 25)

    if st.button("🚀 Lancer la Projection Détaillée", type="primary"):
        # ... (le reste de l'interface est inchangé)
        tableau_financier = generer_tableau_financier(duree_simulation, st.session_state.df_revenus, st.session_state.df_depenses, st.session_state.df_adultes, st.session_state.df_enfants, st.session_state.hyp_retraite)
        st.session_state.tableau_financier = tableau_financier
        
    if 'tableau_financier' in st.session_state:
        tableau_financier = st.session_state.tableau_financier
        st.dataframe(tableau_financier, use_container_width=True, hide_index=True)
        # (Le reste du code d'affichage est inchangé)
        st.subheader("Graphiques de la projection")
        st.subheader("Répartition du Revenu Annuel")
        df_plot = tableau_financier.copy()
        fig_stacked_flows = px.bar(df_plot, x="Année", y=["Charges Fixes", "Impôt sur le Revenu", "Capacité d'Épargne"], title="Répartition du Revenu Annuel", labels={"value": "Montant Annuel (€)", "variable": "Poste de Dépense"}, color_discrete_map={"Charges Fixes": "indianred", "Impôt sur le Revenu": "gold", "Capacité d'Épargne": "mediumseagreen"})
        fig_stacked_flows.add_trace(px.line(df_plot, x="Année", y="Revenu Annuel").data[0])
        fig_stacked_flows.data[-1].name = 'Revenu Annuel'
        fig_stacked_flows.data[-1].line.color = 'royalblue'
        st.plotly_chart(fig_stacked_flows, use_container_width=True)
        st.subheader("Évolution de la Capacité d'Épargne")
        fig_rav = px.line(tableau_financier, x="Année", y="Capacité d'Épargne", title="Évolution de la Capacité d'Épargne Annuelle (Reste à Vivre)")
        st.plotly_chart(fig_rav, use_container_width=True)

# ==============================================================================
# NAVIGATION PRINCIPALE DE L'APPLICATION
# ==============================================================================
st.sidebar.title("Développement Audit")
selection = st.sidebar.radio("Navigation", ["Patrimoine (Stocks)", "Budget (Flux)", "Famille & Événements", "Projection"])

# --- MODIFICATION : Avertissement si OpenFisca n'est pas disponible ---
if not OPENFISCA_READY:
    st.sidebar.warning("OpenFisca non détecté. Le calcul d'impôt sera simplifié. Pour un calcul précis, installez `openfisca-france`.")

if selection == "Patrimoine (Stocks)":
    page_stocks()
elif selection == "Budget (Flux)":
    page_flux()
elif selection == "Famille & Événements":
    page_famille()
elif selection == "Projection":
    page_projection()