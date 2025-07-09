import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageChops
import os
import time

# === CONFIGURATION ===
# Kaç adet soru işleneceğini belirtin
NUM_QUESTIONS = 1

# Dosyaların kaydedileceği klasör
SAVE_DIR = "C:/Users/cetin/Desktop/AnimalWordGameQuestions"

# Selenium'un açacağı yerel HTML dosyasının yolu
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/AnimalWordGame.html"

# API bilgileri
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"} # <<< KENDİ TOKEN'INIZI GİRİN

# --- GÖRSEL İŞLEME AYARLARI ---
# Artık padding ayarları yok, çünkü her zaman tam kırpma yapılacak.

# Soru ve şıkların son boyutları
QUESTION_TARGET_SIZE = (1024, 1024)
CHOICE_TARGET_SIZE = (256, 256)

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Kayıt klasörünü oluştur (varsa hata verme)
os.makedirs(SAVE_DIR, exist_ok=True)

# Web sayfasını aç
driver.get(LOCAL_FILE_URL)
time.sleep(0.5) # Sayfanın tam yüklenmesi için kısa bir bekleme

choice_labels = ['A', 'B', 'C', 'D']

# === GÖRSEL İŞLEME FONKSİYONLARI ===

# <-- DEĞİŞİKLİK: Fonksiyon sadece boşlukları kırpmak için basitleştirildi ve yeniden adlandırıldı.
def trim_whitespace(image_path):
    """
    Bir görüntünün kenarlarındaki arka plan rengini otomatik olarak kırpar.
    Kenarlardaki farklı renkleri de dikkate alır.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size

        # Kenarlardaki baskın olmayan beyaz tonlarını belirlemek için eşik değeri
        threshold = 240  # Beyaza yakın RGB değerleri (0-255 arası)

        def is_mostly_white(color, alpha):
            return alpha > 200 and all(c > threshold for c in color[:3])

        # Sol kenardan ilk dolu pikseli bul
        left = 0
        for x in range(width):
            found = False
            for y in range(height):
                color = img.getpixel((x, y))
                if not is_mostly_white(color[:3], color[-1]):
                    left = x
                    found = True
                    break
            if found:
                break

        # Sağ kenardan ilk dolu pikseli bul
        right = width - 1
        for x in range(width - 1, -1, -1):
            found = False
            for y in range(height):
                color = img.getpixel((x, y))
                if not is_mostly_white(color[:3], color[-1]):
                    right = x
                    found = True
                    break
            if found:
                break

        # Üst kenardan ilk dolu pikseli bul
        top = 0
        for y in range(height):
            found = False
            for x in range(width):
                color = img.getpixel((x, y))
                if not is_mostly_white(color[:3], color[-1]):
                    top = y
                    found = True
                    break
            if found:
                break

        # Alt kenardan ilk dolu pikseli bul
        bottom = height - 1
        for y in range(height - 1, -1, -1):
            found = False
            for x in range(width):
                color = img.getpixel((x, y))
                if not is_mostly_white(color[:3], color[-1]):
                    bottom = y
                    found = True
                    break
            if found:
                break

        # Eğer dolu piksel bulunduysa kırp
        if left <= right and top <= bottom:
            cropped_img = img.crop((left, top, right + 1, bottom + 1))
            cropped_img.save(image_path)
            # print(f"✨ Whitespace trimmed successfully for '{os.path.basename(image_path)}'.")
        else:
            print(f"⚠️ Image '{os.path.basename(image_path)}' seems to be entirely whitespace.")

    except Exception as e:
        print(f"❌ Error while trimming image '{os.path.basename(image_path)}': {e}")


def resize_and_fill_image(path, target_size, fill_color=(255, 255, 255, 255)):
    """
    Bir görüntüyü, en-boy oranını koruyarak hedef boyuta sığacak şekilde
    yeniden boyutlandırır ve boşlukları belirtilen renkle doldurur.
    """
    # try:
    #     img = Image.open(path).convert("RGBA")

    #     original_ratio = img.width / img.height
    #     target_ratio = target_size[0] / target_size[1]

    #     if original_ratio > target_ratio:
    #         new_width = target_size[0]
    #         new_height = int(new_width / original_ratio)
    #     else:
    #         new_height = target_size[1]
    #         new_width = int(new_height * original_ratio)
            
    #     resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    #     new_img = Image.new("RGBA", target_size, fill_color)
    #     x_offset = (target_size[0] - new_width) // 2
    #     y_offset = (target_size[1] - new_height) // 2
    #     new_img.paste(resized_img, (x_offset, y_offset), resized_img)
    #     new_img.save(path)
    # except Exception as e:
    #     print(f"❌ Error while resizing/filling image '{os.path.basename(path)}': {e}")


# === ANA İŞLEM DÖNGÜSÜ ===

for i in range(1, NUM_QUESTIONS + 1):
    print(f"\n--- Soru {i} işleniyor ---")
    time.sleep(0.2)

    # --- Soru görüntüsünü al ve işle ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    question_elem = driver.find_element(By.ID, "question-area")
    question_elem.screenshot(question_path)
    
    # <-- DEĞİŞİKLİK: Sadece kırpma fonksiyonu çağrılıyor.
    trim_whitespace(question_path)
    resize_and_fill_image(question_path, QUESTION_TARGET_SIZE)
    print("✅ Soru görseli alındı ve işlendi.")

    # --- Şık görsellerini al ve işle ---
    options_elements = driver.find_elements(By.CLASS_NAME, "option")
    option_paths = []
    for idx, opt in enumerate(options_elements[:4]):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        opt.screenshot(choice_path)
        
        # <-- DEĞİŞİKLİK: Sadece kırpma fonksiyonu çağrılıyor.
        trim_whitespace(choice_path)
        resize_and_fill_image(choice_path, CHOICE_TARGET_SIZE)
        
        option_paths.append(choice_path)
    print("✅ Şık görselleri alındı ve işlendi.")
    
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

            files = {
                "question_image": q_img, 
                "correct_answer": correct,
                "wrong_answer_1": wrong1, 
                "wrong_answer_2": wrong2, 
                "wrong_answer_3": wrong3
            }
            data = {
                "category_id": "24", 
                "grade": "[1,2,3,4,9]", 
                "knowledge": "0", 
                "level": "1"
            }

            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            response.raise_for_status()
            
            print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Soru {i} API'ye gönderilirken hata oluştu: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"    API Yanıtı: {response.text}")

    # --- Sonraki soruya geç ---
    if i < NUM_QUESTIONS:
        print("... Sayfa yenileniyor ...")
        driver.refresh()
        time.sleep(0.5) # Yenilenen sayfanın yüklenmesini bekle

# === BİTİŞ ===
driver.quit()
print("\n🎉 Tüm sorular başarıyla işlendi. Program sonlandırıldı.")