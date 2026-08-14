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
# 2. CHARGEMENT ROBUSTE DES DONNÉES (CSV / QGIS)
# ---------------------------------------------------------
def nettoyer_coords(df):
    if "Lat" in df.columns and "Longi" in df.columns:
        df["Lat"] = df["Lat"].astype(str).str.replace(",", ".")
        df["Longi"] = df["Longi"].astype(str).str.replace(",", ".")
        df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
        df["Longi"] = pd.to_numeric(df["Longi"], errors="coerce")
        return df.dropna(subset=["Lat", "Longi"])
    return df

@st.cache_data
def charger_toutes_donnees():
    # 1. Réalisations
    p_real = os.path.join(BASE_DIR, "Structure_medicale.csv")
    df_real = nettoyer_coords(pd.read_csv(p_real)) if os.path.exists(p_real) else pd.DataFrame()
    
    # 2. Villages impactés
    p_vil = os.path.join(BASE_DIR, "villages_impactes.csv")
    df_vil = nettoyer_coords(pd.read_csv(p_vil)) if os.path.exists(p_vil) else pd.DataFrame()
    
    # 3. Bureaux / Sites
    p_sites = os.path.join(BASE_DIR, "sites_offices.csv")
    df_sites = nettoyer_coords(pd.read_csv(p_sites)) if os.path.exists(p_sites) else pd.DataFrame()
    
    return df_real, df_vil, df_sites

data_realisations, data_villages, data_sites = charger_toutes_donnees()

def get_image_path(nom_base):
    if not nom_base:
        return None
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".webp"]:
        p = os.path.join(ASSETS_DIR, f"{nom_base}{ext}")
        if os.path.exists(p):
            return p
    return None

# ---------------------------------------------------------
# 3. FILTRE ENTREPRISES / SITES (EN HAUT)
# ---------------------------------------------------------
st.title("🤝 Les Réalisations Communautaires")

if "entreprise_choisie" not in st.session_state:
    st.session_state["entreprise_choisie"] = "Toutes les Entreprises"

entreprises_config = [
    {"id": "Toutes les Entreprises", "titre": "Vue Globale", "sous_titre": "Toutes réalisations", "logo": None, "icone": "🌐"},
    {"id": "SOMIKA - Lupoto", "titre": "SOMIKA - Lupoto", "sous_titre": "Site de Lupoto", "logo": "logo_somika", "icone": "⛏️"},
    {"id": "KIMIN", "titre": "KIMIN", "sous_titre": "Kinsafu Mining SAS", "logo": "logo_kimin", "icone": "🏗️"},
    {"id": "SOMIKA - Kimpe", "titre": "SOMIKA - Kimpe", "sous_titre": "Site de Kimpe", "logo": "logo_somika", "icone": "📍"}
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
                st.image(img_path, width=110)
        else:
            st.markdown(f"""
            <div style="height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                <span style="font-size: 26px; line-height: 1;">{ent['icone']}</span>
            </div>
            """, unsafe_allow_html=True)
            
        btn_label = f"✓ {ent['titre']}" if est_actif else ent["titre"]
        btn_type = "primary" if est_actif else "secondary"
        if st.button(btn_label, key=f"btn_ent_{i}", type=btn_type, use_container_width=True):
            st.session_state["entreprise_choisie"] = ent["id"]
            st.rerun()

entreprise_choisie = st.session_state["entreprise_choisie"]

# Fonction de filtrage par entreprise sur n'importe quelle table
def filtrer_par_ent(df):
    if df.empty or entreprise_choisie == "Toutes les Entreprises":
        return df
    col_ent = next((c for c in ["Entreprise", "Entreprise_Zone"] if c in df.columns), None)
    if col_ent:
        mot_cle = "SOMIKA" if "SOMIKA" in entreprise_choisie else ("KIMIN" if "KIMIN" in entreprise_choisie or "KISANFU" in entreprise_choisie else entreprise_choisie)
        if "Lupoto" in entreprise_choisie:
            return df[df[col_ent].str.contains("LUPOTO", case=False, na=False)]
        elif "Kimpe" in entreprise_choisie:
            return df[df[col_ent].str.contains("KIMPE", case=False, na=False)]
        elif "KIMIN" in entreprise_choisie:
            return df[df[col_ent].str.contains("KIMIN|KISANFU", case=False, na=False)]
    return df

df_real_filtree = filtrer_par_ent(data_realisations)
df_vil_filtree = filtrer_par_ent(data_villages)
df_sites_filtree = filtrer_par_ent(data_sites)

st.markdown("<hr style='margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. BARRE LATÉRALE (GAUCHE) : FILTRES & COUCHES
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

# Filtre Engagement
types_engag = ["Tous"] + list(df_real_filtree["Type_Engag"].dropna().unique()) if ("Type_Engag" in df_real_filtree.columns and not df_real_filtree.empty) else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

# Filtre Chefferie
chefferies = ["Toutes"] + list(df_real_filtree["Chefferie"].dropna().unique()) if ("Chefferie" in df_real_filtree.columns and not df_real_filtree.empty) else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

data_affichee = df_real_filtree.copy()
if not data_affichee.empty:
    if type_selectionne != "Tous":
        data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
    if chefferie_selectionnee != "Toutes":
        data_affichee = data_affichee[data_affichee["Chefferie"] == chefferie_selectionnee]

# Gestion des calques territoriaux
st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Couches Géographiques")
afficher_villages = st.sidebar.checkbox("🏘️ Afficher les Villages Impactés", value=True)
afficher_bureaux = st.sidebar.checkbox("🏢 Afficher les Sièges / Bureaux", value=True)

st.sidebar.caption(f"Réalisations visibles : **{len(data_affichee)}** | Villages : **{len(df_vil_filtree)}**")
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
        st.sidebar.info(f"💡 Affichage de l'ensemble des réalisations.")
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
    # Centrage de la carte
    ref_df = points_carte if not points_carte.empty else (df_vil_filtree if not df_vil_filtree.empty else df_sites_filtree)
    if not ref_df.empty:
        lat_centre = float(ref_df["Lat"].mean())
        long_centre = float(ref_df["Longi"].mean())
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

    # 1. COUCHE : VILLAGES IMPACTÉS
    if afficher_villages and not df_vil_filtree.empty:
        groupe_vil = folium.FeatureGroup(name="🏘️ Villages Impactés", show=True)
        col_nom_vil = "Villages" if "Villages" in df_vil_filtree.columns else "Nom_Village"
        
        for idx, row in df_vil_filtree.iterrows():
            nom_v = row.get(col_nom_vil, "Village")
            cheff_v = row.get("Chefferie", "N/A")
            group_v = row.get("Groupement", "N/A")
            id_v = row.get("ID_Village", "N/A")
            
            folium.CircleMarker(
                location=[float(row["Lat"]), float(row["Longi"])],
                radius=5,
                color="#059669",
                fill=True,
                fill_color="#34d399",
                fill_opacity=0.85,
                weight=1.5,
                tooltip=f"<b>Village : {nom_v}</b> ({id_v})",
                popup=f"<b>Village : {nom_v}</b><br>Groupement : {group_v}<br>Chefferie : {cheff_v}"
            ).add_to(groupe_vil)
            
        groupe_vil.add_to(m)

    # 2. COUCHE : BUREAUX / SIÈGES DES SITES
    if afficher_bureaux and not df_sites_filtree.empty:
        groupe_offices = folium.FeatureGroup(name="🏢 Sièges & Bureaux", show=True)
        for idx, row in df_sites_filtree.iterrows():
            nom_site = row.get("Nom", "Bureau")
            ent_site = row.get("Entreprise", "N/A")
            
            # Badge Bâtiment stylisé
            office_icon_html = f"""
            <div style="background-color: #1e3a8a; border: 2px solid white; border-radius: 6px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">
                <span style="color: white; font-size: 14px;">🏢</span>
            </div>
            """
            custom_office_icon = folium.DivIcon(html=office_icon_html, icon_size=(26, 26), icon_anchor=(13, 13))
            
            folium.Marker(
                location=[float(row["Lat"]), float(row["Longi"])],
                popup=f"<b>{nom_site}</b><br>Entité : {ent_site}",
                tooltip=f"🏢 {nom_site} ({ent_site})",
                icon=custom_office_icon
            ).add_to(groupe_offices)
            
        groupe_offices.add_to(m)

    # 3. COUCHE : RÉALISATIONS COMMUNAUTAIRES
    groupe_real = folium.FeatureGroup(name="🏥 Réalisations Communautaires", show=True)
    for idx, row in points_carte.iterrows():
        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        
        icon_html = """
        <div style="background-color: white; border: 1.5px solid #dc2626; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 4px rgba(0,0,0,0.35);">
            <span style="color: #dc2626; font-size: 13px; font-weight: bold; line-height: 1;">+</span>
        </div>
        """
        custom_icon = folium.DivIcon(html=icon_html, icon_size=(20, 20), icon_anchor=(10, 10))
        
        folium.Marker(
            location=[float(row["Lat"]), float(row["Longi"])],
            popup=f"<b>{nom_projet}</b><br>ID: {id_proj}<br>Engagement: {type_eng}",
            tooltip=f"{nom_projet} ({type_eng})",
            icon=custom_icon
        ).add_to(groupe_real)

    groupe_real.add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=600)

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
st.subheader("📊 Registre des Données")
st.dataframe(points_carte if not points_carte.empty else data_affichee, use_container_width=True)