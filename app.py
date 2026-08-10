import streamlit as st
<<<<<<< HEAD
import pandas as pd
import requests
import json
import zipfile
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Bitrix24 & VibeCode Localization App", page_icon="🌍", layout="wide")

st.title("🌍 Bitrix24 & VibeCode Akıllı Çeviri Asistanı")
st.markdown("VibeCode altyapısı ve referans stil rehberiyle desteklenen çok dilli otomatik lokalizasyon aracı.")

VALID_LANGUAGES = {
    "tr": {"name": "Turkish", "tone": "Professional B2B SaaS", "rule": "Translate accurately, use natural Turkish SaaS terminology."},
    "de": {"name": "German", "tone": "Professional B2B SaaS", "rule": "Use formal 'Sie' form, accurate German technical terms."},
    "br": {"name": "Portuguese (Brazil)", "tone": "Professional B2B SaaS", "rule": "Use Brazilian Portuguese business standards."},
    "pl": {"name": "Polish", "tone": "Professional B2B SaaS", "rule": "Professional corporate Polish."},
    "mx (es)": {"name": "Spanish (Mexico)", "tone": "Professional B2B SaaS", "rule": "Latin American corporate Spanish standards."},
    "fr": {"name": "French", "tone": "Professional B2B SaaS", "rule": "Professional French B2B tone."},
    "it": {"name": "Italian", "tone": "Professional B2B SaaS", "rule": "Professional Italian B2B tone."}
}

with st.sidebar:
    st.header("⚙️ API & Bağlantı Ayarları")
    gemini_key = st.text_input("Gemini API Key", value="", type="password", placeholder="AIzaSy...")
    
    st.markdown("---")
    st.info("Sol menüden Gemini API anahtarınızı girdiğinizden emin olun.")

def read_excel_native(file_obj):
    try:
        with zipfile.ZipFile(file_obj, 'r') as z:
            strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                ss_tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                for si in ss_tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                    t = si.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                    strings.append(t.text if t is not None and t.text is not None else '')
            
            sheet_data = z.read('xl/worksheets/sheet1.xml')
            sheet_tree = ET.fromstring(sheet_data)
            
            rows = []
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for row in sheet_tree.findall('.//main:row', ns):
                row_data = []
                for c in row.findall('main:c', ns):
                    t = c.get('t')
                    v = c.find('main:v', ns)
                    val = v.text if v is not None and v.text is not None else ''
                    if t == 's' and val.isdigit():
                        val = strings[int(val)]
                    row_data.append(val)
                rows.append(row_data)
            
            if not rows:
                return pd.DataFrame()
            
            raw_header = rows[0]
            header = []
            seen = {}
            for i, h in enumerate(raw_header):
                h_str = str(h).strip() if h is not None and str(h).strip() != "" else f"Unnamed_{i}"
                if h_str in seen:
                    seen[h_str] += 1
                    header.append(f"{h_str}_{seen[h_str]}")
                else:
                    seen[h_str] = 0
                    header.append(h_str)

            data = rows[1:]
            max_len = len(header)
            normalized_data = [r + [''] * (max_len - len(r)) for r in data]
            df = pd.DataFrame(normalized_data, columns=header)
            return df
    except Exception:
        file_obj.seek(0)
        return pd.read_excel(file_obj)

def call_gemini_api(api_key, prompt):
    # En güncel ve aktif model uç noktası (gemini-3.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            st.warning(f"API Hatası (Kod {response.status_code}): {response.text}")
    except Exception as e:
        st.warning(f"Bağlantı Hatası: {e}")
    return None

def get_few_shot_examples(ref_df, lang_code, ref_lang_col):
    examples = []
    if ref_df is not None and ref_lang_col in ref_df.columns and lang_code in ref_df.columns:
        valid_rows = ref_df.dropna(subset=[ref_lang_col, lang_code]).head(3)
        for _, row in valid_rows.iterrows():
            examples.append(f"EN: {row[ref_lang_col]}\nTarget ({lang_code}): {row[lang_code]}")
    return "\n---\n".join(examples)

def translate_chunks_for_language(api_key, lang_code, texts, ref_df, ref_lang_col):
    profile = VALID_LANGUAGES.get(lang_code.lower(), {"name": lang_code, "tone": "Professional B2B SaaS", "rule": "Translate accurately."})
    examples_str = get_few_shot_examples(ref_df, lang_code, ref_lang_col)
    
    chunk_size = 5
    all_translated = []
    
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i+chunk_size]
        cleaned_chunk = [str(t) if pd.notna(t) and str(t).strip() != "" else "" for t in chunk]
        
        if all(t == "" for t in cleaned_chunk):
            all_translated.extend([""] * len(chunk))
            continue
            
        formatted_list = "\n".join([f"--- ITEM {idx} ---\n{t}" for idx, t in enumerate(cleaned_chunk) if t != ""])
        
        prompt = f"""You are an expert Bitrix24 Localization Specialist. Translate each English item below strictly to {profile['name']} ({lang_code}).
Tone/Style: {profile['tone']}
Rule: {profile['rule']}

Reference Style Examples:
{examples_str}

CRITICAL: Preserve HTML tags and placeholders. Output matching format precisely:
--- ITEM 0 ---
[Translated text]

Items to translate:
{formatted_list}"""
        
        resp_text = call_gemini_api(api_key, prompt)
        
        if resp_text:
            resp_text = resp_text.strip()
            chunk_results = [""] * len(chunk)
            parts = resp_text.split("--- ITEM ")
            for part in parts:
                if "---" in part:
                    lines = part.split("\n", 1)
                    if len(lines) == 2:
                        idx_str = lines[0].replace("---", "").strip()
                        translation = lines[1].strip()
                        try:
                            idx = int(idx_str)
                            if idx < len(chunk_results):
                                chunk_results[idx] = translation
                        except:
                            continue
            
            for idx, res in enumerate(chunk_results):
                if res == "" and cleaned_chunk[idx] != "":
                    fallback_lines = [l.strip() for l in resp_text.split("\n") if l.strip() and not "---" in l]
                    if idx < len(fallback_lines):
                        chunk_results[idx] = fallback_lines[idx]
                    else:
                        chunk_results[idx] = cleaned_chunk[idx]

            all_translated.extend(chunk_results)
        else:
            all_translated.extend(cleaned_chunk)
            
    return all_translated

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Referans Dosya (Stil Rehberi)")
    ref_file_uploaded = st.file_uploader("referans.xlsx dosyanızı yükleyin", type=["xlsx"], key="ref")

with col2:
    st.subheader("2. Çevrilecek Yeni Dosya")
    target_file_uploaded = st.file_uploader("Yeni Excel dosyanızı yükleyin", type=["xlsx"], key="target")

if target_file_uploaded is not None:
    df_target = read_excel_native(target_file_uploaded)
    
    ref_df = None
    if ref_file_uploaded is not None:
        ref_file_uploaded.seek(0)
        ref_df = read_excel_native(ref_file_uploaded)

    st.markdown("---")
    st.subheader("📊 Yüklenen Dosya Önizlemesi")
    st.dataframe(df_target.head(3), use_container_width=True)
    
    if st.button("🚀 Çeviriyi Başlat", type="primary"):
        if not gemini_key or gemini_key.strip() == "":
            st.error("Lütfen sol menüden geçerli bir Gemini API Key girin!")
            st.stop()
            
        source_cols = [c for c in df_target.columns if c.lower() in ['en', 'en (com)', 'english']]
        source_col = source_cols[0] if source_cols else df_target.columns[0]
        
        ref_source_cols = [c for c in ref_df.columns if c.lower() in ['en', 'en (com)', 'english']] if ref_df is not None else []
        ref_source_col = ref_source_cols[0] if ref_source_cols else (ref_df.columns[0] if ref_df is not None else None)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        target_langs = [c.strip() for c in df_target.columns if c.strip().lower() in VALID_LANGUAGES]
        
        if not target_langs:
            st.error("Dosyada çevrilecek geçerli hedef dil sütunu (de, br, pl, mx (es), fr, it, tr) bulunamadı!")
            st.stop()
            
        total_langs = len(target_langs)
        for idx, lang in enumerate(target_langs):
            status_text.text(f"[{lang}] dili çevriliyor...")
            texts = df_target[source_col].tolist()
            df_target[lang] = translate_chunks_for_language(gemini_key, lang, texts, ref_df, ref_source_col)
            progress_bar.progress((idx + 1) / total_langs)
            
        status_text.text("Tüm çeviriler başarıyla tamamlandı!")
        
        output_filename = "Bitrix_Cevrilmis.csv"
        csv_data = df_target.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📥 Çevrilen Dosyayı İndir (CSV)",
            data=csv_data,
            file_name=output_filename,
            mime="text/csv"
        )
=======
import requests
import os

st.set_page_config(page_title="VibeCode & Bitrix24 Manager", layout="wide")

st.title("🚀 VibeCode & Bitrix24 Entegrasyon Paneli")

# API Anahtarını güvenli bir şekilde çekiyoruz
VIBE_API_KEY = st.secrets.get("VIBE_API_KEY") or os.getenv("VIBE_API_KEY")
API_BASE_URL = "https://vibecode.bitrix24.tech/v1"

if not VIBE_API_KEY:
    st.error("API Anahtarı bulunamadı! Lütfen ayarları kontrol edin.")
    st.stop()

def get_user_info():
    headers = {"Authorization": f"Bearer {VIBE_API_KEY}"}
    try:
        response = requests.get(f"{API_BASE_URL}/me", headers=headers)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

if st.button("Hesap Bilgilerini Getir", type="primary"):
    with st.spinner("VibeCode sunucusuna bağlanılıyor..."):
        data = get_user_info()
        if data:
            st.success("Bağlantı başarılı!")
            st.json(data)
        else:
            st.error("Bağlantı kurulamadı veya API anahtarı geçersiz.")
>>>>>>> 2f0d057 (BitrixTranslator VibeCode entegrasyonu tamamlandi)
