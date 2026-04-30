import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="MyData Monitoring", page_icon="📊")

URL_LOGO = "https://raw.githubusercontent.com/uvsq22103456/monitoring_dataops/main/logo.png"

# Tes textes d'origine conservés à 100%
DOMAINES = {
    "Vente": "",
    "Stock": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(stock, ral, mouvement, rupture)</span>",
    "Bornes": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(entrées magasin)</span>",
    "Détaxe": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(bordereaux)</span>",
    "Productivité entrepôt": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(Avex, heures)</span>"
}

# --- CALCUL DE LA DATE (CALENDRIER) ---
hier_par_defaut = datetime.now() - timedelta(days=1)
date_choisie = st.date_input("📅 Sélectionner la date des données :", hier_par_defaut)

mois_fr = {
    "January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril",
    "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août",
    "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"
}
date_str = f"{date_choisie.strftime('%d')} {mois_fr[date_choisie.strftime('%B')]}"

# --- FONCTION TABLEAU (DESIGN PASTILLES) ---
def generer_html_tableau(date, statuts, titre, texte_alerte=None):
    lignes_html = ""
    for domaine, sous_titre in DOMAINES.items():
        # Style Power BI
        is_pbi_ok = "disponible" in statuts[domaine]["PBI"]
        style_pbi = "background-color: #E8F5E9; color: #2E7D32; border-radius: 4px; padding: 4px 8px;" if is_pbi_ok else "background-color: #FFF3E0; color: #E65100; border-radius: 4px; padding: 4px 8px;"
        
        # Style Décisionnel
        is_deci_ok = "disponible" in statuts[domaine]["Deci"]
        style_deci = "background-color: #E8F5E9; color: #2E7D32; border-radius: 4px; padding: 4px 8px;" if is_deci_ok else "background-color: #FFF3E0; color: #E65100; border-radius: 4px; padding: 4px 8px;"
        
        # Bordure de ligne
        bordure_gauche = "5px solid #4CAF50" if (is_pbi_ok and is_deci_ok) else "5px solid #FF9800"

        lignes_html += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; border-left: {bordure_gauche};">{domaine} {sous_titre}</td>
            <td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center;">
                <span style="{style_pbi}">{statuts[domaine]['PBI']}</span>
            </td>
            <td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center;">
                <span style="{style_deci}">{statuts[domaine]['Deci']}</span>
            </td>
        </tr>
        """
    
    alerte_box = f'<div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; margin-bottom: 15px;"><p style="font-weight: bold;">{texte_alerte}</p></div>' if texte_alerte else ""

    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | {titre} {date}</h2>
        </div>
        {alerte_box}
        <table style="width: 100%; background-color: white; border-collapse: collapse; border: 1px solid #e0e0e0; font-size: 14px;">
            <thead>
                <tr style="background-color: #f9f9f9;">
                    <th style="padding: 12px; border: 1px solid #e0e0e0; text-align: left;">Domaine</th>
                    <th style="padding: 12px; border: 1px solid #e0e0e0;">Power BI</th>
                    <th style="padding: 12px; border: 1px solid #e0e0e0;">Décisionnel</th>
                </tr>
            </thead>
            <tbody>{lignes_html}</tbody>
        </table>
    </div>
    """

def generer_html_orange(rapports, date):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | Données du {date} partiellement disponibles</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #FF9800;">
            <p style="font-weight: bold;">⚠️ Suite à des retards, les données sont indisponibles pour :</p>
            <ul>{liste}</ul>
            <p>L'ensemble des autres rapports est intégralement disponible.</p>
        </div>
    </div>
    """

# --- INTERFACE ---
st.subheader(f"📅 Statut pour le : {date_str}")
mode = st.radio("Statut des rapports :", ["Tout OK ✅", "Partiel ⚠️", "Retard Global 🚨"])

statuts_tableau = {}
rapports_ko = []

if mode == "Tout OK ✅":
    for dom in DOMAINES.keys(): 
        statuts_tableau[dom] = {"PBI": "✅ disponible", "Deci": "✅ disponible"}

elif mode == "Partiel ⚠️":
    rapports_ko = st.multiselect("Sélectionnez les rapports KO :", ["SUIVI VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"])

elif mode == "Retard Global 🚨":
    st.info("Tout est dispo par défaut. Modifie juste ce qui ne l'est pas.")
    for domaine in DOMAINES.keys():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: st.write(f"**{domaine}**")
        with col2: pbi = st.selectbox(f"PBI {domaine}", ["✅ disponible", "⚠️ en cours"], index=0, key=f"r_pbi_{domaine}", label_visibility="collapsed")
        with col3: deci = st.selectbox(f"Deci {domaine}", ["✅ disponible", "⚠️ en cours"], index=0, key=f"r_deci_{domaine}", label_visibility="collapsed")
        statuts_tableau[domaine] = {"PBI": pbi, "Deci": deci}

if st.button("🚀 ENVOYER L'ALERTE", type="primary"):
    try:
        if mode == "Tout OK ✅":
            sujet = f"🟢 MYDATA : Données du {date_str} Disponibles"
            html = generer_html_tableau(date_str, statuts_tableau, "Données Disponibles")
        elif mode == "Partiel ⚠️":
            sujet, html = f"🟠 MYDATA : Partiellement disponible ({date_str})", generer_html_orange(rapports_ko, date_str)
        else:
            sujet = f"🔴 MYDATA : Retard sur les Données du {date_str}"
            html = generer_html_tableau(date_str, statuts_tableau, "Retard sur les Données", "⚠️ Suite à des retards dans les traitements, les données sont incomplètes.")

        msg = EmailMessage()
        msg['Subject'] = sujet
        msg['From'] = "mydata@galerieslafayette.com"
        msg['Reply-To'] = "mydata@galerieslafayette.com"
        msg['To'] = st.secrets["EMAIL_EXPEDITEUR"]
        msg['Bcc'] = st.secrets["DESTINATAIRE"]
        msg.add_alternative(html, subtype='html')

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(st.secrets["EMAIL_EXPEDITEUR"], st.secrets["PASSWORD"])
            server.send_message(msg)
        st.success(f"✅ Alerte envoyée !")
    except Exception as e:
        st.error(f"Erreur : {e}")
