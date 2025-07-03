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
PROJECT_DIRECTORY = "C:/Users/cetin/Desktop/WebTools/" # EXAMPLE: "C:/Games/JigsawGame"

# 2. Enter the name of the HTML file you want to automate.
HTML_FILE_NAME = "GuessTilePiece.html" # EXAMPLE: "jigsaw_game.html"

# 3. Other settings
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/GuessTilePieceQuestions" # Directory to save the screenshots
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
    
    server_process = subprocess.Popen(
        command,
        cwd=directory,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags
    )
    print("✅ Server started successfully.")
    return server_process

def stop_server():
    """Stops the running web server."""
    global server_process
    if server_process:
        print("\n gracefully shutting down the server...")
        server_process.kill()
        server_process = None
        print("✅ Server shut down.")

# Ensure the server is stopped automatically when the script exits
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
start_server(PROJECT_DIRECTORY, port)
LOCAL_FILE_URL = f"http://localhost:{port}/{HTML_FILE_NAME}"

# 2. Run the Selenium automation
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)

try:
    driver.get(LOCAL_FILE_URL)
    time.sleep(1) # Initial wait for the page to load

    choice_labels = ['A', 'B', 'C', 'D']

    def resize_image(path, target_size):
        img = Image.open(path).convert("RGBA")
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
        x_offset, y_offset = (target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2
        new_img.paste(img, (x_offset, y_offset))
        new_img.save(path)

    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Processing Question {i} ---")
        
        # Smart wait: Wait for the game to be fully loaded by checking for the options
        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#choices button")))
            print("👍 Game loaded, taking screenshots.")
            time.sleep(1) # Extra wait for drawing to settle
        except Exception as e:
            print(f"❌ Error: Game could not be loaded for question {i} within 20 seconds.")
            continue 

        # --- Question Image ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "mainCanvas")
        question_elem.screenshot(question_path)
        resize_image(question_path, (800, 800))

        # --- Answer Choices ---
        options_elements = driver.find_elements(By.CSS_SELECTOR, "#choices button")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            resize_image(choice_path, (300, 300))
            option_paths.append(choice_path)

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

            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            print(f"✅ Question {i} sent. Correct choice: {choice_labels[correct_index]} | Status: {response.status_code}")

        # --- Proceed to the Next Question ---
        if i < NUM_QUESTIONS:
            driver.find_element(By.ID, "startBtn").click()
            print("Moving to the next question...")

finally:
    driver.quit()
    print("🎉 Automation complete. Browser closed.")