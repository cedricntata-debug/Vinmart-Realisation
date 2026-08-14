import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import base64

# ---------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & SÉCURITÉ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Les Réalisations Communautaires",
    page_icon="🗺️",
    layout="wide"
)

# Chemins absolus fiables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

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
# 2. CHARGEMENT DES DONNÉES ET IMAGES
# ---------------------------------------------------------
@st.cache_data
def charger_donnees():
    csv_path = os.path.join(BASE_DIR, "Structure_medicale.csv")
    df = pd.read_csv(csv_path)
    df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
    df["Longi"] = pd.to_numeric(df["Longi"], errors="coerce")
    df = df.dropna(subset=["Lat", "Longi"])
    return df

try:
    data = charger_donnees()
except Exception as e:
    st.error(f"Erreur de chargement du fichier 'Structure_medicale.csv' : {e}")
    st.stop()

def get_image_path(nom_base):
    if not nom_base:
        return None
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".webp"]:
        p = os.path.join(ASSETS_DIR, f"{nom_base}{ext}")
        if os.path.exists(p):
            return p
    return None

def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            data_bytes = f.read()
        ext = os.path.splitext(path)[1].lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(data_bytes).decode()}"
    return None

# ---------------------------------------------------------
# 3. FILTRE ENTREPRISES / SITES - ALIGNEMENT PARFAIT
# ---------------------------------------------------------
st.title("🤝 Les Réalisations Communautaires")

if "entreprise_choisie" not in st.session_state:
    st.session_state["entreprise_choisie"] = "Toutes les Entreprises"

entreprises_config = [
    {
        "id": "Toutes les Entreprises",
        "titre": "Vue Globale",
        "sous_titre": "Toutes réalisations",
        "logo": None,
        "icone": "🌐"
    },
    {
        "id": "SOMIKA - Lupoto",
        "titre": "SOMIKA - Lupoto",
        "sous_titre": "Site de Lupoto",
        "logo": "logo_somika",
        "icone": "⛏️"
    },
    {
        "id": "KIMIN",
        "titre": "KIMIN",
        "sous_titre": "Kinsafu Mining SAS",
        "logo": "logo_kimin",
        "icone": "🏗️"
    },
    {
        "id": "SOMIKA - Kimpe",
        "titre": "SOMIKA - Kimpe",
        "sous_titre": "Site de Kimpe",
        "logo": "logo_somika",
        "icone": "📍"
    }
]

st.markdown("##### 🏢 **Sélectionner l'Entité / Entreprise :**")
cols_ent = st.columns(4)

for i, ent in enumerate(entreprises_config):
    with cols_ent[i]:
        est_actif = (st.session_state["entreprise_choisie"] == ent["id"])
        
        border_color = "#0284c7" if est_actif else "#e2e8f0"
        bg_color = "#f0f9ff" if est_actif else "#ffffff"
        shadow = "0 4px 6px -1px rgba(2, 132, 199, 0.25)" if est_actif else "0 1px 3px rgba(0,0,0,0.06)"
        
        img_path = get_image_path(ent["logo"])
        img_b64 = get_image_base64(img_path)
        
        # Bloc d'affichage au dimensionnement et centrage stricts (Hauteur fixe 85px)
        if img_b64:
            contenu_visuel = f"""
                <img src="{img_b64}" style="max-height: 48px; max-width: 90%; object-fit: contain; display: block; margin: 0 auto;">
                <span style="font-size: 10px; color: #64748b; margin-top: 4px; font-weight: 500;">{ent['sous_titre']}</span>
            """
        else:
            contenu_visuel = f"""
                <span style="font-size: 24px; line-height: 1;">{ent['icone']}</span>
                <span style="font-weight: bold; font-size: 12px; color: {'#0284c7' if est_actif else '#334155'}; margin-top: 2px;">{ent['titre']}</span>
                <span style="font-size: 10px; color: #64748b;">{ent['sous_titre']}</span>
            """
            
        carte_html = f"""
        <div style="
            border: 2px solid {border_color}; 
            background-color: {bg_color}; 
            border-radius: 8px; 
            height: 85px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            text-align: center; 
            box-shadow: {shadow}; 
            padding: 6px;
            margin-bottom: 6px;">
            {contenu_visuel}
        </div>
        """
        st.markdown(carte_html, unsafe_allow_html=True)

        # Bouton d'activation aligné
        btn_label = f"✓ {ent['titre']}" if est_actif else ent["titre"]
        btn_type = "primary" if est_actif else "secondary"
        if st.button(btn_label, key=f"btn_ent_{i}", type=btn_type, use_container_width=True):
            st.session_state["entreprise_choisie"] = ent["id"]
            st.rerun()

entreprise_choisie = st.session_state["entreprise_choisie"]

# Application du filtre entreprise
data_filtree_ent = data.copy()
if entreprise_choisie != "Toutes les Entreprises":
    if "Entreprise" in data_filtree_ent.columns:
        data_filtree_ent = data_filtree_ent[data_filtree_ent["Entreprise"] == entreprise_choisie]
    else:
        mot_cle = entreprise_choisie.split(" ")[0]
        filtre_texte = data_filtree_ent.apply(lambda r: r.astype(str).str.contains(mot_cle, case=False).any(), axis=1)
        if filtre_texte.any():
            data_filtree_ent = data_filtree_ent[filtre_texte]

st.markdown("<hr style='margin: 10px 0 16px 0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. BARRE LATÉRALE (GAUCHE) : FILTRES & TABLEAU DESCRIPTIF
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

types_engag = ["Tous"] + list(data_filtree_ent["Type_Engag"].dropna().unique()) if "Type_Engag" in data_filtree_ent.columns else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

chefferies = ["Toutes"] + list(data_filtree_ent["Chefferie"].dropna().unique()) if "Chefferie" in data_filtree_ent.columns else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

data_affichee = data_filtree_ent.copy()
if type_selectionne != "Tous":
    data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
if chefferie_selectionnee != "Toutes":
    data_affichee = data_affichee[data_affichee["Chefferie"] == chefferie_selectionnee]

st.sidebar.caption(f"Réalisations visibles : **{len(data_affichee)} / {len(data)}**")
st.sidebar.markdown("---")

st.sidebar.subheader("📋 Description de la Réalisation")

liste_projets = ["📌 Toutes les réalisations"] + list(data_affichee["Name"].dropna().unique()) if not data_affichee.empty else []

if liste_projets:
    projet_choisi = st.sidebar.selectbox("Sélectionner une réalisation :", liste_projets)
    
    if projet_choisi != "📌 Toutes les réalisations":
        points_carte = data_affichee[data_affichee["Name"] == projet_choisi]
        info = points_carte.iloc[0]
        
        annee_val = str(int(info.get('Annee'))) if (pd.notna(info.get('Annee')) and isinstance(info.get('Annee'), float)) else str(info.get('Annee', 'N/A'))
        services_val = str(info.get('Services', '-')) if pd.notna(info.get('Services')) and str(info.get('Services')) != "nan" else "-"
        budget_val = str(info.get('Budget', '-')) if pd.notna(info.get('Budget')) and str(info.get('Budget')) != "nan" else "-"

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
        
        lien_photo = info.get("Photo")
        if pd.notna(lien_photo) and str(lien_photo).startswith("http"):
            st.sidebar.markdown("<br>", unsafe_allow_html=True)
            st.sidebar.image(lien_photo, caption=info.get("Name"), use_container_width=True)
    else:
        points_carte = data_affichee
        st.sidebar.info(f"💡 Affichage de l'ensemble des **{len(points_carte)}** sites sur la carte.")
else:
    points_carte = pd.DataFrame()
    st.sidebar.warning("Aucune réalisation disponible.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 5. DISPOSITION : CARTE (CENTRE) + LOGOS INSTITUTIONNELS (DROITE)
# ---------------------------------------------------------
col_carte, col_logos = st.columns([5, 1])

with col_carte:
    if not points_carte.empty:
        lat_centre = float(points_carte["Lat"].mean())
        long_centre = float(points_carte["Longi"].mean())
        niveau_zoom = 14 if len(points_carte) == 1 else 11
    else:
        lat_centre, long_centre, niveau_zoom = -11.65, 27.28, 11

    m = folium.Map(location=[lat_centre, long_centre], zoom_start=niveau_zoom, tiles=None)

    folium.TileLayer(tiles='OpenStreetMap', name='Plan (OpenStreetMap)', control=True).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satellite (Esri)',
        control=True,
        max_zoom=19
    ).add_to(m)

    # Marqueurs Croix Rouge Médicale
    for idx, row in points_carte.iterrows():
        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        
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
            location=[float(row["Lat"]), float(row["Longi"])],
            popup=f"<b>{nom_projet}</b><br>ID: {id_proj}<br>Engagement: {type_eng}",
            tooltip=f"{nom_projet} ({type_eng})",
            icon=custom_icon
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=600)

with col_logos:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    
    # 1. Logo Fondation Vinmart
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 4px;'>FONDATION</p>", unsafe_allow_html=True)
    fond_b64 = get_image_base64(get_image_path("logo_vinmart_fondation"))
    if fond_b64:
        st.markdown(f'<img src="{fond_b64}" style="max-height: 65px; max-width: 100%; object-fit: contain; margin-bottom: 8px;">', unsafe_allow_html=True)
    else:
        st.markdown("<div style='border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; background: #f8fafc;'><b style='color: #1e3a8a; font-size: 11px;'>Fondation Vinmart</b></div>", unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    
    # 2. Logo Groupe Vinmart
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 4px;'>GROUPE</p>", unsafe_allow_html=True)
    grp_b64 = get_image_base64(get_image_path("logo_vinmart_groupe"))
    if grp_b64:
        st.markdown(f'<img src="{grp_b64}" style="max-height: 65px; max-width: 100%; object-fit: contain; margin-bottom: 8px;">', unsafe_allow_html=True)
    else:
        st.markdown("<div style='border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; background: #f8fafc;'><b style='color: #0f172a; font-size: 11px;'>Groupe Vinmart</b></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. REGISTRE EN BAS DE PAGE
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Registre des Données")
st.dataframe(points_carte if not points_carte.empty else data_affichee, use_container_width=True)