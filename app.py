import streamlit as st
import sqlite3
import os
from datetime import datetime
import urllib.parse

# DATABASE — PAKAI /tmp BIAR BISA TULIS DI STREAMLIT CLOUD
DB_PATH = "/tmp/kajian_qna.db"
if not os.path.exists(DB_PATH):
    conn_init = sqlite3.connect(DB_PATH)
    cur = conn_init.cursor()
    cur.execute('''CREATE TABLE kajian (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, nama_ustadz TEXT, tanggal_kajian TEXT, aktif INTEGER DEFAULT 0)''')
    cur.execute('''CREATE TABLE pertanyaan (id INTEGER PRIMARY KEY AUTOINCREMENT, kajian_id INTEGER, nama_penanya TEXT, isi TEXT, tanggal TEXT DEFAULT (datetime('now')), approved INTEGER DEFAULT 0)''')
    conn_init.commit()
    conn_init.close()

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# FUNGSI
def get_kajian_aktif():
    c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    return c.fetchone()

# MODE PENANYA
query_params = st.query_params
if query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    aktif = get_kajian_aktif()
    if not aktif:
        st.error("Belum ada kajian aktif!")
        st.stop()

    st.success(f"KAJIAN: {aktif[1]}")
    st.info(f"{aktif[2] or 'Ustadz'} • {aktif[3] or ''}")

    with st.form("tanya"):
        nama = st.text_input("Nama Anda")
        pertanyaan = st.text_area("Pertanyaan", height=150)
        if st.form_submit_button("Kirim Pertanyaan", type="primary"):
            if nama and pertanyaan:
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, isi) VALUES (?, ?, ?)",
                          (aktif[0], nama.strip(), pertanyaan.strip()))
                conn.commit()
                st.success("Berhasil dikirim!")
                st.balloons()
                st.rerun()
            else:
                st.error("Isi semua field!")

    st.stop()

# DASHBOARD (login, operator, ustadz, QR) — tetap pakai kode sebelumnya
st.set_page_config(page_title="Dashboard", layout="wide")
st.title("KajianQNA")

# Login dan dashboard tetap seperti versi sebelumnya...
# (kamu tinggal copy dari kode lama)

st.sidebar.success("Link QR Tetap:")
st.sidebar.code(f"https://tanya-ustadz-dirj.streamlit.app/?penanya=yes")
