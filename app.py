# app.py  ←←← VERSI FINAL YANG KAMU MAU (QR TETAP 1, LANGSUNG PENANYA)

import streamlit as st
import sqlite3
from datetime import datetime

# === DATABASE ===
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT,
                aktif INTEGER DEFAULT 0
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS pertanyaan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kajian_id INTEGER,
                nama_penanya TEXT NOT NULL,
                pertanyaan TEXT NOT NULL,
                tanggal TEXT,
                approved INTEGER DEFAULT 0,
                FOREIGN KEY (kajian_id) REFERENCES kajian (id)
             )''')
conn.commit()

# === PASSWORD ===
PASS_OPERATOR = "operator123"   # ganti sesuka hati
PASS_USTADZ   = "ustadz123"     # ganti sesuka hati

# === DETEKSI: apakah buka dari QR atau bukan ===
# Jika URL mengandung ?penanya=yes → langsung jadi Penanya (ini yang dipakai QR)
if st.query_params.get("penanya") == "yes":
    mode_penanya = True
else:
    mode_penanya = False

# ===================================
# 1. MODE PENANYA (langsung dari QR)
# ===================================
if mode_penanya:
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")
    st.caption("Silakan ajukan pertanyaan Anda dengan nama")

    # Cek kajian aktif
    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()

    if not aktif:
        st.error("Belum ada kajian aktif saat ini. Silakan hubungi panitia.")
        st.stop()

    st.success(f"Kajian aktif: **{aktif[1]}**")

    with st.form("form_penanya"):
        nama = st.text_input("Nama Anda (wajib)", placeholder="Ahmad / Ummu Aisyah")
        pertanyaan = st.text_area("Pertanyaan Anda", height=150, placeholder="Tuliskan dengan sopan dan jelas...")

        kirim = st.form_submit_button("Kirim Pertanyaan", use_container_width=True)

        if kirim:
            if not nama.strip():
                st.error("Nama wajib diisi!")
            elif not pertanyaan.strip():
                st.error("Pertanyaan wajib diisi!")
            elif len(pertanyaan.strip()) < 10:
                st.error("Pertanyaan terlalu pendek.")
            else:
                tgl = datetime.now().strftime("%d/%m/%Y %H:%M")
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, pertanyaan, tanggal, approved) VALUES (?, ?, ?, ?, 0)",
                          (aktif[0], nama.strip(), pertanyaan.strip(), tgl))
                conn.commit()
                st.success(f"Terima kasih {nama.split()[0]}! Pertanyaan Anda sudah terkirim.")
                st.balloons()

    st.info("Pertanyaan akan dimoderasi sebelum ditampilkan kepada Ustadz.")
    st.stop()  # agar tidak lanjut ke kode bawah

# ===================================
# 2. & 3. MODE OPERATOR & USTADZ (bukan dari QR)
# ===================================
else:
    st.set_page_config(page_title="Panel Operator & Ustadz", layout="wide")
    st.title("Panel Operator & Ustadz")

    role = st.sidebar.selectbox("Pilih Role", ["Operator", "Ustadz"])

    if role == "Ustadz":
        st.header("Dashboard Ustadz")
        pwd = st.sidebar.text_input("Password Ustadz", type="password")
        if pwd != PASS_USTADZ:
            st.error("Password salah!")
            st.stop()

        c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.success(f"Kajian aktif: **{aktif[1]}**")
            c.execute("SELECT nama_penanya, pertanyaan, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 1 ORDER BY tanggal", (aktif[0],))
            data = c.fetchall()
            if not data:
                st.info("Belum ada pertanyaan yang di-approve.")
            else:
                for i, (n, q, t) in enumerate(data, 1):
                    st.markdown(f"**{i}. {n}** — _{t}_")
                    st.write(q)
                    st.divider()

    else:  # Operator
        st.header("Panel Operator")
        pwd = st.sidebar.text_input("Password Operator", type="password")
        if pwd != PASS_OPERATOR:
            st.error("Password salah!")
            st.stop()

        tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Code TETAP 1 SELAMANYA"])

        with tab1:
            st.subheader("Buat Kajian Baru")
            nama_kajian = st.text_input("Nama kajian")
            if st.button("Buat Kajian") and nama_kajian:
                c.execute("INSERT INTO kajian (nama, tanggal_dibuat) VALUES (?, ?)",
                          (nama_kajian, datetime.now().strftime("%d/%m/%Y %H:%M")))
                conn.commit()
                st.success("Kajian dibuat!")
                st.rerun()

            st.subheader("Pilih Kajian Aktif")
            c.execute("SELECT id, nama, aktif FROM kajian ORDER BY id DESC")
            for k in c.fetchall():
                col1, col2 = st.columns([5,1])
                status = "AKTIF" if k[2] else "tidak aktif"
                col1.write(f"**{k[1]}** — {status}")
                if col2.button("Aktifkan", key=k[0]):
                    c.execute("UPDATE kajian SET aktif = 0")
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (k[0],))
                    conn.commit()
                    st.rerun()

        with tab2:
            c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
            aktif = c.fetchone()
            if aktif:
                st.write(f"Moderasi untuk: **{aktif[1]}**")
                c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
                for q in c.fetchall():
                    status = "Approved" if q[4] else "Menunggu"
                    with st.expander(f"{q[1]} — {q[3]} — {status}"):
                        st.write(q[2])
                        if q[4] == 0:
                            c1, c2 = st.columns(2)
                            if c1.button("Approve", key=f"a{q[0]}"):
                                c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q[0],))
                                conn.commit()
                                st.rerun()
                            if c2.button("Hapus", key=f"d{q[0]}"):
                                c.execute("DELETE FROM pertanyaan WHERE id = ?", (q[0],))
                                conn.commit()
                                st.rerun()
            else:
                st.info("Belum ada kajian aktif.")

        # TAB QR CODE TETAP 1 SELAMANYA
        with tab3:
            st.success("QR CODE INI HANYA 1 & TIDAK PERNAH GANTI")
            st.write("Cetak sekali → pakai selamanya untuk semua kajian!")
            
            # GANTI DENGAN LINK STREAMLIT KAMU NANTI
            LINK_KAMU = "https://tanya-ustadz-kamu.streamlit.app"  
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={LINK_KAMU}?penanya=yes"
            
            st.image(qr_url, width=350)
            st.code(f"{LINK_KAMU}?penanya=yes")
            st.markdown("**Scan QR ini = langsung masuk Penanya (tanpa sidebar!)**")
