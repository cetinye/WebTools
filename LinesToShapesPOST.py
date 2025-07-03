import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import os
import time

# ==============================================================================
# ===  YAPILANDIRMA (SADECE BU BÖLÜMÜ DEĞİŞTİR) ===
# ==============================================================================

# 1. HTML dosyanızın tam yolunu file:/// protokolü ile buraya yazın.
# ÖNEMLİ: Windows'ta yol için normal eğik çizgi (/) kullanın.
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/LinesToShapes.html" # ÖRNEK: "file:///C:/Oyunlarim/LinesToShapes.html"

# 2. Diğer ayarlar
NUM_QUESTIONS = 1 # Test için sayıyı artırabilirsiniz
SAVE_DIR = "C:/Users/cetin/Desktop/LinesToShapesQuestions"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# ==============================================================================
# === OTOMASYON KODU (DEĞİŞTİRMEYİN) ===
# ==============================================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

def resize_image(path, target_size):
    """Görüntüyü şeffaf arka plan üzerinde orantılı olarak yeniden boyutlandırır."""
    img = Image.open(path).convert("RGBA")
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x_offset, y_offset = (target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2
    new_img.paste(img, (x_offset, y_offset))
    new_img.save(path)

try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")
        
        # Akıllı bekleme: Yeni seçeneklerin yüklenmesini bekle
        try:
            wait = WebDriverWait(driver, 10)
            # Seçeneklerin olduğu konteynerde en az bir tane `.shape-option` elemanı olana kadar bekle
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "shape-option")))
            print("👍 Oyun yüklendi, ekran görüntüleri alınıyor.")
            time.sleep(0.5) # Çizimlerin tam oturması için kısa bir ek bekleme
        except Exception:
            print(f"❌ Hata: Soru {i} için oyun 10 saniyede yüklenemedi.")
            break # Hata olursa döngüyü kır

        # --- Soru görüntüsü ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "question-area")
        question_elem.screenshot(question_path)
        resize_image(question_path, (700, 500))
        print("📸 Soru ekran görüntüsü alındı.")

        # --- Şıklar ---
        options_elements = driver.find_elements(By.CLASS_NAME, "shape-option")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            resize_image(choice_path, (140, 140))
            option_paths.append(choice_path)
        print("📸 Şıkların ekran görüntüleri alındı.")

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
                print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Hata: Soru {i} gönderilirken API hatası oluştu: {e}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            print("Sonraki soruya geçiliyor...")
            
            # --- ÖNEMLİ DÜZELTME: Eskİ seçeneklerin kaybolmasını bekle ---
            # Butona basmadan önce mevcut seçenekleri referans al
            old_options = driver.find_elements(By.CLASS_NAME, "shape-option")
            
            # "Yeni Soru" butonuna bas
            driver.find_element(By.ID, "newGameBtn").click()
            
            # Referans aldığımız eski seçeneklerden en az birinin "bayatlamasını" (DOM'dan kaldırılmasını) bekle
            if old_options:
                try:
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.staleness_of(old_options[0]))
                    print("...Eski seçenekler temizlendi, yeni soru bekleniyor.")
                except Exception:
                    print("...Eski seçenekler temizlenemedi, devam ediliyor.")
            # ----------------------------------------------------------------

finally:
    driver.quit()
    print("\n🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")