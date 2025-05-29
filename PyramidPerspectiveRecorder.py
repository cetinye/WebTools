from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import os
import time

# CONFIGURATION
NUM_QUESTIONS = 3
SAVE_DIR = "C:/Users/cetin/Desktop/PyramidPerspectiveQuestions"
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/PyramidPerspective.html"  # file:/// prefix is required

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Prepare folder
os.makedirs(SAVE_DIR, exist_ok=True)

# Start from the HTML file
driver.get(LOCAL_FILE_URL)
time.sleep(1)

choice_labels = ['A', 'B', 'C', 'D']

for i in range(1, NUM_QUESTIONS + 1):
    time.sleep(0.5)  # wait for drawing

    # --- Screenshot and crop the question canvas ---
    question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
    main_canvas = driver.find_element(By.ID, "mainView")
    main_canvas.screenshot(question_path)

    # Crop horizontal whitespace from main canvas
    img = Image.open(question_path)
    width, height = img.size
    crop_margin = int(width * 0.15)
    cropped = img.crop((crop_margin, 0, width - crop_margin, height))
    cropped.save(question_path)

    # --- Screenshot each option canvas individually ---
    option_elems = driver.find_elements(By.CLASS_NAME, "option-canvas")
    for idx, canvas in enumerate(option_elems):
        label = choice_labels[idx]
        canvas_path = os.path.join(SAVE_DIR, f"choice_{label}_{i}.png")
        canvas.screenshot(canvas_path)

    # --- Move to next question via JavaScript ---
    driver.execute_script("setupGame();")
    time.sleep(0.5)

driver.quit()
print("✅ All screenshots saved and cropped.")
