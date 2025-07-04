import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import os
import time

# ==============================================================================
# ===   YAPILANDIRMA (SADECE BU BÖLÜMÜ DEĞİŞTİR)                            ===
# ==============================================================================

# 1. HTML dosyanızın tam yolunu file:/// protokolü ile buraya yazın.
# ÖNEMLİ: Windows'ta yol için normal eğik çizgi (/) kullanın.
LOCAL_FILE_URL = "file:///C:/Users/cetin/Desktop/WebTools/ShapePerspective.html"

# 2. Diğer ayarlar
NUM_QUESTIONS = 1
SAVE_DIR = "C:/Users/cetin/Desktop/ShapePerspectiveQuestions"
# API_URL = "https://bilsem.izzgrup.com/api/ai-question-generation"
HEADERS = {"Authorization": "Bearer your_token_here"}

# ==============================================================================
# === OTOMASYON KODU (DEĞİŞTİRMEYİN)                                        ===
# ==============================================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

os.makedirs(SAVE_DIR, exist_ok=True)
driver.get(LOCAL_FILE_URL)

choice_labels = ['A', 'B', 'C', 'D']

# ⭐ YENİ: Görüntüleri istenen boyuta getiren fonksiyon eklendi.
def resize_image(path, target_size):
    """
    Bir görüntüyü, en boy oranını koruyarak ve şeffaf bir tuvale ortalayarak
    hedef boyuta getirir. Görüntü esnetilmez.
    """
    try:
        img = Image.open(path).convert("RGBA")
        
        # Orijinal görüntünün en boy oranını koruyarak küçült/büyüt
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Hedef boyutta şeffaf bir arka plan oluştur
        new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
        
        # Görüntüyü ortaya yapıştırmak için pozisyonu hesapla
        paste_x = (target_size[0] - img.width) // 2
        paste_y = (target_size[1] - img.height) // 2
        
        # Boyutlandırılmış görüntüyü yeni şeffaf arka planın üzerine yapıştır
        new_img.paste(img, (paste_x, paste_y))
        
        # Sonucu orijinal dosyanın üzerine kaydet
        new_img.save(path)
    except Exception as e:
        print(f"❌ Görüntü yeniden boyutlandırılamadı {path}: {e}")


try:
    for i in range(1, NUM_QUESTIONS + 1):
        print(f"\n--- Soru {i} işleniyor ---")

        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#option3 > *")))
            print("👍 Oyun yüklendi ve çizimler tamamlandı.")
            time.sleep(0.5) 
        except Exception:
            print(f"❌ Hata: Soru {i} için oyun 10 saniyede yüklenemedi.")
            break

        # --- Soru görüntüsü ---
        question_path = os.path.join(SAVE_DIR, f"question_{i}.png")
        
        try:
            print("🎨 Soru elementi daha net bir görüntü için geçici olarak büyütülüyor...")
            question_elem = driver.find_element(By.ID, "stack")
            
            original_style = driver.execute_script("return arguments[0].getAttribute('style');", question_elem)
            
            # Geçici olarak elementi büyütüp ekran görüntüsü al
            driver.execute_script(
                "arguments[0].style.width = '800px'; arguments[0].style.height = '600px';" +
                "arguments[0].style.backgroundColor = 'white'; arguments[0].style.justifyContent = 'center';",
                question_elem
            )
            time.sleep(0.2)
            
            question_elem.screenshot(question_path)
            
            # Orijinal stilleri geri yükle
            driver.execute_script("arguments[0].setAttribute('style', arguments[1] || '');", question_elem, original_style)
            print("🎨 Soru elementinin stili normale döndürüldü.")
            
            # ⭐ DEĞİŞİKLİK: Soru görüntüsü 800x600 boyutuna getirildi.
            resize_image(question_path, (800, 600))
            print(f"📸 Soru ekran görüntüsü alınıp {question_path} olarak kaydedildi ve 800x600 boyutuna getirildi.")

        except Exception as e:
            print(f"❌ Hata: Soru görüntüsü alınırken bir sorun oluştu: {e}")
            continue


        # --- Şıklar ---
        options_elements = driver.find_elements(By.CLASS_NAME, "option")
        option_paths = []
        for idx, opt in enumerate(options_elements[:4]):
            choice_path = os.path.join(SAVE_DIR, f"choice_{choice_labels[idx]}_{i}.png")
            opt.screenshot(choice_path)
            
            # ⭐ DEĞİŞİKLİK: Her bir şık görüntüsü 256x256 boyutuna getirildi.
            resize_image(choice_path, (256, 256))
            option_paths.append(choice_path)
        print("📸 Şıkların ekran görüntüleri alındı ve 256x256 boyutuna getirildi.")

        # --- Doğru Cevabı Oku ve API'ye Gönder ---
        correct_index = int(driver.execute_script("return document.getElementById('correctIndex').textContent;"))
        correct_path = option_paths[correct_index]
        wrong_paths = [p for j, p in enumerate(option_paths) if j != correct_index]

        # API GÖNDERME BÖLÜMÜ YORUMA ALINDI, İSTERSENİZ AÇABİLİRSİNİZ
        with open(question_path, 'rb') as q_img, \
             open(correct_path, 'rb') as correct, \
             open(wrong_paths[0], 'rb') as wrong1, \
             open(wrong_paths[1], 'rb') as wrong2, \
             open(wrong_paths[2], 'rb') as wrong3:
            
            files = {"question_image": q_img, "correct_answer": correct, "wrong_answer_1": wrong1, "wrong_answer_2": wrong2, "wrong_answer_3": wrong3}
            data = {"category_id": "25", "grade": "[1,2,3,4,9]", "knowledge": "0", "level": "1"}

            try:
                # response = requests.post(API_URL, headers=HEADERS, data=data, files=files)
                # print(f"✅ Soru {i} gönderildi. Doğru şık: {choice_labels[correct_index]} | Status: {response.status_code}")
                print(f"✅ Soru {i} API'ye gönderilmeye hazır. Doğru şık: {choice_labels[correct_index]}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Hata: Soru {i} gönderilirken API hatası oluştu: {e}")

        # --- Sonraki Soruya Geç ---
        if i < NUM_QUESTIONS:
            print("Sonraki soru için sayfa yenileniyor...")
            driver.refresh()

finally:
    driver.quit()
    print("\n🎉 Otomasyon tamamlandı. Tarayıcı kapatıldı.")