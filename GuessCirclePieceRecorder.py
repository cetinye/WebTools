from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import os
import time

# === CONFIGURATION ===
NUM_QUESTIONS = 3
SAVE_DIR = "C:/Users/cetin/Desktop/GuessCirclePieceQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/GuessCirclePiece.html"

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)
time.sleep(0.2)

choice_labels = ['A', 'B', 'C', 'D']

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.2)  # render süresi

    # --- Ana grid (question) ekran görüntüsü ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    grid_elem = driver.find_element(By.ID, "mainGrid")
    grid_elem.screenshot(question_path)

    # Görüntüyü sağ/soldan kırp
    img = Image.open(question_path)
    width, height = img.size
    crop_margin = int(width * 0.001)
    if width - 2 * crop_margin <= 0:
        crop_margin = 0
    cropped = img.crop((crop_margin, 0, width - crop_margin, height))
    cropped.save(question_path)

    # --- Her seçeneğin ekran görüntüsünü al ---
    options = driver.find_elements(By.CLASS_NAME, "option")
    for idx, opt in enumerate(options[:4]):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        opt.screenshot(choice_path)

    # --- Sayfayı yenileyerek yeni soru yükle ---
    driver.refresh()
    time.sleep(0.2)

driver.quit()
print("✅ Tüm sorular ve seçenekler başarıyla kaydedildi.")
