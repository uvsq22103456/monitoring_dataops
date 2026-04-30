import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="MyData Monitoring", page_icon="📊")

URL_LOGO = "https://raw.githubusercontent.com/uvsq22103456/monitoring_dataops/main/logo.png"

DOMAINES = {
    "Vente": "",
    "Stock": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(stock, ral, mouvement, rupture)</span>",
    "Bornes": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(entrées magasin)</span>",
    "Détaxe": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(bordereaux)</span>",
    "Productivité entrepôt": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(Avex, heures)</span>"
}

# --- CALCUL DE LA DATE J-1 EN FRANÇAIS ---
mois_fr = {
    "January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril",
    "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août",
    "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"
}
hier = datetime.now() - timedelta(days=1)
date_str = f"{hier.strftime('%d')} {mois_fr[hier.strftime('%B')]}"

# --- FONCTIONS HTML ---
def generer_html_liste_ok(rapports, date):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | Données du {date} OK</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #4CAF50;">
            <p style="font-weight: bold;">✅ Les rapports suivants sont à jour :</p>
            <ul>{liste}</ul>
        </div>
    </div>
    """

def generer_html_tableau(date, statuts, titre="Retard sur les Données"):
    lignes_html = ""
    for domaine, sous_titre in DOMAINES.items():
        # Style pour "disponible" (Vert) vs "en cours" (Orange)
        style_pbi = "background-color: #E8F5E9; color: #2E7D32;" if "disponible" in statuts[domaine]["PBI"] else "background-color: #FFF3E0; color: #E65100;"
        style_deci = "background-color: #E8F5E9; color: #2E7D32;" if "disponible" in statuts[domaine]["Deci"] else "background-color: #FFF3E0; color: #E65100;"
        
        lignes_html += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold;">{domaine} {sous_titre}</td>
            <td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; font-weight: bold; {style_pbi}">{statuts[domaine]['PBI']}</td>
            <td style="padding: 12px; border: 1px solid #e0e0e0; text-align: center; font-weight: bold; {style_deci}">{statuts[domaine]['Deci']}</td>
        </tr>
        """
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | {titre} {date}</h2>
        </div>
        <table style="width: 100%; background-color: white; border-collapse: collapse; border: 1px solid #e0e0e0;">
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
            <h2 style="margin: 0; color: #000;"><img src="{URL_LOGO}" height="35" style="vertical-align:middle;"> | J-1 partiel</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #FF9800;">
            <p style="font-weight: bold;">⚠️ Données indisponibles pour :</p>
            <ul>{liste}</ul>
        </div>
    </div>
    """

hier_par_defaut = datetime.now() - timedelta(days=1)
# 2. On affiche le calendrier (l'utilisateur peut changer s'il veut)
date_choisie = st.date_input("📅 Sélectionner la date des données concernées :", hier_par_defaut)


mois_fr = {
    "January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril",
    "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août",
    "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"
}
date_str = f"{date_choisie.strftime('%d')} {mois_fr[date_choisie.strftime('%B')]}"

# 4. On affiche un rappel visuel sur l'interface
st.subheader(f"Statut pour les flux du : {date_str}")
# --- INTERFACE UTILISATEUR ---
st.title("MyData Monitoring 📊")
st.subheader(f"📅 Données du {date_str}")

mode = st.radio("Statut des rapports :", ["Tout OK ✅", "Partiel ⚠️", "Retard Global 🚨"])

rapports_selectionnes = []
statuts_tableau = {}
format_success = "Tableau"

if mode == "Tout OK ✅":
    format_success = st.selectbox("Format du mail :", ["Tableau complet", "Liste simple"])
    if format_success == "Liste simple":
        rapports_selectionnes = st.multiselect("Rapports vérifiés :", ["SUIVI VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"], default=["SUIVI VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"])
    else:
        # On pré-remplit tout à disponible
        for dom in DOMAINES.keys(): statuts_tableau[dom] = {"PBI": "✅ disponible", "Deci": "✅ disponible"}

elif mode == "Partiel ⚠️":
    rapports_selectionnes = st.multiselect("Rapports KO :", ["SUIVI VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"])

elif mode == "Retard Global 🚨":
    for domaine in DOMAINES.keys():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: st.write(f"**{domaine}**")
        with col2: pbi = st.selectbox(f"PBI {domaine}", ["✅ disponible", "⚠️ en cours"], index=1, key=f"pbi_{domaine}", label_visibility="collapsed")
        with col3: deci = st.selectbox(f"Deci {domaine}", ["✅ disponible", "⚠️ en cours"], index=1, key=f"deci_{domaine}", label_visibility="collapsed")
        statuts_tableau[domaine] = {"PBI": pbi, "Deci": deci}

if st.button("🚀 ENVOYER L'ALERTE", type="primary"):
    try:
        if mode == "Tout OK ✅":
            sujet = f"🟢 MYDATA : Données du {date_str} Disponibles"
            html = generer_html_tableau(date_str, statuts_tableau, "Données Disponibles") if format_success == "Tableau complet" else generer_html_liste_ok(rapports_selectionnes, date_str)
        elif mode == "Partiel ⚠️":
            sujet, html = f"🟠 MYDATA : J-1 partiel ({date_str})", generer_html_orange(rapports_selectionnes, date_str)
        else:
            sujet, html = f"🔴 MYDATA : Retard sur les Données du {date_str}", generer_html_tableau(date_sel, statuts_tableau)

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
        st.success("✅ Mail envoyé avec succès !")
    except Exception as e:
        st.error(f"Erreur : {e}")
