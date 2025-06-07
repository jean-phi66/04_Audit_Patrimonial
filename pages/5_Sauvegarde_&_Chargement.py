# pages/5_⚙️_Sauvegarde_&_Chargement.py
import streamlit as st
from utils.state_manager import serialize_state, deserialize_and_update_state

st.title("⚙️ Sauvegarde & Chargement de la Session")

st.write("Utilisez les boutons ci-dessous pour sauvegarder l'ensemble de vos données dans un fichier, ou pour charger une session précédente.")

st.divider()

# Bouton de sauvegarde
json_string = serialize_state()
st.download_button(
    label="💾 Sauvegarder les données",
    data=json_string,
    file_name="donnees_audit_patrimonial.json",
    mime="application/json",
    use_container_width=True,
    type="primary"
)

st.divider()

# Bouton de chargement
uploaded_file = st.file_uploader(
    "📂 Charger un fichier de données", 
    type="json"
)
if uploaded_file is not None:
    try:
        deserialize_and_update_state(uploaded_file)
        st.success("Données chargées avec succès ! L'application va se rafraîchir.")
        # Forcer le rechargement de la page pour appliquer les nouvelles données partout
        st.rerun() 
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")