import os
import time
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# === CONFIGURATION ===
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/DiceGameQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/DiceGame.html"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# === SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

def resize_image(path, target_size):
    img = Image.open(path).convert("RGBA")
    img.thumbnail(target_size, Image.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x_offset = (target_size[0] - img.size[0]) // 2
    y_offset = (target_size[1] - img.size[1]) // 2
    new_img.paste(img, (x_offset, y_offset))
    new_img.save(path)

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.5)

    # === Soru görünümünü al
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    question_elem = driver.find_element(By.ID, "question-area")
    question_elem.screenshot(question_path)
    resize_image(question_path, (800, 600))

    # === Bekle: 4 şık gelsin
    WebDriverWait(driver, 5).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".options button")) == 4)
    option_buttons = driver.find_elements(By.CSS_SELECTOR, ".options button .die")

    option_paths = []
    for idx, btn in enumerate(option_buttons):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        btn.screenshot(choice_path)
        resize_image(choice_path, (256, 256))
        option_paths.append(choice_path)

    # ✅ Doğru şıkkı DOM'dan oku
    # ❗ Bekle: correctIndex DOM'da yazılmış olsun
    WebDriverWait(driver, 5).until(lambda d: d.execute_script("return document.getElementById('correctIndex').textContent !== ''"))

    # Artık doğru değer güvenli şekilde alınabilir
    correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent"))
    correct_path = option_paths[correct_index]
    wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

    # === API'ye gönder
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
            "category_id": "25",
            "grade": "[1,2,3,4,9]",
            "knowledge": "0",
            "level": "1"
        }

        response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
        print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")

    driver.refresh()
    time.sleep(0.5)

driver.quit()
print("🎉 Tüm sorular başarıyla gönderildi.")
