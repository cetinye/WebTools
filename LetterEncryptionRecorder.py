from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import os
import time

# CONFIGURATION
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/LetterEncryptionQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/LetterEncryption.html"  # file:/// is required for local files

# SETUP
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# PREPARE SAVE DIR
os.makedirs(SAVE_DIR, exist_ok=True)

# OPEN FILE
driver.get(LOCAL_FILE_URL)
time.sleep(1)

choice_labels = ['A', 'B', 'C', 'D', 'E']

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.7)  # Allow question to render

    # --- Screenshot the question (wordRow + questionRow together) ---
    word_row = driver.find_element(By.ID, "wordRow")
    question_row = driver.find_element(By.ID, "questionRow")

    # Take screenshot of each row and combine them using Pillow
    word_path = os.path.join(SAVE_DIR, f"temp_word_{i}.png")
    question_path = os.path.join(SAVE_DIR, f"temp_question_{i}.png")
    word_row.screenshot(word_path)
    question_row.screenshot(question_path)

    img_word = Image.open(word_path)
    img_question = Image.open(question_path)

    total_width = max(img_word.width, img_question.width)
    total_height = img_word.height + img_question.height

    combined = Image.new("RGB", (total_width, total_height), "white")
    combined.paste(img_word, (0, 0))
    combined.paste(img_question, (0, img_word.height))

    # Crop left/right margin
    crop_margin = int(total_width * 0.30)
    cropped = combined.crop((crop_margin, 0, total_width - crop_margin, total_height))
    cropped.save(os.path.join(SAVE_DIR, f"question_{i}.png"))

    # Cleanup temp files
    os.remove(word_path)
    os.remove(question_path)

    # --- Screenshot individual choices ---
    options = driver.find_elements(By.CLASS_NAME, "option")
    for idx, opt in enumerate(options[:5]):
        choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
        opt.screenshot(choice_path)

    # --- Next question ---
    driver.execute_script("startGame();")
    time.sleep(0.5)

driver.quit()
print("✅ Done! All questions and choices captured.")
