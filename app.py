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

# Chemins système fiables pour le Cloud
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
# 2. CHARGEMENT DES DONNÉES
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

# ---------------------------------------------------------
# 3. FILTRE ENTREPRISES / SITES (EN HAUT)
# ---------------------------------------------------------
st.title("🤝 Les Réalisations Communautaires")

options_entreprises = ["Toutes les Entreprises", "SOMIKA - Lupoto", "KIMIN", "SOMIKA - Kimpe"]
if "Entreprise" in data.columns:
    options_reelles = ["Toutes les Entreprises"] + list(data["Entreprise"].dropna().unique())
    options_entreprises = list(dict.fromkeys(options_entreprises + options_reelles))

entreprise_choisie = st.radio(
    "🏢 **Filtrer par Entité / Entreprise :**",
    options_entreprises,
    horizontal=True
)

data_filtree_ent = data.copy()
if entreprise_choisie != "Toutes les Entreprises":
    if "Entreprise" in data_filtree_ent.columns:
        data_filtree_ent = data_filtree_ent[data_filtree_ent["Entreprise"] == entreprise_choisie]
    else:
        mot_cle = entreprise_choisie.split(" ")[0]
        filtre_texte = data_filtree_ent.apply(lambda r: r.astype(str).str.contains(mot_cle, case=False).any(), axis=1)
        if filtre_texte.any():
            data_filtree_ent = data_filtree_ent[filtre_texte]

# ---------------------------------------------------------
# 4. BARRE LATÉRALE (GAUCHE) : FILTRES & SÉLECTION
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

# Filtre Engagement
types_engag = ["Tous"] + list(data_filtree_ent["Type_Engag"].dropna().unique()) if "Type_Engag" in data_filtree_ent.columns else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

# Filtre Chefferie
chefferies = ["Toutes"] + list(data_filtree_ent["Chefferie"].dropna().unique()) if "Chefferie" in data_filtree_ent.columns else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

data_affichee = data_filtree_ent.copy()
if type_selectionne != "Tous":
    data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
if chefferie_selectionnee != "Toutes":
    data_affichee = data_affichee[data_affichee["Chefferie"] == chefferie_selectionnee]

st.sidebar.caption(f"Réalisations correspondantes : **{len(data_affichee)} / {len(data)}**")
st.sidebar.markdown("---")

# --- SÉLECTION D'UNE RÉALISATION PRÉCISE OU TOUTES ---
st.sidebar.subheader("📋 Description de la Réalisation")

liste_projets = ["📌 Toutes les réalisations"] + list(data_affichee["Name"].dropna().unique()) if not data_affichee.empty else []

if liste_projets:
    projet_choisi = st.sidebar.selectbox("Sélectionner une réalisation :", liste_projets)
    
    # Cas 1 : L'utilisateur sélectionne un site précis
    if projet_choisi != "📌 Toutes les réalisations":
        points_carte = data_affichee[data_affichee["Name"] == projet_choisi]
        info = points_carte.iloc[0]
        
        annee_val = str(int(info.get('Annee'))) if (pd.notna(info.get('Annee')) and isinstance(info.get('Annee'), float)) else str(info.get('Annee', 'N/A'))
        services_val = str(info.get('Services', '-')) if pd.notna(info.get('Services')) and str(info.get('Services')) != "nan" else "-"
        budget_val = str(info.get('Budget', '-')) if pd.notna(info.get('Budget')) and str(info.get('Budget')) != "nan" else "-"

        # Tableau descriptif
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

    # Cas 2 : « Toutes les réalisations » est sélectionné
    else:
        points_carte = data_affichee
        st.sidebar.info(f"💡 Affichage de l'ensemble des **{len(points_carte)}** sites sur la carte. Sélectionnez un nom spécifique dans la liste ci-dessus pour isoler sa fiche et sa position.")

else:
    points_carte = pd.DataFrame()
    st.sidebar.warning("Aucune réalisation trouvée pour ces filtres.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 5. DISPOSITION : CARTE (CENTRE) + LOGOS (DROITE)
# ---------------------------------------------------------
col_carte, col_logos = st.columns([5, 1])

with col_carte:
    # Détermination du centrage et du niveau de zoom
    if not points_carte.empty:
        lat_centre = float(points_carte["Lat"].mean())
        long_centre = float(points_carte["Longi"].mean())
        # Si un seul point est choisi, on zoome dessus de près (zoom 14), sinon vue d'ensemble (zoom 11)
        niveau_zoom = 14 if len(points_carte) == 1 else 11
    else:
        lat_centre, long_centre, niveau_zoom = -11.65, 27.28, 11

    m = folium.Map(location=[lat_centre, long_centre], zoom_start=niveau_zoom, tiles=None)

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

    # Ajout des marqueurs (Uniquement les points filtrés/sélectionnés)
    for idx, row in points_carte.iterrows():
        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        
        icon_html = """
        <div style="
            background-color: white; 
            border: 1.5px solid #dc2626; 
            border-radius: 50%; 
            width: 22px; 
            height: 22px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.4);">
            <span style="color: #dc2626; font-size: 14px; font-weight: bold; line-height: 1;">+</span>
        </div>
        """
        
        custom_icon = folium.DivIcon(
            html=icon_html,
            icon_size=(22, 22),
            icon_anchor=(11, 11)
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
    
    # Helper pour trouver le logo peu importe l'extension (.png, .jpg, etc.)
    def afficher_logo(nom_base, titre_secours):
        trouve = False
        extensions = [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]
        for ext in extensions:
            chemin = os.path.join(ASSETS_DIR, f"{nom_base}{ext}")
            if os.path.exists(chemin):
                st.image(chemin, use_container_width=True)
                trouve = True
                break
        if not trouve:
            st.markdown(f"""
            <div style="border: 1px dashed #94a3b8; padding: 10px 4px; border-radius: 6px; background: #f8fafc; margin-bottom: 10px;">
                <span style="font-weight: bold; font-size: 11px; color: #1e3a8a;">{titre_secours}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 2px;'>FONDATION</p>", unsafe_allow_html=True)
    afficher_logo("logo_vinmart_fondation", "Fondation Vinmart")
    
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 2px;'>GROUPE</p>", unsafe_allow_html=True)
    afficher_logo("logo_vinmart_groupe", "Groupe Vinmart")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. REGISTRE EN BAS
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Registre des Données")
st.dataframe(points_carte if not points_carte.empty else data_affichee, use_container_width=True)