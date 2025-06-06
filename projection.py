import streamlit as st

import pandas as pd
from datetime import datetime

import plotly.graph_objects as go

st.title("Projection évolution des flux")

# Saisie des paramètres par l'utilisateur
duree_simulation = st.number_input("Durée de la simulation (années)", min_value=1, max_value=50, value=25)
range_multiselect = range(datetime.now().year, datetime.now().year + duree_simulation)

st.subheader('Composition Famille')
col1, col2 = st.columns(2)
with col1:
    noms_adultes = st.text_input("Noms des adultes (séparés par des virgules)", "Jean,Laurence")
    noms_adultes = [nom.strip() for nom in noms_adultes.split(",")]
    noms_enfants = st.text_input("Noms des enfants (séparés par des virgules)", "Alice,Louis")
    noms_enfants = [nom.strip() for nom in noms_enfants.split(",")]
with col2:
    ages_adultes = st.text_input("Âges des adultes (séparés par des virgules)", "30,40")
    ages_adultes = [int(age) for age in ages_adultes.split(",")]
    ages_enfants = st.text_input("Âge des enfants (séparés par des virgules)", "13,16")
    ages_enfants = [int(age) for age in ages_enfants.split(",")] if ages_enfants else []

#st.header('Revenus')
st.divider()
col3, col4 = st.columns(2)
with col3:
    st.subheader('Revenus Salariaux')
    revenus_salariaux = st.text_input("Revenus Salariaux du foyer (Euros séparés par des virgules)", "50000, 50000")
    revenus_salariaux = [float(revenus) for revenus in revenus_salariaux.split(",")] if revenus_salariaux else []
    annees_changement_revenus = st.multiselect("Années de changement des revenus salariaux", range_multiselect, default=[])
with col4:
    st.subheader('Autres revenus')
    revenus_autres = st.text_input("Autres revenus du foyer (Euros séparés par des virgules)", "50000, 50000")
    revenus_autres = [float(revenus) for revenus in revenus_autres.split(",")] if revenus_autres else []
    annees_changement_revenus_autres = st.multiselect("Années de changement des revenus", range_multiselect, default=[])

#revenus_annuels = st.number_input("Revenus Annuels du foyer (Euros)", min_value=0, value=50000)
st.divider()
col5, col6 = st.columns(2)
with col5:
    mensualite_pret_immobilier = st.text_input("Mensualités Prêt Immobilier (Euros)", "500")
    mensualite_pret_immobilier = [float(mensualite) * 12 for mensualite in mensualite_pret_immobilier.split(",")] if mensualite_pret_immobilier else []
    annee_changement_pret = st.multiselect("Années de changement dmensualités", range_multiselect, default=[])
with col6:
    montant_taxe_fonciere = st.text_input("Montant taxe fonciere (Euros)","1200")
    montant_taxe_fonciere = [float(TF) for TF in montant_taxe_fonciere.split(",")] if montant_taxe_fonciere else []
    annee_changement_taxe_fonciere = st.multiselect("Années changement taxe foncière", range_multiselect, default=[])

st.divider()
st.subheader('Fiscalité')
st.selectbox('Situation particulière', ['Non','Parent isolé'])

def evolution_montants(montants, annee_changement, annees):
    annee_changement = [annees[0]] + annee_changement # ajout de la première année comme date de changement
    montants_par_an = {}
    pt_changement = 0
    revenu_actuel = montants[0]
    for annee in annees:
        if pt_changement <= len(annee_changement) - 1:
            if annee == annee_changement[pt_changement]:
                revenu_actuel = montants[pt_changement]
                pt_changement += 1
        montants_par_an[annee] = revenu_actuel
    return(montants_par_an)

def evolution_age(age_actuel, annee_actuelle, annees):
    age_evol = [age_actuel + annee - annee_actuelle for annee in annees]
    return(age_evol)

# Définition des tranches d'imposition 2024 (à adapter)
tranches_imposition = [
    (0, 11294, 0),
    (11295, 28797, 0.11),
    (28798, 82341, 0.30),
    (82342, 171330, 0.41),
    (171331, float('inf'), 0.45)
]

# Fonctions utilitaires
def calculer_impot_revenu(revenu_net_imposable, nb_parts):
    """Calcule l'impôt sur le revenu en utilisant le barème progressif."""
    qf = revenu_net_imposable / nb_parts
    impot = 0
    for tranche_min, tranche_max, taux in tranches_imposition:
        if qf > tranche_min:
            base_imposable = min(qf, tranche_max) - tranche_min
            impot += base_imposable * taux
    return impot * nb_parts

def generer_tableau_flux(
    duree_simulation,
    noms_adultes, ages_adultes,
    noms_enfants, age_enfants,
    revenus_salariaux, annees_changement_revenus,
    revenus_autres, annees_changement_revenus_autres,
    mensualite_pret_immobilier, annee_changement_pret,
    montant_taxe_fonciere, annee_changement_taxe_fonciere):
    
    # Calcul de la date de début de la simulation
    date_debut = datetime.now()
    annee_debut = date_debut.year
    
    # On simule sur la durée spécifiée
    nombre_annees = duree_simulation
    annees = range(annee_debut, annee_debut + nombre_annees)
    data = []
    
    # Age et activités
    # Initialisation des listes pour stocker les âges et les activités
    ages_personnes = []
    activites_personnes = []
    for annee in annees:
        # Calcul de l'age pour les adultes
        for i, age_adulte in enumerate(ages_adultes):
            age = annee - annee_debut + age_adulte
            ages_personnes.append(age)
            #activites_personnes.append(determiner_activite(age))
        # Calcul de l'age des enfants
        for age_enfant in age_enfants:
            age = annee - annee_debut + age_enfant
            ages_personnes.append(age)
            #activites_personnes.append(determiner_activite(age))

    
    # evolution des différents flux
    salaires_par_an = evolution_montants(revenus_salariaux, annees_changement_revenus, annees)
    revenus_autres_par_an = evolution_montants(revenus_autres, annees_changement_revenus_autres, annees)
    mensualite_par_an = evolution_montants(mensualite_pret_immobilier, annee_changement_pret, annees)
    taxe_fonciere_par_an = evolution_montants(montant_taxe_fonciere, annee_changement_taxe_fonciere, annees)
    
    data = {"Année": [an for an in annees],
            "Salaire": salaires_par_an.values(),
            "Autres revenus": revenus_autres_par_an.values(),
            "Pret immobilier": mensualite_par_an.values(),
            "Taxe foncière": taxe_fonciere_par_an.values()}
    for nom, age_actuel in zip(noms_adultes, ages_adultes):
        data[f"Age {nom}"] = [age_actuel + annee - annees[0] for annee in annees]
    for nom, age_actuel in zip(noms_enfants, ages_enfants):
        data[f"Age {nom}"] = [age_actuel + annee - annees[0] for annee in annees]
    data['Parts fiscales'] = [1 for an in annees]
    data['Impots sur le revenu'] = [calculer_impot_revenu(salaire * .9, 1) for salaire in salaires_par_an]

    # tableau référençant le type de colonnes
    type_colonne = {"Recettes": ['Salaire', 'Autres revenus'],
                    "Depenses": ['Pret immobilier', 'Taxe foncière', 'Impots sur le revenu']}
    
    df = pd.DataFrame.from_dict(data)
    
    return((df, type_colonne))
    


if st.button("Générer le Tableau Financier"):
    tableau_financier, type_colonne = generer_tableau_flux(
        duree_simulation,
        noms_adultes, ages_adultes,
        noms_enfants, ages_enfants,
        revenus_salariaux, annees_changement_revenus,
        revenus_autres, annees_changement_revenus_autres,
        mensualite_pret_immobilier, annee_changement_pret,
        montant_taxe_fonciere, annee_changement_taxe_fonciere
    )
    #st.text(tableau_financier)
    tableau_financier['Reste à vivre'] = tableau_financier[type_colonne['Recettes']].sum(axis=1) - tableau_financier[type_colonne['Depenses']].sum(axis=1)
    st.dataframe(tableau_financier, use_container_width=True, hide_index=True)
    st.dataframe(type_colonne)
    
    
    def generer_graphique_financier(df, colonnes_a_afficher):
        """Génère un graphique en barres empilées montrant l'évolution des flux financiers."""

        # Préparation des données pour Plotly
        df_plot = df[["Année"] + colonnes_a_afficher].melt(id_vars="Année", var_name="Flux", value_name="Montant")

        # Création du graphique
        fig = go.Figure()
        for flux in df_plot['Flux'].unique():
            df_flux = df_plot[df_plot['Flux'] == flux]
            fig.add_trace(go.Bar(
                x=df_flux['Année'],
                y=df_flux['Montant'],
                name=flux,
                #marker_color=couleurs.get(flux, '#1f77b4') # Vous pouvez définir un dict de couleurs
            ))

        fig.update_layout(
            title='Évolution Annuelle des Flux Financiers',
            xaxis_title='Année',
            yaxis_title='Montant (Euros)',
            barmode='stack',
            hovermode='x unified' # Ajout pour avoir des tooltips combinés
        )
        return fig
    
    graphique_financier = generer_graphique_financier(tableau_financier, ['Reste à vivre'] + type_colonne['Depenses'])
    st.plotly_chart(graphique_financier, use_container_width=True)
    st.text(calculer_impot_revenu(80000 * .9, 1))