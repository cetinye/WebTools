import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageChops, ImageFilter
import os
import time

# === CONFIGURATION ===
# Kaç adet soru işleneceğini belirtin
NUM_QUESTIONS = 1

# Dosyaların kaydedileceği klasör
SAVE_DIR = "C:/Users/cetin/Desktop/NumberSeriesMemoryQuestions"

# Selenium'un açacağı yerel HTML dosyasının yolu
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/NumberSeriesMemory.html"

# API bilgileri
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"} # <<< KENDİ TOKEN'INIZI GİRİN

# --- GÖRSEL İŞLEME AYARLARI ---
# Soru görselinin etrafına eklenecek boşluk (piksel)
QUESTION_PADDING = 0
# Şık görsellerinin etrafına eklenecek boşluk (piksel)
CHOICE_PADDING = 0

# Soru ve şıkların son boyutları
QUESTION_TARGET_SIZE = (1200, 600)
CHOICE_TARGET_SIZE = (256, 256)

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Kayıt klasörünü oluştur (varsa hata verme)
os.makedirs(SAVE_DIR, exist_ok=True)

# Web sayfasını aç
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

# === GÖRSEL İŞLEME FONKSİYONLARI ===

def trim_and_pad_image(image_path, padding=0):
    """
    Bir görüntünün kenarlarındaki arka plan rengini otomatik olarak kırpar ve
    ardından belirtilen miktarda boşluk (padding) ekler.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        # Arka plan rengini sol üst köşeden al
        bg_color = img.getpixel((0, 0))
        
        # Arka plan rengiyle aynı olan piksellerden bir fark görüntüsü oluştur
        bg = Image.new(img.mode, img.size, bg_color)
        diff = ImageChops.difference(img, bg)
        
        # Farklı piksellerin olduğu alanın sınırlayıcı kutusunu bul
        bbox = diff.getbbox()

        if bbox:
            # Görüntüyü sınırlayıcı kutuya göre kırp
            trimmed_img = img.crop(bbox)

            if padding > 0:
                # Yeni bir tuval oluştur ve ortasına yapıştır
                new_size = (trimmed_img.width + 2 * padding, trimmed_img.height + 2 * padding)
                padded_img = Image.new(img.mode, new_size, bg_color)
                padded_img.paste(trimmed_img, (padding, padding))
                padded_img.save(image_path)
            else:
                # Sadece kırpılmış halini kaydet
                trimmed_img.save(image_path)
        else:
            print(f"⚠️ Image '{os.path.basename(image_path)}' is empty, no trim needed.")
    except Exception as e:
        print(f"❌ Error while trimming/padding image '{os.path.basename(image_path)}': {e}")


def resize_and_fill_image(path, target_size, fill_color=(255, 255, 255, 255)):
    """
    Bir görüntüyü, en-boy oranını koruyarak hedef boyuta sığacak şekilde
    yeniden boyutlandırır (gerekirse büyütür) ve boşlukları belirtilen renkle doldurur.
    Varsayılan dolgu rengi beyazdır.
    """
    try:
        img = Image.open(path).convert("RGBA")

        original_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]

        if original_ratio > target_ratio:
            new_width = target_size[0]
            new_height = int(new_width / original_ratio)
        else:
            new_height = target_size[1]
            new_width = int(new_height * original_ratio)

        # Resmi yeni boyutlara ölçekle (LANCZOS en kaliteli filtrelerden biridir)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Hedef boyutta yeni bir tuval oluştur
        new_img = Image.new("RGBA", target_size, fill_color)

        x_offset = (target_size[0] - new_width) // 2
        y_offset = (target_size[1] - new_height) // 2
        new_img.paste(resized_img, (x_offset, y_offset), resized_img) # maske olarak kendisini kullan

        new_img.save(path)
    except Exception as e:
        print(f"❌ Error while resizing/filling image '{os.path.basename(path)}': {e}")


# === ANA İŞLEM DÖNGÜSÜ ===
try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")
        
        wait = WebDriverWait(driver, 10)
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        option_paths = []

        # --- Soru Görüntüsü (Sayılar Görünürken) ---
        try:
            question_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#question:not(.hidden)")))
            print("✅ Sayılar görünür, soru ekran görüntüsü alınıyor.")
            question_elem.screenshot(question_path)
            
            trim_and_pad_image(question_path, padding=QUESTION_PADDING)
            resize_and_fill_image(question_path, QUESTION_TARGET_SIZE)
        except Exception:
            print("❌ Hata: Soru ekran görüntüsü alınamadı. Bu soru atlanıyor.")
            driver.refresh()
            time.sleep(1)
            continue
            
        # --- Şık Görüntüleri (Sayılar Kaybolduktan Sonra) ---
        try:
            print("... Sayıların gizlenmesi ve şıkların belirmesi bekleniyor ...")
            options_container = wait.until(EC.visibility_of_element_located((By.ID, "options")))
            print("✅ Şıklar görünür, şık ekran görüntüleri alınıyor.")
            
            options_elements = options_container.find_elements(By.CLASS_NAME, "option")
            for idx, opt in enumerate(options_elements[:4]):
                choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
                opt.screenshot(choice_path)
                
                trim_and_pad_image(choice_path, padding=CHOICE_PADDING)
                resize_and_fill_image(choice_path, CHOICE_TARGET_SIZE)
                
                option_paths.append(choice_path)
        except Exception:
            print("❌ Hata: Şıklar yakalanamadı. Bu soru atlanıyor.")
            driver.refresh()
            time.sleep(1)
            continue

        # --- Doğru Cevabı Oku ve API'ye Gönder ---
        correct_index_str = driver.execute_script("return document.getElementById('correctIndex').textContent;")
        if not correct_index_str:
            print("❌ Hata: Doğru cevap indeksi bulunamadı. Bu soru atlanıyor.")
            driver.refresh()
            time.sleep(3)
            continue

        correct_index = int(correct_index_str)
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
        print(f"ℹ️ Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")
        
        try:
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
                    "category_id": "29",
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

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            print("... Sonraki oyunun otomatik başlaması bekleniyor ...")
            time.sleep(3) # Oyunun seçim sonrası geri sayım ve yeniden başlama süresi

finally:
    driver.quit()
    print("\n🎉 Tüm sorular başarıyla işlendi. Program sonlandırıldı.")