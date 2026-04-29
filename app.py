import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="MyData Monitoring", page_icon="📊")

# Dictionnaire des domaines avec leurs sous-titres exacts
DOMAINES = {
    "Vente": "",
    "Stock": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(stock, ral, mouvement, rupture)</span>",
    "Bornes": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(entrées magasin)</span>",
    "Détaxe": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(bordereaux)</span>",
    "Productivité entrepôt": "<br><span style='font-weight: normal; font-size: 12px; color: #666;'>(Avex, heures)</span>"
}

# --- FONCTIONS HTML ---
def generer_html_vert(date):
    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><span style="color: #7B61FF;">📊 MyData</span> | Données du {date} Disponibles</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; border-left: 5px solid #4CAF50;">
            <p style="font-weight: bold;">✅ Les données du {date} sont disponibles.</p>
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
            <p style="font-weight: bold;">⚠️ Suite à des retards, les données sont indisponibles pour :</p>
            <ul>{liste}</ul>
            <p>L'ensemble des autres rapports est intégralement disponible.</p>
        </div>
    </div>
    """

def generer_html_tableau(date, statuts):
    # On construit les lignes du tableau dynamiquement
    lignes_html = ""
    for domaine, sous_titre in DOMAINES.items():
        # Couleurs selon le statut
        couleur_pbi = "#2E7D32" if "disponible" in statuts[domaine]["PBI"] else "#E65100"
        couleur_deci = "#2E7D32" if "disponible" in statuts[domaine]["Deci"] else "#E65100"
        couleur_bordure = "#81C784" if "disponible" in statuts[domaine]["PBI"] else "#FFB74D"
        
        lignes_html += f"""
        <tr>
            <td style="padding: 10px; border: 1px solid #e0e0e0; font-weight: bold; border-left: 4px solid {couleur_bordure};">{domaine} {sous_titre}</td>
            <td style="padding: 10px; border: 1px solid #e0e0e0; text-align: center; color: {couleur_pbi}; font-weight: bold;">{statuts[domaine]['PBI']}</td>
            <td style="padding: 10px; border: 1px solid #e0e0e0; text-align: center; color: {couleur_deci}; font-weight: bold;">{statuts[domaine]['Deci']}</td>
        </tr>
        """

    return f"""
    <div style="background-color: #f0f2f5; padding: 20px; font-family: Arial, sans-serif;">
        <div style="background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h2 style="margin: 0; color: #000;"><span style="color: #7B61FF;">📊 MyData</span> | Retard sur les Données du {date}</h2>
        </div>
        <div style="background-color: white; border-radius: 8px; padding: 20px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
            <p style="font-weight: bold;">⚠️ Suite à des retards dans les traitements, les données sont incomplètes.</p>
        </div>
        <table style="width: 100%; background-color: white; border-collapse: collapse; border: 1px solid #e0e0e0; font-size: 14px;">
            <tr style="background-color: #f9f9f9;">
                <th style="padding: 10px; border: 1px solid #e0e0e0; text-align: left;">Domaine</th>
                <th style="padding: 10px; border: 1px solid #e0e0e0;">Power BI</th>
                <th style="padding: 10px; border: 1px solid #e0e0e0;">Décisionnel</th>
            </tr>
            {lignes_html}
        </table>
    </div>
    """

# --- INTERFACE UTILISATEUR ---
st.title("MyData Alerte Mobile 📱")

mode = st.radio("Statut des rapports :", ["Tout OK ✅", "Partiel ⚠️", "Retard Global 🚨"])
date_sel = datetime.now().strftime("%d %B")

rapports_selectionnes = []
statuts_tableau = {}

if mode == "Partiel ⚠️":
    rapports_selectionnes = st.multiselect("Sélectionnez les rapports KO :", 
                                         ["SUIVI VENTES UNITAIRES", "FLASH MARQUES PROPRES", "SUIVI DES STOCKS"])

elif mode == "Retard Global 🚨":
    st.markdown("### Configurer le tableau des statuts :")
    st.info("Par défaut tout est 'disponible', modifie uniquement ce qui est en retard.")
    
    # Interface pour choisir le statut de chaque ligne
    for domaine in DOMAINES.keys():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{domaine}**")
        with col2:
            pbi = st.selectbox(f"PBI {domaine}", ["✅ disponible", "⚠️ en cours"], label_visibility="collapsed")
        with col3:
            deci = st.selectbox(f"Deci {domaine}", ["✅ disponible", "⚠️ en cours"], label_visibility="collapsed")
        
        # On sauvegarde les choix dans le dictionnaire
        statuts_tableau[domaine] = {"PBI": pbi, "Deci": deci}

st.markdown("---")

if st.button("🚀 ENVOYER L'ALERTE", type="primary"):
    try:
        if mode == "Tout OK ✅":
            sujet, html = f"POWERBI : Données du {date_sel} Disponibles", generer_html_vert(date_sel)
        elif mode == "Partiel ⚠️":
            if not rapports_selectionnes:
                st.error("Sélectionne au moins un rapport !")
                st.stop()
            sujet, html = "POWERBI : Partiellement disponible", generer_html_orange(rapports_selectionnes, date_sel)
        else:
            sujet, html = f"POWERBI : Retard sur les Données du {date_sel}", generer_html_tableau(date_sel, statuts_tableau)

        msg = EmailMessage()
        msg['Subject'] = sujet
        msg['From'] = "mydata@galerieslafayette.com"
        msg['To'] = st.secrets["DESTINATAIRE"] 
        msg.add_alternative(html, subtype='html')

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(st.secrets["EMAIL_EXPEDITEUR"], st.secrets["PASSWORD"])
            server.send_message(msg)
        
        st.success("✅ C'est envoyé ! Vérifie ta boîte mail.")
    except Exception as e:
        st.error(f"Erreur : {e}")
