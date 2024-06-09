from pushbullet import Pushbullet
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time

# Configurer les options pour le mode headless
options = Options()
options.add_argument('--headless')  # Activer le mode headless si nécessaire

# Ajouter des arguments pour ignorer les erreurs de certificat SSL
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')

# Ajouter l'argument pour démarrer en mode maximisé
options.add_argument('--start-maximized')

# Initialiser Pushbullet avec votre clé API
pb = Pushbullet("o.tKZ95gnDJTWxrhO4OQPns2l5Va9wB35f")

# Récupérer tous les canaux créés par l'utilisateur actuel
channels = pb.channels

# Choisissez le canal en fonction de son nom
# Vous pouvez modifier cette boucle pour choisir le canal approprié en fonction de son nom ou de tout autre critère
def get_channel(channels):
    for channel in channels:
        if channel.name == 'Actualité Sport France':
            return channel
    return None

my_channel = get_channel(channels)

# Initialiser une liste pour stocker les titres des nouvelles déjà envoyées
sent_news_titles = []

# Initialiser le navigateur en dehors de la fonction pour le garder ouvert
driver = Chrome(options=options)

def fetch_and_send_news(my_channel):
    try:
        # Ouvrir l'URL ou actualiser la page
        driver.get('https://sports.orange.fr')
        print("Page chargée")

        # Cliquer sur le bouton "Tout accepter" si présent
        try:
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[text()="Tout accepter"]'))
            )
            accept_button.click()
            print("Bouton 'Tout accepter' cliqué")
        except Exception as e:
            print(f"Bouton 'Tout accepter' non trouvé ou erreur : {e}")

        # Attendre que les articles soient chargés
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'fil-info-datatitle'))
        )
        print("Articles chargés")

        # Récupérer les éléments de la classe "fil-info-content bloc-commun"
        div_elements = driver.find_elements(By.CSS_SELECTOR, '.fil-info-content.bloc-commun')
        print(f"Nombre d'éléments trouvés: {len(div_elements)}")

        # Initialiser une liste pour stocker les nouvelles de l'heure
        news_hour = []

        # Parcourir les éléments div
        for div_element in div_elements:
            # Récupérer les éléments de la classe "fil-info-datatitle"
            datatitle_elements = div_element.find_elements(By.CLASS_NAME, 'fil-info-datatitle')
            print(f"Nombre d'éléments 'fil-info-datatitle' trouvés: {len(datatitle_elements)}")

            # Parcourir les éléments de la classe "fil-info-datatitle"
            for datatitle_element in datatitle_elements:
                try:
                    # Récupérer les attributs data-texte et data-title
                    data_text = datatitle_element.get_attribute('data-text')
                    data_title = datatitle_element.get_attribute('data-title')
                    # Récupérer l'URL de l'article
                    data_href = datatitle_element.find_element(By.TAG_NAME, 'a').get_attribute('href')

                    # Récupérer l'heure de la nouvelle
                    news_time_element = datatitle_element.find_element(By.CLASS_NAME, 'fil-info-datePublished')
                    news_time = news_time_element.text

                    # Vérifier si l'heure de la nouvelle est dans l'heure actuelle
                    current_hour = datetime.now().strftime('%H')
                    if news_time.startswith(current_hour):
                        # Vérifier si le titre de la nouvelle a déjà été envoyé
                        if data_title not in sent_news_titles:
                            # Ajouter le titre de la nouvelle à la liste des titres envoyés
                            sent_news_titles.append(data_title)
                            # Ajouter la nouvelle à la liste des nouvelles de l'heure
                            news_hour.append(f"{news_time} | {data_title}\n\n{data_text}\n\nPLUS D'INFO : {data_href}\n")
                            print(f"Nouvelle ajoutée : {data_title}")

                except Exception as e:
                    print(f"Erreur lors du traitement de l'élément: {e}")

        # Envoyer les nouvelles de l'heure via Pushbullet
        if news_hour:
            # Vérifiez si le canal a été trouvé
            if my_channel is not None:
                # Envoyer une notification à tous les abonnés de ce canal
                try:
                    push = my_channel.push_note("Nouvelles sur le Sport:", "\n".join(news_hour))
                    print("Notification envoyée au canal Actualité Sport France.")
                except Exception as e:
                    print(f"Erreur lors de l'envoi de la notification au canal : {e}")
            else:
                print("Canal 'Actualité Sport France' introuvable.")

    except Exception as e:
        # Afficher l'erreur en cas de problème lors de la récupération des nouvelles
        print(f"Une erreur s'est produite lors de la récupération des nouvelles : {e}")

# Récupérer et envoyer les dernières nouvelles dès le lancement du script
fetch_and_send_news(my_channel)

try:
    while True:
        # Attendre 2 minutes avant de vérifier à nouveau les nouvelles
        time.sleep(120)
        # Actualiser la page et envoyer les nouvelles qu'il y a eu entre temps
        driver.refresh()
        print("Page actualisée")
        fetch_and_send_news(my_channel)

except Exception as e:
    print(f"Une erreur générale s'est produite : {e}")

finally:
    # Fermer le navigateur
    driver.quit()
