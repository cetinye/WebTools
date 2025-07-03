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
# ===  Konfigürasyon (Sadece bu bölümü değiştir) ===
# ==============================================================================

# 1. Proje dosyalarının bulunduğu klasörün tam yolunu buraya yaz.
PROJECT_DIRECTORY = "C:/Users/cetin/Desktop/WebTools/"

# 2. Otomasyonunu yapmak istediğin HTML dosyasının adını yaz.
HTML_FILE_NAME = "GuessTilePiece.html" # Sorun yaşadığınız oyunun orijinal HTML dosyası

# 3. Diğer ayarların
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/GuessTilePieceQuestions" 
API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

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
if not os.path.isdir(PROJECT_DIRECTORY):
    print(f"❌ Hata: Proje klasörü bulunamadı! -> {PROJECT_DIRECTORY}"); exit()
html_full_path = os.path.join(PROJECT_DIRECTORY, HTML_FILE_NAME)
if not os.path.isfile(html_full_path):
    print(f"❌ Hata: HTML dosyası bulunamadı! -> {html_full_path}"); exit()
port = find_free_port()
start_server(PROJECT_DIRECTORY, port)
LOCAL_FILE_URL = f"http://localhost:{port}/{HTML_FILE_NAME}"
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
os.makedirs(SAVE_DIR, exist_ok=True)
# ==============================================================================

try:
    driver.get(LOCAL_FILE_URL)
    time.sleep(1) 

    choice_labels = ['A', 'B', 'C', 'D']

    def resize_image(path, target_size):
        img = Image.open(path).convert("RGBA")
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
        x_offset, y_offset = (target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2
        new_img.paste(img, (x_offset, y_offset))
        new_img.save(path)

    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")
        
        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#choices button")))
            print("👍 Oyun yüklendi, ekran görüntüleri alınıyor.")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Hata: Soru {i} için oyun 20 saniyede yüklenemedi."); continue 

        # --- Soru görüntüsü ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "mainCanvas")
        
        # Kırpılmayı önlemek için elementi ekranın ortasına kaydır
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", question_elem)
        time.sleep(0.5) # Kaydırmanın tamamlanmasını bekle

        question_elem.screenshot(question_path)
        resize_image(question_path, (800, 800)) # Boyutları oyununuza göre ayarlayabilirsiniz

        # --- Şıklar ---
        options_elements = driver.find_elements(By.CSS_SELECTOR, "#choices button")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            
            # Kırpılmayı önlemek için HER BİR ŞIKKI da ekranın ortasına kaydır
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opt)
            time.sleep(0.3) # Kaydırmanın tamamlanmasını bekle
            
            opt.screenshot(choice_path)
            resize_image(choice_path, (300, 300)) # Boyutları oyununuza göre ayarlayabilirsiniz
            option_paths.append(choice_path)

        # --- Doğru Cevabı Oku ve API'ye Gönder (Çoklu Resim Formatında) ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

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
            data = {"category_id": "27", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            driver.find_element(By.ID, "startBtn").click()
            print("Sonraki soruya geçiliyor...")

finally:
    driver.quit()
    print("🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")