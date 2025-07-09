import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import base64
# ⭐ DEĞİŞİKLİK: Görüntü işleme için Pillow kütüphanesi eklendi
from PIL import Image, ImageChops

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/CountCubeGameQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/CountCubeGame.html"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}  # <<< KENDİ TOKEN'INIZI GİRİN

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1700,1350")
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
choice_labels = ['A', 'B', 'C', 'D']


# CDP ile ekran görüntüsü alma fonksiyonu (değişiklik yok)
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

# ⭐ YENİ FONKSİYON: Görüntüdeki beyaz boşlukları kırpar ⭐
def trim_whitespace(image_path):
    """
    Bir görüntüdeki beyaz (veya tek renkli) kenar boşluklarını
    kaliteyi ve çözünürlüğü bozmadan kırpar.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # Görüntünün tamamı şeffaf ise işlem yapma
        if not img.getbbox():
            return

        # Arka plan rengini belirlemek için görüntüyü RGB'ye çevir
        bg_img = Image.new("RGB", img.size, (255, 255, 255))
        bg_img.paste(img, mask=img.split()[3]) # Alfa kanalını maske olarak kullan

        # Farkı bularak içeriğin olduğu alanı tespit et
        diff = ImageChops.difference(bg_img, Image.new("RGB", img.size, (255, 255, 255)))
        bbox = diff.getbbox()

        if bbox:
            # Orijinal RGBA görüntüyü bu koordinatlara göre kırp
            cropped_img = img.crop(bbox)
            # Kırpılmış görüntüyü kaydet
            cropped_img.save(image_path)
            print(f"  > '{os.path.basename(image_path)}' dosyasındaki boşluklar kırpıldı.")
        else:
            # Görüntü tamamen beyazsa dokunma
            print(f"  > '{os.path.basename(image_path)}' zaten boş, kırpılmadı.")
            
    except Exception as e:
        print(f"❌ Kırpma sırasında hata oluştu '{os.path.basename(image_path)}': {e}")


# === ANA İŞLEM DÖNGÜSÜ ===
for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    
    driver.get(LOCAL_FILE_URL)
    wait = WebDriverWait(driver, 10)
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cube-structure")))
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "answer-btn")))
    time.sleep(1.5)

    # --- Soru görüntüsünü al ve işle ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    print("Soru elementinin tam ekran görüntüsü (CDP ile) alınıyor...")
    if capture_element_with_cdp('#question-area', question_path):
        # ⭐ DEĞİŞİKLİK: Soru görüntüsündeki beyaz boşlukları kırp
        trim_whitespace(question_path)
        print("✅ Soru görseli alındı ve işlendi.")

    # --- Şık görsellerini al ve işle ---
    option_paths = []
    print("Şık elementlerinin tam ekran görüntüleri (CDP ile) alınıyor...")
    option_buttons = driver.find_elements(By.CSS_SELECTOR, ".answer-btn")
    for idx, btn_element in enumerate(option_buttons):
        choice_selector = f".answer-btn:nth-of-type({idx + 1})"
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        if capture_element_with_cdp(choice_selector, choice_path):
            # ⭐ DEĞİŞİKLİK: Her şık görüntüsündeki beyaz boşlukları kırp
            # trim_whitespace(choice_path)
            option_paths.append(choice_path)
            print(f"  > {choice_labels[idx]} şıkkı alındı ve işlendi.")
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
            data = {"category_id": "28", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

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