# ErenAI - SSH Tabanlı AI Asistanı


  Terminal üzerinden çalışan, SSH komutları çalıştırabilen ve GPT destekli AI asistanı


---

## 📋 Özellikler

- **🤖 AI Destekli Yanıtlar:** GPT API ile soruları cevaplayabilir
- **📊 Veritabanı Önbelleği:** Tekrarlanan sorular için hızlı yanıtlar
- **💻 Komut Yürütme:** SSH ve sistem komutlarını doğrudan çalıştırır
- **🧠 Konuşma Bağlamı:** Önceki etkileşimleri hatırlayarak doğal konuşma sağlar
- **🌍 Çoklu Dil Desteği:** Türkçe ve İngilizce dillerinde çalışır
- **🔄 Komut Önerileri:** Sık kullanılan komutları öğrenir ve önerir
- **⚡ İnteraktif Mod:** Sürekli etkileşim için konuşma modu

## 🚀 Hızlı Başlangıç

### Kurulum

```bash
# Depoyu klonla
git clone https://github.com/kullaniciadi/erenai.git
cd erenai

# Kurulum betiğini çalıştır
chmod +x install_script.sh
./install_script.sh

# OpenAI API anahtarını ayarla
export OPENAI_API_KEY=your_api_key_here
```

### Kullanım

```bash
# Tek bir soru sor
erenai "Bugün hava nasıl?"

# İnteraktif moda geç
erenai -i

# Sistem komutu çalıştır
erenai ls -la
```

## 📚 Örnek Kullanımlar

### AI Sorguları

```bash
# Basit sorular
erenai "Python'da liste nasıl oluşturulur?"
erenai "En iyi SSH güvenlik uygulamaları nelerdir?"

# İnteraktif modda konuşma
erenai -i
> Merhaba, nasılsın?
> Python nedir?
> Teşekkürler!
```

### Sistem Komutları

```bash
# Doğrudan komut çalıştırma
erenai ls -la
erenai ps aux | grep python

# Doğal dille komut çalıştırma
erenai "komutu çalıştır: ssh kullanici@sunucu"
erenai "şu komutu çalıştır: systemctl restart apache2"
```

### Ayarlar

```bash
# Dil ayarını değiştir
erenai "dili türkçe"
erenai "language english"
erenai -l en

# Bağlam uzunluğunu ayarla
erenai "bağlam uzunluğu 10"
erenai -c 10

# Komut önerilerini aç/kapa
erenai "komut önerileri aç"
erenai "command suggestions off"
erenai -s  # Aç
erenai -n  # Kapa
```

## ⚙️ Komut Satırı Seçenekleri

```
erenai [SORGU|KOMUT] [SEÇENEKLER]

Seçenekler:
  --setup               Veritabanını ve gerekli dizinleri kur
  --interactive, -i     İnteraktif moda geç
  --language, -l TR|EN  Dil ayarı (tr/en)
  --context, -c SAYI    Bağlam uzunluğu
  --suggestions, -s     Komut önerilerini aç
  --no-suggestions, -n  Komut önerilerini kapa
  --version, -v         Sürüm bilgisini göster
  --help, -h            Yardım mesajını göster
```

## 🛠️ Teknik Detaylar

ErenAI aşağıdaki bileşenlerden oluşur:

- **Python Backend:** AI sorguları, komut yürütme ve veritabanı yönetimi
- **SQLite Veritabanı:** Etkileşimleri, komut geçmişini ve kullanıcı ayarlarını saklar
- **GPT API:** Doğal dil işleme için OpenAI'nin API'sini kullanır
- **Bash Entegrasyonu:** Terminal otomatik tamamlama ve komut çalıştırma

Veriler `~/.erenai/` dizininde saklanır:
- `erenai.db`: SQLite veritabanı
- `session.json`: Oturum bilgileri
- `erenai_completion.bash`: Bash otomatik tamamlama betiği

## 📝 Yapılacaklar Listesi

- [ ] Daha fazla dil desteği eklemek
- [ ] Gömülü shell özellikleri geliştirmek
- [ ] Çoklu API sağlayıcı desteği (GPT, Claude, vb.)
- [ ] Web arayüzü eklemek
- [ ] Ekip işbirliği özellikleri
- [ ] Docker desteği

## 🤝 Katkıda Bulunma

Katkıda bulunmak ister misiniz? Harika! Yapmanız gerekenler:

1. Bu depoyu fork edin
2. Değişiklikleriniz için yeni bir branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Bir Pull Request oluşturun

## 📄 Lisans

Bu proje GPL-3.0 lisansı altında dağıtılmaktadır. Daha fazla bilgi için `LICENSE` dosyasına bakın.

## 🙏 Teşekkürler

- OpenAI API'yi geliştirdikleri için
- Tüm katkıda bulunanlara ve kullanıcılara

---

<p align="center">
  Made with ❤️ in Turkey
</p>
