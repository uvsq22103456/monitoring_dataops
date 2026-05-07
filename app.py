import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import pandas as pd
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="MyData Monitoring", page_icon="📊", layout="centered")

URL_LOGO = "https://raw.githubusercontent.com/uvsq22103456/monitoring_dataops/main/logo.png"
FICHIER_HISTORIQUE = "historique_alertes.csv"

DOMAINES = {
    "Vente": "",
    "Stock": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(stock, ral, mouvement, rupture)</span>",
    "Bornes": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(entrées magasin)</span>",
    "Détaxe": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(bordereaux)</span>",
    "Productivité entrepôt": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(Avex, heures)</span>"
}

# --- FONCTION DE SAUVEGARDE HISTORIQUE ---
def sauvegarder_historique(date_donnees, type_alerte):
    maintenant = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nouveau_statut = pd.DataFrame([{"Date d'envoi": maintenant, "Date des données": date_donnees, "Statut de l'alerte": type_alerte}])
    
    if os.path.exists(FICHIER_HISTORIQUE):
        nouveau_statut.to_csv(FICHIER_HISTORIQUE, mode='a', header=False, index=False)
    else:
        nouveau_statut.to_csv(FICHIER_HISTORIQUE, index=False)

# --- CALCUL DE LA DATE ---
hier_par_defaut = datetime.now() - timedelta(days=1)
date_choisie = st.date_input("📅 Sélectionner la date des données :", hier_par_defaut)

mois_fr = {
    "January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril",
    "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août",
    "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"
}
date_str = f"{date_choisie.strftime('%d')} {mois_fr[date_choisie.strftime('%B')]}"

# --- FONCTIONS HTML (INTACTES) ---
# --- FONCTIONS HTML ---
def generer_html_tableau(date, statuts, titre, texte_alerte=None):
    lignes_html = ""
    for domaine, sous_titre in DOMAINES.items():
        is_pbi_ok = "disponible" in statuts[domaine]["PBI"]
        couleur_pbi = "#2E7D32" if is_pbi_ok else "#E65100"
        is_deci_ok = "disponible" in statuts[domaine]["Deci"]
        couleur_deci = "#2E7D32" if is_deci_ok else "#E65100"
        bordure_gauche = "5px solid #4CAF50" if (is_pbi_ok and is_deci_ok) else "5px solid #FF9800"

        lignes_html += f"<tr><td style='padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; border-left: {bordure_gauche}; text-align: left;'>{domaine} {sous_titre}</td><td style='padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: {couleur_pbi}; font-weight: bold;'>{statuts[domaine]['PBI']}</td><td style='padding: 12px; border: 1px solid #e0e0e0; text-align: center; color: {couleur_deci}; font-weight: bold;'>{statuts[domaine]['Deci']}</td></tr>"
    
    alerte_box = f'<div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; margin-bottom: 15px;"><p style="font-weight: bold;">{texte_alerte}</p></div>' if texte_alerte else ""
    return f"""<div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;"><div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;"><h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | {titre} {date}</h2></div>{alerte_box}<table style="width: 100%; background-color: white; border-collapse: collapse; border: 1px solid #e0e0e0; font-size: 14px;"><thead><tr style="background-color: #f9f9f9;"><th style="padding: 12px; border: 1px solid #e0e0e0; text-align: left;">Domaine</th><th style="padding: 12px; border: 1px solid #e0e0e0; text-align: center;">Power BI</th><th style="padding: 12px; border: 1px solid #e0e0e0; text-align: center;">Décisionnel</th></tr></thead><tbody>{lignes_html}</tbody></table></div>"""

def generer_html_liste_ok(rapports, date):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""<div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;"><div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;"><h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | POWERBI : J-1 Intégralement disponible</h2></div><div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #4CAF50;"><p style="font-weight: bold;">✅ Les rapports suivants sont maintenant à jour avec le J-1 ({date}) :</p><ul style="list-style-type: none; padding-left: 0; font-weight: bold;">{liste}</ul><p>Merci de votre compréhension</p></div></div>"""

def generer_html_orange(rapports):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""<div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;"><div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;"><h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | J-1 partiellement disponible</h2></div><div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #FF9800;"><p style="font-weight: bold;">⚠️ Suite à des retards, les données sont indisponibles pour :</p><ul>{liste}</ul><p>L'ensemble des autres rapports est intégralement disponible.</p></div></div>"""
# ==========================================
# --- CRÉATION DES ONGLETS (TABS) ---
# ==========================================
tab1, tab2 = st.tabs(["🚀 Créer une Alerte", "🗄️ Historique des envois"])

# ==========================================
# --- ONGLET 1 : L'APPLICATION PRINCIPALE ---
# ==========================================
with tab1:
    st.subheader(f"Statut pour le : {date_str}")
    mode = st.radio("Statut des rapports :", ["Tout OK ✅", "Partiel ⚠️", "Retard Global 🚨"])

    statuts_tableau = {}
    rapports_ko_ok = []
    format_ok = ""
    sujet_mail = ""
    html_mail = ""

    # -- LOGIQUE DE CHOIX --
    if mode == "Tout OK ✅":
        format_ok = st.selectbox("Format du mail :", ["Tableau complet", "Liste de rapports"])
        if format_ok == "Liste de rapports":
            rapports_ko_ok = st.multiselect("Rapports à afficher :", ["SUIVI DES VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"], default=["SUIVI DES VENTES UNITAIRES", "FLASH MARQUES PROPRES"])
            sujet_mail, html_mail = f"🟢 POWERBI : J-1 Intégralement disponible", generer_html_liste_ok(rapports_ko_ok, date_str)
        else:
            for dom in DOMAINES.keys(): statuts_tableau[dom] = {"PBI": "✅ disponible", "Deci": "✅ disponible"}
            sujet_mail, html_mail = f"🟢 POWERBI : Données du {date_str} Disponibles", generer_html_tableau(date_str, statuts_tableau, "Données Disponibles")

    elif mode == "Partiel ⚠️":
        rapports_ko_ok = st.multiselect("Sélectionnez les rapports KO :", ["SUIVI DES VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"])
        sujet_mail, html_mail = "🟠 POWERBI : Partiellement disponible", generer_html_orange(rapports_ko_ok)

    elif mode == "Retard Global 🚨":
        st.info("Tout est dispo par défaut. Modifie juste ce qui ne l'est pas.")
        for domaine in DOMAINES.keys():
            st.markdown(f"**🔹 {domaine}**")
            col1, col2 = st.columns(2)
            with col1: pbi = st.selectbox("Power BI", ["✅ disponible", "⚠️ en cours"], index=0, key=f"z_pbi_{domaine}")
            with col2: deci = st.selectbox("Décisionnel", ["✅ disponible", "⚠️ en cours"], index=0, key=f"z_deci_{domaine}")
            statuts_tableau[domaine] = {"PBI": pbi, "Deci": deci}
            st.markdown("---")
        sujet_mail, html_mail = f"🔴 POWERBI : Retard sur les Données du {date_str}", generer_html_tableau(date_str, statuts_tableau, "Retard sur les Données", "⚠️ Suite à des retards dans les traitements, les données sont incomplètes.")

    # -- APERÇU DU MAIL --
    with st.expander("👀 Voir l'aperçu du mail avant envoi", expanded=False):
        st.write(f"**Sujet de l'email :** {sujet_mail}")
        components.html(html_mail, height=450, scrolling=True)

    # -- BOUTON D'ENVOI --
    if st.button("🚀 ENVOYER L'ALERTE", type="primary", use_container_width=True):
        try:
            msg = EmailMessage()
            msg['Subject'] = sujet_mail
            msg['From'] = "mydata@galerieslafayette.com"
            msg['Reply-To'] = "mydata@galerieslafayette.com"
            msg['To'] = st.secrets["EMAIL_EXPEDITEUR"]
            msg['Bcc'] = st.secrets["DESTINATAIRE"]
            msg.add_alternative(html_mail, subtype='html')

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(st.secrets["EMAIL_EXPEDITEUR"], st.secrets["PASSWORD"])
                server.send_message(msg)
            
            # Action de succès
            sauvegarder_historique(date_str, mode) # On log dans le fichier CSV
            st.success(f"✅ Alerte envoyée avec succès !")
            st.balloons() # 🎉 Célébration
        except Exception as e:
            st.error(f"Erreur : {e}")

# ==========================================
# --- ONGLET 2 : L'HISTORIQUE ---
# ==========================================
with tab2:
    st.markdown("### 🗄️ Registre des envois")
    st.write("Retrouvez ici toutes les alertes envoyées via cette application.")
    
    if os.path.exists(FICHIER_HISTORIQUE):
        df_historique = pd.read_csv(FICHIER_HISTORIQUE)
        # On affiche le tableau en pleine largeur et inversé (les plus récents en haut)
        st.dataframe(df_historique.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Aucun historique pour le moment. Le registre se créera au premier envoi.")
