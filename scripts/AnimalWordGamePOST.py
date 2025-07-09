import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time
import base64  # CDP'den gelen veriyi çözmek için gerekli

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/AnimalWordGameQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/AnimalWordGame.html" # Yolu kendi dosya yolunuzla güncelleyin
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}  # <<< KENDİ TOKEN'INIZI GİRİN

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
# Bu yöntem viewport'tan bağımsız olduğu için pencere boyutu daha az kritik,
# ancak yine de makul bir boyutta tutmak iyidir.
options.add_argument("--window-size=1400,1400") 
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)

choice_labels = ['A', 'B', 'C', 'D']


# ⭐ EN GÜVENİLİR FONKSİYON: Chrome DevTools Protocol ile elementi yakalar ⭐
def capture_element_with_cdp(css_selector, save_path):
    """
    Elementin konumunu alır ve Chrome Geliştirici Araçları Protokolü'nü kullanarak
    elementin viewport dışında kalan kısımları da dahil olmak üzere tam bir
    ekran görüntüsünü alır. Bu yöntem en güvenilir olanıdır.
    """
    try:
        # Elementi bul ve boyutlarını/konumunu al
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        location = element.location
        size = element.size
        
        # CDP komutu için kırpma (clip) alanını tanımla
        clip = {
            'x': location['x'],
            'y': location['y'],
            'width': size['width'],
            'height': size['height'],
            'scale': 1  # 1x ölçekte yakala
        }

        # CDP'ye 'Page.captureScreenshot' komutunu gönder
        # Bu komut, belirtilen alandaki görüntüyü base64 formatında döndürür
        result = driver.execute_cdp_cmd('Page.captureScreenshot', {
            'format': 'png',
            'clip': clip,
            'captureBeyondViewport': True # Görünür alanın ötesini de yakala
        })
        
        # Base64 verisini çöz ve resim dosyası olarak kaydet
        screenshot_data = base64.b64decode(result['data'])
        with open(save_path, 'wb') as f:
            f.write(screenshot_data)

    except Exception as e:
        print(f"❌ CDP ile '{css_selector}' ekran görüntüsü alınırken hata oluştu: {e}")

# === ANA İŞLEM DÖNGÜSÜ ===
for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    
    # Sayfayı sadece bir kere en başta yüklemek yeterli
    driver.get(LOCAL_FILE_URL)
    time.sleep(2) # Sayfadaki tüm scriptlerin ve SVG'lerin tam yüklenmesi için bekleme

    # --- Soru görüntüsünü al ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    print("Soru elementinin tam ekran görüntüsü (CDP ile) alınıyor...")
    capture_element_with_cdp('#question-area', question_path)
    print(f"✅ Soru görseli başarıyla alındı: {question_path}")

    # --- Şık görsellerini al ---
    # Bu yöntem sayfayı değiştirmediği için art arda çağrılabilir.
    option_paths = []
    print("Şık elementlerinin tam ekran görüntüleri (CDP ile) alınıyor...")
    for idx in range(4):
        choice_selector = f".option:nth-of-type({idx + 1})"
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        capture_element_with_cdp(choice_selector, choice_path)
        option_paths.append(choice_path)
        print(f"  > {choice_labels[idx]} şıkkı alındı.")
    print("✅ Tüm şık görselleri başarıyla alındı.")
    
    # --- Doğru cevabı HTML'den oku ---
    correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
    correct_path = option_paths[correct_index]
    wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
    print(f"ℹ️ Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")

    # --- API'ye gönder ---
    try:
        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3:

            files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
            data = {"category_id": "24", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            response.raise_for_status()
            
            print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Soru {i} API'ye gönderilirken hata oluştu: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"   API Yanıtı: {response.text}")

# === BİTİŞ ===
driver.quit()
print("\n🎉 Tüm sorular başarıyla işlendi. Program sonlandırıldı.")