import tweepy
import pyodbc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

# Twitter API Bilgileri - Kendi bilgilerinizi buraya girin
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
ACCESS_SECRET = "YOUR_ACCESS_SECRET"

# SQL Server Bağlantı Bilgileri - Kendi bilgilerinizi buraya girin
server = 'YOUR_SERVER_ADDRESS'
database = 'YOUR_DATABASE_NAME'
username = 'YOUR_USERNAME'
password = 'YOUR_PASSWORD'

# Veritabanından veri çekme ve güncelleme
def get_latest_record_and_update():
    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        cursor = conn.cursor()

        # Örnek tablo ve kolon adları kullanıldı
        query_select = """
        SELECT TOP 1 id, sirket_kodu, aciklama
        FROM bildirim_kayitlari
        WHERE durum = 0
        ORDER BY tarih DESC
        """
        cursor.execute(query_select)
        result = cursor.fetchone()

        if result:
            record_id = result[0]
            sirket_kodu = result[1]
            aciklama = result[2]

            query_update = "UPDATE bildirim_kayitlari SET durum = 1 WHERE id = ?"
            cursor.execute(query_update, (record_id,))
            conn.commit()

            return {
                "sirket_kodu": sirket_kodu,
                "aciklama": aciklama
            }
        else:
            return None
    except Exception as e:
        print("Veritabanı hatası:", e)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Web sayfasından ekran görüntüsü alma
def take_element_screenshot(sirket_kodu):
    url = f"https://ornekwebsitesi.com/sirket/{sirket_kodu}"
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(url)
    time.sleep(5)

    driver.fullscreen_window()
    time.sleep(2)

    try:
        # Örnek bir HTML element ID'si kullanıldı
        element = driver.find_element(By.ID, "veriTablosuBot")
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(2)

        screenshot_path = f"{sirket_kodu}_ekran_goruntusu.png"
        element.screenshot(screenshot_path)
        print(f"Ekran görüntüsü alındı: {screenshot_path}")
    except Exception as e:
        print(f"Ekran görüntüsü alınırken hata oluştu: {e}")
        screenshot_path = None

    driver.quit()
    return screenshot_path

# Twitter API bağlantısı
client_v2 = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)

auth_v1 = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api_v1 = tweepy.API(auth_v1)

# Ana işlem
try:
    record = get_latest_record_and_update()
    if record:
        sirket_kodu = record["sirket_kodu"]
        aciklama = record["aciklama"]

        screenshot_path = take_element_screenshot(sirket_kodu)

        tweet_text = (
            f"📊 #{sirket_kodu} {aciklama}\n\n"
            f"Detaylı bilgi için: https://ornekwebsitesi.com/sirket/{sirket_kodu}\n\n"
            f"#Finans #Borsa"
        )

        media = api_v1.media_upload(screenshot_path)

        response = client_v2.create_tweet(text=tweet_text, media_ids=[media.media_id])
        print("Tweet başarıyla gönderildi:", response.data)
    else:
        print("Gönderilecek kayıt bulunamadı.")
except tweepy.TweepyException as e:
    print("Twitter API hatası:", e)
