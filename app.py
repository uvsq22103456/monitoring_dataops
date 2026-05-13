import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os
from zoneinfo import ZoneInfo

# --- CONFIGURATION ---
st.set_page_config(page_title="MyData Monitoring", page_icon="📊", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)
URL_LOGO = "https://raw.githubusercontent.com/uvsq22103456/monitoring_dataops/main/logo.png"
FICHIER_HISTORIQUE = "historique_alertes.csv"

DOMAINES = {
    "Vente": "",
    "Stock": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(stock, ral, mouvement, rupture)</span>",
    "Bornes": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(entrées magasin)</span>",
    "Détaxe": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(bordereaux)</span>",
    "Productivité entrepôt": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(Avex, heures)</span>"
}
LISTE_IMPACTS = [
    "Données Incomplètes", 
    "Retard Global", 
    "Retard STOCK", 
    "Retard Ventes", 
    "Pas de données Stock",
    "START Ko",
    "➕ AUTRE (Saisie libre)"
]

# Ta liste brute (j'ai ajouté le .sort() pour que ce soit rangé de A à Z)
LISTE_RAPPORTS_BRUTE = [
    "1001L - Mariage", "Activité par Tranche Horaire", "Baignoire", "Baignoire client par magasin", 
    "BORNES-ALERTING", "C&C - Pilotage Stratégique", "CA Digital", "CA Horaire Digital", 
    "CA Louis Vuitton", "Cockpit monétique e-commerce", "Commerce dates actualisation", "CRM", 
    "Détection des Fraudes - Scénarios Remboursement", "Digital Dates d'actualisation", 
    "FABRIC SURVEILLANCE CAPACITY (HUB)", "FABRIC USAGE METRICS", "Flash activité", 
    "Flash marque propre", "Flash Réseau & Co", "Go For Good", "GROUPES AD - LICENCES", 
    "GROUPES AD", "KPI Fid & Contactabilité - Suivi d'activité Parc Magasins", "Marque Propre", 
    "Métriques d'utilisation PowerBI", "Montée en ligne", "My Data catalogue", "MyDataset Commerce", 
    "MyDataset Digital", "MyDataset Finance", "MyDataset Flash", "MyDataset International", 
    "MyDataset Supply", "Ouverture tiroir caisse", "Performance business hebdo", "Pilotage beauté", 
    "Pilotage des contributions financières", "Pilotage Flux aller & retour E-commerce", 
    "Pilotage managérial", "Pilotage marge", "Pilotage mensuel performance magasin - Clients", 
    "PIT - Pilotage IT", "Présence des forces de vente", "PVE Pilotage Business", 
    "Qualité de données - Hiérarchie Manager", "Reporting Check saisie coordonnée client à l'adhesion", 
    "Retouches pour Magasin", "Retouches pour Reseau", "ROPO", "Ship From Store", "START", "START HSM", 
    "Statistiques moyennes de remboursements", "STOCK_GL", "Suivi activité HSM", "Suivi CA tracé Marchandise", 
    "Suivi complétude surface", "Suivi de l'activité d'enrichissement du PIM", 
    "Suivi de la démarque connue et inconnue", "Suivi des Cartes Cadeaux Partenaires", 
    "SUIVI DES COUTS MSTR", "Suivi des données CRM", "Suivi des partenaires BTB", 
    "Suivi des performances marché et GL", "Suivi des rapprochements VAD", "Suivi des ventes unitaires", 
    "Suivi détaxe", "SUIVI ECART SOURCING", "Suivi hors marchandises", "Bilan de collection", 
    "Wellness", "Suivi mensuel programme fid", "Suivi performance commerciale", "Suivi Performance Stock", 
    "Suivi Qualité de données", "SUIVI QUALITE DE SERVICE", "Typologie des caisses", "Dataset_BHV", 
    "Pilotage mensuel Performance Magasins", "Suivi SFS RESEAU", "Suivi audience Power BI", 
    "Gestion des coûts GCP"
]


LISTE_RAPPORTS_BRUTE.sort()

# On ajoute l'option "Autre" à la fin pour la flexibilité
LISTE_RAPPORTS = LISTE_RAPPORTS_BRUTE + ["➕ AUTRE (Saisie libre)"]
# --- NOUVEAU : FONCTION DE SAUVEGARDE ENRICHIE ---
def sauvegarder_historique(date_donnees, impact_utilisateur, app_origine="N/A", source="N/A", action_corrective="N/A"):
    
    maintenant = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M:%S")
    
    # On crée une ligne propre
    nouvelle_ligne = {
        "Date de l'alerte": maintenant, 
        "Date des données": date_donnees, 
        "Impact utilisateur": impact_utilisateur,
        "APP (Origine)": app_origine,
        "Source": source,
        "Action Corrective": action_corrective
        
    }
    
    nouveau_statut = pd.DataFrame([nouvelle_ligne])
    
    if os.path.exists(FICHIER_HISTORIQUE):
        nouveau_statut.to_csv(FICHIER_HISTORIQUE, mode='a', header=False, index=False)
    else:
        nouveau_statut.to_csv(FICHIER_HISTORIQUE, index=False)

# --- CALCUL DE LA DATE ET DU "J-X" ---
aujourd_hui = datetime.now().date()
hier_par_defaut = aujourd_hui - timedelta(days=1)
date_choisie = st.date_input("📅 Sélectionner la date des données :", hier_par_defaut)

ecart_jours = (aujourd_hui - date_choisie).days
j_str = f"J-{ecart_jours}" if ecart_jours > 0 else "J-0"

mois_fr = {
    "January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril",
    "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août",
    "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"
}
date_str = f"{date_choisie.strftime('%d')} {mois_fr[date_choisie.strftime('%B')]}"

# --- FONCTIONS HTML (INTACTES) ---
def generer_html_tableau(date, statuts, titre, texte_alerte=None):
    lignes_html = ""
    for domaine, sous_titre in DOMAINES.items():
        is_pbi_ok = "disponible" in statuts[domaine]["PBI"]
        couleur_pbi = "#2E7D32" if is_pbi_ok else "#E65100"
        is_deci_ok = "disponible" in statuts[domaine]["Deci"]
        couleur_deci = "#2E7D32" if is_deci_ok else "#E65100"
        bordure_gauche = "5px solid #4CAF50" if (is_pbi_ok and is_deci_ok) else "5px solid #FF9800"

        lignes_html += f"""<tr><td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; border-left: {bordure_gauche}; text-align: left;">{domaine} {sous_titre}</td><td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: {couleur_pbi}; font-weight: bold;">{statuts[domaine]['PBI']}</td><td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: {couleur_deci}; font-weight: bold;">{statuts[domaine]['Deci']}</td></tr>"""
    
    alerte_box = f"""<div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; margin-bottom: 15px;"><p style="font-weight: bold;">{texte_alerte}</p></div>""" if texte_alerte else ""

    return f"""<div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;"><div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;"><h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | {titre} {date}</h2></div>{alerte_box}<table style="width: 100%; background-color: white; border-collapse: collapse; border: 1px solid #e0e0e0; font-size: 14px;"><thead><tr style="background-color: #f9f9f9;"><th style="padding: 12px; border: 1px solid #e0e0e0; text-align: left;">Domaine</th><th style="padding: 12px; border: 1px solid #e0e0e0; text-align: center;">Power BI</th><th style="padding: 12px; border: 1px solid #e0e0e0; text-align: center;">Décisionnel</th></tr></thead><tbody>{lignes_html}</tbody></table></div>"""

def generer_html_liste_ok(rapports, date, type_j):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""<div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;"><div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;"><h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | {type_j} Intégralement disponible</h2></div><div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #4CAF50;"><p style="font-weight: bold;">✅ Les rapports suivants sont maintenant à jour avec le {type_j} ({date}) :</p><ul style="list-style-type: none; padding-left: 0; font-weight: bold;">{liste}</ul><p>Merci de votre compréhension</p></div></div>"""

def generer_html_orange(rapports, type_j, message_alerte):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""<div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;"><div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;"><h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | {type_j} partiellement disponible</h2></div><div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #FF9800;"><p style="font-weight: bold;">{message_alerte}</p><ul>{liste}</ul><p>L'ensemble des autres rapports est intégralement disponible.</p></div></div>"""

# ==========================================
# --- CRÉATION DES ONGLETS (TABS) ---
# ==========================================
tab1, tab2 = st.tabs(["🚀 Créer une Alerte", "🗄️ Historique & Incidents"])

# ==========================================
# --- ONGLET 1 : L'APPLICATION PRINCIPALE ---
# ==========================================
with tab1:
    st.subheader(f"Statut pour le : {date_str} ({j_str})")
    mode = st.radio("Statut des rapports :", ["Tout OK ✅", "Partiel ⚠️", "Retard Global 🚨"])

    statuts_tableau = {}
    rapports_ko_ok = []
    format_ok = ""
    sujet_mail = ""
    html_mail = "" 
    
    # Variables pour le fichier d'historique (par défaut "N/A" si tout va bien)
    app_origine = "N/A"
    source_incident = "N/A"
    action_cor = "N/A"
    statut_res = "N/A"
    impact_propre = "Données Intégrales"

    # -- LOGIQUE DE CHOIX --
    if mode == "Tout OK ✅":
        impact_propre = "Données Intégrales"
        format_ok = st.selectbox("Format du mail :", ["Tableau complet", "Liste de rapports"])
        if format_ok == "Liste de rapports":
            rapports_ko_ok = st.multiselect("Rapports à afficher :", ["SUIVI DES VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"], default=["SUIVI DES VENTES UNITAIRES", "FLASH MARQUES PROPRES"])
            sujet_mail, html_mail = f"🟢 MYDATA : {j_str} Intégralement disponible", generer_html_liste_ok(rapports_ko_ok, date_str, j_str)
        else:
            for dom in DOMAINES.keys(): statuts_tableau[dom] = {"PBI": "✅ disponible", "Deci": "✅ disponible"}
            sujet_mail, html_mail = f"🟢 MYDATA : Données du {date_str} Disponibles", generer_html_tableau(date_str, statuts_tableau, "Données Disponibles")

    elif mode == "Partiel ⚠️":
        impact_propre = "Données Incomplètes"
        
        # 1. On trie et on utilise la GRANDE liste au lieu de l'ancienne petite liste
        LISTE_RAPPORTS_BRUTE.sort()
        
        # 2. Le multiselect avec la barre de recherche native de Streamlit
        st.write("💡 *Astuce : Cliquez et tapez les premières lettres ou des mots du rapport pour le trouver.*")
        rapports_ko_ok = st.multiselect("Sélectionnez les rapports KO :", LISTE_RAPPORTS_BRUTE)
        
        # 3. L'astuce pour les rapports "en cours de route"
        nouveaux_rapports = st.text_input("✍️ Un autre rapport KO ? (Séparez par une virgule si plusieurs)")
        
        # 4. On fusionne les deux listes pour le mail et le CSV
        liste_finale = rapports_ko_ok
        if nouveaux_rapports:
            # On ajoute les noms tapés à la main à la liste
            extra = [r.strip() for r in nouveaux_rapports.split(",")]
            liste_finale = liste_finale + extra
        
        texte_perso = st.text_input("Message d'alerte (modifiable) :", "⚠️ Suite à des retards, les données sont indisponibles pour :")
        
        # On transforme la liste en texte propre pour le mail et le CSV (C'est ça qui ira dans app_origine)
        rapports_texte = ", ".join(liste_finale)
        
        sujet_mail = f"🟠 MYDATA : Partiellement disponible ({j_str})"
        
        # On passe la 'liste_finale' à ta fonction de mail
        html_mail = generer_html_orange(liste_finale, j_str, texte_perso)
    elif mode == "Retard Global 🚨":
        impact_propre = "Retard Global" # Le texte exact de ton Power BI
        texte_perso = st.text_input("Message d'alerte (modifiable) :", "⚠️ Suite à des retards dans les traitements, les données sont incomplètes.")
        st.info("Décochez simplement les cases en retard dans le tableau ci-dessous :")
        
        # Tableau interactif (Le design compact)
        donnees_tableau = {"Domaine": list(DOMAINES.keys()), "Power BI ✅": [True]*len(DOMAINES), "Décisionnel ✅": [True]*len(DOMAINES)}
        df_modifie = st.data_editor(pd.DataFrame(donnees_tableau), hide_index=True, use_container_width=True, disabled=["Domaine"])

        for index, row in df_modifie.iterrows():
            domaine = row["Domaine"]
            pbi = "✅ disponible" if row["Power BI ✅"] else "⚠️ en cours"
            deci = "✅ disponible" if row["Décisionnel ✅"] else "⚠️ en cours"
            statuts_tableau[domaine] = {"PBI": pbi, "Deci": deci}

        sujet_mail, html_mail = f"🔴 MYDATA : Retard sur les Données du {date_str}", generer_html_tableau(date_str, statuts_tableau, "Retard sur les Données", texte_perso)
    # -- APERÇU DU MAIL --
    with st.expander("👀 Voir l'aperçu du mail avant envoi", expanded=False):
        st.write(f"**Sujet de l'email :** {sujet_mail}")
        components.html(html_mail, height=450, scrolling=True)
        
    # --- NOUVEAU : BLOC TECHNIQUE (INVISIBLE DANS LE MAIL, JUSTE POUR L'HISTORIQUE) ---
    if mode != "Tout OK ✅":
        st.markdown("---")
        st.markdown("### 🛠️ Renseignement de l'incident (Pour suivi QS)")
        st.caption("Ces informations ne seront PAS envoyées dans le mail, elles servent uniquement au Dashboard Power BI Qualité de Service.")

        colA, colB = st.columns(2)
        with colA:
            choix_impact = st.selectbox("Impact utilisateur :", LISTE_IMPACTS)
        
            if choix_impact == "➕ AUTRE (Saisie libre)":
                impact_final = st.text_input("Précisez l'impact personnalisé :")
            else:
                impact_final = choix_impact
    
            app_origine = st.text_input(
                "Origine :", 
                placeholder="Décrivez la cause (ex: Anomalie Lakehouse...)"
            )
        with colB:
            source_incident = st.selectbox("Source :", ["Intra data", "Extra data"])
            action_cor = st.text_input("Action corrective :", "Refresh des tables GCP et relance des datasets...")

   

    # -- BOUTONS D'ACTION --
    if mode != "Tout OK ✅":
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            envoi_mail = st.button("🚀 ENVOYER L'ALERTE (Mail)", type="primary", use_container_width=True)
        with col_btn2:
            envoi_silencieux = st.button("🔕 ENREGISTRER SANS MAIL (< 8h30)", use_container_width=True)
    else:
        envoi_mail = st.button("🚀 ENVOYER L'ALERTE (Mail)", type="primary", use_container_width=True)
        envoi_silencieux = False

    if envoi_mail:
        try:
            msg = EmailMessage()
            msg['Subject'] = sujet_mail
            msg['From'] = "mydata@galerieslafayette.com"
            msg['Reply-To'] = "mydata@galerieslafayette.com"
            #msg['To'] = st.secrets["EMAIL_EXPEDITEUR"]
            msg['Bcc'] = st.secrets["DESTINATAIRE"]
            msg.add_alternative(html_mail, subtype='html')

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(st.secrets["EMAIL_EXPEDITEUR"], st.secrets["PASSWORD"])
                server.send_message(msg)
            
            # Sauvegarde standard pour un vrai retard
            sauvegarder_historique(date_str, impact_propre, app_origine, source_incident, action_cor)
            
            st.success(f"✅ Alerte envoyée avec succès !")
            st.balloons()
        except Exception as e:
            st.error(f"Erreur : {e}")

    if envoi_silencieux:
        # Sauvegarde spéciale "Fantôme"
        sauvegarder_historique(date_str, "Sans impact", app_origine, source_incident, action_cor)
        st.success("🔕 Incident enregistré dans l'historique (Aucun mail envoyé) !")
        

# ==========================================
# --- ONGLET 2 : L'HISTORIQUE ---
# ==========================================
with tab2:
    st.markdown("### 🗄️ Registre des envois et Incidents")
    
    if os.path.exists(FICHIER_HISTORIQUE):
        try:
            df_historique = pd.read_csv(FICHIER_HISTORIQUE)
            
            st.write("💡 *Vous pouvez modifier les lignes (ex: passer un incident en 'Résolu') puis cliquer sur Sauvegarder.*")
            
            # Ton tableau éditable (C'est ton meilleur atout démo !)
            df_edite = st.data_editor(df_historique.iloc[::-1], use_container_width=True, hide_index=True, num_rows="dynamic")
            
            st.markdown("---")
            col_save, col_clear, col_download = st.columns([1, 1, 1])
            
            with col_save:
                if st.button("💾 Sauvegarder les modifications", type="primary"):
                    df_edite.iloc[::-1].to_csv(FICHIER_HISTORIQUE, index=False)
                    st.success("✅ Historique mis à jour !")
                    st.rerun()
            
            with col_clear:
                st.markdown("🗑️ **Vider le registre**")
                confirmation = st.checkbox("Confirmer la suppression totale")
                if confirmation:
                    if st.button("🚨 OUI, TOUT SUPPRIMER"):
                        if os.path.exists(FICHIER_HISTORIQUE):
                            os.remove(FICHIER_HISTORIQUE)
                        st.rerun()

            with col_download:
                st.markdown("📥 **Export**")
                with open(FICHIER_HISTORIQUE, "rb") as file:
                    st.download_button(
                        label="Télécharger le CSV",
                        data=file,
                        file_name="historique_alertes.csv",
                        mime="text/csv"
                    )
                        
        except pd.errors.ParserError:
            st.error("⚠️ Erreur de lecture du fichier.")
            if st.button("🔄 Réinitialiser le fichier"):
                os.remove(FICHIER_HISTORIQUE)
                st.rerun()
    else:
        st.info("Aucun historique pour le moment. Le registre se créera au premier envoi.")


    
