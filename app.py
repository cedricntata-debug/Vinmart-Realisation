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
# 2. CHARGEMENT ET NETTOYAGE DES DONNÉES
# ---------------------------------------------------------
def formater_donnees(df):
    if df.empty:
        return df
    for col in ["Lat", "Longi", "lat", "longi", "latitude", "longitude"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
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
# 3. FILTRE ENTREPRISES / SITES
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

# Fonction pour tester si une ligne appartient à l'entreprise sélectionnée
def appartient_a_entreprise(row, entite_cible):
    if entite_cible == "Toutes les Entreprises":
        return True
    
    val_texte = " ".join([str(v) for v in row.values]).upper()
    if "LUPOTO" in entite_cible.upper():
        return "LUPOTO" in val_texte
    elif "KIMPE" in entite_cible.upper():
        return "KIMPE" in val_texte
    elif "KIMIN" in entite_cible.upper():
        return any(k in val_texte for k in ["KIMIN", "KISANFU", "BAYEKE", "NGUBA"])
    return False

# Données actives pour les tableaux
df_real_actives = data_realisations[data_realisations.apply(lambda r: appartient_a_entreprise(r, entreprise_actuelle), axis=1)] if not data_realisations.empty else pd.DataFrame()
df_vil_actives = data_villages[data_villages.apply(lambda r: appartient_a_entreprise(r, entreprise_actuelle), axis=1)] if not data_villages.empty else pd.DataFrame()

st.markdown("<hr style='margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. BARRE LATÉRALE (GAUCHE) : FILTRES & FICHE SIGNALÉTIQUE
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

types_engag = ["Tous"] + list(df_real_actives["Type_Engag"].dropna().unique()) if ("Type_Engag" in df_real_actives.columns and not df_real_actives.empty) else ["Tous"]
type_selectionne = st.sidebar.selectbox("Type d'engagement :", types_engag)

chefferies = ["Toutes"] + list(df_real_actives["Chefferie"].dropna().unique()) if ("Chefferie" in df_real_actives.columns and not df_real_actives.empty) else ["Toutes"]
chefferie_selectionnee = st.sidebar.selectbox("Chefferie :", chefferies)

data_affichee = df_real_actives.copy()
if not data_affichee.empty:
    if type_selectionne != "Tous":
        data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
    if chefferie_selectionnee != "Toutes":
        data_affichee = data_affichee[data_affichee["Chefferie"] == chefferie_selectionnee]

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Couches Géographiques")
afficher_villages = st.sidebar.checkbox("🏘️ Afficher les Villages Impactés", value=True)
afficher_bureaux = st.sidebar.checkbox("🏢 Afficher les Sièges & Bureaux", value=True)

st.sidebar.caption(f"Réalisations actives : **{len(data_affichee)}** | Villages actifs : **{len(df_vil_actives)}**")
st.sidebar.markdown("---")

# Fiche Signalétique
st.sidebar.subheader("📋 Description de la Réalisation")
liste_projets = ["📌 Toutes les réalisations"] + list(data_affichee["Name"].dropna().unique()) if not data_affichee.empty else []

if liste_projets:
    projet_choisi = st.sidebar.selectbox("Sélectionner une réalisation :", liste_projets)
    
    if projet_choisi != "📌 Toutes les réalisations":
        points_zoom_fiche = data_affichee[data_affichee["Name"] == projet_choisi]
        info = points_zoom_fiche.iloc[0]
        
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
        points_zoom_fiche = pd.DataFrame()
        st.sidebar.info("💡 Affichage de l'ensemble des réalisations.")
else:
    points_zoom_fiche = pd.DataFrame()
    st.sidebar.warning("Aucune réalisation trouvée pour ces filtres.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 5. DISPOSITION : CARTE DYNAMIQUE AVEC FOCUS ET SURBRILLANCE
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

    coords_focus = []

    # 1. COUCHE VILLAGES IMPACTÉS (Actifs en Vert Vif / Autres en Estompé)
    if afficher_villages and not data_villages.empty:
        groupe_vil = folium.FeatureGroup(name="🏘️ Villages Impactés", show=True)
        col_nom_vil = next((c for c in ["Villages", "Nom_Village", "Nom", "village"] if c in data_villages.columns), "Villages")
        
        for idx, row in data_villages.iterrows():
            lat_v, lon_v = float(row["Lat"]), float(row["Longi"])
            est_du_site = appartient_a_entreprise(row, entreprise_actuelle)
            
            nom_v = row.get(col_nom_vil, "Village")
            cheff_v = row.get("Chefferie", "N/A")
            group_v = row.get("Groupement", "N/A")
            id_v = row.get("ID_Village", "")
            
            if est_du_site:
                coords_focus.append([lat_v, lon_v])
                folium.CircleMarker(
                    location=[lat_v, lon_v],
                    radius=6,
                    color="#047857",
                    fill=True,
                    fill_color="#10b981",
                    fill_opacity=0.95,
                    weight=2,
                    tooltip=f"<b>🏘️ Village : {nom_v}</b> ({id_v})",
                    popup=f"<b>Village : {nom_v}</b><br>Groupement : {group_v}<br>Chefferie : {cheff_v}"
                ).add_to(groupe_vil)
            else:
                # Mode surbrillance / arrière-plan estompé
                folium.CircleMarker(
                    location=[lat_v, lon_v],
                    radius=4,
                    color="#94a3b8",
                    fill=True,
                    fill_color="#cbd5e1",
                    fill_opacity=0.35,
                    weight=1,
                    tooltip=f"🏘️ {nom_v} (Autre secteur)",
                ).add_to(groupe_vil)
            
        groupe_vil.add_to(m)

    # 2. COUCHE BUREAUX / SIÈGES
    if afficher_bureaux and not data_sites.empty:
        groupe_offices = folium.FeatureGroup(name="🏢 Sièges & Bureaux", show=True)
        col_nom_site = next((c for c in ["Nom", "Name", "nom"] if c in data_sites.columns), "Nom")
        
        for idx, row in data_sites.iterrows():
            lat_s, lon_s = float(row["Lat"]), float(row["Longi"])
            est_du_site = appartient_a_entreprise(row, entreprise_actuelle)
            nom_site = row.get(col_nom_site, "Bureau")
            ent_site = row.get("Entreprise", "N/A")
            
            if est_du_site:
                coords_focus.append([lat_s, lon_s])
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
            else:
                # Bureau en surbrillance estompée
                office_dim_html = """
                <div style="background-color: rgba(148, 163, 184, 0.4); border: 1px dashed #64748b; border-radius: 6px; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 11px; opacity: 0.6;">🏢</span>
                </div>
                """
                folium.Marker(
                    location=[lat_s, lon_s],
                    tooltip=f"🏢 {nom_site} (Autre site)",
                    icon=folium.DivIcon(html=office_dim_html, icon_size=(20, 20), icon_anchor=(10, 10))
                ).add_to(groupe_offices)
            
        groupe_offices.add_to(m)

    # 3. COUCHE RÉALISATIONS COMMUNAUTAIRES
    groupe_real = folium.FeatureGroup(name="🏥 Réalisations Communautaires", show=True)
    for idx, row in data_realisations.iterrows():
        lat_r, lon_r = float(row["Lat"]), float(row["Longi"])
        est_du_site = appartient_a_entreprise(row, entreprise_actuelle)
        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        
        if est_du_site:
            coords_focus.append([lat_r, lon_r])
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
        else:
            # Réalisations en surbrillance estompée
            dim_real_html = """
            <div style="background-color: rgba(254, 226, 226, 0.4); border: 1px solid rgba(220, 38, 38, 0.3); border-radius: 50%; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center;">
                <span style="color: rgba(220, 38, 38, 0.4); font-size: 9px;">+</span>
            </div>
            """
            folium.Marker(
                location=[lat_r, lon_r],
                tooltip=f"{nom_projet} (Autre secteur)",
                icon=folium.DivIcon(html=dim_real_html, icon_size=(14, 14), icon_anchor=(7, 7))
            ).add_to(groupe_real)

    groupe_real.add_to(m)

    # --- RECADRAGE ET CENTRAGE DYNAMIQUE SUR LES POINTS DU SITE CHOISI ---
    if not points_zoom_fiche.empty:
        # 1. Priorité au projet sélectionné dans la fiche latérale
        m.location = [float(points_zoom_fiche.iloc[0]["Lat"]), float(points_zoom_fiche.iloc[0]["Longi"])]
        m.zoom_start = 14
    elif coords_focus:
        # 2. Zoom direct et centrage sur le groupe de points de l'entreprise choisie
        m.fit_bounds(coords_focus, padding=(25, 25))
    else:
        m.location = [-11.65, 27.28]
        m.zoom_start = 10

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=600, key=f"carte_{entreprise_actuelle}_{len(coords_focus)}")

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