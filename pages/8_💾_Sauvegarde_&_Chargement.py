# pages/5_⚙️_Sauvegarde_&_Chargement.py
import streamlit as st
from utils.state_manager import serialize_state, deserialize_and_update_state

st.title("💾 Sauvegarde & Chargement de la Session")

st.write("Utilisez les boutons ci-dessous pour sauvegarder l'ensemble de vos données dans un fichier, ou pour charger une session précédente.")

st.divider()

# --- Section de Chargement ---
st.subheader("Charger une session depuis un fichier")
uploaded_file = st.file_uploader(
    "📂 Charger un fichier de données",
    type="json"
)
if uploaded_file is not None:
    try:
        deserialize_and_update_state(uploaded_file)
        st.success("Données chargées avec succès ! L'application va se rafraîchir.")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
else:
    # La section de sauvegarde n'est affichée que si aucun fichier n'est en cours de traitement.
    # Cela évite que le st.rerun() du chargement n'invalide le bouton de sauvegarde.
    st.divider()
    st.subheader("Sauvegarder la session actuelle")

    # Initialiser le nom du fichier dans le session_state s'il n'existe pas.
    if 'save_file_name' not in st.session_state:
        st.session_state.save_file_name = "donnees_audit_patrimonial"

    # Le widget text_input met à jour directement st.session_state.save_file_name grâce à la clé.
    st.text_input(
        "Nom du fichier de sauvegarde",
        key="save_file_name",
        help="Entrez un nom pour votre fichier de sauvegarde (l'extension .json sera ajoutée automatiquement)."
    )

    try:
        json_string = serialize_state()
        download_disabled = False
    except Exception as e:
        json_string = f"Erreur de sérialisation: {e}"
        download_disabled = True
        st.error(f"Impossible de préparer les données pour la sauvegarde : {e}")

    st.download_button(
        label="💾 Sauvegarder les données",
        data=json_string,
        file_name=f"{st.session_state.save_file_name}.json" if st.session_state.save_file_name else "donnees_audit_patrimonial.json",
        mime="application/json",
        use_container_width=True,
        type="primary",
        disabled=download_disabled
    )