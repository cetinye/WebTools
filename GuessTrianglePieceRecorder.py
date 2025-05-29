from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import os
import time

# === CONFIGURATION ===
NUM_QUESTIONS = 30
SAVE_DIR = "C:/Users/cetin/Desktop/TrianglePieceQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/GuessTrianglePiece.html"  # file:/// gerekli

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)
time.sleep(0.1)

choice_labels = ['A', 'B', 'C', 'D']

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.1)  # SVG yüklenmesini bekle

    # --- Screenshot the main SVG (question) ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    svg_elem = driver.find_element(By.CSS_SELECTOR, "svg.main")
    svg_elem.screenshot(question_path)

    # Crop horizontal whitespace from question image
    img = Image.open(question_path)
    width, height = img.size
    crop_margin = int(width * 0.01)
    cropped = img.crop((crop_margin, 0, width - crop_margin, height))
    cropped.save(question_path)

    # --- Screenshot each option (svg.option) ---
    option_elems = driver.find_elements(By.CSS_SELECTOR, "svg.option")
    for idx, opt in enumerate(option_elems[:4]):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        opt.screenshot(choice_path)

    # --- Refresh the page for a new question ---
    driver.refresh()
    time.sleep(0.1)

driver.quit()
print("✅ Tamamlandı: Tüm sorular ve seçenekler kaydedildi.")
