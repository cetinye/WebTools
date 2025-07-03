import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import os
import time

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/AnimalWordGameQuestions" # Kaydedilecek klasör
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/AnimalWordGame.html"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}  # Gerekirse kullan

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)
time.sleep(0.5) # Oyunun yüklenmesi için yarım saniye bekle

choice_labels = ['A', 'B', 'C', 'D']

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
    # HTML'e eklediğimiz id="question-area" div'ini buluyoruz.
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    question_elem = driver.find_element(By.ID, "question-area")
    question_elem.screenshot(question_path)
    # Görüntü boyutlarını isteğe bağlı olarak ayarlayabilirsiniz.
    resize_image(question_path, (1190, 330))

    # --- Şıklar ---
    # HTML'deki class="option" olan elementleri buluyoruz.
    # Bu oyunun yapısı önceki kodla aynı olduğu için bu kısım değişmedi.
    options_elements = driver.find_elements(By.CLASS_NAME, "option")
    option_paths = []
    for idx, opt in enumerate(options_elements[:4]):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        opt.screenshot(choice_path)
        # Görüntü boyutlarını isteğe bağlı olarak ayarlayabilirsiniz.
        resize_image(choice_path, (271, 181))
        option_paths.append(choice_path)

    # === ✅ DOĞRU CEVABI HTML'DEN OKU ===
    # Bu kısım, HTML'e eklediğimiz yapı sayesinde sorunsuz çalışır.
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
            "question_image": q_img,
            "correct_answer": correct,
            "wrong_answer_1": wrong1,
            "wrong_answer_2": wrong2,
            "wrong_answer_3": wrong3
        }

        data = {
            "category_id": "24", # Bu değeri API'nize göre ayarlayın
            "grade": "[1,2,3,4,9]",
            "knowledge": "0",
            "level": "1"
        }

        try:
            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")
            # print("Sunucu Cevabı:", response.text) # Hata ayıklama için gerekirse açın
        except requests.exceptions.RequestException as e:
            print(f"❌ Soru {i} gönderilirken hata oluştu: {e}")

    # Yeni soru için sayfayı yenile
    driver.refresh()
    time.sleep(0.5) # Yenileme sonrası oyunun yüklenmesini bekle

driver.quit()
print("🎉 Tüm sorular sunucuya gönderildi.")