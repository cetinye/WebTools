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
from PIL import Image, ImageChops, ImageFilter

# ==============================================================================
# ===  Konfigürasyon (Sadece bu bölümü değiştir) ===
# ==============================================================================

# 1. Proje dosyalarının bulunduğu klasörün tam yolunu buraya yaz.
PROJECT_DIRECTORY = "C:/Users/cetin/Desktop/WebTools/"

# 2. Otomasyonunu yapmak istediğin HTML dosyasının adını yaz.
HTML_FILE_NAME = "GuessTilePiece.html"

# 3. Diğer ayarların
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/GuessTilePieceQuestions"
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"} # <<< KENDİ TOKEN'INIZI GİRİN

# --- GÖRSEL İŞLEME AYARLARI ---
QUESTION_PADDING = 0
CHOICE_PADDING = 0
QUESTION_TARGET_SIZE = (1200, 600)
CHOICE_TARGET_SIZE = (256, 256)


# ==============================================================================
# === Otomatik Sunucu ve Otomasyon Kodu (Değiştirme) ===
# ==============================================================================
server_process = None
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0)); return s.getsockname()[1]

def start_server(directory, port):
    global server_process
    python_executable = sys.executable
    command = [python_executable, "-m", "http.server", str(port)]
    print(f"🌍 {port} portunda sunucu başlatılıyor...")
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    server_process = subprocess.Popen(command, cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
    print("✅ Sunucu başarıyla başlatıldı.")

def stop_server():
    global server_process
    if server_process:
        print("\nSunucu kapatılıyor..."); server_process.kill(); server_process = None; print("✅ Sunucu kapatıldı.")

atexit.register(stop_server)

def trim_and_pad_image(image_path, padding=0):
    try:
        img = Image.open(image_path).convert("RGB")
        bg_color = img.getpixel((0, 0))
        bg = Image.new(img.mode, img.size, bg_color)
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox:
            trimmed_img = img.crop(bbox)
            if padding > 0:
                new_size = (trimmed_img.width + 2 * padding, trimmed_img.height + 2 * padding)
                padded_img = Image.new(img.mode, new_size, bg_color)
                padded_img.paste(trimmed_img, (padding, padding))
                padded_img.save(image_path)
            else:
                trimmed_img.save(image_path)
        else:
            print(f"⚠️ Image '{os.path.basename(image_path)}' is empty, no trim needed.")
    except Exception as e:
        print(f"❌ Error while trimming/padding image '{os.path.basename(image_path)}': {e}")

def resize_and_fill_image(path, target_size, fill_color=(255, 255, 255, 255)):
    try:
        img = Image.open(path).convert("RGBA")
        original_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        if original_ratio > target_ratio:
            new_width = target_size[0]
            new_height = int(new_width / original_ratio)
        else:
            new_height = target_size[1]
            new_width = int(new_height * original_ratio)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", target_size, fill_color)
        x_offset = (target_size[0] - new_width) // 2
        y_offset = (target_size[1] - new_height) // 2
        new_img.paste(resized_img, (x_offset, y_offset), resized_img)
        new_img.save(path)
    except Exception as e:
        print(f"❌ Error while resizing/filling image '{os.path.basename(path)}': {e}")


# --- ANA PROGRAM ---
if not os.path.isdir(PROJECT_DIRECTORY):
    print(f"❌ Hata: Proje klasörü bulunamadı! -> {PROJECT_DIRECTORY}"); sys.exit(1)
html_full_path = os.path.join(PROJECT_DIRECTORY, HTML_FILE_NAME)
if not os.path.isfile(html_full_path):
    print(f"❌ Hata: HTML dosyası bulunamadı! -> {html_full_path}"); sys.exit(1)

port = find_free_port()
SERVER_URL = f"http://localhost:{port}/{HTML_FILE_NAME}"
start_server(PROJECT_DIRECTORY, port)

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(SERVER_URL)
choice_labels = ['A', 'B', 'C', 'D']

try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")
        
        # Oyunun yüklenmesini bekle
        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#choices button")))
            time.sleep(1)
        except Exception:
            print(f"❌ Hata: Soru {i} için oyun 20 saniyede yüklenemedi."); continue

        # --- Soru görüntüsünü al ve işle ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "mainCanvas")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", question_elem)
        time.sleep(0.5)
        question_elem.screenshot(question_path)
        trim_and_pad_image(question_path, padding=QUESTION_PADDING)
        resize_and_fill_image(question_path, QUESTION_TARGET_SIZE)
        print("✅ Soru görseli alındı ve işlendi.")

        # --- Şık görsellerini al ve işle ---
        options_elements = driver.find_elements(By.CSS_SELECTOR, "#choices button")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opt)
            time.sleep(0.3)
            opt.screenshot(choice_path)
            trim_and_pad_image(choice_path, padding=CHOICE_PADDING)
            resize_and_fill_image(choice_path, CHOICE_TARGET_SIZE)
            option_paths.append(choice_path)
        print("✅ Şık görselleri alındı ve işlendi.")
        
        # --- Doğru cevabı HTML'den oku ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]
        print(f"ℹ️ Doğru cevap '{choice_labels[correct_index]}' olarak belirlendi.")

        # --- API'ye gönder ---
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
                    "category_id": "27",
                    "grade": "[1,2,3,4,9]", 
                    "knowledge": "0", 
                    "level": "1"
                }
                response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                response.raise_for_status()
                print(f"🚀 Soru {i} API'ye başarıyla gönderildi. Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Soru {i} API'ye gönderilirken hata oluştu: {e}")
            if 'response' in locals() and response is not None:
                print(f"    API Yanıtı: {response.text}")

        # --- Sonraki soruya geç ---
        if i < NUM_QUESTIONS:
            print("... Yeni soru için butona tıklandı ...")
            driver.find_element(By.ID, "startBtn").click()

finally:
    driver.quit()
    print("\n🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")