import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageChops
import os
import time
import base64 # ✨ DEĞİŞİKLİK: CDP için gerekli import eklendi

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/DiceGameQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/DiceGame.html"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"} # <<< KENDİ TOKEN'INIZI GİRİN

# --- GÖRSEL İŞLEME AYARLARI ---
QUESTION_PADDING = 35
CHOICE_PADDING = 25
QUESTION_TARGET_SIZE = (1200, 1200)
CHOICE_TARGET_SIZE = (512, 512)

# === SETUP ===
options = webdriver.ChromeOptions()
# ✨ DEĞİŞİKLİK: Otomasyon için daha güvenilir olan headless ve sabit pencere boyutu ayarları geri getirildi
options.add_argument("--headless")
options.add_argument("--window-size=2500,2500") # Büyük elementlerin sığabileceği devasa bir sanal ekran
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)
time.sleep(1)
choice_labels = ['A', 'B', 'C', 'D']


# ✨ DEĞİŞİKLİK: Güçlü CDP ekran görüntüsü alma fonksiyonu eklendi
def capture_element_with_cdp(css_selector, save_path):
    """
    Ekran dışına taşsa bile bir elementin tamamının görüntüsünü alır.
    """
    try:
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        location = element.location
        size = element.size
        
        if not size['width'] > 0 or not size['height'] > 0: return False

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
        print(f"❌ CDP ile '{css_selector}' alınırken hata: {e}")
        return False

# === GÖRSEL İŞLEME FONKSİYONLARI (Değişiklik yok) ===
def trim_and_pad_image(image_path, padding=0, bg_color_to_use=None):
    try:
        img = Image.open(image_path).convert("RGB")
        bg_color = bg_color_to_use if bg_color_to_use else img.getpixel((0, 0))
        bg = Image.new(img.mode, img.size, bg_color)
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox:
            trimmed_img = img.crop(bbox)
            if padding > 0:
                new_size = (trimmed_img.width + 2 * padding, trimmed_img.height + 2 * padding)
                padded_img = Image.new(img.mode, new_size, bg_color)
                padded_img.paste(trimmed_img, (padding, padding))
                padded_img.save(image_path)
            else:
                trimmed_img.save(image_path)
    except Exception as e:
        print(f"❌ '{os.path.basename(image_path)}' kırpılırken hata: {e}")

def resize_and_fill_image(path, target_size, fill_color=(244, 247, 250)):
    try:
        img = Image.open(path).convert("RGBA")
        original_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        if original_ratio > target_ratio:
            new_width = target_size[0]; new_height = int(new_width / original_ratio)
        else:
            new_height = target_size[1]; new_width = int(new_height * original_ratio)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", target_size, fill_color)
        x_offset = (target_size[0] - new_width) // 2
        y_offset = (target_size[1] - new_height) // 2
        new_img.paste(resized_img, (x_offset, y_offset), resized_img)
        new_img.save(path, 'PNG')
    except Exception as e:
        print(f"❌ '{os.path.basename(path)}' yeniden boyutlandırılırken hata: {e}")

# === ANA İŞLEM DÖNGÜSÜ ===
for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    time.sleep(0.5)

    # ✨ DEĞİŞİKLİK: Soru görüntüsü artık CDP ile, kırpılmadan alınıyor.
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    if not capture_element_with_cdp('#question-area', question_path):
        print("❌ Soru görseli alınamadı, bu soru atlanıyor.")
        continue
    
    trim_and_pad_image(question_path, padding=QUESTION_PADDING, bg_color_to_use=(255, 255, 255))
    resize_and_fill_image(question_path, QUESTION_TARGET_SIZE)
    print("✅ Soru görseli alındı ve işlendi.")

    # ✨ DEĞİŞİKLİK: Şık görselleri artık CDP ile, kırpılmadan alınıyor.
    option_paths = []
    all_options_captured = True
    for idx, label in enumerate(choice_labels):
        # Her şık için benzersiz bir CSS seçici oluşturuyoruz
        choice_selector = f".options button:nth-of-type({idx + 1}) .die"
        choice_path = os.path.join(SAVE_DIR, f"choice_{label}_{i}.png")
        
        if not capture_element_with_cdp(choice_selector, choice_path):
            all_options_captured = False
            break

        trim_and_pad_image(choice_path, padding=CHOICE_PADDING, bg_color_to_use=(255, 255, 255))
        resize_and_fill_image(choice_path, CHOICE_TARGET_SIZE)
        option_paths.append(choice_path)
        
    if not all_options_captured:
        print("❌ Şık görselleri alınamadığı için bu soru atlanıyor.")
        continue
    print("✅ Şık görselleri alındı ve işlendi.")
    
    # --- Doğru cevabı oku ve API'ye gönder (Değişiklik yok) ---
    wait = WebDriverWait(driver, 10)
    wait.until(lambda d: d.execute_script("return document.getElementById('correctIndex').textContent !== ''"))
    correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent"))
    correct_path = option_paths[correct_index]
    wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
    print(f"ℹ️ Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")

    try:
        with open(question_path, 'rb') as q_img, open(correct_path, 'rb') as correct, open(wrong_paths[0], 'rb') as wrong1, open(wrong_paths[1], 'rb') as wrong2, open(wrong_paths[2], 'rb') as wrong3:
            files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
            data = {"category_id": "25", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}
            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            response.raise_for_status()
            print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Soru {i} API'ye gönderilirken veya dosyalar hazırlanırken hata oluştu: {e}")

    if i < NUM_QUESTIONS:
        print("... Sayfa yenileniyor ...")
        driver.refresh()
        time.sleep(1)

# === BİTİŞ ===
driver.quit()
print("\n🎉 Tüm sorular başarıyla işlendi. Program sonlandırıldı.")