import streamlit as st
import pandas as pd
import plotly.express as px

# Définir le DataFrame initial avec des exemples
liste_actifs_ref = ["Résidence Principale", "Résidence Secondaire", "Autres biens immobiliers",
              "Immo Locatif (meublé)", "Immo locatif (nu)",
              "SCPI",
              "Livret bancaire", "Autre epargne bancaire",
              "Assurance Vie", "Epargne Retraite",
              "Epargne Salariale",
              "FIP/FCPI"
              ]
data = {
    "Actif": liste_actifs_ref,
    "Valeur Brute": [300000, 10000,
                     0, 0,
                     0, 0, 
                     25000, 0,
                     0., 0.,
                     0.,
                     0.],
    "Valeur Nette": [10000, 10000.,
                     10000., 10000.,
                     10000., 10000., 
                     10000., 10000.,
                     10000., 10000.,
                     10000.,
                     10000.],
}

df = pd.DataFrame(data)

# Définir le type de patrimoine
def get_type_patrimoine(actif):
    if actif in ["Résidence Principale", "Résidence Secondaire", "SCPI", "Autres biens immobiliers", "Immo Locatif (meublé)", "Immo locatif (nu)"]:
        if actif in ["Résidence Principale", "Résidence Secondaire", "Autres biens immobiliers"]:
            return "Immobilier de jouissance"
        else:
            return "Immobilier productif"
    else:
        return "Financier"

df["Type de Patrimoine"] = df["Actif"].apply(get_type_patrimoine)

# Définir l'horizon d'investissement
def get_horizon_investissement(actif):
    if actif in ["Livret bancaire"]:
        return "Trésorerie"
    elif actif in ["Autre epargne bancaire"]:
        return 'Court Terme'
    elif actif in ["Résidence Principale", "Résidence Secondaire", "SCPI", "Autres biens immobiliers", "Immo Locatif (meublé)", "Immo locatif (nu)",
                   'Epargne retraite']:
        return "Long Terme"
    else:
        return "Moyen Terme"

df["Horizon d'Investissement"] = df["Actif"].apply(get_horizon_investissement)

# Titre de l'application
st.title("Représentation du Patrimoine du Foyer")

# Texte explicatif
st.write(
    "Ce tableau vous permet de saisir et de visualiser la composition de votre patrimoine."
    " Vous pouvez modifier les valeurs directement dans le tableau.  Les modifications sont prises"
    " en compte pour recalculer le graphique de répartition."
)

# Rendre le DataFrame éditable avec st.data_editor
edited_df = st.data_editor(df, num_rows="dynamic") # num_rows="dynamic" permet d'ajouter des lignes

# Calcul de la part de chaque actif dans la valeur nette totale
total_valeur_nette = edited_df["Valeur Nette"].sum()
edited_df["Part (%)"] = (edited_df["Valeur Nette"] / total_valeur_nette) * 100

# Calcul de la répartition par type de patrimoine
repartition_type = edited_df.groupby("Type de Patrimoine")["Valeur Nette"].sum().reset_index()
repartition_type["Part (%)"] = (repartition_type["Valeur Nette"] / total_valeur_nette) * 100

# Calcul de la répartition par horizon d'investissement
repartition_horizon = edited_df.groupby("Horizon d'Investissement")["Valeur Nette"].sum().reset_index()
repartition_horizon["Part (%)"] = (repartition_horizon["Valeur Nette"] / total_valeur_nette) * 100

# Définir les couleurs pour Immobilier et Financier
couleurs_patrimoine = {"Immobilier de jouissance": "#1f77b4", "Immobilier productif": "#636EFA","Financier": "#ff7f0e"}  # Bleu et Orange, cohérent avec Plotly par défaut
couleurs_horizon = {"Court Terme": "#2ca02c", "Moyen Terme": "#d62728", "Long Terme": "#9467bd"} #vert, rouge, violet

# Créer le graphique de répartition (treemap) avec Plotly
if total_valeur_nette > 0: # Vérifier que le patrimoine n'est pas vide
    fig = px.treemap(edited_df,
                    path=['Type de Patrimoine', 'Actif'],  # Utiliser le type de patrimoine dans le chemin
                    values='Valeur Nette',
                    color='Type de Patrimoine',  # Colorer par type de patrimoine
                    color_discrete_map=couleurs_patrimoine, # Appliquer les couleurs définies
                    hover_data=['Valeur Nette', 'Part (%)', 'Horizon d\'Investissement'], #ajouter horizon
                    title='Répartition du Patrimoine Net')
    fig.update_traces(textinfo='label+percent parent+value')
    fig.update_layout(width=700)  # Réduire la hauteur du graphique

    # Afficher le graphique
    st.plotly_chart(fig, use_container_width=False)

    # Créer un treemap montrant la répartition entre Immobilier et Financier
    fig_repartition_type = px.treemap(repartition_type,
                                    path=['Type de Patrimoine'],
                                    values='Valeur Nette',
                                    color='Type de Patrimoine',
                                    color_discrete_map=couleurs_patrimoine,
                                    hover_data=['Valeur Nette', 'Part (%)'],
                                    title='Répartition du Patrimoine entre Immobilier et Financier')
    fig_repartition_type.update_layout(height=300, width=700)  # Réduire la hauteur du graphique
    fig_repartition_type.update_traces(textinfo='label+percent parent+value')
    st.plotly_chart(fig_repartition_type, use_container_width=False)

    # Créer un barplot montrant la répartition par horizon d'investissement
    fig_repartition_horizon = px.bar(repartition_horizon,
                                    x="Horizon d'Investissement",
                                    y="Valeur Nette",
                                    color="Horizon d'Investissement",
                                    color_discrete_map=couleurs_horizon,
                                    title="Répartition du Patrimoine par Horizon d'Investissement")
    fig_repartition_horizon.update_layout(height=350, width=600)
    
    fig_repartition_horizon.update_xaxes(categoryorder='array', categoryarray= ['Trésorerie', 'Court Terme','Moyen Terme','Long Terme'])
    st.plotly_chart(fig_repartition_horizon, use_container_width=False)
    
    # Créer un pie chart de la répartition par actif
        # Définir les couleurs pour chaque type de patrimoine
    couleurs_actifs = {
        "Immobilier de jouissance": ['rgb(0, 0, 255)', 'rgb(0, 50, 255)', 'rgb(25, 100, 255)', 'rgb(112, 150, 255)', 'rgb(150, 200, 255)'], # Nuances de bleu
        'Financier' : ['rgb(255, 165, 0)', 'rgb(255, 183, 50)', 'rgb(255, 202, 100)', 'rgb(255, 221, 150)', 'rgb(255, 240, 200)', 'rgb(255, 240, 220)'],  # Nuances d'orange
        'Immobilier productif' : ['rgb(0, 255, 0)', 'rgb(125, 255, 125)', 'rgb(150, 255, 100)', 'rgb(150, 255, 150)', 'rgb(200, 255, 200)'],   # Nuances de vert  
    }
    map_color = {k:v for k, v in zip(liste_actifs_ref[0:3], couleurs_actifs['Immobilier de jouissance'][0:3])} | \
        {k:v for k, v in zip(liste_actifs_ref[3:6], couleurs_actifs['Immobilier productif'][0:3])} | \
        {k:v for k, v in zip(liste_actifs_ref[6:], couleurs_actifs['Financier'][0:])}
    # Créer le pie chart
    fig_pie_actif = px.pie(edited_df,
                            values='Valeur Nette',
                            names='Actif',
                            color='Actif',  # Utiliser la colonne Couleur
                            color_discrete_map= map_color,
                            category_orders={'Actif': liste_actifs_ref},
                            title='Répartition du Patrimoine par Actif')
    fig_pie_actif.update_traces(textposition='inside', textinfo='percent+label', sort=False)
    
    reference_data = {'Actif':['Immoblier de jouissance', 'Immobilier productif', 'Financier'],
                      'Valeur Nette': [103., 101., 102.]}
    fig_pie_ref = px.pie(pd.DataFrame(reference_data),
                         values='Valeur Nette',
                         names='Actif',
                         color='Actif',
                         color_discrete_map={'Immoblier de jouissance':'rgb(0, 0, 255)', 
                                             'Immobilier productif': 'rgb(0, 255, 0)', 
                                             'Financier': 'rgb(255, 165, 0)'}, 
                        title='Patrimoine idéal')
    fig_pie_ref.update_traces(textposition='inside', textinfo='label', sort=True)


    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_pie_actif, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pie_ref, use_container_width=True)

else:
    st.warning("Votre patrimoine est vide. Veuillez ajouter des actifs et leurs valeurs.")
    # Afficher un tableau vide avec les colonnes pour que l'utilisateur sache quoi entrer.
    empty_df = pd.DataFrame(columns=["Actif", "Valeur Brute", "Valeur Nette", "Type de Patrimoine", "Horizon d'Investissement"])
    st.dataframe(empty_df)
