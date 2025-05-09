#!/bin/bash

# ErenAI Kurulum Betiği
echo "ErenAI Kurulum Betiği başlatılıyor..."

# Gerekli paketleri kur
echo "Gerekli Python paketleri kuruluyor..."
pip install requests argparse

# ErenAI klasörünü oluştur
mkdir -p ~/.erenai

# Uygulamayı indir
echo "ErenAI betiği /usr/local/bin/ dizinine kopyalanıyor..."
sudo cp ./erenai_cli.py /usr/local/bin/erenai
sudo chmod +x /usr/local/bin/erenai

# Veritabanını oluştur
echo "Veritabanı oluşturuluyor..."
python3 -c "
import os
import sqlite3

db_path = os.path.expanduser('~/.erenai/erenai.db')
conn = sqlite3.connect(db_path)
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
    ('language', 'tr'),
    ('context_length', '5'),
    ('command_suggestions', '1')
]

for key, value in default_settings:
    cursor.execute(
        'INSERT OR IGNORE INTO user_settings (key, value) VALUES (?, ?)',
        (key, value)
    )

conn.commit()
conn.close()
print('Veritabanı başarıyla oluşturuldu:', db_path)
"

# Otomatik tamamlama özelliğini ekle
echo "Bash otomatik tamamlama özelliği ekleniyor..."
cat > ~/.erenai/erenai_completion.bash << 'EOF'
_erenai_completions()
{
  COMPREPLY=()
  local word="${COMP_WORDS[COMP_CWORD]}"
  local completions="--setup --interactive -i --language -l --context -c --suggestions -s --no-suggestions -n --version -v"
  
  if [ "${COMP_CWORD}" -eq 1 ]; then
    completions="$completions $(python3 -c "
import os
import sqlite3

db_path = os.path.expanduser('~/.erenai/erenai.db')
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT command FROM command_history WHERE success = 1 GROUP BY command ORDER BY COUNT(*) DESC LIMIT 5')
        commands = [row[0].split()[0] for row in cursor.fetchall()]
        print(' '.join(commands))
        conn.close()
    except:
        pass
")"
  fi
  
  COMPREPLY=( $(compgen -W "$completions" -- "$word") )
}

complete -F _erenai_completions erenai
EOF

# Bash profiline ekle
if ! grep -q "erenai_completion.bash" ~/.bashrc; then
    echo "source ~/.erenai/erenai_completion.bash" >> ~/.bashrc
    echo "Otomatik tamamlama özelliği ~/.bashrc dosyasına eklendi."
fi

# OpenAI API Key kontrolü
if [ -z "$OPENAI_API_KEY" ]; then
    echo "UYARI: OPENAI_API_KEY ortam değişkeni tanımlanmamış."
    echo "Lütfen API anahtarınızı aşağıdaki komutu çalıştırarak ekleyin:"
    echo "echo 'export OPENAI_API_KEY=your_api_key_here' >> ~/.bashrc && source ~/.bashrc"
else
    echo "OPENAI_API_KEY değişkeni tanımlı, iyi iş!"
fi

echo -e "\nErenAI kurulumu tamamlandı! Şimdi 'erenai' komutunu kullanabilirsiniz."
echo "Örnek kullanım:"
echo "  erenai merhaba dünya                  # Tek seferlik soru sor"
echo "  erenai -i                             # İnteraktif moda geç"
echo "  erenai -l en                          # İngilizce dil ayarı"
echo "  erenai ls -la                         # Sistem komutu çalıştır"
echo "  erenai komutu çalıştır: ps aux        # AI'ya komut çalıştırmasını söyle"
echo "  erenai \"dili türkçe\"                  # Dil ayarını değiştir"
echo "  erenai \"komut önerileri aç\"           # Komut önerilerini aç"
echo -e "\nDaha fazla bilgi için: erenai --help"
