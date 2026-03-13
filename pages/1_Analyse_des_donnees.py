import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analyse des données", layout="wide")
st.title("Analyse des données")

#1 Initialiser la mémoire de la session
if "df" not in st.session_state:
    st.session_state["df"] = None
#2 Widget d'upload
uploaded_file = st.file_uploader("Charge un fichier CSV ou Excel", type=["csv","xlsx"])

#3 Lire le fichier si l'utilisateur en a chargé un
if uploaded_file is not None:
    file_name = uploaded_file.name.lower()  # normaliser le nom du fichier pour éviter les problèmes de nom

    try:
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format non supporté.")
        
        if df is not None:
            st.session_state["df"] = df
            st.success("Fichier chargé avec succès !")
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
#4 Récuperer  le DataFrame depuis la session

df = st.session_state["df"]

#5 Affichage si dataset existe
if df is not None:

    st.subheader("Aperçu du dataset")
    st.dataframe(df.head())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Nombre de lignes", df.shape[0])
    with col2:
        st.metric("Nombres de colonnes", df.shape[1])
    with col3:
        st.metric("Valeurs manquantes", int(df.isna().sum().sum()))
    with col4:
        st.metric("Pourcentage manquant", f"{(df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100).round(2)}%")

    st.subheader("Type de colonnes")
    types_df = pd.DataFrame({
        "colonne": df.columns,
        "Type" : df.dtypes.astype(str),
        "valeurs_manquantes": df.isna().sum().values,
        "Pourcentage_manquant": (df.isna().sum().values / len(df) * 100).round(2)

    })
    st.dataframe(types_df)

else:
    st.info("Aucun dataset chargé pour le moment.")