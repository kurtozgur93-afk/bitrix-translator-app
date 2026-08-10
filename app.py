import os
import requests
import streamlit as st

# Sayfa yapılandırması
st.set_page_config(
    page_title="Bitrix24 & VibeCode Akıllı Çeviri Asistanı",
    page_icon="🌍",
    layout="wide",
)

# API Anahtarını al (Önce Streamlit Secrets, yoksa .env / ortam değişkeni)
API_KEY = None
if "VIBE_API_KEY" in st.secrets:
  API_KEY = st.secrets["VIBE_API_KEY"]
else:
  API_KEY = os.getenv("VIBE_API_KEY")

# Vibe API Yapılandırması
VIBE_API_URL = "https://api.vibe.io/v1/translate"  # Örnek uç nokta


def translate_with_vibe(text, target_language, context=""):
  if not API_KEY:
    return (
        "Hata: VIBE_API_KEY bulunamadı! Lütfen Streamlit Secrets veya .env"
        " dosyanızı kontrol edin."
    )

  headers = {
      "Authorization": f"Bearer {API_KEY}",
      "Content-Type": "application/json",
  }

  payload = {
      "text": text,
      "target_language": target_language,
      "context": context,
  }

  try:
    # Gerçek API entegrasyonu için istek bloğu
    # response = requests.post(VIBE_API_URL, json=payload, headers=headers, timeout=30)
    # if response.status_code == 200:
    #     return response.json().get("translated_text", "Çeviri alınamadı.")
    # else:
    #     return f"API Hatası: {response.status_code} - {response.text}"

    # Test/Simülasyon Modu (API bağlantısı aktif olana kadar güvenli dönüş)
    return f"[VibeCode Simülasyon Çevirisi - {target_language}]: {text}"
  except Exception as e:
    return f"Bağlantı hatası oluştu: {str(e)}"


# Arayüz Tasarımı
st.title("🌍 Bitrix24 & VibeCode Akıllı Çeviri Asistanı")
st.markdown(
    "Bitrix24 projeleriniz, pazarlama kampanyalarınız ve yerelleştirme"
    " süreçleriniz için yapay zeka destekli profesyonel çeviri asistanı."
)

st.divider()

# Yan Menü (Ayarlar)
st.sidebar.header("⚙️ Çeviri Ayarları")
target_lang = st.sidebar.selectbox(
    "Hedef Dil",
    [
        "Türkçe (Turkish)",
        "Rusça (Russian)",
        "İngilizce (English)",
        "İspanyolca (Spanish)",
        "Almanca (German)",
    ],
)

content_context = st.sidebar.selectbox(
    "İçerik Tonu / Bağlam",
    [
        "Kurumsal & Resmi (Corporate)",
        "Pazarlama & Sosyal Medya (Marketing)",
        "Yazılım & Teknik (Technical)",
        "Günlük & Ofis Mizahı (Casual)",
    ],
)

# Ana Ekran - Giriş Alanı
col1, col2 = st.columns(2)

with col1:
  st.subheader("📝 Kaynak Metin")
  source_text = st.text_area(
      "Çevrilmesini istediğiniz metni buraya girin:",
      height=200,
      placeholder="Örn: Bitrix24 CRM süreçlerinizi optimize edin...",
  )

with col2:
  st.subheader("🎯 Çeviri Sonucu")
  output_placeholder = st.empty()

# Çeviri Butonu
if st.button("🚀 Çeviriyi Başlat", type="primary"):
  if source_text.strip() == "":
    st.warning("Lütfen çevrilecek bir metin girin.")
  else:
    with st.spinner("VibeCode yapay zeka modelleri çalışıyor..."):
      result = translate_with_vibe(
          source_text, target_lang, content_context
      )
      with col2:
        output_placeholder.text_area(
            "Sonuç:", value=result, height=200, label_visibility="collapsed"
        )
      st.success("Çeviri başarıyla tamamlandı!")
