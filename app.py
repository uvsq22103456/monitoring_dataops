import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="MyData Monitoring", page_icon="📊")

# --- FONCTIONS POUR GÉNÉRER LE HTML ---
def generer_html_vert(date):
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><span style="color: #7B61FF;">📊 MyData</span> | Données du {date} Disponibles</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #4CAF50;">
            <p style="font-weight: bold;">✅ Les rapports sont à jour.</p>
            <p>Merci de votre compréhension.</p>
        </div>
    </div>
    """

def generer_html_orange(rapports, date):
    liste = "".join([f"<li>{r}</li>" for r in rapports])
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><span style="color: #7B61FF;">📊 MyData</span> | J-1 partiellement disponible</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #FF9800;">
            <p style="font-weight: bold;">⚠️ Données indisponibles pour :</p>
            <ul>{liste}</ul>
            <p>Le reste est disponible.</p>
        </div>
    </div>
    """

def generer_html_tableau(date):
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><span style="color: #7B61FF;">📊 MyData</span> | Retard Global {date}</h2>
        </div>
        <table style="width: 100%; background-color: white; border-collapse: collapse; border: 1px solid #e0e0e0;">
            <tr style="background-color: #f9f9f9;">
                <th style="padding: 10px; border: 1px solid #e0e0e0; text-align: left;">Domaine</th>
                <th style="padding: 10px; border: 1px solid #e0e0e0;">Statut</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #e0e0e0; font-weight: bold;">Vente / Stock</td>
                <td style="padding: 10px; border: 1px solid #e0e0e0; text-align: center; color: #E65100;">⚠️ En cours</td>
            </tr>
        </table>
    </div>
    """

# --- INTERFACE UTILISATEUR ---
st.title("MyData Alerte Mobile 📱")

mode = st.radio("Statut des rapports :", ["Tout OK ✅", "Partiel ⚠️", "Retard Global 🚨"])
date_sel = datetime.now().strftime("%d/%m/%Y")

rapports_selectionnes = []
if mode == "Partiel ⚠️":
    rapports_selectionnes = st.multiselect("Sélectionnez les rapports KO :", 
                                         ["SUIVI VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"])

if st.button("🚀 ENVOYER L'ALERTE", type="primary"):
    try:
        # On prépare le contenu selon le choix
        if mode == "Tout OK ✅":
            sujet, html = "POWERBI : Rapports OK", generer_html_vert(date_sel)
        elif mode == "Partiel ⚠️":
            if not rapports_selectionnes:
                st.error("Sélectionne au moins un rapport !")
                st.stop()
            sujet, html = "POWERBI : Partiellement disponible", generer_html_orange(rapports_selectionnes, date_sel)
        else:
            sujet, html = "POWERBI : Retard Global", generer_html_tableau(date_sel)

        # Config du mail
        msg = EmailMessage()
        msg['Subject'] = sujet
        msg['From'] = "mydata@galerieslafayette.com"
        msg['To'] = st.secrets["DESTINATAIRE"] # On pourra le changer dans les secrets
        msg.add_alternative(html, subtype='html')

        # ENVOI VIA LES SECRETS (COFFRE-FORT)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(st.secrets["EMAIL_EXPEDITEUR"], st.secrets["PASSWORD"])
            server.send_message(msg)
        
        st.success("C'est envoyé ! Vérifie ta boîte mail.")
    except Exception as e:
        st.error(f"Erreur : {e}")
