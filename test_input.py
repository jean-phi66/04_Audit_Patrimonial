import streamlit as st

# Titre de l'application
st.title("Calculateur d'Investissements")

# Liste des types d'investissement
types_investissement = ['PER', 'SCPI', 'Assurance-Vie', 'FIP', 'LMNP', 'Locatif']

# Sélection multiple des types d'investissement
types_investissement_choisis = st.multiselect("Choisissez les types d'investissement :", types_investissement)

# Dictionnaire des entrées pour chaque type d'investissement
entrees_investissement = {
    'PER': {
        'montant_investi': "Montant investi (€)",
        'rendement': "Rendement annuel (%)",
        'flux_annuel': "Versement annuel (€)",
    },
    'SCPI': {
        'montant_investi': "Montant investi (€)",
        'rendement': "Rendement annuel (%)",
        'flux_annuel': "Revenus locatifs annuels (€)",
    },
    'Assurance-Vie': {
        'montant_investi': "Montant investi (€)",
        'rendement': "Rendement annuel (%)",
        'flux_annuel': "Versement annuel (€)",
    },
    'FIP': {
        'montant_investi': "Montant investi (€)",
        'rendement': "Rendement annuel (%)",
        'flux_annuel': "Distribution annuelle (€)",
    },
    'LMNP': {
        'montant_investi': "Montant investi (€)",
        'rendement': "Rendement locatif (%)",
        'flux_annuel': "Revenus locatifs annuels (€)",
    },
    'Locatif': {
        'montant_investi': "Montant investi (€)",
        'rendement': "Rendement locatif (%)",
        'flux_annuel': "Loyer annuel (€)",
    },
}

# Affichage des entrées pour chaque type d'investissement choisi
investissements_data = {}
if types_investissement_choisis:
    for type_investissement in types_investissement_choisis:
        st.subheader(f"Entrez les informations pour l'investissement {type_investissement} :")
        montant_investi = st.number_input(entrees_investissement[type_investissement]['montant_investi'], min_value=0.0, format="%.2f", key=f"{type_investissement}_montant")
        rendement = st.number_input(entrees_investissement[type_investissement]['rendement'], min_value=0.0, format="%.2f", key=f"{type_investissement}_rendement")
        flux_annuel = st.number_input(entrees_investissement[type_investissement]['flux_annuel'], min_value=0.0, format="%.2f", key=f"{type_investissement}_flux")
        investissements_data[type_investissement] = {
            'montant_investi': montant_investi,
            'rendement': rendement,
            'flux_annuel': flux_annuel,
        }

    # Exemple de calcul pour chaque investissement (à adapter)
    if st.button("Calculer"):
        resultats = {}
        for type_investissement, data in investissements_data.items():
            montant_investi = data['montant_investi']
            rendement = data['rendement']
            flux_annuel = data['flux_annuel']
            resultat = montant_investi * (rendement / 100) + flux_annuel
            resultats[type_investissement] = resultat
            st.success(f"Le résultat estimé pour {type_investissement} est de : {resultat:.2f} €")

        # Affichage des résultats (vous pouvez personnaliser l'affichage)
        st.subheader("Résultats par investissement :")
        for type_investissement, resultat in resultats.items():
            st.write(f"{type_investissement} : {resultat:.2f} €")
else:
    st.write("Veuillez choisir au moins un type d'investissement.")
