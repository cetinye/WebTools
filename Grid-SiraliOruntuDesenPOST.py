import os
import sys
import socket
import subprocess
import atexit
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

# ==============================================================================
# ===  CONFIGURATION (EDIT ONLY THIS SECTION) ===
# ==============================================================================

# 1. Enter the full path to the folder containing your project files.
# IMPORTANT: Use forward slashes (/) or double backslashes (\\) in Windows.
PROJECT_DIRECTORY = "C:/Users/cetin/Desktop/WebTools" # EXAMPLE: "C:/Games/PatternGame"

# 2. Enter the name of the HTML file you want to automate.
HTML_FILE_NAME = "Grid-SiraliOruntuDesen.html" # This must match the name of your saved HTML file.

# 3. Other settings
NUM_QUESTIONS = 1
SAVE_DIR = os.path.join(PROJECT_DIRECTORY, "Grid-SiraliOruntuDesen")
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# ==============================================================================
# === AUTOMATIC SERVER & AUTOMATION CODE (DO NOT CHANGE) ===
# ==============================================================================

server_process = None

def find_free_port():
    """Finds a free port on the local machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_server(directory, port):
    """Starts a web server in the specified directory and port."""
    global server_process
    python_executable = sys.executable
    command = [python_executable, "-m", "http.server", str(port)]
    print(f"🌍 Starting web server for '{directory}' on port {port}...")
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    server_process = subprocess.Popen(command, cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
    print("✅ Server started successfully.")
    return server_process

def stop_server():
    """Stops the running web server."""
    global server_process
    if server_process:
        print("\n Shutting down the server...")
        server_process.kill()
        server_process = None
        print("✅ Server shut down.")

atexit.register(stop_server)

# --- MAIN PROGRAM ---
if not os.path.isdir(PROJECT_DIRECTORY):
    print(f"❌ Error: The specified project directory was not found! -> {PROJECT_DIRECTORY}")
    exit()

html_full_path = os.path.join(PROJECT_DIRECTORY, HTML_FILE_NAME)
if not os.path.isfile(html_full_path):
    print(f"❌ Error: The specified HTML file was not found! -> {html_full_path}")
    exit()

# 1. Start the web server
port = find_free_port()
SERVER_URL = f"http://localhost:{port}/{HTML_FILE_NAME}"
start_server(PROJECT_DIRECTORY, port)

# 2. Run the Selenium automation
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(SERVER_URL)

choice_labels = ['A', 'B', 'C', 'D']

def resize_image(path, target_size):
    img = Image.open(path).convert("RGBA")
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x_offset, y_offset = (target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2
    new_img.paste(img, (x_offset, y_offset))
    new_img.save(path)

try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Processing Question {i} ---")
        
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "option-item")))
            print("👍 Game loaded, taking screenshots.")
            time.sleep(0.5) 
        except Exception:
            print(f"❌ Error: Game could not be loaded for question {i} within 10 seconds.")
            break 

        # --- Question Image ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "pattern-sequence-container")
        question_elem.screenshot(question_path)
        resize_image(question_path, (800, 100))
        print("📸 Question screenshot taken.")

        # --- Answer Choices ---
        options_elements = driver.find_elements(By.CLASS_NAME, "option-item")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            resize_image(choice_path, (100, 100))
            option_paths.append(choice_path)
        print("📸 Options screenshots taken.")

        # --- Read Correct Answer and Send to API ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3:
            
            files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
            data = {"category_id": "25", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            try:
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                print(f"✅ Question {i} sent. Correct choice: {choice_labels[correct_index]} | Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error: API error while sending question {i}: {e}")

        # --- Proceed to the Next Question ---
        if i < NUM_QUESTIONS:
            print("Clicking 'Yeni Oyun' button for the next question...")
            
            old_options = driver.find_elements(By.CLASS_NAME, "option-item")
            driver.find_element(By.ID, "new-game-button").click()
            
            if old_options:
                try:
                    wait = WebDriverWait(driver, 5)
                    wait.until(EC.staleness_of(old_options[0]))
                    print("...Old options cleared, waiting for new question.")
                except Exception:
                    print("...Could not confirm old options were cleared, proceeding anyway.")

finally:
    driver.quit()
    print("\n🎉 Automation complete. Browser closed.")