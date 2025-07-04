import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageChops
import os
import time

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/AnimalWordGameQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/AnimalWordGame.html"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# EKLENDİ: Soru görselinin etrafına eklenecek boşluk miktarı (piksel cinsinden)
QUESTION_PADDING = 25

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)
time.sleep(0.5)

choice_labels = ['A', 'B', 'C', 'D']

# EKLENDİ: Görüntüdeki Boşlukları Otomatik Olarak Kırpan ve Boşluk Ekleyen Fonksiyon
def trim_and_pad_image(image_path, padding=0):
    """
    Bir görüntünün kenarlarındaki boş alanları kırpar ve ardından belirtilen miktarda
    boşluk (padding) ekler.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        # Arka plan rengiyle aynı olan piksellerden bir fark görüntüsü oluştur
        bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
        diff = ImageChops.difference(img, bg)
        # Farklı piksellerin olduğu alanın sınırlayıcı kutusunu bul
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
            # Görüntü tamamen boşsa dokunma
            print("⚠️ Image is empty, no trim needed.")
    except Exception as e:
        print(f"❌ Error while trimming/padding image: {e}")


def resize_image(path, target_size):
    """Görüntüyü şeffaf arka plan üzerinde orantılı olarak yeniden boyutlandırır."""
    img = Image.open(path).convert("RGBA")
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x_offset = (target_size[0] - img.size[0]) // 2
    y_offset = (target_size[1] - img.size[1]) // 2
    new_img.paste(img, (x_offset, y_offset))
    new_img.save(path)

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.2)

    # --- Soru görüntüsü ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    question_elem = driver.find_element(By.ID, "question-area")
    
    question_elem.screenshot(question_path)
    
    # EKLENDİ: Soru görselindeki gereksiz beyaz boşlukları kırp ve padding ekle
    trim_and_pad_image(question_path, padding=QUESTION_PADDING)

    # Temizlenmiş ve padding eklenmiş görüntüyü yeniden boyutlandır
    resize_image(question_path, (800, 600))
    print("📸 Question screenshot taken and processed.")

    # --- Şıklar (DEĞİŞİKLİK YOK) ---
    options_elements = driver.find_elements(By.CLASS_NAME, "option")
    option_paths = []
    for idx, opt in enumerate(options_elements[:4]):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        opt.screenshot(choice_path)
        resize_image(choice_path, (256, 256))
        option_paths.append(choice_path)
    print("📸 Options screenshots taken.")
    
    # === DOĞRU CEVABI HTML'DEN OKU ===
    correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
    correct_path = option_paths[correct_index]
    wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

    # --- API'ye gönder ---
    with open(question_path, 'rb') as q_img, \
         open(correct_path, 'rb') as correct, \
         open(wrong_paths[0], 'rb') as wrong1, \
         open(wrong_paths[1], 'rb') as wrong2, \
         open(wrong_paths[2], 'rb') as wrong3:

        files = {
            "question_image": q_img, "correct_answer": correct,
            "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3
        }
        data = {
            "category_id": "24", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"
        }

        try:
            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")
            # print(f"✅ Soru {i} işlendi. Doğru şık: {choice_labels[correct_index]}. (API çağrısı yorum satırında)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Soru {i} gönderilirken hata oluştu: {e}")

    # Yeni soru için sayfayı yenile
    driver.refresh()
    time.sleep(0.5)

driver.quit()
print("🎉 Tüm sorular işlendi.")