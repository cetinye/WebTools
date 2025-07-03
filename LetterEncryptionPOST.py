import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageChops
import os
import time

# ==============================================================================
# ===  CONFIGURATION (EDIT ONLY THIS SECTION) ===
# ==============================================================================

LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/LetterEncryption.html"
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/LetterEncryptionQuestions"
# API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# EKLENDİ: Soru görselinin etrafına eklenecek boşluk miktarı (piksel cinsinden)
QUESTION_PADDING = 15

# ==============================================================================
# === AUTOMATION CODE (DO NOT CHANGE) ===
# ==============================================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--force-device-scale-factor=1")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D', 'E'] 

# GÜNCELLENDİ: Fonksiyon artık boşlukları kırpıp padding ekliyor
def trim_and_pad_image(image_path, padding=0):
    """
    Bir görüntünün kenarlarındaki boş alanları kırpar ve ardından belirtilen miktarda
    boşluk (padding) ekler.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        
        if bbox:
            # Görüntüyü sınırlayıcı kutuya göre kırp
            trimmed_img = img.crop(bbox)

            # Eğer padding isteniyorsa, yeni bir tuval oluştur ve ortasına yapıştır
            if padding > 0:
                new_size = (trimmed_img.width + 2 * padding, trimmed_img.height + 2 * padding)
                # Orijinal arka plan rengiyle yeni bir tuval oluştur
                padded_img = Image.new(img.mode, new_size, img.getpixel((0,0)))
                # Kırpılmış resmi bu yeni tuvalin ortasına yapıştır
                padded_img.paste(trimmed_img, (padding, padding))
                # Son resmi kaydet
                padded_img.save(image_path)
                print(f"✨ Whitespace trimmed and {padding}px padding added.")
            else:
                # Padding istenmiyorsa sadece kırpılmış halini kaydet
                trimmed_img.save(image_path)
                print("✨ Whitespace trimmed successfully.")
        else:
            print("⚠️ Image is empty, no trim needed.")
    except Exception as e:
        print(f"❌ Error while trimming/padding image: {e}")


def resize_image(path, target_size):
    """Resizes the image proportionally on a transparent background."""
    if not os.path.exists(path): return
    img = Image.open(path).convert("RGBA")
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x_offset, y_offset = (target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2
    new_img.paste(img, (x_offset, y_offset))
    new_img.save(path)

try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Processing Question {i} ---")
        
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "option")))
            print("👍 Game loaded, taking screenshots.")
            time.sleep(0.5) 
        except Exception:
            print(f"❌ Error: Game could not be loaded for question {i} within 10 seconds.")
            break 

        # --- Question Image ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "question-area")
        
        question_elem.screenshot(question_path)
        print("📸 Question screenshot taken.")

        # GÜNCELLENDİ: Fonksiyon çağrısı artık padding parametresini de içeriyor
        trim_and_pad_image(question_path, padding=QUESTION_PADDING)
        
        resize_image(question_path, (600, 150))
        

        # --- Answer Choices (DEĞİŞİKLİK YOK) ---
        options_elements = driver.find_elements(By.CLASS_NAME, "option")
        option_paths = []
        for idx, opt in enumerate(options_elements[:5]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            resize_image(choice_path, (600, 60))
            option_paths.append(choice_path)
        print("📸 Options screenshots taken.")

        # --- API'ye Gönderme Kısmı (Değişiklik yok) ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3, \
             open(wrong_paths[3], 'rb') as wrong4:
            
            files = {
                "question_image": q_img, "correct_answer": correct,
                "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3,
            }
            data = {"category_id": "25", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            try:
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                print(f"✅ Question {i} sent. Correct choice: {choice_labels[correct_index]} | Status: {response.status_code}")
                print(f"✅ Question {i} processed. Correct choice: {choice_labels[correct_index]}. (API call is commented out)")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error: API error while sending question {i}: {e}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            print("Refreshing page for the next question...")
            driver.refresh()
            
finally:
    driver.quit()
    print("\n🎉 Automation complete. Browser closed.")