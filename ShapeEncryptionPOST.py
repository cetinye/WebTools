import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# === YAPILANDIRMA (SADECE BU BÖLÜMÜ DEĞİŞTİR) ===
# Kaç adet soru işleneceğini belirtin
NUM_QUESTIONS = 1

# Dosyaların kaydedileceği klasör
SAVE_DIR = "C:/Users/cetin/Desktop/ShapeEncryption"

# Selenium'un açacağı yerel HTML dosyasının yolu
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/ShapeEncryption.html"

# API bilgileri
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"} # <<< KENDİ TOKEN'INIZI GİRİN

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Kayıt klasörünü oluştur (varsa hata verme)
os.makedirs(SAVE_DIR, exist_ok=True)

# Web sayfasını aç
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

# === ANA İŞLEM DÖNGÜSÜ ===
try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")
        
        # Oyunun ve şıkların yüklenmesini bekle
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "game-grid")))
            wait.until(lambda d: len(d.find_elements(By.CLASS_NAME, "option")) == 4)
            print("✅ Oyun yüklendi, ekran görüntüleri alınıyor.")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Hata: Soru {i} için oyun 10 saniyede yüklenemedi. Hata: {e}")
            break

        # --- Soru görüntüsünü al ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        try:
            question_elem = driver.find_element(By.ID, "game-grid")
            
            # Görüntü kalitesi için arka planı geçici olarak beyaza ayarla
            original_style = driver.execute_script("return arguments[0].getAttribute('style');", question_elem)
            driver.execute_script("arguments[0].style.backgroundColor = 'white';", question_elem)
            time.sleep(0.2) # Stil değişikliğinin uygulanmasını bekle
            
            question_elem.screenshot(question_path)
            
            # Orijinal stilleri geri yükle
            driver.execute_script("arguments[0].setAttribute('style', arguments[1] || '');", question_elem, original_style)
            print("✅ Soru görseli alındı.")

        except Exception as e:
            print(f"❌ Hata: Soru görüntüsü alınırken bir sorun oluştu: {e}")
            continue

        # --- Şık görsellerini al ---
        options_elements = driver.find_elements(By.CLASS_NAME, "option")
        option_paths = []
        for idx, opt in enumerate(options_elements):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            option_paths.append(choice_path)
        print("✅ Şık görselleri alındı.")

        # --- Doğru Cevabı Oku ve API'ye Gönder ---
        try:
            wait.until(lambda d: d.find_element(By.ID, "correct-answer-index").get_attribute('textContent') != '')
            correct_index_holder = driver.find_element(By.ID, "correct-answer-index")
            correct_index_str = correct_index_holder.get_attribute('textContent')
            correct_index = int(correct_index_str)
            correct_path = option_paths[correct_index]
            wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
            print(f"ℹ️ Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")

            with open(question_path, 'rb') as q_img, \
                 open(correct_path, 'rb') as correct, \
                 open(wrong_paths[0], 'rb') as wrong1, \
                 open(wrong_paths[1], 'rb') as wrong2, \
                 open(wrong_paths[2], 'rb') as wrong3:

                files = {
                    "question_image": q_img, 
                    "correct_answer": correct,
                    "wrong_answer_1": wrong1, 
                    "wrong_answer_2": wrong2, 
                    "wrong_answer_3": wrong3
                }
                data = {
                    "category_id": "25",
                    "grade": "[1,2,3,4,9]", 
                    "knowledge": "0", 
                    "level": "1"
                }
                
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                response.raise_for_status() # Hata durumunda (4xx, 5xx) exception fırlat
                
                print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Soru {i} API'ye gönderilirken hata oluştu: {e}")
            if 'response' in locals() and response is not None:
                print(f"    API Yanıtı: {response.text}")
        except Exception as e:
            print(f"❌ Hata: Doğru cevap işlenirken bir sorun oluştu: {e}")
            continue

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            print("... Sayfa yenileniyor ...")
            driver.refresh()

finally:
    driver.quit()
    print("\n🎉 Tüm sorular başarıyla işlendi. Program sonlandırıldı.")