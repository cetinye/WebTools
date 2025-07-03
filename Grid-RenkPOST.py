import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import os
import time

# ==============================================================================
# === 			CONFIGURATION (SADECE BU BÖLÜMÜ DÜZENLEYİN) 		 ===
# ==============================================================================

# 1. HTML dosyanızın tam yolunu "file:///" protokolü ile girin.
# ÖNEMLİ: Yol için ters eğik çizgi (\) yerine düz eğik çizgi (/) kullanın.
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/Grid-Renk.html" # ÖRNEK: "file:///C:/Oyunlar/Matrix/oyun.html"

# 2. Kaç adet soru işleneceğini belirtin.
NUM_QUESTIONS = 1

# 3. Görüntülerin kaydedileceği klasör.
SAVE_DIR = "C:/Users/cetin/Desktop/Grid-Renk"

# 4. API Bilgileri (Bu bilgileri kendi API'nize göre düzenleyin).
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer YOUR_SECRET_TOKEN_HERE"} # "YOUR_SECRET_TOKEN_HERE" kısmını kendi token'ınız ile değiştirin.

# ==============================================================================
# === 			OTOMASYON KODU (DEĞİŞTİRMEYİN) 				 ===
# ==============================================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

def resize_image(path, target_size):
    """Görüntüyü şeffaf bir arka plan üzerinde orantılı olarak yeniden boyutlandırır."""
    img = Image.open(path).convert("RGBA")
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x_offset, y_offset = (target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2
    new_img.paste(img, (x_offset, y_offset))
    new_img.save(path)

try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")

        try:
            wait = WebDriverWait(driver, 10)
            # Sayfanın hazır olduğunu anlamak için seçenek butonlarını bekle
            option_buttons = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "option-button")))
            # Butonların tıklanabilir olmasını bekle
            wait.until(EC.element_to_be_clickable(option_buttons[0]))
            print("👍 Oyun yüklendi, ekran görüntüleri alınıyor.")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Hata: Oyun 10 saniye içinde yüklenemedi. Hata: {e}")
            break

        # --- Soru ve Cevapların Görüntülerini Alma ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        driver.find_element(By.ID, "game-grid").screenshot(question_path)
        resize_image(question_path, (600, 600))
        print("📸 Soru ekran görüntüsü alındı.")

        options_elements = driver.find_elements(By.CLASS_NAME, "option-button")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            resize_image(choice_path, (120, 120))
            option_paths.append(choice_path)
        print("📸 Seçeneklerin ekran görüntüleri alındı.")

        # --- Doğru Cevabı Oku ---
        correct_index_str = driver.execute_script("return document.getElementById('correctIndex').textContent;")
        if not correct_index_str:
            print("❌ Hata: 'correctIndex' elementi boş. Lütfen HTML dosyasındaki JavaScript kodunu kontrol edin.")
            break

        correct_index = int(correct_index_str)
        print(f"🧠 Doğru cevap {correct_index}. indekste ({choice_labels[correct_index]}).")

        # --- API için Dosyaları ve Verileri Hazırla ve Gönder ---
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

        # Dosyaları 'with' bloğu içinde açarak otomatik kapanmalarını sağla
        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct_img, \
             open(wrong_paths[0], 'rb') as wrong1_img, \
             open(wrong_paths[1], 'rb') as wrong2_img, \
             open(wrong_paths[2], 'rb') as wrong3_img:

            # API'nin beklediği dosya anahtarlarını ve verileri tanımla
            files = {
                "question_image": q_img,
                "correct_answer": correct_img,
                "wrong_answer_1": wrong1_img,
                "wrong_answer_2": wrong2_img,
                "wrong_answer_3": wrong3_img
            }
            data = {
                "category_id": "25",
                "grade": "[1,2,3,4,9]",
                "knowledge": "0",
                "level": "1"
            }

            try:
                print("📤 API'ye gönderiliyor...")
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                response.raise_for_status() # Hatalı durum kodları (4xx veya 5xx) için bir exception fırlatır
                print(f"✅ Soru {i} başarıyla gönderildi. Doğru seçenek: {choice_labels[correct_index]} | Sunucu Yanıtı: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Hata: Soru {i} gönderilirken API hatası oluştu: {e}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            # Doğru cevaba tıkla ve bir sonraki butonun görünmesini bekle
            options_elements[correct_index].click()
            print("🖱️ Doğru seçenek tıklandı, sonraki bulmaca bekleniyor.")
            
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "next-level-button"))
            )
            next_button.click()

finally:
    time.sleep(2) # Kapanmadan önce son durumu görmek için
    driver.quit()
    print("\n🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")