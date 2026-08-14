import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# ---------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & SÉCURITÉ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Les Réalisations Communautaires",
    page_icon="🗺️",
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
# 3. FILTRE ENTREPRISES / SITES (EN HAUT DE PAGE)
# ---------------------------------------------------------
st.title("🤝 Les Réalisations Communautaires")

# Boutons horizontaux pour filtrer par Entreprise / Site
options_entreprises = ["Toutes les Entreprises", "SOMIKA - Lupoto", "KIMIN", "SOMIKA - Kimpe"]
if "Entreprise" in data.columns:
    options_reelles = ["Toutes les Entreprises"] + list(data["Entreprise"].dropna().unique())
    options_entreprises = list(dict.fromkeys(options_entreprises + options_reelles))

entreprise_choisie = st.radio(
    "🏢 **Sélectionner l'Entité / Entreprise :**",
    options_entreprises,
    horizontal=True
)

# Application du filtre Entreprise
data_filtree_ent = data.copy()
if entreprise_choisie != "Toutes les Entreprises":
    if "Entreprise" in data_filtree_ent.columns:
        data_filtree_ent = data_filtree_ent[data_filtree_ent["Entreprise"] == entreprise_choisie]
    else:
        # Recherche par mot-clé dans les colonnes texte si la colonne spécifique n'existe pas encore
        filtre_texte = data_filtree_ent.apply(lambda r: r.astype(str).str.contains(entreprise_choisie.split(" ")[0], case=False).any(), axis=1)
        if filtre_texte.any():
            data_filtree_ent = data_filtree_ent[filtre_texte]

# ---------------------------------------------------------
# 4. BARRE LATÉRALE (GAUCHE) : FILTRES & TABLEAU DE DESCRIPTION
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

# Filtre Engagement
types_engag = ["Tous"] + list(data_filtree_ent["Type_Engag"].dropna().unique()) if "Type_Engag" in data_filtree_ent.columns else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

# Filtre Chefferie
chefferies = ["Toutes"] + list(data_filtree_ent["Chefferie"].dropna().unique()) if "Chefferie" in data_filtree_ent.columns else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

# Application des filtres secondaires
data_affichee = data_filtree_ent.copy()
if type_selectionne != "Tous":
    data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
if chefferie_selectionnee != "Toutes":
    data_affichee = data_affichee[data_affichee["Chefferie"] == chefferie_selectionnee]

st.sidebar.caption(f"Réalisations visibles : **{len(data_affichee)} / {len(data)}**")
st.sidebar.markdown("---")

# --- TABLEAU STRUCTURÉ : DESCRIPTION DE LA RÉALISATION ---
st.sidebar.subheader("📋 Description de la Réalisation")

liste_projets = data_affichee["Name"].tolist() if not data_affichee.empty else []

if liste_projets:
    projet_choisi = st.sidebar.selectbox("Sélectionner une réalisation :", liste_projets)
    info = data_affichee[data_affichee["Name"] == projet_choisi].iloc[0]
    
    annee_val = str(int(info.get('Annee'))) if (pd.notna(info.get('Annee')) and isinstance(info.get('Annee'), float)) else str(info.get('Annee', 'N/A'))
    services_val = str(info.get('Services', '-')) if pd.notna(info.get('Services')) and str(info.get('Services')) != "nan" else "-"
    budget_val = str(info.get('Budget', '-')) if pd.notna(info.get('Budget')) and str(info.get('Budget')) != "nan" else "-"

    # Tableau HTML soigné pour la fiche descriptive
    tableau_html = f"""
    <table style="width:100%; border-collapse: collapse; font-size: 13px; margin-top: 8px;">
        <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Nom</td>
            <td style="padding: 6px; font-weight: bold; color: #0f172a;">{info.get('Name', 'N/A')}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Code ID</td>
            <td style="padding: 6px; color: #0284c7; font-family: monospace;">{info.get('ID_Projet', 'N/A')}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Engagement</td>
            <td style="padding: 6px;">{info.get('Type_Engag', 'N/A')}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Chefferie</td>
            <td style="padding: 6px;">{info.get('Chefferie', 'N/A')}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Année</td>
            <td style="padding: 6px;">{annee_val}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Coordonnées</td>
            <td style="padding: 6px; font-size: 11px;">{round(float(info.get('Lat')), 4)}, {round(float(info.get('Longi')), 4)}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Services</td>
            <td style="padding: 6px;">{services_val}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 6px; font-weight: bold; color: #475569;">Budget</td>
            <td style="padding: 6px;">{budget_val}</td>
        </tr>
    </table>
    """
    st.sidebar.markdown(tableau_html, unsafe_allow_html=True)
    
    # Affichage Photo si disponible
    lien_photo = info.get("Photo")
    if pd.notna(lien_photo) and str(lien_photo).startswith("http"):
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        st.sidebar.image(lien_photo, caption=info.get("Name"), use_container_width=True)
else:
    st.sidebar.info("Aucune donnée disponible pour ces critères.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 5. DISPOSITION : CARTE (CENTRE) + LOGOS INSTITUTIONNELS (DROITE)
# ---------------------------------------------------------
col_carte, col_logos = st.columns([5, 1])

with col_carte:
    lat_centre = data_affichee["Lat"].mean() if not data_affichee.empty else -11.65
    long_centre = data_affichee["Longi"].mean() if not data_affichee.empty else 27.28

    m = folium.Map(location=[lat_centre, long_centre], zoom_start=11, tiles=None)

    # 1. Plan OpenStreetMap
    folium.TileLayer(
        tiles='OpenStreetMap', 
        name='Plan (OpenStreetMap)', 
        control=True
    ).add_to(m)

    # 2. Satellite Esri
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satellite (Esri)',
        control=True,
        max_zoom=19
    ).add_to(m)

    # Marqueurs Croix Rouge DIMINUÉS (20px au lieu de 30px)
    for idx, row in data_affichee.iterrows():
        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        
        # Style compact et élégant
        icon_html = """
        <div style="
            background-color: white; 
            border: 1.5px solid #dc2626; 
            border-radius: 50%; 
            width: 20px; 
            height: 20px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            box-shadow: 0 1px 4px rgba(0,0,0,0.35);">
            <span style="color: #dc2626; font-size: 13px; font-weight: bold; line-height: 1;">+</span>
        </div>
        """
        
        custom_icon = folium.DivIcon(
            html=icon_html,
            icon_size=(20, 20),
            icon_anchor=(10, 10)
        )
        
        folium.Marker(
            location=[row["Lat"], row["Longi"]],
            popup=f"<b>{nom_projet}</b><br>ID: {id_proj}<br>Engagement: {type_eng}",
            tooltip=f"{nom_projet} ({type_eng})",
            icon=custom_icon
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=600)

with col_logos:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    
    # 1. Logo Fondation Vinmart
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 2px;'>FONDATION</p>", unsafe_allow_html=True)
    if os.path.exists("assets/logo_vinmart_fondation.png"):
        st.image("assets/logo_vinmart_fondation.png", use_container_width=True)
    else:
        st.markdown("""
        <div style="border: 1px dashed #cbd5e1; padding: 12px 6px; border-radius: 8px; margin-bottom: 12px; background: #f8fafc;">
            <b style="color: #1e3a8a; font-size: 12px;">Fondation Vinmart</b>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    
    # 2. Logo Groupe Vinmart
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 2px;'>GROUPE</p>", unsafe_allow_html=True)
    if os.path.exists("assets/logo_vinmart_groupe.png"):
        st.image("assets/logo_vinmart_groupe.png", use_container_width=True)
    else:
        st.markdown("""
        <div style="border: 1px dashed #cbd5e1; padding: 12px 6px; border-radius: 8px; background: #f8fafc;">
            <b style="color: #0f172a; font-size: 12px;">Groupe Vinmart</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. REGISTRE COMPLET
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Registre des Données")
st.dataframe(data_affichee, use_container_width=True)