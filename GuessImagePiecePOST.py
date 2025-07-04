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
# ===  konfigurasyon (SADECE BU BÖLÜMÜ DEĞİŞTİR) ===
# ==============================================================================

# 1. Proje dosyalarının bulunduğu klasörün tam yolunu buraya yaz.
# ÖNEMLİ: Windows'ta ters eğik çizgileri (\\) veya normal eğik çizgileri (/) kullan.
PROJECT_DIRECTORY = "C:/Users/cetin/Desktop/WebTools/"

# 2. Otomasyonunu yapmak istediğin HTML dosyasının adını yaz.
HTML_FILE_NAME = "GuessImagePiece.html" #ÖRNEK: "yedinci_oyun.html"

# 3. Diğer ayarların
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/GuessImagePiece" # Directory to save the screenshots
# API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# ==============================================================================
# === OTOMATİK SUNUCU VE OTOMASYON KODU (DEĞİŞTİRME) ===
# ==============================================================================

server_process = None

def find_free_port():
    """Bilgisayarda boş bir port bulur."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_server(directory, port):
    """Belirtilen klasörde ve portta bir web sunucusu başlatır."""
    global server_process
    # Python'un mevcut sürümünü kullanarak sunucuyu başlat
    python_executable = sys.executable
    command = [python_executable, "-m", "http.server", str(port)]
    
    print(f"🌍 {port} portunda, '{directory}' klasörü için web sunucusu başlatılıyor...")
    
    # Windows'ta yeni bir konsol penceresi açılmasını engelle
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    
    server_process = subprocess.Popen(
        command,
        cwd=directory, # Sunucunun doğru klasörde çalışmasını sağlar
        stdout=subprocess.DEVNULL, # Sunucu loglarını gizle
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags
    )
    print("✅ Sunucu başarıyla başlatıldı.")
    return server_process

def stop_server():
    """Başlatılan web sunucusunu durdurur."""
    global server_process
    if server_process:
        print("\n gracefully sunucuyu kapatıyor...")
        server_process.kill()
        server_process = None
        print("✅ Sunucu kapatıldı.")

# Programdan çıkıldığında sunucunun otomatik olarak kapanmasını sağla
atexit.register(stop_server)

# --- ANA PROGRAM ---
if not os.path.isdir(PROJECT_DIRECTORY):
    print(f"❌ Hata: Belirtilen proje klasörü bulunamadı! -> {PROJECT_DIRECTORY}")
    exit()

html_full_path = os.path.join(PROJECT_DIRECTORY, HTML_FILE_NAME)
if not os.path.isfile(html_full_path):
    print(f"❌ Hata: Belirtilen HTML dosyası bulunamadı! -> {html_full_path}")
    exit()

# 1. Web sunucusunu başlat
port = find_free_port()
start_server(PROJECT_DIRECTORY, port)
LOCAL_FILE_URL = f"http://localhost:{port}/{HTML_FILE_NAME}"

# 2. Selenium otomasyonunu çalıştır
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)

try:
    driver.get(LOCAL_FILE_URL)

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
        
        # Akıllı bekleme: Oyunun tam olarak yüklenmesini bekle
        try:
            wait = WebDriverWait(driver, 20)
            # Seçenek butonlarının olduğu konteynerde en az bir buton oluşana kadar bekle
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#choices button")))
            print("👍 Oyun yüklendi, ekran görüntüleri alınıyor.")
            time.sleep(1) # Çizimlerin tam oturması için ek bir bekleme
        except Exception:
            print(f"❌ Hata: Soru {i} için oyun 20 saniyede yüklenemedi.")
            continue # Bu soruyu atla, sonrakiyle devam et

        # --- Soru görüntüsü ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        question_elem = driver.find_element(By.ID, "mainCanvas")
        question_elem.screenshot(question_path)
        resize_image(question_path, (800, 600))

        # --- Şıklar ---
        options_elements = driver.find_elements(By.CSS_SELECTOR, "#choices button")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            resize_image(choice_path, (200, 150))
            option_paths.append(choice_path)

        # --- Doğru Cevabı Oku ve API'ye Gönder ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3:
            
            files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
            data = {"category_id": "27", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
            print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            driver.find_element(By.ID, "newGameButton").click()
            print("Sonraki soruya geçiliyor...")

finally:
    driver.quit()
    print("🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")