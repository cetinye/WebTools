import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import base64
from PIL import Image, ImageChops

# === CONFIGURATION ===
NUM_QUESTIONS = 1
# Bu oyuna ait klasör adını kullanın
SAVE_DIR = "C:/Users/cetin/Desktop/CubeGapPerspectiveQuestions_Final" 
# Kullandığınız HTML dosyasının tam yolu
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/CubeGapPerspectiveGame.html" 
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}  # <<< KENDİ TOKEN'INIZI GİRİN

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1300,1350")
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
choice_labels = ['A', 'B', 'C', 'D']


# EN GÜVENİLİR FONKSİYON: Chrome DevTools Protocol ile elementi yakalar
def capture_element_with_cdp(css_selector, save_path):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        location = element.location
        size = element.size
        if size['width'] == 0 or size['height'] == 0:
            raise Exception(f"Element '{css_selector}' has zero dimensions.")
        clip = {
            'x': location['x'], 'y': location['y'],
            'width': size['width'], 'height': size['height'],
            'scale': 1
        }
        result = driver.execute_cdp_cmd('Page.captureScreenshot', {
            'format': 'png', 'clip': clip, 'captureBeyondViewport': True
        })
        screenshot_data = base64.b64decode(result['data'])
        with open(save_path, 'wb') as f:
            f.write(screenshot_data)
        return True
    except Exception as e:
        print(f"❌ CDP ile '{css_selector}' ekran görüntüsü alınırken hata oluştu: {e}")
        return False

# Sadece soru için kullanılacak beyaz boşlukları kırpma fonksiyonu
def trim_whitespace(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")
        if not img.getbbox(): return
        
        # Arka planı beyaz olarak varsayarak işlem yapıyoruz
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3]) # Şeffaflığı koru
        diff = ImageChops.difference(bg, Image.new("RGB", img.size, (255, 255, 255)))
        bbox = diff.getbbox()

        if bbox:
            # Kenarlardan küçük bir pay bırakmak için bbox'ı genişlet
            bbox = (bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2)
            cropped_img = img.crop(bbox)
            cropped_img.save(image_path)
            print(f"  > '{os.path.basename(image_path)}' dosyasındaki boşluklar kırpıldı.")
            
    except Exception as e:
        print(f"❌ Kırpma sırasında hata oluştu '{os.path.basename(image_path)}': {e}")


# === ANA İŞLEM DÖNGÜSÜ ===
for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    
    driver.get(LOCAL_FILE_URL)
    wait = WebDriverWait(driver, 10)
    
    # Oyunun ve seçeneklerin yüklenmesini bekle
    wait.until(EC.presence_of_element_located((By.ID, "canvas")))
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "option")))
    time.sleep(1.5)

    # --- Soru görüntüsünü al ve işle ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    print("Soru elementinin tam ekran görüntüsü (CDP ile) alınıyor...")
    if capture_element_with_cdp('#question-area', question_path):
        trim_whitespace(question_path) # Sadece soruyu kırp
        print("✅ Soru görseli alındı ve işlendi.")

    # --- Şık görsellerini al (kırpma yok) ---
    option_paths = []
    print("Şık elementlerinin tam ekran görüntüleri (CDP ile) alınıyor...")
    option_elements = driver.find_elements(By.CSS_SELECTOR, ".option")
    for idx, opt_element in enumerate(option_elements):
        choice_selector = f".option:nth-of-type({idx + 1})"
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        if capture_element_with_cdp(choice_selector, choice_path):
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
            # Bu oyun için kategori ID'sini doğrulayın
            data = {"category_id": "34", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

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