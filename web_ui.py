# ===================================================
# web_ui.py — Streamlit Web Arayüzü
# ===================================================
# Google AI Asistan'ın modern web tabanlı arayüzü.
# Chat arayüzü, yan panel durum bilgileri ve sesli
# komut desteği içerir.
#
# Çalıştırma: streamlit run web_ui.py
# ===================================================

import streamlit as st
import time
import json
import io
import httpx
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder

import config
from auth_google import authenticate, get_all_services
from llm_router import analyze_intent, get_chat_response

# ---- Agent modülleri ----
import drive_agent
import docs_agent
import sheets_agent
import slides_agent
import calendar_agent
import gmail_agent


# ================================================================
# Sayfa Konfigürasyonu
# ================================================================
st.set_page_config(
    page_title="Google AI Asistan",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# Özel CSS — Modern Koyu Tema
# ================================================================
st.markdown("""
<style>
    /* Mikrofon alanı */
    .mic-container {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.8rem 1rem;
        background: linear-gradient(135deg, #1e1e2e 0%, #181825 100%);
        border: 1px solid #313244;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .mic-status {
        font-size: 0.85rem;
        color: #a6adc8;
    }
    .mic-status.recording {
        color: #f38ba8;
        animation: pulse 1.5s infinite;
    }
    .mic-status.success {
        color: #a6e3a1;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .voice-text-box {
        background: #1e1e2e;
        border: 1px solid #a6e3a1;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin: 0.5rem 0;
        color: #cdd6f4;
        font-size: 0.95rem;
    }

    /* Ana başlık stili */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }

    /* Durum kartları */
    .status-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .status-card.success {
        border-left: 4px solid #a6e3a1;
    }
    .status-card.error {
        border-left: 4px solid #f38ba8;
    }
    .status-card.warning {
        border-left: 4px solid #f9e2af;
    }

    /* Servis badge'leri */
    .service-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.15rem;
    }
    .badge-drive { background: #1a73e8; color: white; }
    .badge-docs { background: #4285f4; color: white; }
    .badge-sheets { background: #0f9d58; color: white; }
    .badge-slides { background: #f4b400; color: #333; }
    .badge-calendar { background: #4285f4; color: white; }
    .badge-gmail { background: #ea4335; color: white; }

    /* Örnek komut butonları */
    .example-btn {
        display: block;
        width: 100%;
        text-align: left;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        border-radius: 8px;
        border: 1px solid #313244;
        background: #1e1e2e;
        color: #cdd6f4;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .example-btn:hover {
        background: #313244;
        border-color: #667eea;
    }

    /* Chat mesaj stilleri */
    .stChatMessage {
        border-radius: 12px !important;
    }

    /* Sidebar başlıkları */
    .sidebar-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #a6adc8;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #313244;
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# Ses Tanıma (Speech-to-Text) — Tarayıcı Mikrofonu
# ================================================================

def transcribe_audio(audio_bytes: bytes) -> str | None:
    """
    Tarayıcıdan gelen WAV ses verisini metne çevirir.
    Google Speech Recognition API kullanır.

    Args:
        audio_bytes: WAV formatında ses verisi.

    Returns:
        str | None: Tanınan metin veya hata durumunda None.
    """
    if not audio_bytes:
        return None

    recognizer = sr.Recognizer()
    try:
        # Byte verisini AudioFile olarak oku
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

        # Google Speech Recognition ile metne çevir
        text = recognizer.recognize_google(
            audio_data, language=config.SPEECH_LANGUAGE
        )
        return text

    except sr.UnknownValueError:
        return None  # Ses anlaşılamadı
    except sr.RequestError as e:
        st.error(f"Ses tanıma servisi hatası: {e}")
        return None
    except Exception as e:
        st.error(f"Ses işleme hatası: {e}")
        return None


# ================================================================
# Servis Yönlendirme Haritası (main.py ile aynı)
# ================================================================
ACTION_MAP = {
    ("drive", "list_files"): {"func": drive_agent.list_files, "svc_key": "drive"},
    ("drive", "search_files"): {"func": drive_agent.search_files, "svc_key": "drive"},
    ("drive", "download_file"): {"func": drive_agent.download_file, "svc_key": "drive"},
    ("drive", "get_file_info"): {"func": drive_agent.get_file_info, "svc_key": "drive"},
    ("docs", "read_document"): {"func": docs_agent.read_document, "svc_key": "docs"},
    ("docs", "create_document"): {"func": docs_agent.create_document, "svc_key": "docs"},
    ("docs", "create_professional_document"): {"func": docs_agent.create_professional_document, "svc_key": "docs"},
    ("docs", "append_to_document"): {"func": docs_agent.append_to_document, "svc_key": "docs"},
    ("sheets", "read_sheet"): {"func": sheets_agent.read_sheet, "svc_key": "sheets"},
    ("sheets", "write_to_sheet"): {"func": sheets_agent.write_to_sheet, "svc_key": "sheets"},
    ("sheets", "append_to_sheet"): {"func": sheets_agent.append_to_sheet, "svc_key": "sheets"},
    ("sheets", "create_spreadsheet"): {"func": sheets_agent.create_spreadsheet, "svc_key": "sheets"},
    ("slides", "read_presentation"): {"func": slides_agent.read_presentation, "svc_key": "slides"},
    ("slides", "create_presentation"): {"func": slides_agent.create_presentation, "svc_key": "slides"},
    ("slides", "create_full_presentation"): {"func": slides_agent.create_full_presentation, "svc_key": "slides"},
    ("slides", "add_slide_with_text"): {"func": slides_agent.add_slide_with_text, "svc_key": "slides"},
    ("calendar", "list_upcoming_events"): {"func": calendar_agent.list_upcoming_events, "svc_key": "calendar"},
    ("calendar", "create_event"): {"func": calendar_agent.create_event, "svc_key": "calendar"},
    ("calendar", "delete_event"): {"func": calendar_agent.delete_event, "svc_key": "calendar"},
    ("calendar", "search_events"): {"func": calendar_agent.search_events, "svc_key": "calendar"},
    ("gmail", "send_email"): {"func": gmail_agent.send_email, "svc_key": "gmail"},
    ("gmail", "create_draft"): {"func": gmail_agent.create_draft, "svc_key": "gmail"},
    ("gmail", "list_messages"): {"func": gmail_agent.list_messages, "svc_key": "gmail"},
    ("gmail", "read_message"): {"func": gmail_agent.read_message, "svc_key": "gmail"},
}


# ================================================================
# Yardımcı Fonksiyonlar
# ================================================================

def check_ollama_status() -> tuple[bool, list[str]]:
    """Ollama servisinin durumunu ve yüklü modelleri kontrol eder."""
    try:
        resp = httpx.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []


@st.cache_resource(show_spinner=False)
def init_google_services():
    """
    Google servislerini başlatır ve cache'ler.
    Sadece ilk çalıştırmada authenticate edilir.
    """
    try:
        creds = authenticate()
        services = get_all_services(creds)
        return services, None
    except Exception as e:
        return None, str(e)


def execute_command(intent: dict, services: dict) -> str:
    """Niyet nesnesini alır ve ilgili agent fonksiyonunu çalıştırır."""
    service_name = intent.get("service", "")
    action = intent.get("action", "")
    params = intent.get("params", {})

    # Genel sohbet
    if service_name == "chat":
        return params.get("message", intent.get("explanation", ""))

    # Eylem haritasında bul
    map_key = (service_name, action)
    if map_key not in ACTION_MAP:
        return f"❌ '{service_name}.{action}' eylemi desteklenmiyor."

    action_info = ACTION_MAP[map_key]
    func = action_info["func"]
    svc_key = action_info["svc_key"]

    api_service = services.get(svc_key)
    if api_service is None:
        return f"❌ '{svc_key}' servisi başlatılamadı."

    try:
        return func(api_service, **params)
    except TypeError as e:
        return f"⚠️ Parametre hatası: {e}\nLütfen komutunuzu daha ayrıntılı verin."
    except Exception as e:
        return f"❌ İşlem hatası: {e}"


def get_service_icon(service: str) -> str:
    """Servis adına göre emoji döndürür."""
    icons = {
        "drive": "📁", "docs": "📄", "sheets": "📊",
        "slides": "🎞️", "calendar": "📅", "gmail": "📧", "chat": "💬",
    }
    return icons.get(service, "⚡")


def get_service_color(service: str) -> str:
    """Servis adına göre badge CSS sınıfı döndürür."""
    return f"badge-{service}" if service in ("drive", "docs", "sheets", "slides", "calendar", "gmail") else ""


# ================================================================
# Session State Başlatma
# ================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "services" not in st.session_state:
    st.session_state.services = None

if "services_error" not in st.session_state:
    st.session_state.services_error = None

if "initialized" not in st.session_state:
    st.session_state.initialized = False

if "voice_text" not in st.session_state:
    st.session_state.voice_text = None

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

if "selected_model" not in st.session_state:
    st.session_state.selected_model = config.OLLAMA_MODEL


# ================================================================
# Yan Panel (Sidebar)
# ================================================================
with st.sidebar:
    st.markdown("### 🤖 Google AI Asistan")
    st.caption(f"v{config.APP_VERSION} — Ollama Lokal LLM")

    st.divider()

    # --- Ollama Durum ---
    st.markdown('<p class="sidebar-title">🧠 LLM Durumu</p>', unsafe_allow_html=True)
    ollama_ok, ollama_models = check_ollama_status()

    if ollama_ok:
        st.success("Ollama Aktif", icon="✅")

        # Model seçici — yüklü modeller arasından seç
        if ollama_models:
            # Mevcut seçim listede yoksa ilk modele düş
            current = st.session_state.selected_model
            if current not in ollama_models:
                current = ollama_models[0]
                st.session_state.selected_model = current

            chosen = st.selectbox(
                "Aktif Model",
                options=ollama_models,
                index=ollama_models.index(current),
                key="model_selectbox",
            )
            if chosen != st.session_state.selected_model:
                st.session_state.selected_model = chosen
                config.OLLAMA_MODEL = chosen
                st.rerun()
            else:
                config.OLLAMA_MODEL = chosen
        else:
            st.warning("Yüklü model bulunamadı!")
            st.code(f"ollama pull {config.OLLAMA_MODEL}", language="bash")
    else:
        st.error("Ollama bağlantısı yok!", icon="❌")
        st.code("ollama serve", language="bash")

    st.divider()

    # --- Google Servisleri ---
    st.markdown('<p class="sidebar-title">☁️ Google Servisleri</p>', unsafe_allow_html=True)

    if not st.session_state.initialized:
        with st.spinner("Google hesabına bağlanılıyor..."):
            services, error = init_google_services()
            st.session_state.services = services
            st.session_state.services_error = error
            st.session_state.initialized = True

    if st.session_state.services:
        svc = st.session_state.services
        service_labels = {
            "drive": ("📁", "Drive"),
            "docs": ("📄", "Docs"),
            "sheets": ("📊", "Sheets"),
            "slides": ("🎞️", "Slides"),
            "calendar": ("📅", "Calendar"),
            "gmail": ("📧", "Gmail"),
        }
        active = sum(1 for v in svc.values() if v is not None)
        st.success(f"{active}/{len(svc)} servis aktif", icon="✅")

        cols = st.columns(3)
        for i, (key, (icon, label)) in enumerate(service_labels.items()):
            with cols[i % 3]:
                if svc.get(key):
                    st.markdown(f"<span style='color:#a6e3a1'>{icon} {label}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:#f38ba8'>{icon} {label}</span>", unsafe_allow_html=True)
    elif st.session_state.services_error:
        st.error(f"Bağlantı hatası: {st.session_state.services_error}", icon="❌")
    else:
        st.warning("Servisler başlatılıyor...", icon="⏳")

    st.divider()

    # --- Örnek Komutlar ---
    st.markdown('<p class="sidebar-title">💡 Örnek Komutlar</p>', unsafe_allow_html=True)

    examples = [
        "📁 Drive dosyalarımı listele",
        "📅 Yarın saat 14'te toplantı ekle",
        "📧 ali@mail.com'a merhaba yaz",
        "📄 Yeni bir Google Docs oluştur",
        "📊 Takvimimdeki etkinlikleri göster",
        "📬 Gmail gelen kutumu göster",
    ]

    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            # Örnek komutu chat input'a gönder
            st.session_state.pending_example = ex

    st.divider()

    # --- Ayarlar ---
    st.markdown('<p class="sidebar-title">⚙️ Ayarlar</p>', unsafe_allow_html=True)

    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔄 Servisleri Yenile", use_container_width=True):
        st.cache_resource.clear()
        st.session_state.initialized = False
        st.rerun()


# ================================================================
# Ana İçerik Alanı
# ================================================================

# Başlık
st.markdown("""
<div class="main-header">
    <h1>🤖 Google AI Asistan</h1>
    <p>Google ekosistemi ile tam entegre kişisel yapay zeka asistanınız</p>
</div>
""", unsafe_allow_html=True)

# ================================================================
# 🎤 Sesli Komut Alanı
# ================================================================
with st.container():
    mic_col1, mic_col2 = st.columns([1, 11])

    with mic_col1:
        # Mikrofon kayıt butonu
        audio_bytes = audio_recorder(
            text="",
            recording_color="#f38ba8",
            neutral_color="#a6adc8",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=2.5,   # 2.5 sn sessizlikten sonra otomatik dur
            sample_rate=16000,
        )

    with mic_col2:
        # Ses kaydedildiyse ve yeni bir kayıtsa
        if audio_bytes and audio_bytes != st.session_state.last_audio_bytes:
            st.session_state.last_audio_bytes = audio_bytes
            with st.spinner("🎤 Ses tanınıyor..."):
                text = transcribe_audio(audio_bytes)

            if text:
                st.session_state.voice_text = text
                st.markdown(
                    f'<div class="voice-text-box">🎤 <strong>Tanınan:</strong> {text}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning("Ses anlaşılamadı. Lütfen tekrar deneyin.", icon="🎤")
        elif not audio_bytes:
            st.markdown(
                '<span class="mic-status">⬅️ Mikrofon simgesine tıklayıp konuşun, '
                'bırakınca otomatik tanınır</span>',
                unsafe_allow_html=True,
            )

# Sesli komut tanındıysa "Gönder" butonu göster
if st.session_state.voice_text:
    vc1, vc2, vc3 = st.columns([6, 2, 2])
    with vc1:
        st.info(f"🎤 **Sesli komut:** {st.session_state.voice_text}")
    with vc2:
        if st.button("✅ Gönder", key="voice_send", use_container_width=True, type="primary"):
            st.session_state.pending_example = st.session_state.voice_text
            st.session_state.voice_text = None
            st.rerun()
    with vc3:
        if st.button("❌ İptal", key="voice_cancel", use_container_width=True):
            st.session_state.voice_text = None
            st.rerun()

# Eğer henüz hiç mesaj yoksa hoş geldin mesajı göster
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding: 2rem; opacity: 0.7;">
        <p style="font-size: 3rem; margin-bottom: 0.5rem;">👋</p>
        <p style="font-size: 1.1rem;">Merhaba! Size nasıl yardımcı olabilirim?</p>
        <p style="font-size: 0.85rem; opacity: 0.7;">
            Metin yazın, yandaki örnek komutları deneyin veya 🎤 mikrofon ile sesli komut verin.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Hızlı başlangıç kartları
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 📁 Drive & Docs")
        st.markdown("Dosya arama, listeleme, belge oluşturma ve düzenleme")
    with col2:
        st.markdown("#### 📅 Takvim & Mail")
        st.markdown("Etkinlik ekleme, mail gönderme ve taslak oluşturma")
    with col3:
        st.markdown("#### 🎞️ Sheets & Slides")
        st.markdown("Tablo okuma/yazma, sunum oluşturma")


# ================================================================
# Chat Geçmişini Göster
# ================================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

        # Eğer asistan mesajında servis bilgisi varsa küçük badge göster
        if msg["role"] == "assistant" and "service_info" in msg:
            info = msg["service_info"]
            icon = get_service_icon(info.get("service", ""))
            st.caption(f"{icon} {info.get('service', '').title()} → {info.get('action', '')}")


# ================================================================
# Kullanıcı Girdisi İşleme
# ================================================================

# Örnek komut butonu tıklandıysa
pending = st.session_state.pop("pending_example", None)

# Chat input
user_input = st.chat_input("Komutunuzu yazın... (ör: Drive dosyalarımı listele)")

# Pending varsa onu kullan, yoksa normal input
if pending:
    prompt = pending
elif user_input:
    prompt = user_input
else:
    prompt = None

if prompt:
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Asistan yanıtı oluştur
    with st.chat_message("assistant", avatar="🤖"):
        # Servisler hazır mı?
        if not st.session_state.services:
            error_msg = "❌ Google servisleri henüz başlatılmadı. Lütfen sayfayı yenileyin."
            st.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            # LLM ile niyet analizi — seçili modeli uygula
            config.OLLAMA_MODEL = st.session_state.selected_model
            with st.spinner(f"🧠 Düşünüyorum... ({st.session_state.selected_model})"):
                intent = analyze_intent(prompt)

            if intent is None:
                fail_msg = "⚠️ Komutunuz anlaşılamadı. Lütfen farklı bir şekilde ifade edin."
                st.markdown(fail_msg)
                st.session_state.messages.append({"role": "assistant", "content": fail_msg})
            else:
                service_name = intent.get("service", "?")
                action = intent.get("action", "?")
                explanation = intent.get("explanation", "")

                # Açıklama göster
                if explanation:
                    st.info(f"💡 {explanation}")

                # Komutu çalıştır
                with st.spinner(f"{get_service_icon(service_name)} İşlem yürütülüyor..."):
                    result = execute_command(intent, st.session_state.services)

                # Sonucu göster
                st.markdown(result)

                # Servis badge'i
                st.caption(f"{get_service_icon(service_name)} {service_name.title()} → {action}")

                # Mesaj geçmişine ekle
                full_response = ""
                if explanation:
                    full_response += f"💡 *{explanation}*\n\n"
                full_response += result

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "service_info": {"service": service_name, "action": action},
                })

    st.rerun()
