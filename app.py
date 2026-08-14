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
    p_real = os.path.join(BASE_DIR, "Toutes_Realisations.csv")
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
# 3. FILTRE ENTREPRISES / SITES (EN HAUT)
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
                st.image(img_path, width=95)
        else:
            st.markdown(f"""
            <div style="height: 48px; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 24px;">{ent['icone']}</span>
            </div>
            """, unsafe_allow_html=True)
            
        btn_label = f"✓ {ent['titre']}" if est_actif else ent["titre"]
        btn_type = "primary" if est_actif else "secondary"
        if st.button(btn_label, key=f"btn_ent_{i}", type=btn_type, use_container_width=True):
            st.session_state["entreprise_choisie"] = ent["id"]
            st.rerun()

entreprise_actuelle = st.session_state["entreprise_choisie"]

# Fonction d'appartenance à l'entreprise
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

df_real_actives = data_realisations[data_realisations.apply(lambda r: appartient_a_entreprise(r, entreprise_actuelle), axis=1)] if not data_realisations.empty else pd.DataFrame()
df_vil_actives = data_villages[data_villages.apply(lambda r: appartient_a_entreprise(r, entreprise_actuelle), axis=1)] if not data_villages.empty else pd.DataFrame()

# ---------------------------------------------------------
# 4. BARRE LATÉRALE : FILTRES MULTI-CRITÈRES & DESCRIPTION
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filtres de Recherche")

# 1. Filtre Secteur
secteurs_dispos = ["Tous"] + sorted(list(df_real_actives["Secteur"].dropna().unique())) if ("Secteur" in df_real_actives.columns and not df_real_actives.empty) else ["Tous"]
secteur_selectionne = st.sidebar.selectbox("📂 Secteur d'intervention :", secteurs_dispos)

# 2. Filtre Engagement
types_engag = ["Tous"] + sorted(list(df_real_actives["Type_Engag"].dropna().unique())) if ("Type_Engag" in df_real_actives.columns and not df_real_actives.empty) else ["Tous"]
type_selectionne = st.sidebar.selectbox("⚖️ Type d'engagement :", types_engag)

# 3. Filtre Année
annees_dispos = ["Toutes"]
if "Annee" in df_real_actives.columns and not df_real_actives.empty:
    an_list = sorted([str(int(a)) for a in df_real_actives["Annee"].dropna().unique() if str(a).replace('.','').isdigit()])
    annees_dispos += an_list
annee_selectionnee = st.sidebar.selectbox("📅 Année :", annees_dispos)

# Application des filtres
data_affichee = df_real_actives.copy()
if not data_affichee.empty:
    if secteur_selectionne != "Tous":
        data_affichee = data_affichee[data_affichee["Secteur"] == secteur_selectionne]
    if type_selectionne != "Tous":
        data_affichee = data_affichee[data_affichee["Type_Engag"] == type_selectionne]
    if annee_selectionnee != "Toutes":
        data_affichee = data_affichee[data_affichee["Annee"].astype(str).str.startswith(annee_selectionnee)]

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Couches Géographiques")
afficher_villages = st.sidebar.checkbox("🏘️ Afficher les Villages Impactés", value=True)
afficher_bureaux = st.sidebar.checkbox("🏢 Afficher les Sièges & Bureaux", value=True)
st.sidebar.markdown("---")

# Fiche Signalétique
st.sidebar.subheader("📋 Description de la Réalisation")

# Nommage explicite dans la liste déroulante (Nom + ID Projet)
if not data_affichee.empty:
    data_affichee["Libelle_Select"] = data_affichee.apply(lambda r: f"{r.get('Name','Projet')} ({r.get('ID_Projet','')})", axis=1)
    liste_options = ["📌 Toutes les réalisations"] + list(data_affichee["Libelle_Select"].unique())
    projet_choisi_libelle = st.sidebar.selectbox("Sélectionner une réalisation :", liste_options)
    
    if projet_choisi_libelle != "📌 Toutes les réalisations":
        points_zoom_fiche = data_affichee[data_affichee["Libelle_Select"] == projet_choisi_libelle]
        info = points_zoom_fiche.iloc[0]
        
        annee_val = str(int(info.get('Annee'))) if (pd.notna(info.get('Annee')) and str(info.get('Annee')).replace('.','').isdigit()) else str(info.get('Annee', '-'))
        services_val = str(info.get('Services', '-')) if pd.notna(info.get('Services')) and str(info.get('Services')).strip() != "" else "-"
        budget_val = str(info.get('Budget', '-')) if pd.notna(info.get('Budget')) and str(info.get('Budget')).strip() != "" else "-"
        group_val = str(info.get('Groupement', '-')) if pd.notna(info.get('Groupement')) and str(info.get('Groupement')).strip() != "" else "-"

        tableau_html = f"""
        <table style="width:100%; border-collapse: collapse; font-size: 13px; margin-top: 6px;">
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Nom</td>
                <td style="padding: 5px; font-weight: bold; color: #0f172a;">{info.get('Name', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Code ID</td>
                <td style="padding: 5px; color: #0284c7; font-family: monospace; font-weight: bold;">{info.get('ID_Projet', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Secteur</td>
                <td style="padding: 5px; font-weight: 600;">{info.get('Secteur', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Engagement</td>
                <td style="padding: 5px;">{info.get('Type_Engag', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Groupement</td>
                <td style="padding: 5px;">{group_val}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Année</td>
                <td style="padding: 5px;">{annee_val}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Coordonnées</td>
                <td style="padding: 5px; font-size: 11px;">{round(float(info.get('Lat')), 4)}, {round(float(info.get('Longi')), 4)}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Services</td>
                <td style="padding: 5px;">{services_val}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                <td style="padding: 5px; font-weight: bold; color: #475569;">Budget</td>
                <td style="padding: 5px;">{budget_val}</td>
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
        st.sidebar.info("💡 Affichage de toutes les réalisations filtrées.")
else:
    points_zoom_fiche = pd.DataFrame()
    st.sidebar.warning("Aucune réalisation trouvée pour ces filtres.")

st.sidebar.markdown("---")
if st.sidebar.button("Déconnexion"):
    st.session_state["authentifie"] = False
    st.rerun()

# ---------------------------------------------------------
# 5. SECTION INDICATEURS CLÉS (KPIS DYNAMIQUES)
# ---------------------------------------------------------
st.markdown("##### 📈 **Indicateurs Clés des Réalisations**")

# Calcul dynamique des compteurs par secteur
nb_total = len(data_affichee)
nb_sante = len(data_affichee[data_affichee["Secteur"].str.contains("Sante|Santé", case=False, na=False)]) if not data_affichee.empty and "Secteur" in data_affichee.columns else 0
nb_eau = len(data_affichee[data_affichee["Secteur"].str.contains("Eau|Energie|Forage", case=False, na=False)]) if not data_affichee.empty and "Secteur" in data_affichee.columns else 0
nb_educ = len(data_affichee[data_affichee["Secteur"].str.contains("Educ|Éduc|Ecole|Institut", case=False, na=False)]) if not data_affichee.empty and "Secteur" in data_affichee.columns else 0
nb_eco = len(data_affichee[data_affichee["Secteur"].str.contains("Econ|Écon|Marche|Pain|Agri", case=False, na=False)]) if not data_affichee.empty and "Secteur" in data_affichee.columns else 0

kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)

def kpi_card(titre, valeur, icone, couleur_fond, couleur_texte):
    return f"""
    <div style="background-color: {couleur_fond}; border-left: 4px solid {couleur_texte}; border-radius: 6px; padding: 8px 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 10px;">
        <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">{titre}</div>
        <div style="font-size: 20px; font-weight: 800; color: {couleur_texte}; margin-top: 2px;">{icone} {valeur}</div>
    </div>
    """

with kpi_c1: st.markdown(kpi_card("Total Réalisations", nb_total, "📊", "#f8fafc", "#0f172a"), unsafe_allow_html=True)
with kpi_c2: st.markdown(kpi_card("Santé", nb_sante, "🏥", "#fef2f2", "#dc2626"), unsafe_allow_html=True)
with kpi_c3: st.markdown(kpi_card("Eau & Forages", nb_eau, "💧", "#f0f9ff", "#0284c7"), unsafe_allow_html=True)
with kpi_c4: st.markdown(kpi_card("Éducation", nb_educ, "🎓", "#fffbeb", "#d97706"), unsafe_allow_html=True)
with kpi_c5: st.markdown(kpi_card("Économie & Infrastr.", nb_eco, "🏪", "#f0fdf4", "#16a34a"), unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. MOTEUR DE SYMBIOLOGIE (ICÔNES & COULEURS PAR ENGAGEMENT)
# ---------------------------------------------------------
def get_symbologie(secteur_val, engag_val):
    sec = str(secteur_val).upper()
    eng = str(engag_val).upper()
    
    # 1. FORME / SYMBOLE INTÉRIEUR SELON LE SECTEUR
    if any(k in sec for k in ["SANTE", "SANTÉ"]):
        symbole = "+"
        font_size = "12px"
    elif any(k in sec for k in ["EAU", "ENERGIE", "FORAGE"]):
        symbole = "💧"
        font_size = "10px"
    elif any(k in sec for k in ["EDUC", "ÉDUC", "ECOLE", "INSTITUT"]):
        symbole = "🎓"
        font_size = "10px"
    elif any(k in sec for k in ["ECON", "ÉCON", "MARCHE", "PAIN"]):
        symbole = "🏪"
        font_size = "10px"
    else:
        symbole = "★"
        font_size = "10px"
        
    # 2. CODE COULEUR SELON LE TYPE D'ENGAGEMENT
    if "CDC 1" in eng or "CDC1" in eng:
        couleur = "#2563eb" # Bleu Royal
    elif "CDC 2" in eng or "CDC2" in eng:
        couleur = "#4338ca" # Indigo
    elif "VOLONTAIRE" in eng:
        couleur = "#16a34a" # Vert Émeraude
    elif "DOT" in eng or "REDEV" in eng:
        couleur = "#d97706" # Ambre / Cuivre
    else:
        couleur = "#64748b" # Gris Ardoise (Autres / État)
        
    return symbole, couleur, font_size

# ---------------------------------------------------------
# 7. DISPOSITION : CARTE DYNAMIQUE + LOGOS
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

    # 1. COUCHE VILLAGES IMPACTÉS
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
                    radius=5,
                    color="#047857",
                    fill=True,
                    fill_color="#10b981",
                    fill_opacity=0.9,
                    weight=1.5,
                    tooltip=f"<b>🏘️ Village : {nom_v}</b> ({id_v})",
                    popup=f"<b>Village : {nom_v}</b><br>Groupement : {group_v}<br>Chefferie : {cheff_v}"
                ).add_to(groupe_vil)
            else:
                folium.CircleMarker(
                    location=[lat_v, lon_v],
                    radius=3.5,
                    color="#94a3b8",
                    fill=True,
                    fill_color="#cbd5e1",
                    fill_opacity=0.3,
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
                <div style="background-color: #1e3a8a; border: 2px solid white; border-radius: 5px; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.4);">
                    <span style="color: white; font-size: 12px;">🏢</span>
                </div>
                """
                folium.Marker(
                    location=[lat_s, lon_s],
                    popup=f"<b>{nom_site}</b><br>Entité : {ent_site}",
                    tooltip=f"🏢 {nom_site} ({ent_site})",
                    icon=folium.DivIcon(html=office_icon_html, icon_size=(22, 22), icon_anchor=(11, 11))
                ).add_to(groupe_offices)
            else:
                office_dim_html = """
                <div style="background-color: rgba(148, 163, 184, 0.3); border: 1px dashed #94a3b8; border-radius: 5px; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 10px; opacity: 0.5;">🏢</span>
                </div>
                """
                folium.Marker(
                    location=[lat_s, lon_s],
                    tooltip=f"🏢 {nom_site} (Autre site)",
                    icon=folium.DivIcon(html=office_dim_html, icon_size=(18, 18), icon_anchor=(9, 9))
                ).add_to(groupe_offices)
            
        groupe_offices.add_to(m)

    # 3. COUCHE RÉALISATIONS (MARQUEURS RÉDUITS 16px & SYMBIOLOGIE DOUBLE)
    groupe_real = folium.FeatureGroup(name="📍 Réalisations Communautaires", show=True)
    for idx, row in data_realisations.iterrows():
        lat_r, lon_r = float(row["Lat"]), float(row["Longi"])
        est_du_site = appartient_a_entreprise(row, entreprise_actuelle)
        
        # Filtre additionnel si on est sur l'entreprise active
        if est_du_site and not data_affichee.empty and (row["ID_Projet"] not in data_affichee["ID_Projet"].values):
            continue

        nom_projet = row.get("Name", "Réalisation")
        id_proj = row.get("ID_Projet", "N/A")
        type_eng = row.get("Type_Engag", "N/A")
        sec_proj = row.get("Secteur", "N/A")
        
        symbole, couleur_engag, font_sz = get_symbologie(sec_proj, type_eng)
        
        if est_du_site:
            coords_focus.append([lat_r, lon_r])
            # Marqueur compact actif (16px x 16px)
            icon_html = f"""
            <div style="
                background-color: white; 
                border: 1.5px solid {couleur_engag}; 
                border-radius: 50%; 
                width: 16px; 
                height: 16px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);">
                <span style="color: {couleur_engag}; font-size: {font_sz}; font-weight: bold; line-height: 1;">{symbole}</span>
            </div>
            """
            folium.Marker(
                location=[lat_r, lon_r],
                popup=f"<b>{nom_projet}</b> ({id_proj})<br>Secteur : {sec_proj}<br>Engagement : {type_eng}",
                tooltip=f"{nom_projet} [{id_proj}] - {type_eng}",
                icon=folium.DivIcon(html=icon_html, icon_size=(16, 16), icon_anchor=(8, 8))
            ).add_to(groupe_real)
        else:
            # Marqueur estompé hors focus
            dim_real_html = f"""
            <div style="
                background-color: rgba(241, 245, 249, 0.4); 
                border: 1px solid rgba(148, 163, 184, 0.35); 
                border-radius: 50%; 
                width: 12px; 
                height: 12px; 
                display: flex; 
                align-items: center; 
                justify-content: center;">
                <span style="color: rgba(148, 163, 184, 0.5); font-size: 8px;">{symbole}</span>
            </div>
            """
            folium.Marker(
                location=[lat_r, lon_r],
                tooltip=f"{nom_projet} ({type_eng})",
                icon=folium.DivIcon(html=dim_real_html, icon_size=(12, 12), icon_anchor=(6, 6))
            ).add_to(groupe_real)

    groupe_real.add_to(m)

    # Recentrage dynamique
    if not points_zoom_fiche.empty:
        m.location = [float(points_zoom_fiche.iloc[0]["Lat"]), float(points_zoom_fiche.iloc[0]["Longi"])]
        m.zoom_start = 14
    elif coords_focus:
        m.fit_bounds(coords_focus, padding=(25, 25))
    else:
        m.location = [-11.65, 27.28]
        m.zoom_start = 10

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=580, key=f"carte_{entreprise_actuelle}_{len(coords_focus)}")

with col_logos:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    
    # 1. Logo Fondation Vinmart
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 4px;'>FONDATION</p>", unsafe_allow_html=True)
    p_fond = get_image_path("logo_vinmart_fondation")
    if p_fond:
        st.image(p_fond, use_container_width=True)
    else:
        st.markdown("<div style='border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; background: #f8fafc;'><b style='color: #1e3a8a; font-size: 11px;'>Fondation Vinmart</b></div>", unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    
    # 2. Logo Groupe Vinmart
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #64748b; margin-bottom: 4px;'>GROUPE</p>", unsafe_allow_html=True)
    p_grp = get_image_path("logo_vinmart_groupe")
    if p_grp:
        st.image(p_grp, use_container_width=True)
    else:
        st.markdown("<div style='border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; background: #f8fafc;'><b style='color: #0f172a; font-size: 11px;'>Groupe Vinmart</b></div>", unsafe_allow_html=True)

    # 3. LÉGENDE RAPIDE DES COULEURS D'ENGAGEMENT
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: left; font-size: 11px; color: #475569; background: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;">
        <b>Légende Engagement :</b><br>
        <span style="color: #2563eb;">■</span> CDC 1<br>
        <span style="color: #4338ca;">■</span> CDC 2<br>
        <span style="color: #16a34a;">■</span> Volontaire<br>
        <span style="color: #d97706;">■</span> Dot & Redev.<br>
        <span style="color: #64748b;">■</span> Autres / État
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. REGISTRE COMPLET EN BAS DE PAGE
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Registre des Réalisations")
st.dataframe(data_affichee, use_container_width=True)