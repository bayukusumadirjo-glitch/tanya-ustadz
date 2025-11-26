# app.py – Tanya Ustadz (Streamlit) – FULL & AMAN 100% (25 Nov 2025)

import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ============== KONEKSI DATABASE ==============
DB_NAME = "tanya_ustadz.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabel Kajian
    c.execute('''
        CREATE TABLE IF NOT EXISTS kajian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jud Judul TEXT NOT NULL,
            ustadz TEXT NOT NULL,
            tanggal TEXT NOT NULL,
            status TEXT DEFAULT 'nonaktif'  -- aktif / nonaktif
        )
    ''')
    
    # Tabel Pertanyaan
    c.execute('''
        CREATE TABLE IF NOT EXISTS pertanyaan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kajian_id INTEGER NOT NULL,
            nama_penanya TEXT NOT NULL,
            isi TEXT NOT NOT NULL,
            waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sudah_dibaca INTEGER DEFAULT 0,
            FOREIGN KEY (kajian_id) REFERENCES kajian(id)
        )
    ''')
    
    # Insert contoh kajian kalau tabel masih kosong
    c.execute("SELECT COUNT(*) FROM kajian")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO kajian (judul, ustadz, tanggal, status) VALUES (?, ?, ?, ?)",
                  ("Kajian Rutin Malam Selasa", "Ustadz Ahmad", "2025-11-25", "aktif"))
    
    conn.commit()
    conn.close()

init_db()

# ============== FUNGSI BANTUAN ==============
def get_kajian_aktif():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, judul, ustadz FROM kajian WHERE status = 'aktif' LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row  # (id, judul, ustadz) atau None

def tambah_pertanyaan(kajian_id, nama, isi):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO pertanyaan (kajian_id, nama_penanya, isi, waktu) 
                 VALUES (?, ?, ?, datetime('now','localtime'))""",
              (kajian_id, nama.strip(), isi.strip()))
    conn.commit()
    conn.close()

def get_pertanyaan_belum_dibaca():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT p.id, p.nama_penanya, p.isi, p.waktu, k.judul 
        FROM pertanyaan p 
        JOIN kajian k ON p.kajian_id = k.id 
        WHERE p.sudah_dibaca = 0 
        ORDER BY p.waktu ASC
    """, conn)
    conn.close()
    return df

def tandai_sudah_dibaca(pertanyaan_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE pertanyaan SET sudah_dibaca = 1 WHERE id = ?", (pertanyaan_id,))
    conn.commit()
    conn.close()

# ============== STREAMLIT UI ==============
st.set_page_config(page_title="Tanya Ustadz", layout="centered")
st.title("Tanya Ustadz – Kajian Online")

# Cek kajian aktif
kajian = get_kajian_aktif()

if kajian is None:
    st.error("Maaf, saat ini tidak ada kajian yang sedang aktif.")
    st.info("Tunggu admin mengaktifkan kajian berikutnya.")
    st.stop()

kajian_id, judul_kajian, ustadz = kajian

st.success(f"**Kajian Aktif:** {judul_kajian} – {ustadz}")

# Form tanya
with st.form("form_tanya"):
    st.write("### Kirim Pertanyaan")
    nama = st.text_input("Nama Anda", placeholder="Masukkan nama Anda")
    pertanyaan = st.text_area("Pertanyaan Anda", placeholder="Tuliskan pertanyaan Anda di sini...", height=150)
    submit = st.form_submit_button("Kirim Pertanyaan")

    if submit:
        if not nama.strip() or not pertanyaan.strip():
            st.error("Nama dan pertanyaan wajib diisi!")
        else:
            try:
                tambah_pertanyaan(kajian_id, nama, pertanyaan)
                st.success("Pertanyaan berhasil dikirim! Jazakumullah khairan.")
                st.balloons()
            except Exception as e:
                st.error("Gagal mengirim pertanyaan. Coba lagi.")

# Tampilkan pertanyaan masuk (hanya untuk admin / ustadz)
st.markdown("---")
if st.checkbox("Mode Admin / Ustadz (Lihat pertanyaan masuk)"):
    st.write("### Pertanyaan Belum Dibaca")
    df = get_pertanyaan_belum_dibaca()
    
    if df.empty:
        st.info("Belum ada pertanyaan baru.")
    else:
        for idx, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{row['nama_penanya']}** – {row['waktu'][-8:-3]}")
                    st.write(row['isi'])
                    st.caption(f"Kajian: {row['judul']}")
                with col2:
                    if st.button("Sudah Dibaca", key=row['id']):
                        tandai_sudah_dibaca(row['id'])
                        st.experimental_rerun()

st.markdown("---")
st.caption("© 2025 – Tanya Ustadz Online | Dibuat dengan ❤️ menggunakan Streamlit")
