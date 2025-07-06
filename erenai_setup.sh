#!/bin/bash

# ErenAI Kurulum Scripti
echo "ErenAI Kurulumu Başlatılıyor..."

# Gerekli dizinleri oluştur
mkdir -p ~/.erenai
mkdir -p ~/.erenai/logs

# Python gereksinimleri kontrol et
if ! command -v python3 &> /dev/null; then
    echo "Python3 kurulu değil. Lütfen önce Python3 kurun."
    exit 1
fi

# Gerekli Python paketlerini kur
echo "Gerekli Python paketleri kuruluyor..."
pip3 install openai requests

# Ana Python scripti oluştur
cat > ~/.erenai/erenai.py << 'EOF'
#!/usr/bin/env python3
import sys
import sqlite3
import hashlib
import os
import json
from openai import OpenAI

DB_PATH = os.path.expanduser('~/.erenai/erenai.db')
CONFIG_PATH = os.path.expanduser('~/.erenai/config.json')

class ErenAI:
    def __init__(self):
        self.setup_config()
        self.client = OpenAI(api_key=self.api_key)
        self.init_database()
        self.server_name = os.uname().nodename
    
    def setup_config(self):
        """API key yapılandırması"""
        if not os.path.exists(CONFIG_PATH):
            api_key = input("OpenAI API anahtarınızı girin: ").strip()
            config = {"api_key": api_key}
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f)
            print("API anahtarı kaydedildi.")
        
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        self.api_key = config['api_key']
    
    def init_database(self):
        """Veritabanını başlat"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_hash TEXT UNIQUE,
                question TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT,
                question TEXT,
                answer TEXT,
                source TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_question(self, question):
        """Soruyu hash'le"""
        return hashlib.md5(question.lower().strip().encode()).hexdigest()
    
    def search_cache(self, question):
        """Önbelleği ara"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        question_hash = self.hash_question(question)
        cursor.execute('SELECT answer FROM qa_cache WHERE question_hash = ?', (question_hash,))
        result = cursor.fetchone()
        
        if result:
            # Kullanım sayısını artır
            cursor.execute('UPDATE qa_cache SET usage_count = usage_count + 1 WHERE question_hash = ?', (question_hash,))
            conn.commit()
        
        conn.close()
        return result[0] if result else None
    
    def save_to_cache(self, question, answer):
        """Önbelleğe kaydet"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        question_hash = self.hash_question(question)
        cursor.execute('''
            INSERT OR REPLACE INTO qa_cache (question_hash, question, answer)
            VALUES (?, ?, ?)
        ''', (question_hash, question, answer))
        
        conn.commit()
        conn.close()
    
    def log_usage(self, question, answer, source):
        """Kullanım istatistiklerini kaydet"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO usage_stats (server_name, question, answer, source)
            VALUES (?, ?, ?, ?)
        ''', (self.server_name, question, answer, source))
        
        conn.commit()
        conn.close()
    
    def ask_openai(self, question):
        """OpenAI'dan cevap al"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Kısa ve net cevap ver. Maksimum 3 satır. Eğer kod gerekiyorsa sadece kodu göster, açıklama yapma."},
                    {"role": "user", "content": question}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Hata: {str(e)}"
    
    def process_question(self, question):
        """Soruyu işle"""
        # Önce cache'e bak
        cached_answer = self.search_cache(question)
        
        if cached_answer:
            self.log_usage(question, cached_answer, "cache")
            return cached_answer
        
        # Cache'de yoksa OpenAI'a sor
        answer = self.ask_openai(question)
        
        # Cache'e kaydet
        self.save_to_cache(question, answer)
        self.log_usage(question, answer, "openai")
        
        return answer

def main():
    if len(sys.argv) < 2:
        print("Kullanım: erenai 'sorunuz'")
        return
    
    question = ' '.join(sys.argv[1:])
    
    try:
        erenai = ErenAI()
        answer = erenai.process_question(question)
        print(answer)
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()
EOF

# Python scriptini çalıştırılabilir yap
chmod +x ~/.erenai/erenai.py

# Bash wrapper scripti oluştur
cat > ~/.erenai/erenai_wrapper.sh << 'EOF'
#!/bin/bash
python3 ~/.erenai/erenai.py "$@"
EOF

chmod +x ~/.erenai/erenai_wrapper.sh

# Sistem genelinde erişim için sembolik link oluştur
if [ -w /usr/local/bin ]; then
    sudo ln -sf ~/.erenai/erenai_wrapper.sh /usr/local/bin/erenai
else
    # Kullanıcının bin dizinini kullan
    mkdir -p ~/bin
    ln -sf ~/.erenai/erenai_wrapper.sh ~/bin/erenai
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/bin:$PATH"
fi

echo "ErenAI kurulumu tamamlandı!"
echo "Kullanım: erenai 'sorunuz'"
echo "Örnek: erenai 'Python ile dosya nasıl okunur?'"
echo ""
echo "İlk kullanımda OpenAI API anahtarınız istenecek."
