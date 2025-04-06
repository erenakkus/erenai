# 🧠 ErenAI - SSH Üzerinden Yapay Zeka Asistanı

Terminalde çalışan, kullanıcıdan GPT API anahtarını alıp yanıt üreten bir yapay zeka projesidir.

## 🚀 Özellikler

- SSH üzerinden `erenai` komutuyla çalışır
- İlk kullanımda kullanıcıdan GPT API anahtarını ister
- Sorular önce kendi veritabanına (API sunucusuna) sorulur
- Veri yoksa GPT ile cevap üretir ve cevabı kaydeder
- Herkese açık API sunucusu ile entegredir

## 🔧 Kurulum

```bash
git clone https://github.com/erenakkus/erenai.git
cd erenai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py install

## 🚀 Kullanım

```bash
erenai Merhaba, nasılsın?

## 🚀 Gereksinimler
Python
3.8+
OpenAI GPT API Key (sadece ilk kullanımda ve bilmediği soruları öğrenmek için istenir)


