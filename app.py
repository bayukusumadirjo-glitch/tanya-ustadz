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
PASS_OPERATOR = "operator123"
PASS_USTADZ = "ustadz123"

# === DETEKSI QR: Jika ?penanya=yes → langsung Penanya ===
if st.query_params.get("penanya") == "yes":
    is_penanya = True
else:
    is_penanya = False

# ===================================
# MODE PENANYA (dari QR)
# ===================================
if is_penanya:
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("🙋 Tanya Ustadz")
    st.info("Scan QR kode kajian → ajukan pertanyaan Anda (nama wajib).")

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()
    if not aktif:
        st.warning("❌ Belum ada kajian aktif. Hubungi operator.")
        st.stop()

    st.success(f"📌 Kajian: **{aktif[1]}**")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda", placeholder="Ahmad S. / Ibu Fatimah")
        pertanyaan = st.text_area("Pertanyaan Anda", height=150, placeholder="Tuliskan dengan sopan...")
        submitted = st.form_submit_button("Kirim Pertanyaan")

        if submitted:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama & pertanyaan wajib!")
            else:
                tanggal = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, pertanyaan, tanggal, approved) VALUES (?, ?, ?, ?, 0)",
                          (aktif[0], nama.strip(), pertanyaan.strip(), tanggal))
                conn.commit()
                st.success("✅ Terima kasih! Tunggu moderasi.")
                st.balloons()
    st.stop()

# ===================================
# PANEL USTADZ & OPERATOR
# ===================================
st.set_page_config(page_title="Panel", layout="wide")
st.title("👳‍♂️ Panel Ustadz & Operator")

role = st.sidebar.selectbox("Pilih Role", ["Ustadz", "Operator"])

if role == "Ustadz":
    st.header("Dashboard Ustadz")
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd != PASS_USTADZ:
        st.error("Password salah!")
        st.stop()

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()
    if not aktif:
        st.info("Tidak ada kajian aktif.")
    else:
        st.success(f"Kajian: **{aktif[1]}**")
        c.execute("SELECT nama_penanya, pertanyaan, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 1 ORDER BY tanggal", (aktif[0],))
        data = c.fetchall()
        if not data:
            st.info("Belum ada pertanyaan approved.")
        else:
            for i, (n, q, t) in enumerate(data, 1):
                st.markdown(f"**{i}. {n}** — _{t}_")
                st.write(q)
                st.divider()

else:  # Operator
    st.header("Dashboard Operator")
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd != PASS_OPERATOR:
        st.error("Password salah!")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Code Tetap"])

    with tab1:
        st.subheader("Buat Kajian Baru")
        nama = st.text_input("Nama kajian")
        if st.button("Buat") and nama:
            c.execute("INSERT INTO kajian (nama, tanggal_dibuat, aktif) VALUES (?, ?, 0)", (nama, datetime.now().strftime("%d-%m-%Y %H:%M")))
            conn.commit()
            st.success("Dibuat!")
            st.rerun()

        st.subheader("Aktifkan Kajian")
        c.execute("SELECT id, nama, aktif FROM kajian ORDER BY id DESC")
        for k in c.fetchall():
            col1, col2 = st.columns([4,1])
            status = "🟢 Aktif" if k[2] else "⚪"
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
            st.write(f"Moderasi: **{aktif[1]}**")
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
            for q in c.fetchall():
                status = "✅ Approved" if q[4] else "⏳ Menunggu"
                with st.expander(f"{q[1]} — {q[3]} — {status}"):
                    st.write(q[2])
                    if q[4] == 0:
                        col1, col2 = st.columns(2)
                        if col1.button("Approve", key=f"a{q[0]}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q[0],))
                            conn.commit()
                            st.rerun()
                        if col2.button("Hapus", key=f"d{q[0]}"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (q[0],))
                            conn.commit()
                            st.rerun()
        else:
            st.info("Belum ada kajian aktif.")

    with tab3:
        st.success("QR Code Tetap 1 Selamanya!")
        # GANTI INI DENGAN IP/URL KAMU NANTI
        url_base = "https://tanya-ustadz-abc.streamlit.app"  # Lokal dulu
        qr_data = f"{url_base}?penanya=yes"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={qr_data}"
        st.image(qr_url)
        st.code(qr_data)
        st.info("Scan QR ini → langsung ke Penanya. Setelah deploy, ganti url_base ke link Streamlit kamu.")

