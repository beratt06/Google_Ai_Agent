# ===================================================
# config.py — Merkezi Konfigürasyon Dosyası
# ===================================================
# Bu dosya, projedeki tüm sabit değerleri ve ortam
# değişkenlerini tek bir noktadan yönetir.
# ===================================================

import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")

TOKEN_FILE = os.getenv("TOKEN_FILE", "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


SPEECH_LANGUAGE = os.getenv("SPEECH_LANGUAGE", "tr-TR")

APP_NAME = "Google AI Asistan"
APP_VERSION = "1.0.0"
