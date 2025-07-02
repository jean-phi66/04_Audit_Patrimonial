# pages/4_📈_Projection.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime # Ajout de l'import datetime
from utils.calculs_projection import generer_projection_complete
def _setup_sidebar():
    """Configure la barre latérale et retourne les paramètres de simulation."""
    st.sidebar.title("Paramètres de Projection")
    duree_simulation = st.sidebar.slider("Durée de la simulation (années)", 1, 50, 25)

    with st.sidebar.expander("Hypothèses Économiques", expanded=True):
        inflation = st.slider(
            "Taux d'inflation annuel moyen (%)", 0.0, 5.0, 0.0, 0.1, format="%.1f",
            help="Utilisé pour revaloriser les charges, les revenus non-salariaux et les coûts des études."
        )
        revalo_salaire = st.slider(
            "Taux de revalorisation annuelle des salaires (%)", 0.0, 5.0, 0.0, 0.1, format="%.1f"
        )
        st.session_state.hyp_economiques['inflation'] = inflation
        st.session_state.hyp_economiques['revalo_salaire'] = revalo_salaire

    return duree_simulation

def _get_adult_names():
    """Récupère les noms des adultes et s'assure que leur âge est numérique."""
    if 'df_adultes' in st.session_state and not st.session_state.df_adultes.empty:
        if 'Âge' in st.session_state.df_adultes.columns:
            st.session_state.df_adultes['Âge'] = pd.to_numeric(st.session_state.df_adultes['Âge'], errors='coerce')
        return st.session_state.df_adultes['Prénom'].tolist()
    return []

def _configure_retraite_parameters(adult_names):
    """Affiche les widgets pour configurer les hypothèses de retraite."""
    st.subheader("Hypothèses de Retraite (Pensions Annuelles par Adulte)")
    if not adult_names:
        st.info("Veuillez ajouter des adultes (onglet 'Famille & Événements') pour définir leurs hypothèses.")
        return

    st.session_state.df_pension_hypotheses = st.session_state.df_pension_hypotheses[
        st.session_state.df_pension_hypotheses['Prénom Adulte'].isin(adult_names)
    ]

    updated_pensions_data = []
    indices_to_delete = []

    for adult_name in adult_names:
        st.markdown(f"##### Hypothèses pour {adult_name}")
        hypotheses_for_adult = st.session_state.df_pension_hypotheses[st.session_state.df_pension_hypotheses['Prénom Adulte'] == adult_name]
        
        if hypotheses_for_adult.empty:
            st.write("_Aucune hypothèse pour cet adulte._")

        for i, row in hypotheses_for_adult.iterrows():
            exp_title = f"Hypothèse (Départ à {int(row.get('Âge Départ Retraite', 0))} ans)" if pd.notna(row.get('Âge Départ Retraite')) else "Nouvelle Hypothèse"
            with st.expander(exp_title, expanded=not pd.notna(row.get('Âge Départ Retraite'))):
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                age = c1.number_input("Âge Départ Retraite", value=int(row.get('Âge Départ Retraite', 65)), min_value=50, max_value=80, step=1, key=f"p_age_{i}")
                montant = c2.number_input("Montant Pension Annuelle (€)", value=float(row.get('Montant Pension Annuelle (€)', 0.0)), min_value=0.0, step=1000.0, format="%.0f", key=f"p_montant_{i}")
                active = c3.checkbox("Active ?", value=bool(row.get('Active', False)), key=f"p_active_{i}")
                if c4.button("🗑️", key=f"p_del_{i}", use_container_width=True):
                    indices_to_delete.append(i)
                
                updated_pensions_data.append({'Prénom Adulte': adult_name, 'Âge Départ Retraite': age, 'Montant Pension Annuelle (€)': montant, 'Active': active})

        if st.button(f"➕ Ajouter une hypothèse pour {adult_name}", key=f"add_p_{adult_name}", use_container_width=True):
            new = pd.DataFrame([{'Prénom Adulte': adult_name, 'Âge Départ Retraite': 65, 'Montant Pension Annuelle (€)': 0.0, 'Active': False, 'Année Départ Retraite': pd.NA}])
            st.session_state.df_pension_hypotheses = pd.concat([st.session_state.df_pension_hypotheses, new], ignore_index=True)
            
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
