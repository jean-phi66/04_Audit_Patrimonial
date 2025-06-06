import streamlit as st
import pandas as pd
from datetime import datetime

# Configuration des paramètres financiers
inflation_annuelle = 0.02  # Inflation annuelle de 2%
taux_credit_immobilier = 0.03  # Taux d'intérêt du prêt immobilier
duree_max_credit = 25  # Durée maximale du crédit immobilier en années
frais_de_notaire_pourcentage = 0.08 # Pourcentage des frais de notaire

# Définition des tranches d'imposition 2024 (à adapter)
tranches_imposition = [
    (0, 11294, 0),
    (11295, 28797, 0.11),
    (28798, 82341, 0.30),
    (82342, 171330, 0.41),
    (171331, float('inf'), 0.45)
]

# Définition des montants forfaitaires de taxe foncière (exemple)
montant_taxe_fonciere_paris = 1000  # Exemple pour Paris
montant_taxe_fonciere_province = 800  # Exemple pour la province

# Définition des coûts annuels d'études (exemple)
cout_etudes_lycee = 500  # Par enfant
cout_etudes_sup = 3000  # Par enfant

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

def calculer_taxe_fonciere(ville, est_proprietaire):
    """Calcule la taxe foncière en fonction de la ville et du statut de propriété."""
    if not est_proprietaire:
        return 0
    if ville.lower() == "paris":
        return montant_taxe_fonciere_paris
    else:
        return montant_taxe_fonciere_province  # Simplification : même montant pour toute la province

def calculer_cout_etudes(age_enfants, duree_etudes):
    """Calcule le coût total des études pour tous les enfants."""
    cout_total = 0
    for i, age in enumerate(age_enfants):
        if 15 <= age <= 18:  # Âge typique du lycée
            cout_total += cout_etudes_lycee
        elif age > 18:  # Âge typique des études supérieures
            # Utilisation de la durée des études spécifiée par l'utilisateur
            duree = duree_etudes[i] if i < len(duree_etudes) else 5  # Durée par défaut de 5 ans
            for annee in range(duree):
                cout_total += cout_etudes_sup
    return cout_total

def calculer_remboursement_pret(montant_pret, duree_pret, taux_interet):
    """Calcule la mensualité et le total remboursé d'un prêt immobilier à taux fixe."""
    if montant_pret == 0:
        return 0, 0
    taux_mensuel = taux_interet / 12
    nombre_mensualites = duree_pret * 12
    mensualite = (montant_pret * taux_mensuel) / (1 - (1 + taux_mensuel) ** -nombre_mensualites)
    total_rembourse = mensualite * nombre_mensualites
    return mensualite, total_rembourse

def determiner_activite(age):
    """Détermine l'activité d'une personne en fonction de son âge."""
    if age < 6:
        return "Ecolier"
    elif 6 <= age < 11:
        return "Collégien"
    elif 11 <= age < 18:
        return "Lycéen"
    elif 18 <= age < 25:
        return "Etudiant"
    elif 25 <= age < 65:
        return "Actif"
    else:
        return "Retraité"

def generer_tableau_financier(
    noms_adultes,
    ages_adultes,
    noms_enfants,
    age_enfants,
    revenus_annuels,
    annees_changement_revenus,
    montant_pret_immobilier,
    duree_pret_immobilier,
    annees_achat_immobilier,
    ville_residence,
    duree_etudes,
    annees_debut_etudes,
    colonne_a_afficher,
    duree_simulation):
    """Génère le tableau financier annuel sur la période de simulation."""

    # Initialisation des données
    nb_adultes = len(noms_adultes)
    nb_enfants = len(noms_enfants)
    nb_parts = nb_adultes + nb_enfants * 0.5  # 0.5 part par enfant

    # Calcul de la date de début de la simulation
    date_debut = datetime.now()
    annee_debut = date_debut.year
    # On simule sur la durée spécifiée
    nombre_annees = duree_simulation
    annees = range(annee_debut, annee_debut + nombre_annees)
    data = []
    cumul_impots = 0
    est_proprietaire = False

    # Gestion de l'inflation des revenus
    revenus_par_an = {annee_debut: revenus_annuels[0]}
    pt_changement = 0
    annee_changement =  annees_changement_revenus[pt_changement]
    for annee in range(annee_debut + 1, annee_debut + nombre_annees):
        if annee == annee_changement:
            pt_changement += 1
            revenus_par_an[annee] = revenus_annuels[pt_changement]
            if (pt_changement + 1 <= len(annees_changement_revenus)):
                annee_changement =  annees_changement_revenus[pt_changement]    
        else:
            revenus_par_an[annee] = revenus_par_an[annee - 1]
    #evenus_par_an = {annee_debut: revenus_annuels[0]}
    #pt_revenus = 1
    #for annee_changement in annees_changement_revenus:
    #    if annee_changement > annee_debut:
    #        revenus_par_an[annee_changement] = revenus_annuels[]
    ## Boucle d'inflation
    #annees_revenus = sorted(revenus_par_an.keys())
    #for i in range(len(annees_revenus) - 1):
    #    annee_courante = annees_revenus[i]
    #    annee_suivante = annees_revenus[i+1]
    #    for annee in range(annee_courante + 1, annee_suivante):
    #        revenus_par_an[annee] = revenus_par_an[annee_courante] * (1 + inflation_annuelle)**(annee - annee_courante)
    ##appliquer l'inflation pour les années après le dernier changement
    #derniere_annee_revenu = annees_revenus[-1]
    #for annee in range(derniere_annee_revenu + 1, annee_debut + nombre_annees):
    #    revenus_par_an[annee] = revenus_par_an[derniere_annee_revenu] * (1 + inflation_annuelle)**(annee - derniere_annee_revenu)
    
    # Calcul des mensualités du prêt
    mensualite_pret, total_rembourse = calculer_remboursement_pret(montant_pret_immobilier, duree_pret_immobilier, taux_credit_immobilier)
    annees_remboursement_pret = range(annees_achat_immobilier[0], annees_achat_immobilier[0] + duree_pret_immobilier if montant_pret_immobilier > 0 else 0)


    # Boucle principale pour chaque année de la simulation
    for annee in annees:
        # Récupération du revenu pour l'année en cours
        revenu_annuel = revenus_par_an.get(annee, revenus_par_an[annee_debut])

        # Détermination de la propriété
        if annee in annees_achat_immobilier:
            est_proprietaire = True
            annee_achat = annee
        #Remboursement du pret
        remboursement_annuel_pret = mensualite_pret * 12 if annee in annees_remboursement_pret else 0

        # Calcul de l'impôt sur le revenu
        impot_annuel = calculer_impot_revenu(revenu_annuel, nb_parts)
        cumul_impots += impot_annuel

        # Calcul de la taxe foncière
        taxe_fonciere = calculer_taxe_fonciere(ville_residence, est_proprietaire)

        # Calcul du coût des études
        cout_etudes = calculer_cout_etudes(age_enfants, duree_etudes)

        # Initialisation des listes pour stocker les âges et les activités
        ages_personnes = []
        activites_personnes = []
        # Calcul de l'age pour les adultes
        for i, age_adulte in enumerate(ages_adultes):
            age = annee - annee_debut + age_adulte
            ages_personnes.append(age)
            activites_personnes.append(determiner_activite(age))
        # Calcul de l'age des enfants
        for age_enfant in age_enfants:
            age = annee - annee_debut + age_enfant
            ages_personnes.append(age)
            activites_personnes.append(determiner_activite(age))

        # Ajout des données de l'année au tableau
        annee_data = {
            "Année": annee,
            "Revenu Annuel": revenu_annuel,
            "Remboursement Prêt Immobilier": remboursement_annuel_pret,
            "Impôt sur le Revenu": impot_annuel,
            "Taxe Foncière": taxe_fonciere,
            "Coût des Études": cout_etudes,
            "Reste à Vivre Annuel": 0, #reste_a_vivre_annuel,
            "Cumul Impôts": cumul_impots
        }
        # Ajout des âges et activités au dictionnaire
        for i, nom in enumerate(noms_adultes + noms_enfants):
            annee_data[f"Âge {nom}"] = ages_personnes[i]
            annee_data[f"Activité {nom}"] = activites_personnes[i]
        data.append(annee_data)

    # Création du DataFrame pandas
    df = pd.DataFrame(data)

    # Filtrage des colonnes à afficher
    colonnes_selectionnees = ["Année"]
    for nom in noms_adultes + noms_enfants:
        colonnes_selectionnees.extend([f"Âge {nom}", f"Activité {nom}"])
    colonnes_selectionnees.extend(colonne_a_afficher + ["Reste à Vivre Annuel", "Cumul Impôts"])
    df = df[colonnes_selectionnees]
    df['Année'] = df['Année'].astype(str)

    return df

#"""Fonction principale pour l'application Streamlit."""
st.title("Projection évolution des flux")

# Saisie des paramètres par l'utilisateur
duree_simulation = st.number_input("Durée de la simulation (années)", min_value=1, max_value=50, value=25)
st.subheader('Composition Famille')
col1, col2 = st.columns(2)
with col1:
    noms_adultes = st.text_input("Noms des adultes (séparés par des virgules)", "Dupont,Durand")
    noms_adultes = [nom.strip() for nom in noms_adultes.split(",")]
    noms_enfants = st.text_input("Noms des enfants (séparés par des virgules)", "Alice,Bob")
    noms_enfants = [nom.strip() for nom in noms_enfants.split(",")]
with col2:
    ages_adultes = st.text_input("Âges des adultes (séparés par des virgules)", "30,40")
    ages_adultes = [int(age) for age in ages_adultes.split(",")]
    age_enfants = st.text_input("Âge des enfants (séparés par des virgules)", "13,16")
    age_enfants = [int(age) for age in age_enfants.split(",")] if age_enfants else []
composition_familiale = ["Adulte"] * len(noms_adultes) + ["Enfant"] * len(noms_enfants)

#st.header('Revenus')
st.divider()
col3, col4 = st.columns(2)
with col3:
    st.subheader('Revenus Salariaux')
    annees_changement_revenus = st.multiselect("Années de changement des revenus salariaux", range(datetime.now().year, datetime.now().year + 25), default=[])
    revenus_salariaux = st.text_input("Revenus Salariaux du foyer (Euros séparés par des virgules)", "50000, 50000")
    revenus_salariaux = [float(revenus) for revenus in revenus_salariaux.split(",")] if revenus_salariaux else []
with col4:
    st.subheader('Autres revenus')
    annees_changement_revenus_autre = st.multiselect("Années de changement des revenus", range(datetime.now().year, datetime.now().year + 25), default=[])
    revenus_autres = st.text_input("Autres revenus du foyer (Euros séparés par des virgules)", "50000, 50000")
    revenus_autres = [float(revenus) for revenus in revenus_autres.split(",")] if revenus_autres else []

#revenus_annuels = st.number_input("Revenus Annuels du foyer (Euros)", min_value=0, value=50000)
st.divider()
col5, col6 = st.columns(2)
with col5:
    montant_pret_immobilier = st.number_input("Montant du Prêt Immobilier (Euros)", min_value=0, value=0)
    duree_pret_immobilier = st.number_input("Durée du Prêt Immobilier (années)", min_value=0, max_value=duree_max_credit, value=20)
    annees_achat_immobilier = st.multiselect("Années d'achat immobilier", range(datetime.now().year, datetime.now().year + 25), default=[datetime.now().year])
with col6:
    montant_taxe_fonciere = st.number_input("Montant taxe fonciere (Euros)", min_value=0, value=0)
ville_residence = st.selectbox("Ville de résidence", ["Paris", "Province"], index=1)

duree_etudes = st.text_input("Durée des études pour chaque enfant (séparées par des virgules, 0 pour pas d'études)", "0,0")
duree_etudes = [int(duree) for duree in duree_etudes.split(",")] if duree_etudes else []
annees_debut_etudes = st.multiselect("Années de début des études des enfants", range(datetime.now().year, datetime.now().year + 25), default=[])


# Sélection des colonnes à afficher
colonnes_disponibles = ["Revenu Annuel", "Remboursement Prêt Immobilier", "Impôt sur le Revenu", "Taxe Foncière", "Coût des Études"]
colonnes_a_afficher = st.multiselect("Colonnes à afficher dans le tableau", colonnes_disponibles, default=["Revenu Annuel", "Impôt sur le Revenu", "Coût des Études"])

# Génération et affichage du tableau
if st.button("Générer le Tableau Financier"):
    tableau_financier = generer_tableau_financier(
        noms_adultes,
        ages_adultes,
        noms_enfants,
        age_enfants,
        revenus_salariaux,
        annees_changement_revenus,
        montant_pret_immobilier,
        duree_pret_immobilier,
        annees_achat_immobilier,
        ville_residence,
        duree_etudes,
        annees_debut_etudes,
        colonnes_a_afficher,
        duree_simulation
    )
    st.dataframe(tableau_financier, use_container_width=True, hide_index=True)
