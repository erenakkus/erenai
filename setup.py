#!/usr/bin/env python3
import os
import stat
import json
import shutil

CONFIG_PATH = os.path.expanduser("~/.erenai_config.json")
BIN_PATH = "/usr/local/bin/erenai"
SCRIPT_PATH = os.path.abspath("erenai.py")

def create_config():
    if os.path.exists(CONFIG_PATH):
        print("[✓] API anahtarı zaten kayıtlı.")
        return

    api_key = input("Lütfen OpenAI GPT API anahtarınızı girin: ").strip()
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key}, f)
    print("[+] API anahtarı kaydedildi.")

def make_executable():
    st = os.stat(SCRIPT_PATH)
    os.chmod(SCRIPT_PATH, st.st_mode | stat.S_IEXEC)
    print(f"[+] {SCRIPT_PATH} çalıştırılabilir yapıldı.")

def create_symlink():
    if os.path.exists(BIN_PATH):
        os.remove(BIN_PATH)
    os.symlink(SCRIPT_PATH, BIN_PATH)
    print(f"[+] {BIN_PATH} komutu eklendi.")

def main():
    create_config()
    make_executable()
    create_symlink()
    print("\n[✓] Kurulum tamamlandı! Artık terminalde `erenai <soru>` yazarak kullanabilirsin.")

if __name__ == "__main__":
    main()
