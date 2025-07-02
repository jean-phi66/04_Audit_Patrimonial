# pages/4_📈_Projection.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.calculs_projection import generer_projection_complete

# Configuration de la barre latérale pour cette page
st.sidebar.title("Paramètres de Projection")
duree_simulation = st.sidebar.slider("Durée de la simulation (années)", 1, 50, 25)
lancer_projection = st.sidebar.button("🚀 Lancer la Projection Complète", type="primary", use_container_width=True)

st.title("📈 Projection de l'Évolution des Flux et du Patrimoine")
if lancer_projection:
    with st.spinner("Calcul de la projection en cours..."):
        # S'assurer que les hypothèses d'inflation et de revalorisation des salaires sont à 0
        # pour cette projection, suite à la suppression des sliders.
        hyp_economiques_projection = st.session_state.hyp_economiques.copy()
        hyp_economiques_projection['inflation'] = 0.0
        hyp_economiques_projection['revalo_salaire'] = 0.0

        tableau_financier, logs = generer_projection_complete(
            duree_simulation,
            st.session_state.df_stocks,
            st.session_state.df_revenus,
            st.session_state.df_depenses,
            st.session_state.df_prets,
            st.session_state.df_adultes,
            st.session_state.df_enfants,
            st.session_state.df_pension_hypotheses,
            hyp_economiques_projection, # Utilisation des hypothèses modifiées
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
    colonnes_statut_membres_existantes = [col for col in colonnes_statut_membres if col in dfp.columns]

    flux_columns_base = ["Revenu Annuel", "Charges (hors prêts)", "Mensualités Prêts", "Impôt sur le Revenu", "Reste à Vivre"]
    flux_columns_final = ["Année"] + colonnes_statut_membres_existantes + flux_columns_base
    df_flux_table = dfp[[col for col in flux_columns_final if col in dfp.columns]] # S'assurer que toutes les colonnes existent
    st.dataframe(df_flux_table.style.format(precision=0, na_rep='-'), use_container_width=True, hide_index=True)

    st.subheader("Analyse du Patrimoine")

    # Graphique de la composition du patrimoine BRUT
    fig_pat_composition = px.area(
        dfp,
        x='Année',
        y=['Patrimoine Financier', 'Immobilier Jouissance', 'Immobilier Productif'],
        title="Évolution de la Composition du Patrimoine Brut",
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

    st.subheader("Tableau de l'Évolution du Patrimoine")
    patrimoine_columns = ["Année", "Patrimoine Net", "Actifs Totaux", "Passifs Totaux", "Patrimoine Financier", "Immobilier Jouissance", "Immobilier Productif"]
    df_patrimoine_table = dfp[patrimoine_columns]
    st.dataframe(df_patrimoine_table.style.format(precision=0, na_rep='-'), use_container_width=True, hide_index=True)
