import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time
import base64
from PIL import Image # Pillow kütüphanesi import edildi

# === YAPILANDIRMA ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/CubeSidePerspectiveQuestions" 
# ❗ DİKKAT: Oyununuzun HTML dosyasının tam yolunu buraya girin!
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/Webtools/CubeSidePerspective.html" 
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
# ❗ DİKKAT: Kendi API anahtarınızı (token) buraya girin!
HEADERS = {"Authorization": "Bearer your_token_here"} 

# === KURULUM ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1400,1800") 
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
choice_labels = ['A', 'B', 'C', 'D']


# Chrome DevTools Protocol (CDP) ile ekran görüntüsü alma fonksiyonu
def capture_element_with_cdp(css_selector, save_path):
    try:
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        location = element.location
        size = element.size
        
        if not size['width'] > 0 or not size['height'] > 0:
            return False

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

# En boy oranını koruyarak kare kırpma fonksiyonu
def crop_to_square_and_save(image_path, padding=20):
    """
    Verilen yoldaki bir görüntünün etrafındaki beyaz boşlukları,
    sonucun kare (1:1 en boy oranı) kalmasını sağlayacak şekilde kırpar.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        diff = Image.alpha_composite(bg, img)
        bbox = diff.getbbox()

        if not bbox:
            print(f"⚠️  Uyarı: '{os.path.basename(image_path)}' dosyasında kırpılacak içerik bulunamadı.")
            return

        content_width = bbox[2] - bbox[0]
        content_height = bbox[3] - bbox[1]

        side_length = max(content_width, content_height) + (padding * 2)

        center_x = bbox[0] + content_width / 2
        center_y = bbox[1] + content_height / 2

        left = center_x - (side_length / 2)
        top = center_y - (side_length / 2)
        right = left + side_length
        bottom = top + side_length
        
        if left < 0: right -= left; left = 0
        if top < 0: bottom -= top; top = 0
        if right > img.width: left -= (right - img.width); right = img.width
        if bottom > img.height: top -= (bottom - img.height); bottom = img.height

        final_crop_box = (int(left), int(top), int(right), int(bottom))
        square_cropped_img = img.crop(final_crop_box)
        square_cropped_img.save(image_path)
        
    except FileNotFoundError:
        print(f"❌ Kırpma hatası: '{image_path}' dosyası bulunamadı.")
    except Exception as e:
        print(f"❌ Görüntü kırpılırken beklenmedik bir hata oluştu: {e}")


# === ANA İŞLEM DÖNGÜSÜ ===
for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    
    driver.get(LOCAL_FILE_URL)
    time.sleep(5) 

    # --- Soru görüntüsünü al ve işle ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    print("Soru elementinin ekran görüntüsü alınıyor...")
    if capture_element_with_cdp('#threeJsContainer', question_path):
        print("Görüntü, en-boy oranı korunarak kare olarak kırpılıyor...")
        crop_to_square_and_save(question_path)
        print(f"✅ Soru görseli başarıyla alındı ve kare olarak kırpıldı: {question_path}")
    else:
        print("❌ Soru görseli alınamadığı için bu soru atlanıyor.")
        continue

    # --- Şık görsellerini al ---
    option_paths = []
    all_options_captured = True
    print("Şık elementlerinin ekran görüntüleri alınıyor...")
    for idx in range(4):
        choice_selector = f"#optionsContainer .option:nth-of-type({idx + 1})"
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        if capture_element_with_cdp(choice_selector, choice_path):
            option_paths.append(choice_path)
        else:
            all_options_captured = False
            break
    
    if not all_options_captured:
        print("❌ Şık görsellerinden biri alınamadığı için bu soru atlanıyor.")
        continue
    
    print("✅ Tüm şık görselleri başarıyla alındı.")
    
    # --- Doğru cevabı HTML'den oku ---
    try:
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
        print(f"ℹ️  Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")
    except Exception as e:
        print(f"❌ Doğru cevap indeksi okunurken hata oluştu: {e}")
        continue

    # --- API'ye gönder ---
    try:
        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3:

            files = {
                "question_image": q_img, "correct_answer": correct, 
                "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3
            }
            # ❗ DİKKAT: Bu kategorinin ID'sini ve diğer verileri API dokümantasyonunuza göre kontrol edin!
            data = {
                "category_id": "34",
                "grade": "[1,2,3,4,9]", 
                "knowledge": "0", 
                "level": "1"
            }

            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            response.raise_for_status()
            print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
            
    except (requests.exceptions.RequestException, FileNotFoundError, IndexError) as e:
        print(f"❌ Soru {i} API'ye gönderilirken veya dosyalar hazırlanırken hata oluştu: {e}")

# === BİTİŞ ===
driver.quit()
print("\n🎉 Tüm sorular işlendi. Program sonlandırıldı.")