from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import os
import time

# CONFIGURATION
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/NextStepCircleQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/NextStepCircle.html"  # Note: file:/// prefix is required

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Create folder if not exists
os.makedirs(SAVE_DIR, exist_ok=True)

# Start from the quiz file
driver.get(LOCAL_FILE_URL)
time.sleep(1)

choice_labels = ['A', 'B', 'C', 'D']

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.5)  # Wait for question to render

    # --- Screenshot and crop the question ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    sequence = driver.find_element(By.ID, "sequence")
    sequence.screenshot(question_path)

    # Crop left/right margins using Pillow
    img = Image.open(question_path)
    width, height = img.size
    crop_margin = int(width * 0.30)  # crop 30% from each side
    cropped = img.crop((crop_margin, 0, width - crop_margin, height))
    cropped.save(question_path)

    # --- Screenshot each choice individually ---
    option_elements = driver.find_elements(By.CLASS_NAME, "option")
    for idx, option in enumerate(option_elements):
        if idx >= len(choice_labels):
            break
        label = choice_labels[idx]
        choice_path = os.path.join(SAVE_DIR, f"choice_{label}_{i}.png")
        option.screenshot(choice_path)

    # --- Load next question ---
    driver.execute_script("createGame();")
    time.sleep(0.5)

driver.quit()
print("✅ Done! All screenshots saved and cropped.")
