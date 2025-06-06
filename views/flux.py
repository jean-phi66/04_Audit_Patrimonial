import streamlit as st
import pandas as pd
import plotly.express as px

# Titre de l'application
st.title("Suivi des Flux Financiers du Foyer")

# Créer des DataFrames avec des montants exemples
revenus_data = {
    'Poste': ['Salaire', 'Revenus locatifs'],
    'Montant Annuel': [50000, 12000]
}
depenses_data = {
    'Poste': ['Prêt immobilier', 'Impots', 'Taxe foncière', 'Logement'],
    'Montant Annuel': [15000, 6000, 3000, 350*12]
}

df_revenus = pd.DataFrame(revenus_data)
df_depenses = pd.DataFrame(depenses_data)

# Formatter les montants en euros
def formatter_euro(montant):
    return f"{montant:,.0f} €"

# Créer des tableaux éditables côte à côte
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenus Annuels")
    df_revenus['Montant Annuel'] = df_revenus['Montant Annuel'].apply(formatter_euro)
    df_revenus = st.data_editor(df_revenus, num_rows=5, key="revenus", hide_index=True)
    total_revenus_col1 = sum(pd.to_numeric(df_revenus['Montant Annuel'].str.replace('€', '').str.replace(',', ''))) #calcul du total
    st.markdown(f"**Total:** {total_revenus_col1:,.0f} €") #affichage du total

    
with col2:
    st.subheader("Dépenses Annuelles")
    df_depenses['Montant Annuel'] = df_depenses['Montant Annuel'].apply(formatter_euro)
    df_depenses = st.data_editor(df_depenses, num_rows=5, key="depenses", hide_index=True)
    total_depenses_col2 = sum(pd.to_numeric(df_depenses['Montant Annuel'].str.replace('€', '').str.replace(',', ''))) #calcul du total
    st.markdown(f"**Total:** {total_depenses_col2:,.0f} €") #affichage du total

# Calcul des totaux
# Les totaux doivent être calculés à partir des valeurs numériques, pas des chaînes formatées
# Correction : Conversion en numérique avant de calculer la somme
df_revenus['Montant Annuel'] = df_revenus['Montant Annuel'].str.replace('€', '').str.replace(',', '')
df_revenus['Montant Annuel'] = pd.to_numeric(df_revenus['Montant Annuel'])
total_revenus = df_revenus['Montant Annuel'].sum()

df_depenses['Montant Annuel'] = df_depenses['Montant Annuel'].str.replace('€', '').str.replace(',', '')
df_depenses['Montant Annuel'] = pd.to_numeric(df_depenses['Montant Annuel'])
total_depenses = df_depenses['Montant Annuel'].sum()

reste_a_vivre_annuel = total_revenus - total_depenses

# Affichage des totaux annuels
#st.subheader("Totaux Annuels")
#st.markdown(f"**Total des revenus annuels :** {total_revenus:,.0f} €")
#st.markdown(f"**Total des dépenses annuelles :** {total_depenses:,.0f} €")
#st.markdown(f"**Reste à vivre annuel :** {reste_a_vivre_annuel:,.0f} €")

# Calcul des montants mensuels
df_revenus_mensuel = df_revenus.copy()
df_revenus_mensuel['Montant Mensuel'] = (df_revenus_mensuel['Montant Annuel'] / 12).round().apply(formatter_euro)
df_revenus_mensuel.pop('Montant Annuel')


df_depenses_mensuel = df_depenses.copy()
df_depenses_mensuel['Montant Mensuel'] = (df_depenses_mensuel['Montant Annuel'] / 12).round().apply(formatter_euro)
df_depenses_mensuel.pop('Montant Annuel')
    
reste_a_vivre_mensuel = int(round(reste_a_vivre_annuel / 12))

# Affichage des tableaux mensuels
col3, col4 = st.columns(2)

with col3:
    st.subheader("Revenus Mensuels")
    st.dataframe(df_revenus_mensuel, hide_index=True)
    total_revenus_mensuel_col1 = sum(pd.to_numeric(df_revenus_mensuel['Montant Mensuel'].str.replace('€', '').str.replace(',', ''))) #calcul du total
    st.markdown(f"**Total:** {total_revenus_mensuel_col1:,.0f} €") #affichage du total

    
with col4:
    st.subheader("Dépenses Mensuelles")
    st.dataframe(df_depenses_mensuel, hide_index=True)
    total_depenses_mensuel_col1 = sum(pd.to_numeric(df_depenses_mensuel['Montant Mensuel'].str.replace('€', '').str.replace(',', ''))) #calcul du total
    st.markdown(f"**Total:** {total_depenses_mensuel_col1:,.0f} €") #affichage du total

# Affichage du reste à vivre mensuel
#st.subheader("Reste à Vivre Mensuel")
#st.markdown(f"**Reste à vivre mensuel :** {reste_a_vivre_mensuel:,.0f} €")

# Reste à vivre dans un tableau
reste_a_vivre_data = {
    "Période": ["Annuel", "Mensuel"],
    "Revenus": [f"{total_revenus:,.0f} €", f"{int(round(total_revenus / 12)):,.0f} €"],
    "Dépenses": [f"{total_depenses:,.0f} €", f"{int(round(total_depenses / 12)):,.0f} €"],
    "Reste à vivre": [f"{reste_a_vivre_annuel:,.0f} €", f"{reste_a_vivre_mensuel:,.0f} €"]
}
df_reste_a_vivre = pd.DataFrame(reste_a_vivre_data)

# Calcul des pourcentages
pourcentage_depenses = (total_depenses / total_revenus) * 100
pourcentage_reste_a_vivre = (reste_a_vivre_annuel / total_revenus) * 100

# Créer un DataFrame pour les pourcentages
pourcentages_data = {
    "Poste": ["Dépenses", "Reste à vivre"],
    "Pourcentage": [f"{int(round(pourcentage_depenses))}%", f"{int(round(pourcentage_reste_a_vivre))}%"],
    "Montant": [f"{int(round(total_depenses)):,.0f} €", f"{int(round(reste_a_vivre_annuel)):,.0f} €"]
}
df_pourcentages = pd.DataFrame(pourcentages_data)


col5, col6 = st.columns(2)
with col5:
    st.subheader("Bilan")
    st.dataframe(df_reste_a_vivre, hide_index=True)
with col6:
    # Afficher le tableau des pourcentages
    st.subheader("Ratios")
    st.dataframe(df_pourcentages, hide_index=True)
    


# Préparation des données pour le Treemap
treemap_data = df_depenses.copy()
treemap_data['Reste à Vivre'] = reste_a_vivre_annuel  # Ajouter le reste à vivre comme une catégorie

# Utiliser pd.concat pour ajouter une ligne à la fin
new_row = pd.DataFrame([{'Poste': 'Reste à Vivre', 'Montant Annuel': reste_a_vivre_annuel}])
treemap_data = pd.concat([treemap_data, new_row], ignore_index=True)

# Créer de nouvelles colonnes pour les montants formatés et les pourcentages
treemap_data['Montant_formatte'] = treemap_data['Montant Annuel'].apply(formatter_euro)
treemap_data['Pourcentage'] = (treemap_data['Montant Annuel'] / total_revenus * 100).round(2)


# Créer le Treemap avec Plotly Express
fig = px.treemap(treemap_data, 
                 path=['Poste'], 
                 values='Montant Annuel',
                 color='Poste',  # Colorer par poste
                 hover_data=['Montant_formatte', 'Pourcentage'], # Afficher le montant formatté et le pourcentage au survol
                 title='Répartition des Dépenses Annuelles et Reste à Vivre')
fig.update_layout(
    treemapcolorway = ["#EF553B", "#636EFA", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E885", "#4D566E", "#F46A9B", "#1E90FF"], # Palette de couleurs plus sympa
    font_color="white",  # Couleur du texte à l'intérieur des cases
    )
fig.update_traces(textinfo='label+percent parent+value')
fig.update_layout(width=700)  # Réduire la hauteur du graphique
st.plotly_chart(fig, use_container_width=False)
