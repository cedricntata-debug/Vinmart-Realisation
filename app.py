import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & SÉCURITÉ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Les Réalisations Communautaires",
    page_icon="🏥",
    layout="wide"
)

MOT_DE_PASSE_SECRET = "Fondation2026!" 

if "authentifie" not in st.session_state:
    st.session_state["authentifie"] = False

def verifier_mot_de_passe():
    if st.session_state["password_input"] == MOT_DE_PASSE_SECRET:
        st.session_state["authentifie"] = True
        st.session_state["password_input"] = ""
    else:
        st.error("Mot de passe incorrect")

if not st.session_state["authentifie"]:
    st.title("🔒 Accès Restreint - Les Réalisations Communautaires")
    st.markdown("Veuillez saisir le mot de passe pour accéder au portail cartographique.")
    st.text_input("Mot de passe :", type="password", key="password_input", on_change=verifier_mot_de_passe)
    st.stop()

# ---------------------------------------------------------
# 2. CHARGEMENT DES DONNÉES
# ---------------------------------------------------------
@st.cache_data
def charger_donnees():
    df = pd.read_csv("Structure_medicale.csv")
    df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
    df["Longi"] = pd.to_numeric(df["Longi"], errors="coerce")
    df = df.dropna(subset=["Lat", "Longi"])
    return df

try:
    data = charger_donnees()
except Exception as e:
    st.error(f"Erreur de chargement du fichier 'Structure_medicale.csv' : {e}")
    st.stop()

# ---------------------------------------------------------
# 3. BARRE LATÉRALE (GAUCHE) : FILTRES + FICHE SIGNALÉTIQUE
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

types_engag = ["Tous"] + list(data["Type_Engag"].dropna().unique()) if "Type_Engag" in data.columns else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

chefferies = ["Toutes"] + list(data["Chefferie"].dropna().unique()) if "Chefferie" in data.columns else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

data_filtree = data.copy()
if type_selectionne != "Tous":
    data_filtree = data_filtree[data_filtree["Type_Engag"] == type_selectionne]
if chefferie_selectionnee != "Toutes":
    data_filtree = data_filtree[data_filtree["Chefferie"] == chefferie_selectionnee]

st.sidebar.caption(f"Structures affichées : **{len(data_filtree)} / {len(data)}**")
st.sidebar.markdown("---")

# --- FICHE SIGNALÉTIQUE DANS LA BARRE LATÉRALE ---
st.sidebar.subheader("📋 Description de la Réalisation")

liste_projets = data_filtree["Name"].tolist() if not data_filtree.empty else []

if liste_projets:
    projet_choisi = st.sidebar.selectbox("Sélectionner une structure :", liste_projets)
    info = data_filtree[data_filtree["Name"] == projet_choisi].iloc[0]
    
    st.sidebar.markdown(f"### {info.get('Name', 'N/A')}")
    st.sidebar.markdown(f"**Code ID :** `{info.get('ID_Projet', 'N/A')}`")
    st.sidebar.markdown(f"**Engagement :** {info.get('Type_Engag', 'N/A')}")
    st.sidebar.markdown(f"**Chefferie :** {info.get('Chefferie', 'N/A')}")
    
    if pd.notna(info.get("Annee")):
        annee_val = int(info.get('Annee')) if isinstance(info.get('Annee'), float) else info.get('Annee')
        st.sidebar.markdown(f"**Année :** {annee_val}")
        
    st.sidebar.markdown(f"**GPS :** `{info.get('Lat')}, {info.get('Longi')}`")
    
    if pd.notna(info.get("Services")) and str(info.get("Services")) != "nan":
        st.sidebar.markdown(f"**Services :** {info.get('Services')}")
    if pd.notna(info.get("Budget")) and str(info.get("Budget")) != "nan":
        st.sidebar.markdown(f"**Budget :** {info.get('Budget')}")
        
    lien_photo = info.get("Photo")
    if pd.notna(lien_photo) and str(lien_photo).startswith("http"):
        st.sidebar.image(lien_photo, caption=info.get("Name"), use_column_width=True)
else:
    st.sidebar.info("Aucune structure ne correspond aux filtres.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 4. ZONE PRINCIPALE (EN-TÊTE + CARTE À DROITE)
# ---------------------------------------------------------

# EN-TÊTE LOGOS ET TITRE
st.title("🤝 Les Réalisations Communautaires")

col_logo1, col_logo2, col_empty = st.columns([2, 2, 3])
with col_logo1:
    st.markdown("""
        <div style="background-color: #f8fafc; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #1e3a8a;">
            <span style="font-weight: bold; color: #1e3a8a; font-size: 13px;">SOMIKA - Lupoto</span><br>
            <span style="font-size: 11px; color: #64748b;">Sociétés Minières du Katanga</span>
        </div>
    """, unsafe_allow_html=True)

with col_logo2:
    st.markdown("""
        <div style="background-color: #f8fafc; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #059669;">
            <span style="font-weight: bold; color: #059669; font-size: 13px;">KIMIN</span><br>
            <span style="font-size: 11px; color: #64748b;">Kinsafu Mining</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# CARTE INTERACTIVE (OCCUPE TOUTE LA LARGEUR DE LA ZONE PRINCIPALE)
lat_centre = data_filtree["Lat"].mean() if not data_filtree.empty else -11.65
long_centre = data_filtree["Longi"].mean() if not data_filtree.empty else 27.28

m = folium.Map(location=[lat_centre, long_centre], zoom_start=11, tiles=None)

# --- UNIQUEMENT 2 FONDS DE CARTE ---
# 1. Plan (OpenStreetMap)
folium.TileLayer(
    tiles='OpenStreetMap', 
    name='Plan (OpenStreetMap)', 
    control=True
).add_to(m)

# 2. Satellite (Esri)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri World Imagery',
    name='Satellite (Esri)',
    control=True,
    max_zoom=19
).add_to(m)

# Marqueurs avec Croix Rouge très visible
for idx, row in data_filtree.iterrows():
    nom_projet = row.get("Name", "Structure Médicale")
    id_proj = row.get("ID_Projet", "N/A")
    type_eng = row.get("Type_Engag", "N/A")
    
    # Icône Croix Rouge Médicale sur fond blanc avec bordure rouge
    icon_html = """
    <div style="
        background-color: white; 
        border: 2px solid #dc2626; 
        border-radius: 50%; 
        width: 30px; 
        height: 30px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);">
        <span style="color: #dc2626; font-size: 18px; font-weight: bold; line-height: 1;">+</span>
    </div>
    """
    
    custom_icon = folium.DivIcon(
        html=icon_html,
        icon_size=(30, 30),
        icon_anchor=(15, 15)
    )
    
    folium.Marker(
        location=[row["Lat"], row["Longi"]],
        popup=f"<b>{nom_projet}</b><br>ID: {id_proj}<br>Engagement: {type_eng}",
        tooltip=f"{nom_projet} ({type_eng})",
        icon=custom_icon
    ).add_to(m)

# Sélecteur de fond de carte discret (collapsé par défaut pour ne pas gêner)
folium.LayerControl(collapsed=True).add_to(m)

st_folium(m, width="100%", height=620)

# ---------------------------------------------------------
# 5. REGISTRE EN BAS DE PAGE
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Registre des Données")
st.dataframe(data_filtree, use_container_width=True)