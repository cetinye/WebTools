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