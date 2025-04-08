import os
import sys
import json
import requests

def load_api_key():
    if os.path.exists("api_key.txt"):
        with open("api_key.txt", "r") as f:
            return f.read().strip()
    else:
        key = input("Lütfen GPT API anahtarınızı girin: ").strip()
        with open("api_key.txt", "w") as f:
            f.write(key)
        return key

def ask_api_server(question):
    try:
        response = requests.post("http://89.43.28.204:5000/ask", json={"question": question})
        if response.status_code == 200:
            data = response.json()
            return data.get("answer")
    except Exception as e:
        print("API sunucusuna ulaşılamadı:", e)
    return None

def save_to_api_server(question, answer):
    try:
        requests.post("http://89.43.28.204:5000/save", json={"question": question, "answer": answer})
    except Exception as e:
        print("API sunucusuna kayıt yapılamadı:", e)

def ask_gpt(api_key, question):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": question}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("GPT'den cevap alınamadı:", response.text)
        return "Üzgünüm, şu anda cevap veremiyorum."

def main():
    question = " ".join(sys.argv[1:])
    api_key = load_api_key()

    answer = ask_api_server(question)
    if answer:
        print(f"ErenAI: {answer}")
        return

    answer = ask_gpt(api_key, question)
    print(f"ErenAI: {answer}")

    save_to_api_server(question, answer)

if __name__ == "__main__":
    main()
