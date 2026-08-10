import os
import requests
import streamlit as st

# Sayfa yapılandırması
st.set_page_config(
    page_title="Bitrix24 & VibeCode Akıllı Çeviri Asistanı",
    page_icon="🌍",
    layout="wide",
)

# API Anahtarını al (Streamlit Secrets'tan)
API_KEY = st.secrets.get("VIBE_API_KEY")

# VibeCode Deploy API Uç Noktası
VIBE_API_URL = "https://vibecode.bitrix24.tech/v1/infra/servers/43d1897c-400e-43bd-9fb5-2f1af6425ca3/exec"

def translate_with_vibe(text, target_language, context=""):
    if not API_KEY:
        return "Hata: API anahtarı 'Secrets' kısmına eklenmemiş."

    # API'nin beklediği header yapısı
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    # API'nin beklediği payload yapısı
    payload = {
        "command": "translate",
        "text": text,
        "target_language": target_language,
        "context": context,
    }

    try:
        response = requests.post(VIBE_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # API yanıtından sonucu al
            return data.get("result", data.get("output", "Çeviri başarıyla tamamlandı."))
        else:
            return f"API Hatası ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"Bağlantı hatası oluştu: {str(e)}"

# Arayüz
st.title("🌍 Bitrix24 & VibeCode Çeviri Asistanı")

# Ayarlar
target_lang = st.sidebar.selectbox("Hedef Dil", ["Türkçe", "Rusça", "İngilizce", "İspanyolca", "Almanca"])
context = st.sidebar.selectbox("Bağlam", ["Kurumsal", "Pazarlama", "Teknik", "Günlük"])

# Giriş
source_text = st.text_area("Çevrilecek Metin:", height=200)

if st.button("🚀 Çevir"):
    if source_text.strip():
        with st.spinner("VibeCode API ile işleniyor..."):
            result = translate_with_vibe(source_text, target_lang, context)
            st.subheader("🎯 Çeviri Sonucu:")
            st.text_area("", value=result, height=200)
    else:
        st.warning("Lütfen bir metin girin.")
