<div align="center">

# 🤖 Google AI Asistan

**Sesli ve yazılı komutlarla Google ekosistemini yöneten,  
yerel LLM (Ollama) tabanlı kişisel yapay zeka asistanı**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Lokal_LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)
![Google API](https://img.shields.io/badge/Google_API-6_Servis-4285F4?style=for-the-badge&logo=google&logoColor=white)
![License](https://img.shields.io/badge/Lisans-MIT-green?style=for-the-badge)

</div>

---

## 📖 İçindekiler

- [Genel Bakış](#-genel-bakış)
- [Özellikler](#-özellikler)
- [Mimari](#-mimari)
- [Desteklenen Google Servisleri](#-desteklenen-google-servisleri)
- [Kurulum](#-kurulum)
- [Konfigürasyon](#-konfigürasyon)
- [Kullanım](#-kullanım)
- [Proje Yapısı](#-proje-yapısı)
- [Ajan Modülleri](#-ajan-modülleri)
- [LLM Modeli Seçimi](#-llm-modeli-seçimi)
- [Sesli Komut](#-sesli-komut)
- [Sık Sorulan Sorular](#-sık-sorulan-sorular)

---

## 🌟 Genel Bakış

**Google AI Asistan**, doğal dilde verdiğiniz komutları anlayarak Google Drive, Docs, Sheets, Slides, Calendar ve Gmail üzerinde işlem gerçekleştiren tam entegre bir yapay zeka asistanıdır.

Tüm dil modeli işlemleri **internet bağlantısı gerektirmeden** yerel makinenizde [Ollama](https://ollama.com) aracılığıyla çalışır. Llama 3, Mistral, Gemma, Phi gibi açık kaynaklı modeller arasından dilediğinizi seçerek kullanabilirsiniz.

```
Kullanıcı Komutu (Ses / Metin)
        │
        ▼
  Ollama (Lokal LLM)
  → Niyeti analiz et → JSON üret
        │
        ▼
  İlgili Google Agent
  (Drive / Docs / Sheets / Slides / Calendar / Gmail)
        │
        ▼
  Google API → İşlem Gerçekleştir → Sonuç
```

---

## ✨ Özellikler

### 🧠 Yapay Zeka
- **Doğal dil anlayışı** — "Yarın saat 14'te toplantı ekle" gibi komutlar otomatik ayrıştırılır
- **Yerel LLM** — Ollama üzerinden internet gerektirmeyen işlem; gizlilik öncelikli
- **Dinamik model seçimi** — Web arayüzünden yüklü Ollama modelleri arasında anlık geçiş
- **Akıllı yönlendirme** — Komut otomatik olarak doğru Google servisine iletilir

### 📄 Google Docs — Profesyonel Belge Oluşturma
- Markdown benzeri sözdizimi desteği (`#`, `##`, `###`, `*`, `1.`, `---`)
- Otomatik H1/H2/H3 başlık stilizasyonu (renk, boyut, aralık)
- Gerçek madde işareti ve numaralı liste (Google Docs native bullet)
- Bölümlere ayrılmış `create_professional_document` fonksiyonu
- İki renk teması: `blue` (kurumsal) ve `dark`

### 🎞️ Google Slides — Profesyonel Sunum Oluşturma
- Tek komutla kapak + içerik + bölüm slaytlarından oluşan tam sunum
- 4 renk teması: `blue`, `teal`, `dark`, `red`
- Renkli arka plan, büyük başlık, alt yazılı kapak slaytı
- Bölüm ayırıcı slaytlar (`"section": true`)
- Google Sans + Arial font kombinasyonu

### 🎤 Sesli Komut
- Mikrofon ile konuşun → Google Speech Recognition → metin → komut
- Web arayüzünde tarayıcı mikrofonu entegrasyonu
- Terminal arayüzünde PyAudio tabanlı dinleme
- Türkçe dil desteği (`tr-TR`)

### 🖥️ İki Arayüz
| Özellik | Web (Streamlit) | Terminal (Rich) |
|---|---|---|
| Chat geçmişi | ✅ | ❌ |
| Model seçici | ✅ | ❌ |
| Sesli komut | ✅ Tarayıcı mikrofonu | ✅ PyAudio |
| Servis durumu | ✅ Canlı panel | ✅ Başlangıçta |
| Örnek komutlar | ✅ Tek tık | ❌ |

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                    Kullanıcı Arayüzü                    │
│         web_ui.py (Streamlit)  │  main.py (Terminal)    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│         llm_router.py           │
│   • Ollama API istemcisi        │
│   • Sistem promptu              │
│   • JSON niyet ayrıştırıcı      │
└─────────────────┬───────────────┘
                  │
        ┌─────────┴──────────┐
        │    ACTION_MAP       │
        │  (servis yönlendirme)│
        └─────────┬──────────┘
                  │
    ┌─────────────┼─────────────────┐
    ▼             ▼                 ▼
drive_agent   docs_agent       slides_agent
sheets_agent  calendar_agent   gmail_agent
    │
    ▼
Google API (OAuth 2.0 — auth_google.py)
```

---

## ☁️ Desteklenen Google Servisleri

| Servis | İşlemler |
|--------|----------|
| 📁 **Google Drive** | Dosya listeleme, arama, indirme, bilgi görüntüleme |
| 📄 **Google Docs** | Belge okuma, biçimlendirilmiş belge oluşturma, içerik ekleme |
| 📊 **Google Sheets** | Tablo okuma/yazma, satır ekleme, yeni tablo oluşturma |
| 🎞️ **Google Slides** | Sunum okuma, profesyonel sunum oluşturma, slayt ekleme |
| 📅 **Google Calendar** | Etkinlik listeleme/oluşturma/silme/arama |
| 📧 **Gmail** | Mail gönderme, taslak oluşturma, gelen kutusu okuma |

---

## 🚀 Kurulum

### Ön Koşullar

- Python **3.11+**
- [Ollama](https://ollama.com/download) kurulu ve çalışıyor olmalı
- Google Cloud Console'da OAuth 2.0 kimlik bilgileri

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/kullanici/google-ai-asistan.git
cd google-ai-asistan
```

### 2. Sanal Ortam Oluşturun

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Ollama Modelini İndirin

```bash
# Ollama servisini başlatın
ollama serve

# Model indirin (önerilen seçenekler)
ollama pull llama3        # Meta Llama 3 8B
ollama pull mistral       # Mistral 7B
ollama pull gemma2        # Google Gemma 2 9B
ollama pull phi3          # Microsoft Phi-3
ollama pull qwen2         # Alibaba Qwen 2
```

### 5. Google API Kimlik Bilgileri

1. [Google Cloud Console](https://console.cloud.google.com) adresine gidin
2. Yeni proje oluşturun → **APIs & Services → Enable APIs**
3. Şu API'leri etkinleştirin:
   - Google Drive API
   - Google Docs API
   - Google Sheets API
   - Google Slides API
   - Google Calendar API
   - Gmail API
4. **Credentials → Create Credentials → OAuth 2.0 Client ID** oluşturun
5. İndirilen `credentials.json` dosyasını projenin kök dizinine kopyalayın

### 6. Ortam Değişkenlerini Ayarlayın

`.env.example` dosyasını kopyalayıp düzenleyin:

```bash
cp .env.example .env
```

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
CREDENTIALS_FILE=credentials.json
TOKEN_FILE=token.json
SPEECH_LANGUAGE=tr-TR
```

---

## ⚙️ Konfigürasyon

Tüm ayarlar `config.py` üzerinden yönetilir ve `.env` dosyasıyla geçersiz kılınabilir.

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama sunucu adresi |
| `OLLAMA_MODEL` | `llama3` | Kullanılacak model adı |
| `CREDENTIALS_FILE` | `credentials.json` | Google OAuth kimlik dosyası |
| `TOKEN_FILE` | `token.json` | Oturum token dosyası (otomatik oluşur) |
| `SPEECH_LANGUAGE` | `tr-TR` | Ses tanıma dili |

---

## 🖥️ Kullanım

### Web Arayüzü (Önerilen)

```bash
streamlit run web_ui.py
```

Tarayıcıda `http://localhost:8501` adresini açın.

**İlk çalıştırmada** Google hesabınızla oturum açmanız istenecektir. Oluşturulan `token.json` sonraki çalıştırmalarda otomatik kullanılır.

### Terminal Arayüzü

```bash
python main.py
```

| Komut | Açıklama |
|-------|----------|
| Herhangi bir metin | Doğal dil komutu |
| `s` | Sesli komut modunu başlat |
| `yardım` | Yardım menüsünü göster |
| `q` | Programdan çık |

### Örnek Komutlar

```
# Google Drive
"Drive'daki son 10 dosyamı listele"
"projeler klasöründeki PDF'leri ara"

# Google Docs
"Python programlama hakkında profesyonel belge oluştur"
"makine öğrenimi raporu oluştur"

# Google Slides
"yapay zeka hakkında 8 slaytlık profesyonel sunum oluştur"
"şirket tanıtımı için teal temalı sunum hazırla"

# Google Sheets
"Q1 satış verilerini oku"
"bütçe takibi için yeni tablo oluştur"

# Google Calendar
"yarın saat 15'te ekip toplantısı ekle"
"bu haftaki etkinliklerimi göster"

# Gmail
"ali@sirket.com'a proje güncellemesi gönder"
"gelen kutumda son 5 maili göster"
```

---

## 📁 Proje Yapısı

```
google-ai-asistan/
│
├── 📄 main.py               # Terminal arayüzü — ana döngü
├── 🌐 web_ui.py             # Streamlit web arayüzü
│
├── 🧠 llm_router.py         # Ollama LLM bağlantısı ve niyet analizi
├── ⚙️  config.py             # Merkezi konfigürasyon
├── 🔑 auth_google.py        # Google OAuth 2.0 kimlik doğrulama
├── 🎤 voice_handler.py      # Ses tanıma (PyAudio + SpeechRecognition)
│
├── 📁 drive_agent.py        # Google Drive işlemleri
├── 📄 docs_agent.py         # Google Docs işlemleri (biçimli)
├── 📊 sheets_agent.py       # Google Sheets işlemleri
├── 🎞️  slides_agent.py       # Google Slides işlemleri (profesyonel)
├── 📅 calendar_agent.py     # Google Calendar işlemleri
├── 📧 gmail_agent.py        # Gmail işlemleri
│
├── 📋 requirements.txt      # Python bağımlılıkları
├── 🔒 .env                  # Ortam değişkenleri (git'e eklenmez)
├── 🔒 .env.example          # Örnek .env şablonu
├── 🔐 credentials.json      # Google OAuth kimlik bilgileri (git'e eklenmez)
└── 🎫 token.json            # Oturum tokeni (otomatik oluşur, git'e eklenmez)
```

---

## 🔌 Ajan Modülleri

### `docs_agent.py` — Akıllı Belge Oluşturma

Markdown benzeri sözdizimini Google Docs native biçimlendirmesine dönüştürür:

```
# Başlık          → HEADING_1 (22pt, kalın, mavi, Google Sans)
## Bölüm          → HEADING_2 (16pt, kalın, koyu mavi)
### Alt Başlık    → HEADING_3 (13pt, kalın)
* veya - Madde   → Bullet listesi (native)
1. Madde         → Numaralı liste (native)
---              → Ayırıcı
Normal metin     → Arial 11pt, 120% satır aralığı
```

**Fonksiyonlar:**

| Fonksiyon | Açıklama |
|-----------|----------|
| `create_document(title, body_text, theme)` | Markdown içerikli yeni belge |
| `create_professional_document(title, sections, theme)` | Bölüm listesinden belge |
| `append_to_document(doc_id, text, theme)` | Var olan belgeye ekle |
| `read_document(doc_id)` | Belge içeriğini oku |

---

### `slides_agent.py` — Profesyonel Sunum Motoru

**Fonksiyonlar:**

| Fonksiyon | Açıklama |
|-----------|----------|
| `create_full_presentation(title, slides, subtitle, theme)` | Tam sunum (kapak dahil) |
| `add_slide_with_text(pres_id, title, body, theme)` | Var olan sunuma slayt ekle |
| `read_presentation(pres_id)` | Sunum içeriğini oku |

**`slides` parametresi formatı:**

```python
slides = [
    {"title": "Giriş", "content": "Madde 1\nMadde 2\nMadde 3"},
    {"title": "Bölüm 1", "section": True},          # Bölüm ayırıcı
    {"title": "Detaylar", "content": "Açıklama\nÖrnekler"},
    {"title": "Sonuç", "layout": "TITLE_ONLY"},      # İçeriksiz slayt
]
```

**Temalar:**

| Tema | Kullanım Alanı | Renk Paleti |
|------|---------------|-------------|
| `blue` | Kurumsal, iş sunumları | Koyu lacivert kapak |
| `teal` | Teknoloji, yazılım | Koyu yeşil-mavi kapak |
| `dark` | Modern, yaratıcı | Neredeyse siyah kapak |
| `red` | Güçlü, acil mesaj | Bordo kapak |

---

## 🧠 LLM Modeli Seçimi

Web arayüzünde sol panelden Ollama'da yüklü modeller arasında anlık geçiş yapılabilir.

Terminal arayüzü için `.env` dosyasında model adını değiştirin:

```env
OLLAMA_MODEL=mistral
```

**Önerilen modeller:**

| Model | Boyut | Güçlü Yönü |
|-------|-------|------------|
| `llama3` | 8B | Genel amaçlı, hızlı |
| `mistral` | 7B | Kod ve analiz |
| `gemma2` | 9B | Çok dilli destek |
| `phi3` | 3.8B | Hafif, düşük RAM |
| `qwen2` | 7B | Türkçe destek |

---

## 🎤 Sesli Komut

### Web Arayüzü
Sayfanın üst kısmındaki 🎤 mikrofon simgesine tıklayın, konuşun ve bırakın. Ses otomatik tanınarak komut kutusuna düşer.

### Terminal Arayüzü
Komut satırında `s` yazıp Enter'a basın. Mikrofon dinlemeye geçer.

> **Not:** Ses tanıma için internet bağlantısı gereklidir (Google Speech Recognition API). Tamamen offline kullanım için `voice_handler.py`'deki recognizer'ı Whisper gibi yerel bir çözümle değiştirin.

---

## ❓ Sık Sorulan Sorular

**Ollama bağlanamıyor?**
```bash
ollama serve   # Önce servisi başlatın
```

**`credentials.json` bulunamıyor?**  
Google Cloud Console'dan OAuth client indirip proje dizinine kopyalamanız gerekiyor. [Kurulum → Adım 5](#5-google-api-kimlik-bilgileri) bölümüne bakın.

**`token.json` hatası?**  
Dosyayı silin ve uygulamayı yeniden başlatın; Google yetkilendirme ekranı açılacaktır:
```bash
del token.json   # Windows
rm token.json    # macOS / Linux
```

**Ses tanıma çalışmıyor (Terminal)?**  
PyAudio kurulumu bazen sorunlu olabilir:
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# macOS
brew install portaudio
pip install pyaudio
```

**Yeni bir Google servisi eklemek istiyorum?**  
1. `<servis>_agent.py` oluşturun  
2. `auth_google.py`'de `get_all_services()` fonksiyonuna ekleyin  
3. `main.py` ve `web_ui.py` içindeki `ACTION_MAP`'e girdileri ekleyin  
4. `llm_router.py`'deki sistem promptuna servisi tanımlayın

---

## 🔒 Güvenlik

- `credentials.json` ve `token.json` dosyaları `.gitignore`'da tanımlıdır — **asla commit etmeyin**
- `.env` dosyası da `.gitignore`'dadır; hassas bilgileri buraya yazın
- Tüm LLM işlemleri yerel makinenizde çalışır; komutlarınız dış sunuculara gönderilmez
- Google API'ye yalnızca `config.py`'deki kapsamlar (scopes) dahilinde erişilir

---

## 📦 Bağımlılıklar

| Paket | Versiyon | Kullanım |
|-------|---------|----------|
| `google-api-python-client` | 2.131.0 | Google API istemcisi |
| `google-auth-oauthlib` | 1.2.0 | OAuth 2.0 kimlik doğrulama |
| `openai` | 1.51.0 | Ollama OpenAI-uyumlu API |
| `ollama` | 0.4.7 | Ollama Python SDK |
| `streamlit` | 1.38.0 | Web arayüzü |
| `SpeechRecognition` | 3.10.4 | Ses tanıma |
| `PyAudio` | 0.2.14 | Mikrofon erişimi |
| `rich` | 13.7.1 | Renkli terminal çıktısı |
| `httpx` | 0.27.0 | HTTP istemcisi |
| `python-dotenv` | 1.0.1 | `.env` dosyası desteği |
| `audio-recorder-streamlit` | 0.0.10 | Tarayıcı mikrofon kaydı |

---

## 👥 Geliştirici Ekibi

Bu proje **YZT MEVZUU** katkılarıyla geliştirilmiştir.

---

<div align="center">

**Google AI Asistan** — Yerel LLM gücüyle Google ekosisteminizi yönetin.

</div>
