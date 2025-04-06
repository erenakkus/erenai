import requests
import json

# API sunucun (veritabanı kontrolü ve kayıt)
API_SERVER = "http://89.43.28.204:5000"

def ask_api_server(question):
    try:
        response = requests.get(f"{API_SERVER}/ask", params={"q": question})
        if response.status_code == 200:
            data = response.json()
            return data.get("answer")
    except Exception as e:
        print(f"[API] Sunucuya bağlanırken hata oluştu: {e}")
    return None

def save_to_api_server(question, answer):
    try:
        payload = {"question": question, "answer": answer}
        response = requests.post(f"{API_SERVER}/save", json=payload)
        if response.status_code == 200:
            print("[API] Cevap başarıyla veritabanına kaydedildi.")
    except Exception as e:
        print(f"[API] Veritabanına kayıt sırasında hata: {e}")

def ask_gpt(api_key, question):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print("[GPT] API hatası:", response.text)
    except Exception as e:
        print(f"[GPT] API'ye bağlanırken hata: {e}")
    return "Bir hata oluştu. Lütfen tekrar deneyin."
