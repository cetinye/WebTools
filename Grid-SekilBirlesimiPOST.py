import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import os
import time

# ==============================================================================
# ===   CONFIGURATION (EDIT ONLY THIS SECTION)                               ===
# ==============================================================================

# 1. HTML dosyanızın tam yolunu file:/// protokolü ile girin.
# ÖNEMLİ: Yol için ters eğik çizgi (\) yerine düz eğik çizgi (/) kullanın.
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/Grid-SekilBirlesimi.html" # ÖRNEK: "file:///C:/Games/Matrix/game.html"

# 2. Diğer ayarlar
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/Grid-SekilBirlesimi"
# API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# ==============================================================================
# === AUTOMATION CODE (DO NOT CHANGE)                                        ===
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
        
        # Akıllı bekleme: Seçeneklerin yüklenmesini bekleyerek oyunun tam olarak hazır olmasını sağla
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "option-button")))
            print("👍 Oyun yüklendi, ekran görüntüleri alınıyor.")
            time.sleep(0.5) 
        except Exception:
            print(f"❌ Hata: {i}. soru için oyun 10 saniye içinde yüklenemedi.")
            break 

        # --- Soru Görseli ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "matrix-grid")
        
        # DÜZELTME: Kırpılmayı önlemek için elementi ekranın ortasına kaydır
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", question_elem)
        time.sleep(0.2) # Kaydırma animasyonunun bitmesi için kısa bir bekleme
        
        question_elem.screenshot(question_path)
        resize_image(question_path, (350, 350))
        print("📸 Soru ekran görüntüsü alındı.")

        # --- Cevap Seçenekleri ---
        options_elements = driver.find_elements(By.CLASS_NAME, "option-button")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            
            # DÜZELTME: Kırpılmayı önlemek için her bir seçeneği de ekranın ortasına kaydır
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", opt)
            time.sleep(0.2) # Kaydırma animasyonunun bitmesi için kısa bir bekleme

            opt.screenshot(choice_path)
            resize_image(choice_path, (120, 120))
            option_paths.append(choice_path)
        print("📸 Seçeneklerin ekran görüntüleri alındı.")

        # --- Doğru Cevabı Oku ve API'ye Gönder ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3:
            
            files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
            data = {"category_id": "25", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            try:
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Durum: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Hata: {i}. soru gönderilirken API hatası: {e}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            print("'Yeni Oyun' butonuna tıklanıyor...")
            
            old_options = driver.find_elements(By.CLASS_NAME, "option-button")
            
            driver.find_element(By.ID, "reset-button").click()
            
            if old_options:
                try:
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.staleness_of(old_options[0]))
                    print("...Eski seçenekler temizlendi, yeni soru bekleniyor.")
                except Exception:
                    print("...Eski seçeneklerin temizlendiği doğrulanamadı, yine de devam ediliyor.")

finally:
    driver.quit()
    print("\n🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")