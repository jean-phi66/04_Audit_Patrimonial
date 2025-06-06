import streamlit as st
import pandas as pd

# Titre de l'application
st.title("Éditeur de DataFrame Interactif")

# Initialisation des données de session si elles n'existent pas
if 'df_data' not in st.session_state:
    # Exemple de DataFrame initial
    data = {
        'Nom': ['Produit A', 'Produit B', 'Produit C', 'Produit D'],
        'Quantité': [10, 0, 25, 5],
        'Prix Unitaire (€)': [15.99, 100.50, 10.00, 75.25],
        'Catégorie': ['Électronique', 'Mobilier', 'Fournitures', 'Électronique'],
        'Priorité': ['Haute', 'Moyenne', 'Basse', 'Haute'],
        'En Stock': [True, False, True, True]
    }
    st.session_state.df_data = pd.DataFrame(data)

# Options pour les colonnes de sélection
categories_options = ['Électronique', 'Mobilier', 'Fournitures', 'Vêtements', 'Alimentation']
priorite_options = ['Haute', 'Moyenne', 'Basse']

st.subheader("Éditez le DataFrame ci-dessous :")

# Utilisation de st.data_editor pour rendre le DataFrame éditable
# La configuration des colonnes permet de spécifier le type d'éditeur pour chaque colonne
edited_df = st.data_editor(
    st.session_state.df_data,
    column_config={
        "Nom": st.column_config.TextColumn(
            "Nom du Produit",  # Label personnalisé pour la colonne
            help="Entrez le nom du produit.",
            required=True, # Rend ce champ obligatoire
        ),
        "Quantité": st.column_config.NumberColumn(
            "Quantité en Stock",
            help="Nombre d'unités actuellement en stock.",
            min_value=0,
            max_value=1000,
            step=1,
            format="%d", # Format d'affichage pour les entiers
            required=True,
        ),
        "Prix Unitaire (€)": st.column_config.NumberColumn(
            "Prix par Unité",
            help="Le prix de vente d'une seule unité du produit.",
            min_value=0.0,
            step=0.01,
            format="€%.2f", # Format pour afficher la devise avec 2 décimales
            required=True,
        ),
        "Catégorie": st.column_config.SelectboxColumn(
            "Catégorie de Produit",
            help="Sélectionnez la catégorie à laquelle le produit appartient.",
            options=categories_options,
            required=True,
        ),
        "Priorité": st.column_config.SelectboxColumn(
            "Niveau de Priorité",
            help="Définissez la priorité pour le réapprovisionnement ou la gestion.",
            options=priorite_options,
            required=True,
        ),
        "En Stock": st.column_config.CheckboxColumn(
            "Disponible en Stock?",
            help="Cochez si le produit est actuellement en stock.",
            default=False, # Valeur par défaut si non spécifié
        )
    },
    num_rows="dynamic", # Permet d'ajouter ou de supprimer des lignes
    use_container_width=True # Utilise toute la largeur disponible
)

# Mettre à jour le DataFrame dans l'état de session si des modifications ont été apportées
if edited_df is not None:
    st.session_state.df_data = edited_df

st.subheader("Aperçu du DataFrame (après édition) :")
st.dataframe(st.session_state.df_data, use_container_width=True)

# Option pour réinitialiser le DataFrame à son état initial
if st.button("Réinitialiser le DataFrame"):
    data_initial = {
        'Nom': ['Produit A', 'Produit B', 'Produit C', 'Produit D'],
        'Quantité': [10, 0, 25, 5],
        'Prix Unitaire (€)': [15.99, 100.50, 10.00, 75.25],
        'Catégorie': ['Électronique', 'Mobilier', 'Fournitures', 'Électronique'],
        'Priorité': ['Haute', 'Moyenne', 'Basse', 'Haute'],
        'En Stock': [True, False, True, True]
    }
    st.session_state.df_data = pd.DataFrame(data_initial)
    st.rerun()

st.caption("Cette application utilise `st.data_editor` pour permettre l'édition directe des cellules. "
           "Les colonnes 'Quantité' et 'Prix Unitaire (€)' sont des champs numériques. "
           "Les colonnes 'Catégorie' et 'Priorité' offrent une sélection dans une liste. "
           "La colonne 'En Stock' est une case à cocher.")

