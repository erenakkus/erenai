#!/usr/bin/env python3
import os
import stat
import json

# Konfigürasyon ve komut dosyalarının yollarını belirtiyoruz
CONFIG_PATH = os.path.expanduser("~/.erenai_config.json")
BIN_PATH = "/usr/local/bin/erenai"
SCRIPT_PATH = os.path.abspath("erenai.py")

def create_config():
    # Konfigürasyon dosyasını kontrol et ve kullanıcıdan API anahtarını al
    if os.path.exists(CONFIG_PATH):
        print("[✓] API anahtarı zaten kayıtlı.")
        return

    api_key = input("Lütfen OpenAI GPT API anahtarınızı girin: ").strip()
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key}, f)
    print("[+] API anahtarı kaydedildi.")

def make_executable():
    # erenai.py dosyasını çalıştırılabilir yap
    st = os.stat(SCRIPT_PATH)
    os.chmod(SCRIPT_PATH, st.st_mode | stat.S_IEXEC)
    print(f"[+] {SCRIPT_PATH} çalıştırılabilir yapıldı.")

def create_symlink():
    # Bash wrapper script oluşturuluyor
    wrapper = f'''#!/usr/bin/env bash
python3 {SCRIPT_PATH} "$@"
'''
    with open(BIN_PATH, 'w') as f:
        f.write(wrapper)
    os.chmod(BIN_PATH, 0o755)
    print(f"[+] {BIN_PATH} komutu eklendi.")

def main():
    # Kurulum işlemini başlat
    create_config()
    make_executable()
    create_symlink()
    print("\n[✓] Kurulum tamamlandı! Artık terminalde `erenai <soru>` yazarak kullanabilirsiniz.")

if __name__ == "__main__":
    main()
