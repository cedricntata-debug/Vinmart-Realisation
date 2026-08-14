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
# 2. CHARGEMENT ET NETTOYAGE DES DONNÉES (CSV & QGIS)
# ---------------------------------------------------------
def formater_donnees(df):
    if df.empty:
        return df
    # Nettoyage des coordonnées (prise en compte des virgules françaises de QGIS)
    for col in ["Lat", "Longi", "lat", "longi", "latitude", "longitude"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Harmonisation des noms de colonnes Lat/Longi
    if "lat" in df.columns and "Lat" not in df.columns: df["Lat"] = df["lat"]
    if "longi" in df.columns and "Longi" not in df.columns: df["Longi"] = df["longi"]
    
    return df.dropna(subset=["Lat", "Longi"])

@st.cache_data
def charger_fichiers():
    p_real = os.path.join(BASE_DIR, "Structure_medicale.csv")
    p_vil = os.path.join(BASE_DIR, "villages_impactes.csv")
    p_sites = os.path.join(BASE_DIR, "sites_offices.csv")
    
    df_real = formater_donnees(pd.read_csv(p_real)) if os.path.exists(p_real) else pd.DataFrame()
    df_vil = formater_donnees(pd.read_csv(p_vil)) if os.path.exists(p_vil) else pd.DataFrame()
    df_sites = formater_donnees(pd.read_csv(p_sites)) if os.path.exists(p_sites) else pd.DataFrame()
    
    return df_real, df_vil, df_sites

data_realisations, data_villages, data_sites = charger_fichiers()

def get_image_path(nom_base):
    if not nom_base:
        return None
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".webp"]:
        p = os.path.join(ASSETS_DIR, f"{nom_base}{ext}")
        if os.path.exists(p):
            return p
    return None

# ---------------------------------------------------------
# 3. FILTRE PAR ENTREPRISE / SITE
# ---------------------------------------------------------
st.title("🤝 Les Réalisations Communautaires")

if "entreprise_choisie" not in st.session_state:
    st.session_state["entreprise_choisie"] = "Toutes les Entreprises"

entreprises_config = [
    {"id": "Toutes les Entreprises", "titre": "Vue Globale", "logo": None, "icone": "🌐"},
    {"id": "SOMIKA - Lupoto", "titre": "SOMIKA - Lupoto", "logo": "logo_somika", "icone": "⛏️"},
    {"id": "KIMIN", "titre": "KIMIN", "logo": "logo_kimin", "icone": "🏗️"},
    {"id": "SOMIKA - Kimpe", "titre": "SOMIKA - Kimpe", "logo": "logo_somika", "icone": "📍"}
]

st.markdown("##### 🏢 **Sélectionner l'Entité / Entreprise :**")
cols_ent = st.columns(4)

for i, ent in enumerate(entreprises_config):
    with cols_ent[i]:
        est_actif = (st.session_state["entreprise_choisie"] == ent["id"])
        img_path = get_image_path(ent["logo"])
        
        if img_path:
            col_g, col_img, col_d = st.columns([1, 2, 1])
            with col_img:
                st.image(img_path, width=100)
        else:
            st.markdown(f"""
            <div style="height: 50px; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 26px;">{ent['icone']}</span>
            </div>
            """, unsafe_allow_html=True)
            
        btn_label = f"✓ {ent['titre']}" if est_actif else ent["titre"]
        btn_type = "primary" if est_actif else "secondary"
        if st.button(btn_label, key=f"btn_ent_{i}", type=btn_type, use_container_width=True):
            st.session_state["entreprise_choisie"] = ent["id"]
            st.rerun()

entreprise_actuelle = st.session_state["entreprise_choisie"]

# Logique de filtrage flexible (insensible à la casse et aux tirets)
def filtrer_par_entite(df):
    if df.empty or entreprise_actuelle == "Toutes les Entreprises":
        return df
    
    col_ent = next((c for c in ["Entreprise", "Entreprise_Zone", "entreprise"] if c in df.columns), None)
    if not col_ent:
        return df
    
    serie = df[col_ent].astype(str).str.upper()
    if "LUPOTO" in entreprise_actuelle.upper():
        return df[serie.str.contains("LUPOTO")]
    elif "KIMPE" in entreprise_actuelle.upper():
        return df[serie.str.contains("KIMPE")]
    elif "KIMIN" in entreprise_actuelle.upper():
        return df[serie.str.contains("KIMIN|KISANFU|BAYEKE|NGUBA")]
    return df

df_real_filtree = filtrer_par_entite(data_realisations)
df_vil_filtree = filtrer_par_entite(data_villages)
df_sites_filtree = filtrer_par_entite(data_sites)

st.markdown("<hr style='margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. BARRE LATÉRALE (GAUCHE) : FILTRES & DESCRIPTION
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

types_engag = ["Tous"] + list(df_real_filtree["Type_Engag"].dropna().unique()) if ("Type_Engag" in df_real_filtree.columns and not df_real_filtree.empty) else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

chefferies = ["Toutes"] + list(df_real_filtree["Chefferie"].dropna().unique()) if ("Chefferie" in df_real_filtree.columns and not df_real_filtree.empty) else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

data_affichee = df_real_filtree.copy()
if not data_affichee.empty:
    if type_selectionne != "Tous":
        data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
    if chefferie_selectionnee != "Toutes":
        data_affichee = data_affichee[data_affichee["Chefferie"] == chefferie_selectionnee]

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Couches Géographiques")
afficher_villages = st.sidebar.checkbox("🏘️ Afficher les Villages Impactés", value=True)
afficher_bureaux = st.sidebar.checkbox("🏢 Afficher les Sièges & Bureaux", value=True)

st.sidebar.caption(f"Réalisations : **{len(data_affichee)}** | Villages : **{len(df_vil_filtree)}**")
st.sidebar.markdown("---")

# Fiche Signalétique
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
            <tr style="border-bottom: 1px solid #e2e8f0;">
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
        st.sidebar.info("💡 Affichage de l'ensemble des réalisations.")
else:
    points_carte = pd.DataFrame()
    st.sidebar.warning("Aucune réalisation trouvée pour ces filtres.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 5. DISPOSITION : CARTE DYNAMIQUE + LOGOS
# ---------------------------------------------------------
col_carte, col_logos = st.columns([5, 1])

with col_carte:
    m = folium.Map(tiles=None)

    folium.TileLayer(tiles='OpenStreetMap', name='Plan (OpenStreetMap)', control=True).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satellite (Esri)',
        control=True,
        max_zoom=19
    ).add_to(m)

    coords_visibles = []

    # 1. COUCHE : VILLAGES IMPACTÉS
    if afficher_villages and not df_vil_filtree.empty:
        groupe_vil = folium.FeatureGroup(name="🏘️ Villages Impactés", show=True)
        col_nom_vil = next((c for c in ["Villages", "Nom_Village", "Nom", "village"] if c in df_vil_filtree.columns), "Villages")
        
        for idx, row in df_vil_filtree.iterrows():
            lat_v, lon_v = float(row["Lat"]), float(row["Longi"])
            coords_visibles.append([lat_v, lon_v])
            
            nom_v = row.get(col_nom_vil, "Village")
            cheff_v = row.get("Chefferie", "N/A")
            group_v = row.get("Groupement", "N/A")
            id_v = row.get("ID_Village", "")
            
            folium.CircleMarker(
                location=[lat_v, lon_v],
                radius=6,
                color="#047857",
                fill=True,
                fill_color="#10b981",
                fill_opacity=0.9,
                weight=2,
                tooltip=f"<b>🏘️ Village : {nom_v}</b> ({id_v})",
                popup=f"<b>Village : {nom_v}</b><br>Groupement : {group_v}<br>Chefferie : {cheff_v}"
            ).add_to(groupe_vil)
            
        groupe_vil.add_to(m)

    # 2. COUCHE : BUREAUX & SIÈGES DES SITES
    if afficher_bureaux and not df_sites_filtree.empty:
        groupe_offices = folium.FeatureGroup(name="🏢 Sièges & Bureaux", show=True)
        col_nom_site = next((c for c in ["Nom", "Name", "nom"] if c in df_sites_filtree.columns), "Nom")
        
        for idx, row in df_sites_filtree.iterrows():
            lat_s, lon_s = float(row["Lat"]), float(row["Longi"])
            coords_visibles.append([lat_s, lon_s])
            
            nom_site = row.get(col_nom_site, "Bureau")
            ent_site = row.get("Entreprise", "N/A")
            
            office_icon_html = """
            <div style="background-color: #1e3a8a; border: 2px solid white; border-radius: 6px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">
                <span style="color: white; font-size: 14px;">🏢</span>
            </div>
            """
            folium.Marker(
                location=[lat_s, lon_s],
                popup=f"<b>{nom_site}</b><br>Entité : {ent_site}",
                tooltip=f"🏢 {nom_site} ({ent_site})",
                icon=folium.DivIcon(html=office_icon_html, icon_size=(26, 26), icon_anchor=(13, 13))
            ).add_to(groupe_offices)
            
        groupe_offices.add_to(m)

    # 3. COUCHE : RÉALISATIONS COMMUNAUTAIRES
    groupe_real = folium.FeatureGroup(name="🏥 Réalisations Communautaires", show=True)
    for idx, row in points_carte.iterrows():
        lat_r, lon_r = float(row["Lat"]), float(row["Longi"])
        coords_visibles.append([lat_r, lon_r])
        
        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        
        icon_html = """
        <div style="background-color: white; border: 1.5px solid #dc2626; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 4px rgba(0,0,0,0.35);">
            <span style="color: #dc2626; font-size: 13px; font-weight: bold; line-height: 1;">+</span>
        </div>
        """
        folium.Marker(
            location=[lat_r, lon_r],
            popup=f"<b>{nom_projet}</b><br>ID: {id_proj}<br>Engagement: {type_eng}",
            tooltip=f"{nom_projet} ({type_eng})",
            icon=folium.DivIcon(html=icon_html, icon_size=(20, 20), icon_anchor=(10, 10))
        ).add_to(groupe_real)

    groupe_real.add_to(m)

    # --- RECADRAGE ET ZOOM AUTOMATIQUE SUR LES POINTS ACTIFS ---
    if len(points_carte) == 1:
        # Si une seule réalisation est sélectionnée dans la fiche, zoom rapproché
        m.location = [float(points_carte.iloc[0]["Lat"]), float(points_carte.iloc[0]["Longi"])]
        m.zoom_start = 14
    elif coords_visibles:
        # Si vue globale ou entreprise choisie, adapte automatiquement l'emprise
        m.fit_bounds(coords_visibles, padding=(30, 30))
    else:
        m.location = [-11.65, 27.28]
        m.zoom_start = 10

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=600, key=f"carte_{entreprise_actuelle}_{len(coords_visibles)}")

with col_logos:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 4px;'>FONDATION</p>", unsafe_allow_html=True)
    p_fond = get_image_path("logo_vinmart_fondation")
    if p_fond:
        st.image(p_fond, use_container_width=True)
    else:
        st.markdown("<div style='border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; background: #f8fafc;'><b style='color: #1e3a8a; font-size: 11px;'>Fondation Vinmart</b></div>", unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 4px;'>GROUPE</p>", unsafe_allow_html=True)
    p_grp = get_image_path("logo_vinmart_groupe")
    if p_grp:
        st.image(p_grp, use_container_width=True)
    else:
        st.markdown("<div style='border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; background: #f8fafc;'><b style='color: #0f172a; font-size: 11px;'>Groupe Vinmart</b></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. REGISTRE EN BAS DE PAGE
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Registre des Réalisations")
st.dataframe(data_affichee, use_container_width=True)