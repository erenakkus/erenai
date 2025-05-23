#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import subprocess
import requests
import argparse
import json
from datetime import datetime
import hashlib
import uuid
import re
from collections import Counter

# Yapılandırma
CONFIG = {
    "api_key": os.environ.get("OPENAI_API_KEY", ""),
    "api_url": "https://api.openai.com/v1/chat/completions",
    "model": "gpt-3.5-turbo",
    "db_path": os.path.expanduser("~/.erenai/erenai.db"),
    "log_file": os.path.expanduser("~/.erenai/erenai.log"),
    "session_file": os.path.expanduser("~/.erenai/session.json"),
    "context_length": 5,  # Son 5 etkileşimi bağlam olarak tut
    "language": os.environ.get("ERENAI_LANG", "tr"),  # Varsayılan dil
    "command_suggestions": True,  # Komut önerileri aktif
    "max_command_history": 50,  # Öğrenme için tutulacak maksimum komut sayısı
    "CENTRAL_API_URL": os.environ.get("ERENAI_CENTRAL_API_URL", ""),
    "USER_API_KEY": os.environ.get("ERENAI_USER_API_KEY", "")
}

def setup_database():
    """Veritabanı kurulumunu yapar"""
    os.makedirs(os.path.dirname(CONFIG["db_path"]), exist_ok=True)
    
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    # Etkileşim tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_hash TEXT NOT NULL,
        query TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        source TEXT NOT NULL,
        session_id TEXT,
        language TEXT
    )
    ''')
    
    # Komut geçmişi tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS command_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        success INTEGER NOT NULL
    )
    ''')
    
    # Kullanıcı ayarları tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    ''')
    
    # Varsayılan ayarları ekle
    default_settings = [
        ("language", CONFIG["language"]),
        ("context_length", str(CONFIG["context_length"])),
        ("command_suggestions", "1" if CONFIG["command_suggestions"] else "0")
    ]
    
    for key, value in default_settings:
        cursor.execute(
            "INSERT OR IGNORE INTO user_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    conn.commit()
    conn.close()

    # Merkezi API ayarlarını kontrol et
    if not CONFIG["CENTRAL_API_URL"]:
        print("Central API URL is not configured. Please set the ERENAI_CENTRAL_API_URL environment variable.")
    if not CONFIG["USER_API_KEY"]:
        print("User API Key is not configured. Please set the ERENAI_USER_API_KEY environment variable. You can obtain this key from your ErenAI central server.")

def get_or_create_session_id():
    """Mevcut oturum ID'sini alır veya yeni bir tane oluşturur"""
    if os.path.exists(CONFIG["session_file"]):
        try:
            with open(CONFIG["session_file"], "r") as f:
                session_data = json.load(f)
                return session_data.get("session_id")
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Yeni oturum oluştur
    session_id = str(uuid.uuid4())
    os.makedirs(os.path.dirname(CONFIG["session_file"]), exist_ok=True)
    
    with open(CONFIG["session_file"], "w") as f:
        json.dump({"session_id": session_id, "created_at": datetime.now().isoformat()}, f)
    
    return session_id

def get_user_settings():
    """Kullanıcı ayarlarını veritabanından alır"""
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM user_settings")
    settings = dict(cursor.fetchall())
    
    conn.close()
    
    # Ayarları uygun tiplere dönüştür
    settings["context_length"] = int(settings.get("context_length", CONFIG["context_length"]))
    settings["command_suggestions"] = settings.get("command_suggestions", "1") == "1"
    
    return settings

def log_interaction(query, response, source):
    """Etkileşimi merkezi API'ye veya yerel veritabanına kaydeder."""
    if CONFIG["CENTRAL_API_URL"] and CONFIG["USER_API_KEY"]:
        # Merkezi API yapılandırılmışsa, SADECE API'ye loglamayı dene.
        api_url = f"{CONFIG['CENTRAL_API_URL'].rstrip('/')}/interactions"
        payload = {
            "api_key": CONFIG['USER_API_KEY'],
            "query": query,
            "response": response,
            "language": detect_language(query),
            "source": source
        }
        try:
            resp = requests.post(api_url, json=payload, timeout=10)
            if resp.status_code == 201:
                # print("Interaction logged to central server.") # Optional
                return # Başarılı loglama, çık.
            else:
                print(f"Central server returned error {resp.status_code} for logging: {resp.text}")
                return # API hatası, çık (yerel loglama yok).
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to central server for logging: {e}")
            return # Bağlantı hatası, çık (yerel loglama yok).
        # NOT: Eğer buraya gelinirse, API'ye loglama denenmiş ama başarısız olmuştur.
        # Subtask'a göre yerel fallback yapılmaz.
    else:
        # Merkezi API yapılandırılmamışsa, uyarı ver ve yerel veritabanına logla.
        print("Warning: Central API not configured. Logging interaction to local SQLite database.")
        # Yerel loglama kodu aşağıda devam ediyor.
    
    # Bu kısım yalnızca merkezi API yapılandırılmadığında çalışır.
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    query_hash = hashlib.md5(query.encode()).hexdigest()
    session_id = get_or_create_session_id()
    language = detect_language(query)
    
    try:
        cursor.execute(
            "INSERT INTO interactions (query_hash, query, response, timestamp, source, session_id, language) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (query_hash, query, response, datetime.now().isoformat(), source, session_id, language)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error during log_interaction: {e}")
    finally:
        conn.close()

def detect_language(text):
    """Basit dil tespiti yapar (Türkçe/İngilizce)"""
    # Türkçe'ye özgü karakterler
    turkish_chars = set("çğıöşüÇĞİÖŞÜ")
    
    # Metinde Türkçe karakter varsa Türkçe kabul et
    if any(char in turkish_chars for char in text):
        return "tr"
    
    # İngilizce kelimeler ve stop words sayısı
    english_words = {"the", "and", "is", "in", "to", "a", "what", "how", "why", "when", "where", "who"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    
    if len(words.intersection(english_words)) > 0:
        return "en"
    
    # Varsayılan olarak yapılandırma dosyasındaki dili kullan
    return CONFIG["language"]

def log_command(command, success=True):
    """Komutu geçmişe kaydeder"""
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO command_history (command, timestamp, success) VALUES (?, ?, ?)",
        (command, datetime.now().isoformat(), 1 if success else 0)
    )
    
    conn.commit()
    conn.close()

def get_from_database(query):
    """Veritabanından sorgu için daha önce verilmiş cevabı arar"""
    query_hash = hashlib.md5(query.encode()).hexdigest()
    
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT response FROM interactions WHERE query_hash = ? ORDER BY timestamp DESC LIMIT 1",
        (query_hash,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_from_central_api(query):
    """Merkezi API'den sorgu için cevap arar."""
    # Bu fonksiyon çağrıldığında CENTRAL_API_URL ve USER_API_KEY'in ayarlı olduğu varsayılır.
    # get_from_database ana fonksiyonu bu kontrolü yapar.
    
    api_url = f"{CONFIG['CENTRAL_API_URL'].rstrip('/')}/interactions"
    params = {'query': query, 'api_key': CONFIG['USER_API_KEY']}
    
    try:
        # print(f"Attempting to GET from Central API: {api_url} with params: {params}") # Debug
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                # print(f"Central API response JSON: {response_data}") # Debug
                if response_data.get("found"):
                    return response_data.get("response")
                else:
                    # print("Query not found in central API (found: false).") # Debug
                    return None # Yanıt bulundu ama 'found' false veya yok
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response from central server: {response.text}. Exception: {e}")
                return None
        # Subtask: "If not 200, print an error ... and return None."
        # 404 (Not Found) özel bir durum değil, genel bir hata olarak ele alınır.
        else:
            print(f"Central server returned error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to central server: {e}")
        return None

def get_from_database(query):
    """Veritabanından veya merkezi API'den sorgu için daha önce verilmiş cevabı arar"""
    if CONFIG["CENTRAL_API_URL"] and CONFIG["USER_API_KEY"]:
        # Merkezi API yapılandırılmışsa, SADECE API'yi kullan.
        # print(f"Central API is configured. Querying central API for: {query[:30]}...") # Debug
        # get_from_central_api hatayı kendi içinde basar ve None döner.
        return get_from_central_api(query) 
        # Yerel DB'ye fallback yok. API sonucu neyse o (cevap veya None).
    else:
        # Merkezi API yapılandırılmamışsa, uyarı ver ve None dön (subtask tanımına göre).
        print("Warning: Central API not configured. Cannot fetch interaction from central server.")
        return None # Yerel SQLite'a fallback yok.
    
    # NOT: Aşağıdaki kod etkisiz hale geldi, çünkü yukarıdaki koşul ya API'yi çağırır ya da None döner.
    # Eğer yerel fallback isteniyorsa, yukarıdaki 'else' bloğu değiştirilmeli.
    # Mevcut subtask tanımına göre, bu kısım çalışmamalı.
    # query_hash = hashlib.md5(query.encode()).hexdigest()
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT response FROM interactions WHERE query_hash = ? ORDER BY timestamp DESC LIMIT 1",
            (query_hash,)
        )
        result = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"SQLite error during get_from_database: {e}")
        result = None
    finally:
        conn.close()
    
    # if result: # Bu blok artık etkisiz.
        # print("Response found in local database.") # Debugging
        # return result[0] # Bu blok artık etkisiz.
    
    # print("Response not found in local database.") # Debugging
    # return None # Bu blok artık etkisiz.

# execute_command fonksiyonu burada başlıyor...
def execute_command(command):
    """Sistem komutunu çalıştırır"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        success = result.returncode == 0
        output = result.stdout if success else f"Hata: {result.stderr}"
        
        # Komutu geçmişe kaydet
        log_command(command, success)
        
        return output
    except Exception as e:
        log_command(command, False)
        return f"Komut çalıştırma hatası: {str(e)}"

def get_command_suggestions(partial_command=None):
    """Geçmiş komutlardan öneriler sunar"""
    settings = get_user_settings()
    
    if not settings["command_suggestions"]:
        return []
    
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    # En çok kullanılan başarılı komutları al
    cursor.execute(
        "SELECT command FROM command_history WHERE success = 1 ORDER BY timestamp DESC LIMIT ?",
        (CONFIG["max_command_history"],)
    )
    
    commands = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Frekans sayımı yap
    counter = Counter(commands)
    most_common = counter.most_common(5)  # En çok kullanılan 5 komut
    
    # Eğer kısmi komut verildiyse, filtrele
    suggestions = []
    if partial_command:
        for cmd, count in most_common:
            if cmd.startswith(partial_command):
                suggestions.append(cmd)
    else:
        suggestions = [cmd for cmd, _ in most_common]
    
    return suggestions

def get_conversation_context():
    """Son etkileşimleri bağlam olarak alır"""
    settings = get_user_settings()
    session_id = get_or_create_session_id()
    
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT query, response FROM interactions WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
        (session_id, settings["context_length"])
    )
    
    context = cursor.fetchall()
    conn.close()
    
    # En eskiden en yeniye sırala
    context.reverse()
    
    return context

def ask_gpt(query):
    """GPT API'ye sorguyu gönderir ve cevabı alır"""
    if not CONFIG["api_key"]:
        return "HATA: OpenAI API anahtarı bulunamadı. Lütfen OPENAI_API_KEY ortam değişkenini ayarlayın."
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CONFIG['api_key']}"
    }
    
    # Konuşma bağlamını al
    context = get_conversation_context()
    
    # Mesajları oluştur
    messages = []
    
    # Sistem talimatı - dile göre ayarla
    language = detect_language(query)
    if language == "tr":
        system_message = "Sen kullanıcıya Türkçe yanıt veren ve onların SSH komutlarını çalıştırmalarına yardımcı olan bir asistansın."
    else:
        system_message = "You are an assistant that responds in English and helps users run SSH commands."
    
    messages.append({"role": "system", "content": system_message})
    
    # Bağlam mesajlarını ekle
    for prev_query, prev_response in context:
        messages.append({"role": "user", "content": prev_query})
        messages.append({"role": "assistant", "content": prev_response})
    
    # Mevcut sorguyu ekle
    messages.append({"role": "user", "content": query})
    
    data = {
        "model": CONFIG["model"],
        "messages": messages,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(CONFIG["api_url"], headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"API hatası: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Yanıt çözme hatası: {str(e)}"

def is_system_command(query):
    """Sorgunun bir sistem komutu olup olmadığını kontrol eder"""
    system_command_prefixes = [
        "ssh", "scp", "restart", "reboot", "shutdown", "apt", "yum", "systemctl",
        "service", "start", "stop", "ls", "cd", "mkdir", "rm", "cp", "mv", "grep",
        "find", "cat", "ps", "top", "tail", "head", "sed", "awk", "ping", "ifconfig",
        "ip", "netstat", "wget", "curl", "docker", "kubectl"
    ]
    
    # Yapay zeka komutlarını tanı
    ai_command_patterns = [
        r"(çalıştır|run|execute)[\s:]+(.+)",
        r"(komutu çalıştır|run command|execute command)[\s:]+(.+)",
        r"(şu komutu çalıştır|run this command|execute this command)[\s:]+(.+)"
    ]
    
    # Basit bir kontrol: Sorgunun herhangi bir sistem komutu ile başlayıp başlamadığını kontrol et
    query_lower = query.lower()
    words = query_lower.split()
    
    # Doğrudan komut kontrolü
    if len(words) >= 1:
        for prefix in system_command_prefixes:
            if words[0] == prefix:
                # Komutu çıkart
                command = query.strip()
                return True, command
    
    # AI'a komut çalıştırmasını söyleyen bir cümle mi?
    for pattern in ai_command_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            command = match.group(2).strip()
            return True, command
    
    return False, None

def update_user_settings(key, value):
    """Kullanıcı ayarlarını günceller"""
    conn = sqlite3.connect(CONFIG["db_path"])
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    
    conn.commit()
    conn.close()

def parse_internal_commands(query):
    """ErenAI'nin iç komutlarını işler"""
    # Ayarları değiştirme komutları
    settings_patterns = {
        r"(dili?|language)[\s:]+(türkçe|turkish|tr)": ("language", "tr"),
        r"(dili?|language)[\s:]+(ingilizce|english|en)": ("language", "en"),
        r"(bağlam uzunluğu|context length)[\s:]+(\d+)": ("context_length", lambda m: int(m.group(2))),
        r"(komut önerileri|command suggestions)[\s:]+(aç|on|1|true|yes|evet)": ("command_suggestions", True),
        r"(komut önerileri|command suggestions)[\s:]+(kapa|off|0|false|no|hayır)": ("command_suggestions", False),
    }
    
    for pattern, (key, value_or_func) in settings_patterns.items():
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            if callable(value_or_func):
                value = value_or_func(match)
            else:
                value = value_or_func
                
            update_user_settings(key, value)
            
            # Dil ayarına göre yanıt ver
            if key == "language":
                if value == "tr":
                    return "Dil Türkçe olarak ayarlandı."
                else:
                    return "Language set to English."
            elif key == "context_length":
                if get_user_settings()["language"] == "tr":
                    return f"Bağlam uzunluğu {value} olarak ayarlandı."
                else:
                    return f"Context length set to {value}."
            elif key == "command_suggestions":
                status = "açık" if value else "kapalı"
                status_en = "enabled" if value else "disabled"
                if get_user_settings()["language"] == "tr":
                    return f"Komut önerileri {status}."
                else:
                    return f"Command suggestions {status_en}."
    
    # Durum sorgulama
    if re.search(r"(ayarlar|settings)(\?|nedir|göster|show|what are)", query, re.IGNORECASE):
        settings = get_user_settings()
        if settings["language"] == "tr":
            return (f"Mevcut ayarlar:\n"
                   f"- Dil: {'Türkçe' if settings['language'] == 'tr' else 'İngilizce'}\n"
                   f"- Bağlam uzunluğu: {settings['context_length']}\n"
                   f"- Komut önerileri: {'Açık' if settings['command_suggestions'] else 'Kapalı'}")
        else:
            return (f"Current settings:\n"
                   f"- Language: {'Turkish' if settings['language'] == 'tr' else 'English'}\n"
                   f"- Context length: {settings['context_length']}\n"
                   f"- Command suggestions: {'Enabled' if settings['command_suggestions'] else 'Disabled'}")
    
    # İç komut değilse None dön
    return None

def interactive_mode():
    """İnteraktif mod - sürekli sorguları işler"""
    settings = get_user_settings()

    # Merkezi API ayarlarını kontrol et
    if not CONFIG["CENTRAL_API_URL"] or not CONFIG["USER_API_KEY"]:
        warning_message = "ErenAI is not fully configured for central server communication. Q&A will only use local cache (if any) and GPT."
        if settings["language"] == "tr":
            warning_message = "ErenAI merkezi sunucu iletişimi için tam olarak yapılandırılmamış. Soru-Cevap yalnızca yerel önbelleği (varsa) ve GPT'yi kullanacaktır."
        print(f"UYARI: {warning_message}")
    
    if settings["language"] == "tr":
        print("ErenAI: Merhaba! Size nasıl yardımcı olabilirim? (Çıkmak için 'exit' veya 'quit' yazın)")
    else:
        print("ErenAI: Hello! How can I help you? (Type 'exit' or 'quit' to exit)")
    
    while True:
        # Komut önerileri aktifse, en son kullanılan komutları göster
        if settings["command_suggestions"]:
            suggestions = get_command_suggestions()
            if suggestions:
                if settings["language"] == "tr":
                    print("\nÖnerilen komutlar:")
                else:
                    print("\nSuggested commands:")
                for i, cmd in enumerate(suggestions, 1):
                    print(f"{i}. {cmd}")
                print()
        
        # Kullanıcı girdisini al
        query = input("> ")
        
        # Çıkış kontrolü
        if query.lower() in ["exit", "quit", "çıkış", "kapat"]:
            if settings["language"] == "tr":
                print("ErenAI: Görüşmek üzere!")
            else:
                print("ErenAI: See you later!")
            break
        
        # Sorgu boş ise devam et
        if not query.strip():
            continue
        
        # İç komutları kontrol et
        internal_response = parse_internal_commands(query)
        if internal_response:
            print(f"ErenAI: {internal_response}")
            continue
        
        # Sistem komutu kontrolü
        is_command, command = is_system_command(query)
        
        if is_command:
            if settings["language"] == "tr":
                print(f"Komut çalıştırılıyor: {command}")
            else:
                print(f"Executing command: {command}")
            
            response = execute_command(command)
            print(response)
            log_interaction(query, response, "system_command")
            continue
        
        # Veritabanında sor
        cached_response = get_from_database(query)
        
        if cached_response:
            print("ErenAI:", cached_response)
            continue
        
        # GPT'ye sor
        if settings["language"] == "tr":
            print("ErenAI düşünüyor...")
        else:
            print("ErenAI thinking...")
            
        gpt_response = ask_gpt(query)
        print("ErenAI:", gpt_response)
        
        # Etkileşimi kaydet
        log_interaction(query, gpt_response, "gpt_api")
        
        # Ayarların en son halini al (kullanıcı ayarları değiştirmiş olabilir)
        settings = get_user_settings()

def main():
    """Ana uygulama fonksiyonu"""
    parser = argparse.ArgumentParser(description="ErenAI - Terminal tabanlı AI asistanı")
    parser.add_argument("query", nargs="*", help="Sorgu veya komut")
    parser.add_argument("--setup", action="store_true", help="Veritabanını ve gerekli dizinleri kur")
    parser.add_argument("--interactive", "-i", action="store_true", help="İnteraktif mod")
    parser.add_argument("--language", "-l", choices=["tr", "en"], help="Dil ayarı (tr/en)")
    parser.add_argument("--context", "-c", type=int, help="Bağlam uzunluğu")
    parser.add_argument("--suggestions", "-s", action="store_true", help="Komut önerilerini aç")
    parser.add_argument("--no-suggestions", "-n", action="store_true", help="Komut önerilerini kapa")
    parser.add_argument("--version", "-v", action="store_true", help="Sürüm bilgisini göster")
    args = parser.parse_args()

    # Merkezi API ayarlarını kontrol et (setup modu hariç)
    if not args.setup and (not CONFIG["CENTRAL_API_URL"] or not CONFIG["USER_API_KEY"]):
        print("WARNING: ErenAI is not fully configured for central server communication. Q&A will only use local cache (if any) and GPT. Please run with --setup or set ERENAI_CENTRAL_API_URL and ERENAI_USER_API_KEY environment variables.")

    # Sürüm bilgisi
    if args.version:
        print("ErenAI v1.0.0 - SSH Tabanlı AI Asistanı")
        print("(c) 2025 ErenAI Project - GPLv3 License")
        return
    
    # Kurulum
    if args.setup:
        setup_database()
        print("ErenAI kurulumu tamamlandı.")
        return
    
    # Veritabanı yoksa oluştur
    if not os.path.exists(CONFIG["db_path"]):
        setup_database()
    
    # Komut satırı argümanları ile ayarları güncelle
    if args.language:
        update_user_settings("language", args.language)
    
    if args.context:
        update_user_settings("context_length", args.context)
    
    if args.suggestions:
        update_user_settings("command_suggestions", True)
    
    if args.no_suggestions:
        update_user_settings("command_suggestions", False)
    
    # İnteraktif mod
    if args.interactive or not args.query:
        interactive_mode()
        return
    
    # Tek seferlik sorgu için
    settings = get_user_settings()
    
    # Sorgu argümanlarını al
    query = " ".join(args.query)
    
    # İç komutları kontrol et
    internal_response = parse_internal_commands(query)
    if internal_response:
        print(f"ErenAI: {internal_response}")
        return
    
    # Sistem komutu kontrolü
    is_command, command = is_system_command(query)
    
    if is_command:
        if settings["language"] == "tr":
            print(f"Komut çalıştırılıyor: {command}")
        else:
            print(f"Executing command: {command}")
        
        response = execute_command(command)
        print(response)
        log_interaction(query, response, "system_command")
        return
    
    # Veritabanında sor
    cached_response = get_from_database(query)
    
    if cached_response:
        print("ErenAI:", cached_response)
        return
    
    # GPT'ye sor
    if settings["language"] == "tr":
        print("ErenAI düşünüyor...")
    else:
        print("ErenAI thinking...")
        
    gpt_response = ask_gpt(query)
    print("ErenAI:", gpt_response)
    
    # Etkileşimi kaydet
    log_interaction(query, gpt_response, "gpt_api")

if __name__ == "__main__":
    main()
