#!/usr/bin/env python3
import os
import stat
import subprocess
import json
import sys

CONFIG_PATH = os.path.expanduser("~/.erenai_config.json")
BIN_PATH = "/usr/local/bin/erenai"
SCRIPT_PATH = os.path.abspath("erenai.py")

# Gerekli bağımlılıkları yükleyen fonksiyon
def install_dependencies():
    print("[+] Bağımlılıkları yükliyoruz...")

    # Python 3 ve pip'in yüklü olduğunu kontrol et
    try:
        subprocess.check_call(["python3", "--version"])
    except subprocess.CalledProcessError:
        print("[!] Python 3 yüklü değil, lütfen Python 3'ü yükleyin.")
        sys.exit(1)

    try:
        subprocess.check_call(["pip3", "--version"])
    except subprocess.CalledProcessError:
        print("[+] Pip yükleniyor...")
        subprocess.check_call([ "sudo", "apt", "install", "-y", "python3-pip"])

    # Gerekli Python bağımlılıklarını yükle
    try:
        subprocess.check_call(["pip3", "install", "--upgrade", "pip"])
        subprocess.check_call(["pip3", "install", "openai", "requests"])  # Burada daha fazla bağımlılık eklenebilir
    except subprocess.CalledProcessError:
        print("[!] Bağımlılıkları yüklerken bir hata oluştu.")
        sys.exit(1)

    print("[✓] Bağımlılıklar yüklendi.")

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
    # Bash wrapper script yazılıyor
    wrapper = f'''#!/usr/bin/env bash
python3 {SCRIPT_PATH} "$@"
'''
    with open(BIN_PATH, 'w') as f:
        f.write(wrapper)
    os.chmod(BIN_PATH, 0o755)
    print(f"[+] {BIN_PATH} komutu eklendi.")

def main():
    # Gerekli bağımlılıkları yükle
    install_dependencies()

    # API anahtarı, dosya izinleri ve symlink kurulumlarını yap
    create_config()
    make_executable()
    create_symlink()

    print("\n[✓] Kurulum tamamlandı! Artık terminalde `erenai <soru>` yazarak kullanabilirsiniz.")

if __name__ == "__main__":
    main()
