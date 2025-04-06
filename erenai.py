#!/usr/bin/env python3
import os
import json
import sys
import requests
from utils import ask_gpt, ask_api_server, save_to_api_server

CONFIG_PATH = os.path.expanduser("~/.erenai_config.json")

def load_api_key():
    if not os.path.exists(CONFIG_PATH):
        api_key = input("OpenAI GPT API anahtarınızı girin: ").strip()
        with open(CONFIG_PATH, "w") as f:
            json.dump({"api_key": api_key}, f)
    with open(CONFIG_PATH) as f:
        return json.load(f)["api_key"]

def main():
    if len(sys.argv) < 2:
        print("Kullanım: erenai <soru>")
        return

    question = " ".join(sys.argv[1:])
    api_key = load_api_key()

    # Önce API sunucudaki veritabanına sor
    answer = ask_api_server(question)
    if answer:
        print(f"ErenAI: {answer}")
        return

    # Eğer veritabanında yoksa GPT'ye sor
    answer = ask_gpt(api_key, question)
    print(f"ErenAI : {answer}")

    # Veritabanına kaydet
    save_to_api_server(question, answer)

if __name__ == "__main__":
    main()
