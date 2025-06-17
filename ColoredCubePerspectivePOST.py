import os
import time
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/PerspectiveGameQuestions" # DEĞİŞTİ: Klasör adını yeni oyuna uygun hale getirdim
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/ColoredCubePerspective.html"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

def resize_image(path, target_size):
    """Resimleri yeniden boyutlandırır ve ortalar."""
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", target_size, (255, 255, 255, 0))
        x_offset = (target_size[0] - img.size[0]) // 2
        y_offset = (target_size[1] - img.size[1]) // 2
        new_img.paste(img, (x_offset, y_offset))
        new_img.save(path, "PNG")
    except Exception as e:
        print(f"Resim işlenirken hata oluştu: {path} | Hata: {e}")

for i in range(1, NUM_QUESTIONS + 1):
    print(f"--- Soru {i} oluşturuluyor... ---")
    time.sleep(1) # Oyunun tam yüklenmesi için kısa bir bekleme

    # === Soru prizma yapısının ekran görüntüsünü al ===
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    # DEĞİŞTİ: Soru alanı artık "puzzle-area" class'ına sahip
    structure_elem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "puzzle-area"))
    )
    structure_elem.screenshot(question_path)
    resize_image(question_path, (1000, 300))
    print(f"Soru ekran görüntüsü alındı: {question_path}")

    # === 4 seçeneğin de oluşmasını ve doğru cevabın yazılmasını bekle ===
    # DEĞİŞTİ: Artık body etiketindeki 'data-correct-index' attribute'unu bekliyoruz
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.TAG_NAME, "body").get_attribute("data-correct-index") is not None
    )

    # === Seçeneklerin ekran görüntülerini al ===
    # DEĞİŞTİ: Seçenek kutularının class'ı artık ".option-box"
    option_elements = driver.find_elements(By.CSS_SELECTOR, ".option-box")
    option_paths = []

    # Eğer 4 seçenek bulunamazsa, bir sonraki denemeye geç
    if len(option_elements) != 4:
        print(f"HATA: {len(option_elements)} adet seçenek bulundu, 4 bekleniyordu. Sayfa yenileniyor.")
        driver.refresh()
        continue

    for idx, btn in enumerate(option_elements):
        option_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        btn.screenshot(option_path)
        resize_image(option_path, (271, 181))
        option_paths.append(option_path)
    print("4 adet seçenek görüntüsü alındı.")

    # === Doğru cevabın index'ini HTML'den oku ===
    # DEĞİŞTİ: Değeri body etiketinin 'data-correct-index' attribute'undan alıyoruz
    correct_index_str = driver.find_element(By.TAG_NAME, "body").get_attribute("data-correct-index")
    correct_index = int(correct_index_str)
    
    correct_path = option_paths[correct_index]
    wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

    print(f"Doğru cevap tespit edildi: Şık {choice_labels[correct_index]}")

    # === API'ye Gönder ===
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
                "category_id": "25", # Kategori ID'nizi buraya girebilirsiniz
                "grade": "[1,2,3,4,9]",
                "knowledge": "0",
                "level": "1"
            }

            # response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            # print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")
            if response.status_code != 200:
                print("Hata mesajı:", response.text)

    except FileNotFoundError as e:
        print(f"HATA: Resim dosyası bulunamadı - {e}")
    except Exception as e:
        print(f"API'ye gönderilirken bir hata oluştu: {e}")


    # === Bir sonraki soru için sayfayı yenile ===
    driver.refresh()

driver.quit()
print("\n🎉 Tüm işlemler tamamlandı.")