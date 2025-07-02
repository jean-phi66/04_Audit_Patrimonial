# pages/4_📈_Projection.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime # Ajout de l'import datetime
from utils.calculs_projection import generer_projection_complete

# Initialisation de la clé de session_state si elle n'existe pas
if 'hyp_economiques' not in st.session_state:
    st.session_state.hyp_economiques = {}

# Configuration de la barre latérale pour cette page
st.sidebar.title("Paramètres de Projection")
duree_simulation = st.sidebar.slider("Durée de la simulation (années)", 1, 50, 25)

with st.sidebar.expander("Hypothèses Économiques", expanded=True):
    # Ajout du slider pour le taux d'inflation
    inflation = st.slider(
        "Taux d'inflation annuel moyen (%)",
        0.0, 5.0, 0.0, 0.1, format="%.1f", # Valeur par défaut changée à 0.0
        help="Utilisé pour revaloriser les charges, les revenus non-salariaux (loyers, etc.) et les coûts des études."
    )
    st.session_state.hyp_economiques['inflation'] = inflation

    # Ajout du slider pour le taux de revalorisation des salaires
    revalo_salaire = st.slider(
        "Taux de revalorisation annuelle des salaires (%)",
        0.0, 5.0, 0.0, 0.1, format="%.1f" # Défaut à 0.0%
    )
    st.session_state.hyp_economiques['revalo_salaire'] = revalo_salaire

st.title("📈 Projection de l'Évolution des Flux et du Patrimoine")

st.header("Paramètres Spécifiques à la Projection")

st.subheader("Hypothèses de Retraite (Pensions Annuelles par Adulte)")

adult_names = []
if 'df_adultes' in st.session_state and not st.session_state.df_adultes.empty:
    adult_names = st.session_state.df_adultes['Prénom'].tolist()

    # S'assurer que l'âge des adultes est numérique pour les calculs
    if 'Âge' in st.session_state.df_adultes.columns:
        st.session_state.df_adultes['Âge'] = pd.to_numeric(st.session_state.df_adultes['Âge'], errors='coerce')

# Assurer que df_pension_hypotheses existe et a les bonnes colonnes
required_pension_cols = ['Prénom Adulte', 'Âge Départ Retraite', 'Montant Pension Annuelle (€)', 'Active', 'Année Départ Retraite']
if 'df_pension_hypotheses' not in st.session_state or not isinstance(st.session_state.df_pension_hypotheses, pd.DataFrame) or not all(col in st.session_state.df_pension_hypotheses.columns for col in required_pension_cols):
    st.session_state.df_pension_hypotheses = pd.DataFrame(columns=required_pension_cols)
    # Initialiser les types pour la cohérence, similaire à state_manager.py
    st.session_state.df_pension_hypotheses['Prénom Adulte'] = st.session_state.df_pension_hypotheses['Prénom Adulte'].astype('object')
    st.session_state.df_pension_hypotheses['Âge Départ Retraite'] = pd.to_numeric(st.session_state.df_pension_hypotheses['Âge Départ Retraite'], errors='coerce').astype('Int64')
    st.session_state.df_pension_hypotheses['Montant Pension Annuelle (€)'] = pd.to_numeric(st.session_state.df_pension_hypotheses['Montant Pension Annuelle (€)'], errors='coerce').astype('float64')
    st.session_state.df_pension_hypotheses['Active'] = st.session_state.df_pension_hypotheses['Active'].astype('boolean')
    st.session_state.df_pension_hypotheses['Année Départ Retraite'] = pd.to_numeric(st.session_state.df_pension_hypotheses['Année Départ Retraite'], errors='coerce').astype('Int64')

if not adult_names:
    st.info("Veuillez d'abord ajouter des adultes (dans l'onglet 'Famille & Événements') pour définir leurs hypothèses de pension.")
else:
    # Nettoyer les hypothèses des adultes qui n'existent plus
    st.session_state.df_pension_hypotheses = st.session_state.df_pension_hypotheses[st.session_state.df_pension_hypotheses['Prénom Adulte'].isin(adult_names)]

    updated_pensions_data = []
    indices_to_delete_pensions = []
    df_pensions_copy = st.session_state.df_pension_hypotheses.copy()

    for adult_name in adult_names:
        st.markdown(f"##### Hypothèses de pension pour {adult_name}")
        
        hypotheses_for_adult = df_pensions_copy[df_pensions_copy['Prénom Adulte'] == adult_name]
        if hypotheses_for_adult.empty:
            st.write("_Aucune hypothèse pour cet adulte._")

        for i, row in hypotheses_for_adult.iterrows():
            expander_title = f"Hypothèse (Départ à {int(row.get('Âge Départ Retraite', 0))} ans)" if pd.notna(row.get('Âge Départ Retraite')) and row.get('Âge Départ Retraite') > 0 else "Nouvelle Hypothèse"
            with st.expander(expander_title, expanded=not (pd.notna(row.get('Âge Départ Retraite')) and row.get('Âge Départ Retraite') > 0)):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    age_depart = st.number_input("Âge Départ Retraite", value=int(row.get('Âge Départ Retraite', 65)), min_value=50, max_value=80, step=1, key=f"pension_age_{i}")
                with col2:
                    montant_pension = st.number_input("Montant Pension Annuelle (€)", value=float(row.get('Montant Pension Annuelle (€)', 0.0)), min_value=0.0, step=1000.0, format="%.0f", key=f"pension_montant_{i}")
                with col3:
                    is_active = st.checkbox("Active ?", value=bool(row.get('Active', False)), key=f"pension_active_{i}")
                with col4:
                    st.write("")
                    if st.button("🗑️ Supprimer", key=f"delete_pension_{i}", use_container_width=True):
                        indices_to_delete_pensions.append(i)
                
                updated_pensions_data.append({
                    'Prénom Adulte': adult_name,
                    'Âge Départ Retraite': age_depart,
                    'Montant Pension Annuelle (€)': montant_pension,
                    'Active': is_active
                })

        if st.button(f"➕ Ajouter une hypothèse pour {adult_name}", key=f"add_pension_{adult_name}", use_container_width=True):
            new_row = pd.DataFrame([{'Prénom Adulte': adult_name, 'Âge Départ Retraite': 65, 'Montant Pension Annuelle (€)': 0.0, 'Active': False, 'Année Départ Retraite': pd.NA}])
            st.session_state.df_pension_hypotheses = pd.concat([st.session_state.df_pension_hypotheses, new_row], ignore_index=True)
            st.rerun()

    if indices_to_delete_pensions:
        st.session_state.df_pension_hypotheses = st.session_state.df_pension_hypotheses.drop(indices_to_delete_pensions).reset_index(drop=True)
        st.rerun()

    final_pensions_df = pd.DataFrame(updated_pensions_data)

    if 'Année Départ Retraite' not in final_pensions_df.columns:
        final_pensions_df['Année Départ Retraite'] = pd.NA

    if not final_pensions_df.empty and not st.session_state.df_adultes.empty:
        current_year = datetime.now().year
        adult_birth_years = { adult['Prénom']: current_year - adult['Âge'] for _, adult in st.session_state.df_adultes.iterrows() if pd.notna(adult['Âge']) }
        for index, row in final_pensions_df.iterrows():
            adult_name_hyp = row['Prénom Adulte']
            age_depart_hyp = row['Âge Départ Retraite']
            if pd.notna(adult_name_hyp) and adult_name_hyp in adult_birth_years and pd.notna(age_depart_hyp):
                birth_year = adult_birth_years[adult_name_hyp]
                final_pensions_df.loc[index, 'Année Départ Retraite'] = int(birth_year + age_depart_hyp)
            else:
                final_pensions_df.loc[index, 'Année Départ Retraite'] = pd.NA
    st.session_state.df_pension_hypotheses = final_pensions_df

    if 'Active' in st.session_state.df_pension_hypotheses.columns:
        for adult_name_check in adult_names:
            active_count = st.session_state.df_pension_hypotheses[ (st.session_state.df_pension_hypotheses['Prénom Adulte'] == adult_name_check) & (st.session_state.df_pension_hypotheses['Active'] == True) ].shape[0]
            if active_count > 1:
                st.warning(f"Attention : {adult_name_check} a {active_count} hypothèses de retraite 'Actives'. La projection utilisera la première (âge de départ le plus bas).")

st.subheader("Événements Immobiliers (optionnel)")
st.write("Planifiez ici la revente d'un bien au cours de la projection.")
df_immobilier = st.session_state.df_stocks[st.session_state.df_stocks['Type'].str.contains('Immobilier', na=False)]
liste_biens_immobiliers = df_immobilier['Actif'].tolist() if not df_immobilier.empty else []

# Define required columns for df_ventes
required_ventes_cols = ['Bien à Vendre', 'Année de Vente']

# Ensure df_ventes exists and has the correct columns, even if empty
if 'df_ventes' not in st.session_state or not isinstance(st.session_state.df_ventes, pd.DataFrame) or not all(col in st.session_state.df_ventes.columns for col in required_ventes_cols):
    st.session_state.df_ventes = pd.DataFrame(columns=required_ventes_cols)
    st.session_state.df_ventes['Année de Vente'] = st.session_state.df_ventes['Année de Vente'].astype('Int64')
    st.session_state.df_ventes['Bien à Vendre'] = st.session_state.df_ventes['Bien à Vendre'].astype('object')

if not liste_biens_immobiliers and st.session_state.df_ventes.empty: # Only show info if no properties and no sales events
    st.info("Aucun bien de type 'Immobilier' n'a été saisi dans l'onglet 'Patrimoine & Dettes'.")
else:
    updated_ventes_data = []
    indices_to_delete_ventes = []
    df_ventes_copy = st.session_state.df_ventes.copy()

    for i, row in df_ventes_copy.iterrows():
        expander_title = f"Vente de '{row.get('Bien à Vendre')}'" if row.get('Bien à Vendre') else f"Nouvel Événement de Vente #{i+1}"
        with st.expander(expander_title, expanded=not row.get('Bien à Vendre')):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                try:
                    bien_index = liste_biens_immobiliers.index(row.get('Bien à Vendre')) if row.get('Bien à Vendre') in liste_biens_immobiliers else 0
                except (ValueError, TypeError):
                    bien_index = 0
                bien_a_vendre = st.selectbox("Bien à Vendre", options=liste_biens_immobiliers, index=bien_index, key=f"vente_bien_{i}")
            with col2:
                annee_vente = st.number_input("Année de Vente", value=int(row.get('Année de Vente', datetime.now().year)), min_value=datetime.now().year, step=1, key=f"vente_annee_{i}", format="%d")
            with col3:
                st.write("")
                if st.button("🗑️ Supprimer", key=f"delete_vente_{i}", use_container_width=True):
                    indices_to_delete_ventes.append(i)
            
            updated_ventes_data.append({'Bien à Vendre': bien_a_vendre, 'Année de Vente': annee_vente})

    if indices_to_delete_ventes:
        st.session_state.df_ventes = st.session_state.df_ventes.drop(indices_to_delete_ventes).reset_index(drop=True)
        st.rerun()

    if updated_ventes_data:
        st.session_state.df_ventes = pd.DataFrame(updated_ventes_data)
    else:
        # If no data, ensure the DataFrame still has the correct columns
        st.session_state.df_ventes = pd.DataFrame(columns=required_ventes_cols)

    if st.button("➕ Ajouter un événement de vente", key="add_vente", use_container_width=True):
        new_row = pd.DataFrame([{'Bien à Vendre': liste_biens_immobiliers[0], 'Année de Vente': datetime.now().year}])
        st.session_state.df_ventes = pd.concat([st.session_state.df_ventes, new_row], ignore_index=True)
        st.rerun()

st.divider()
lancer_projection = st.sidebar.button("🚀 Lancer la Projection Complète", type="primary", use_container_width=True)
if lancer_projection:
    with st.spinner("Calcul de la projection en cours..."):
        # --- Consolidate Revenues for Projection ---
        # Start with user-entered revenues
        df_revenus_for_projection = st.session_state.df_revenus.copy()

        # Calculate rental income from df_stocks
        if(False):
            total_loyers_annuels = 0
            if 'df_stocks' in st.session_state and not st.session_state.df_stocks.empty:
                df_immobilier_productif = st.session_state.df_stocks[st.session_state.df_stocks['Type'] == 'Immobilier productif'].copy()
                if 'Loyer Mensuel Brut (€)' in df_immobilier_productif.columns:
                    df_immobilier_productif['Loyer Mensuel Brut (€)'] = pd.to_numeric(df_immobilier_productif['Loyer Mensuel Brut (€)'], errors='coerce').fillna(0)
                    total_loyers_annuels = (df_immobilier_productif['Loyer Mensuel Brut (€)'] * 12).sum()
                
            if total_loyers_annuels > 0:
                # Check if 'Revenus Locatifs (calculé)' already exists to avoid duplicates
                if 'Revenus Locatifs (calculé)' in df_revenus_for_projection['Poste'].values:
                    df_revenus_for_projection.loc[df_revenus_for_projection['Poste'] == 'Revenus Locatifs (calculé)', 'Montant Annuel'] = total_loyers_annuels
                else:
                    new_loyer_row = pd.DataFrame([{'Poste': 'Revenus Locatifs (calculé)', 'Montant Annuel': total_loyers_annuels}])
                    df_revenus_for_projection = pd.concat([df_revenus_for_projection, new_loyer_row], ignore_index=True)
            else:
                # If no rental income, ensure the row is removed if it exists
                df_revenus_for_projection = df_revenus_for_projection[df_revenus_for_projection['Poste'] != 'Revenus Locatifs (calculé)']

        # S'assurer que les hypothèses d'inflation et de revalorisation des salaires sont à 0
        # pour cette projection, suite à la suppression des sliders.
        tableau_financier, logs = generer_projection_complete(
            duree_simulation,
            st.session_state.df_stocks,
            df_revenus_for_projection, # Pass the consolidated revenues
            st.session_state.df_depenses,
            st.session_state.df_prets,
            st.session_state.df_adultes,
            st.session_state.df_enfants,
            st.session_state.df_pension_hypotheses,
            st.session_state.hyp_economiques, # Utilisation des hypothèses du session_state
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
    # Nouveau graphique pour l'évolution des statuts
    st.subheader("Évolution des Statuts des Membres du Foyer")
    statuts_cols = [col for col in dfp.columns if col.endswith('_Statut')]

    # Définition de noms_membres ici pour qu'il soit disponible pour le graphique et le tableau
    noms_membres = []
    if 'df_adultes' in st.session_state and not st.session_state.df_adultes.empty:
        noms_membres.extend(st.session_state.df_adultes['Prénom'].tolist())
    if 'df_enfants' in st.session_state and not st.session_state.df_enfants.empty:
        noms_membres.extend(st.session_state.df_enfants['Prénom'].tolist())

    colonnes_statut_membres = [] # Sera utilisé plus tard pour le tableau des flux
    for nom in noms_membres:
        colonnes_statut_membres.append(f"{nom}_Statut")

    if statuts_cols:
        timeline_data = []
        ordre_statuts = ["Scolarisé", "Étudiant", "Actif", "Retraité"]
        # Définir des couleurs pour chaque statut pour la cohérence
        couleurs_statuts = {
            "Scolarisé": "skyblue",
            "Étudiant": "lightgreen",
            "Actif": "royalblue",
            "Retraité": "silver"
        }

        for col_name in statuts_cols:
            membre_nom = col_name.replace('_Statut', '')
            current_status = None
            start_year = None
            for index, row in dfp.iterrows():
                year = row['Année']
                status_annee = row[col_name]

                if status_annee != current_status:
                    if current_status is not None and start_year is not None:
                        # Ajouter la période précédente
                        timeline_data.append(dict(
                            Task=membre_nom,
                            Start=str(start_year) + '-01-01',
                            Finish=str(year) + '-01-01',
                            Resource=current_status,
                            Label=current_status
                        ))
                    current_status = status_annee
                    start_year = year

            # Ajouter la dernière période pour ce membre
            if current_status is not None and start_year is not None:
                timeline_data.append(dict(
                    Task=membre_nom,
                    Start=str(start_year) + '-01-01',
                    Finish=str(dfp['Année'].max() + 1) + '-01-01', # La période va jusqu'au début de l'année suivante
                    Resource=current_status,
                    Label=current_status
                ))

        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)

            # Ensure Task, Resource, and Label are explicitly strings
            if not df_timeline.empty:
                df_timeline['Task'] = df_timeline['Task'].astype(str).str.strip()
                df_timeline['Resource'] = df_timeline['Resource'].astype(str).str.strip()
                df_timeline['Label'] = df_timeline['Label'].astype(str).str.strip()
                # Convert Start and Finish to datetime objects for Plotly
                df_timeline['Start'] = pd.to_datetime(df_timeline['Start'])
                df_timeline['Finish'] = pd.to_datetime(df_timeline['Finish'])
                # Remplacer "Fin d'études" par "Actif"
                df_timeline['Resource'] = df_timeline['Resource'].replace("Fin d'études", "Actif")
                df_timeline['Label'] = df_timeline['Label'].replace("Fin d'études", "Actif")


            fig_statuts_evolution = px.timeline(
                df_timeline,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Resource",
                text="Label",
                title="Chronologie des Statuts par Membre du Foyer",
                labels={"Task": "Membre", "Resource": "Statut"},
                category_orders={"Resource": ordre_statuts}, # Ordonne les légendes et potentiellement les couleurs si non mappées
                color_discrete_map=couleurs_statuts
            )
            fig_statuts_evolution.update_yaxes(categoryorder="array", categoryarray=noms_membres) # Ordonner les membres sur l'axe Y
            fig_statuts_evolution.update_layout(xaxis_title="Année")
            st.plotly_chart(fig_statuts_evolution, use_container_width=True)
        else:
            st.info("Aucune donnée de période de statut n'a pu être générée pour la chronologie (timeline_data est vide).")
    st.subheader("Analyse des Flux Annuels")
    df_plot_flux = dfp.copy()
    # Pour avoir le Reste à Vivre en bas, il doit être le premier dans la liste y
    # et on s'assure qu'il est positif pour un empilement correct.
    # Si le Reste à Vivre peut être négatif, un graphique en cascade serait plus adapté,
    # mais pour un empilement simple, on le traite comme une composante positive.
    fig_stacked_flux = px.bar(
        df_plot_flux,
        x="Année",
        y=["Reste à Vivre", "Charges (hors prêts)", "Mensualités Prêts", "Impôt sur le Revenu"],
        title="Répartition du Revenu Annuel (depuis le Reste à Vivre)",
        labels={"value": "Montant Annuel (€)", "variable": "Poste"},
        color_discrete_map={
            "Reste à Vivre": "mediumseagreen",
            "Charges (hors prêts)": "lightcoral", # Ajustement couleur pour contraste
            "Mensualités Prêts": "sandybrown",  # Ajustement couleur pour contraste
            "Impôt sur le Revenu": "khaki" # Ajustement couleur pour contraste
        }
    )
    st.plotly_chart(fig_stacked_flux, use_container_width=True)

    # Graphique pour les réductions fiscales
    if 'Réduction Fiscale Annuelle' in dfp.columns and dfp['Réduction Fiscale Annuelle'].sum() > 0:
        fig_reduction = px.bar(
            dfp,
            x='Année',
            y='Réduction Fiscale Annuelle',
            title="Évolution des Réductions Fiscales Annuelles (Pinel, etc.)",
            labels={"Réduction Fiscale Annuelle": "Montant de la Réduction (€)"},
        )
        fig_reduction.update_traces(marker_color='teal')
        st.plotly_chart(fig_reduction, use_container_width=True)

    # Graphique pour le cumul de la fiscalité
    if 'Impôt sur le Revenu' in df_plot_flux.columns:
        df_plot_flux['Impôt Cumulé'] = df_plot_flux['Impôt sur le Revenu'].cumsum()
        fig_impot_cumule = px.area(
            df_plot_flux,
            x='Année',
            y='Impôt Cumulé',
            title="Évolution du Cumul de la Fiscalité Payée",
            labels={"Impôt Cumulé": "Total Impôts Payés (cumulé) (€)"},
            markers=True
        )
        fig_impot_cumule.update_traces(fillcolor='rgba(239, 83, 80, 0.3)', line_color='rgba(239, 83, 80, 1.0)')
        st.plotly_chart(fig_impot_cumule, use_container_width=True)



    st.subheader("Tableau des Flux Annuels")

    # Utiliser colonnes_statut_membres déjà défini plus haut
    colonnes_statut_membres_existantes = [col for col in colonnes_statut_membres if col in dfp.columns] # Ensure columns exist

    flux_columns_base = ["Revenu Annuel", "Salaires Annuels", "Pensions Annuelles", "Revenus Locatifs Annuels", "Autres Revenus Annuels", "Charges (hors prêts)", "Mensualités Prêts", "Impôt sur le Revenu", "Réduction Fiscale Annuelle", "Reste à Vivre"]
    flux_columns_final = ["Année"] + colonnes_statut_membres_existantes + flux_columns_base
    df_flux_table = dfp[[col for col in flux_columns_final if col in dfp.columns]] # S'assurer que toutes les colonnes existent
    st.dataframe(df_flux_table.style.format(precision=0, na_rep='-'), use_container_width=True, hide_index=True)

    st.subheader("Analyse du Patrimoine")

    net_patrimony_cols = ['Patrimoine Financier Net', 'Immobilier Jouissance Net', 'Immobilier Productif Net']

    # Ensure columns exist and are numeric
    for col in net_patrimony_cols:
        if col not in dfp.columns:
            # If a column is missing, add it with zeros to prevent px.area from failing
            dfp[col] = 0.0
            st.warning(f"Column '{col}' was missing in the projection data and has been added with zeros for plotting.")
        else:
            # Ensure it's numeric and fill NaNs with 0
            dfp[col] = pd.to_numeric(dfp[col], errors='coerce').fillna(0)

    # Graphique de la composition du patrimoine NET
    fig_pat_composition = px.area(
        dfp,
        x='Année',
        y=net_patrimony_cols, # Pass the list of column names
        title="Évolution de la Composition du Patrimoine Net",
        labels={"value": "Valeur (€)", "variable": "Type d'Actif"},
        color_discrete_map={
            "Patrimoine Financier Net": "#ff7f0e",
            "Immobilier Jouissance Net": "#1f77b4",
            "Immobilier Productif Net": "#636EFA"
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

    st.subheader("Tableau de l'Évolution du Patrimoine")
    patrimoine_columns = ["Année", "Patrimoine Net", "Actifs Totaux", "Passifs Totaux", "Patrimoine Financier", "Immobilier Jouissance", "Immobilier Productif"]
    df_patrimoine_table = dfp[patrimoine_columns]
    st.dataframe(df_patrimoine_table.style.format(precision=0, na_rep='-'), use_container_width=True, hide_index=True)
