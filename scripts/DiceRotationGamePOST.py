import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageChops
import os
import time
import base64

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/DiceRotationGameQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/DiceRotationGame.html" 
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# --- GÖRSEL İŞLEME AYARLARI ---
QUESTION_PADDING = 40
CHOICE_PADDING = 30
# ✨ DEĞİŞİKLİK: Soru için sadece hedef genişlik belirliyoruz
QUESTION_TARGET_WIDTH = 1600
CHOICE_TARGET_SIZE = (512, 512)

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=5000,4000") # Çok geniş element için büyük sanal ekran
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
choice_labels = ['A', 'B', 'C', 'D']


def capture_element_with_cdp(css_selector, save_path):
    try:
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        location = element.location; size = element.size
        if not size['width'] > 0 or not size['height'] > 0: return False
        clip = {'x': location['x'], 'y': location['y'], 'width': size['width'], 'height': size['height'], 'scale': 1}
        result = driver.execute_cdp_cmd('Page.captureScreenshot', {'format': 'png', 'clip': clip, 'captureBeyondViewport': True})
        screenshot_data = base64.b64decode(result['data'])
        with open(save_path, 'wb') as f: f.write(screenshot_data)
        return True
    except Exception as e:
        print(f"❌ CDP ile '{css_selector}' alınırken hata: {e}"); return False

def trim_and_pad_image(image_path, padding=0):
    try:
        img = Image.open(image_path).convert("RGB")
        bg = Image.new(img.mode, img.size, (255, 255, 255))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox:
            trimmed_img = img.crop(bbox)
            if padding > 0:
                new_size = (trimmed_img.width + 2 * padding, trimmed_img.height + 2 * padding)
                padded_img = Image.new(img.mode, new_size, (255, 255, 255))
                padded_img.paste(trimmed_img, (padding, padding))
                padded_img.save(image_path)
            else: trimmed_img.save(image_path)
    except Exception as e:
        print(f"❌ '{os.path.basename(image_path)}' kırpılırken hata: {e}")

# ✨ YENİ FONKSİYON: Genişliğe göre ölçekler, dikey boşluk bırakmaz.
def scale_to_width(path, target_width):
    """Görüntüyü, en-boy oranını koruyarak hedef genişliğe ölçekler."""
    try:
        img = Image.open(path).convert("RGBA")
        
        # Orijinal en-boy oranına göre yeni yüksekliği hesapla
        source_ratio = img.height / img.width
        new_height = int(target_width * source_ratio)
        
        # Görüntüyü yeni boyutlara ölçekle
        resized_img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        resized_img.save(path, 'PNG')
    except Exception as e:
        print(f"❌ '{os.path.basename(path)}' genişliğe ölçeklenirken hata: {e}")

# Şıklar için standart "ortala ve doldur" fonksiyonu
def resize_and_fill_image(path, target_size, fill_color=(255, 255, 255)):
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", target_size, fill_color)
        x_offset = (target_size[0] - img.width) // 2
        y_offset = (target_size[1] - img.height) // 2
        new_img.paste(img, (x_offset, y_offset), img)
        new_img.save(path, 'PNG')
    except Exception as e:
        print(f"❌ '{os.path.basename(path)}' yeniden boyutlandırılırken hata: {e}")


# === ANA İŞLEM DÖNGÜSÜ ===
for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    driver.get(LOCAL_FILE_URL)
    time.sleep(1.5)

    # --- Soru görüntüsünü al ve işle ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    if not capture_element_with_cdp('#cube-sequence', question_path):
        print("❌ Soru görseli alınamadı, bu soru atlanıyor."); continue
        
    trim_and_pad_image(question_path, padding=QUESTION_PADDING)
    # ✨ DEĞİŞİKLİK: Yeni "genişliğe ölçekle" fonksiyonu çağrılıyor.
    scale_to_width(question_path, QUESTION_TARGET_WIDTH)
    print("✅ Soru görseli alındı ve genişliğe göre ölçeklendi.")

    # --- Şık görsellerini al ve işle ---
    option_paths = []
    for idx, label in enumerate(choice_labels):
        choice_selector = f".options-container .option-btn:nth-of-type({idx + 1})"
        choice_path = os.path.join(SAVE_DIR, f"choice_{label}_{i}.png")
        if not capture_element_with_cdp(choice_selector, choice_path):
            print("❌ Şık görselleri alınamadı, bu soru atlanıyor."); break
        resize_and_fill_image(choice_path, CHOICE_TARGET_SIZE)
        option_paths.append(choice_path)
    else: # for-else: break olmadan döngü biterse çalışır
        print("✅ Şık görselleri alındı ve işlendi.")
        # --- Doğru cevabı oku ve API'ye gönder ---
        correct_index = int(driver.execute_script("return window.correctIndex;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
        print(f"ℹ️ Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")
        try:
            with open(question_path, 'rb') as q_img, open(correct_path, 'rb') as correct, open(wrong_paths[0], 'rb') as wrong1, open(wrong_paths[1], 'rb') as wrong2, open(wrong_paths[2], 'rb') as wrong3:
                files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
                data = {"category_id": "28", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                response.raise_for_status()
                print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Soru {i} API'ye gönderilirken veya dosyalar hazırlanırken hata oluştu: {e}")
        continue # API'ye gönderdikten sonra döngüye devam et
    
    # Döngü 'break' ile kırıldıysa bu satıra ulaşılır
    print("Döngü şık alınamadığı için erken sonlandırıldı.")


driver.quit()
print("\n🎉 Tüm sorular başarıyla işlendi. Program sonlandırıldı.")