import streamlit as st
import sqlite3
from datetime import datetime

# === DATABASE ===
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

# Tabel kajian
c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT,
                aktif INTEGER DEFAULT 0
             )''')

# Tabel pertanyaan — INI YANG DIPERBAIKI (NOT NOT NULL → NOT NULL)
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

# === PASSWORD (ganti kalau mau) ===
PASS_OPERATOR = "operator123"
PASS_USTADZ   = "ustadz123"

# === DETEKSI QR ===
if st.query_params.get("penanya") == "yes":
    is_penanya = True
else:
    is_penanya = False

# ===================================
# MODE PENANYA (dari QR)
# ===================================
if is_penanya:
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")
    st.caption("Silakan ajukan pertanyaan Anda")

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()
    if not aktif:
        st.error("Belum ada kajian aktif. Silakan hubungi panitia.")
        st.stop()

    st.success(f"Kajian aktif: **{aktif[1]}**")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda (wajib)", placeholder="Ahmad / Ummu Aisyah")
        pertanyaan = st.text_area("Pertanyaan Anda", height=150, placeholder="Tuliskan dengan jelas dan sopan...")

        kirim = st.form_submit_button("Kirim Pertanyaan", use_container_width=True)

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                tgl = datetime.now().strftime("%d/%m/%Y %H:%M")
                c.execute("""INSERT INTO pertanyaan 
                             (kajian_id, nama_penanya, pertanyaan, tanggal, approved) 
                             VALUES (?, ?, ?, ?, 0)""",
                          (aktif[0], nama.strip(), pertanyaan.strip(), tgl))
                conn.commit()
                st.success(f"**Jawaban Anda sudah ditampung. Terima kasih, {nama.split()[0]}!**")
                st.info("Pertanyaan akan dimoderasi sebelum ditampilkan kepada Ustadz.")
    st.stop()

# ===================================
# PANEL OPERATOR & USTADZ
# ===================================
st.set_page_config(page_title="Panel Operator & Ustadz", layout="wide")
st.title("Panel Operator & Ustadz")

role = st.sidebar.selectbox("Pilih Role", ["Operator", "Ustadz"])

# ==================== USTADZ ====================
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
        c.execute("""SELECT nama_penanya, pertanyaan, tanggal 
                     FROM pertanyaan WHERE kajian_id = ? AND approved = 1 
                     ORDER BY tanggal ASC""", (aktif[0],))
        data = c.fetchall()
        if not data:
            st.info("Belum ada pertanyaan yang di-approve.")
        else:
            for i, (n, q, t) in enumerate(data, 1):
                st.markdown(f"**{i}. {n}** — _{t}_")
                st.write(q)
                st.divider()

# ==================== OPERATOR ====================
else:
    st.header("Dashboard Operator")
    pwd = st.sidebar.text_input("Password Operator", type="password")
    if pwd != PASS_OPERATOR:
        st.error("Password salah!")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Code"])

    # TAB 1 — Kelola Kajian (bisa aktif/nonaktif + hapus)
    with tab1:
        st.subheader("Buat Kajian Baru")
        nama_baru = st.text_input("Nama kajian")
        if st.button("Buat Kajian") and nama_baru:
            c.execute("INSERT INTO kajian (nama, tanggal_dibuat) VALUES (?, ?)",
                      (nama_baru, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            st.success("Kajian dibuat!")
            st.rerun()

        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, aktif FROM kajian ORDER BY id DESC")
        for row in c.fetchall():
            idk, namak, stat = row
            c1, c2, c3, c4 = st.columns([4,1.5,1.5,2])
            c1.write(f"**{namak}**")
            c2.write("AKTIF" if stat else "Nonaktif")
            if stat:
                if c3.button("Nonaktifkan", key=f"off_{idk}"):
                    c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (idk,))
                    conn.commit()
                    st.rerun()
            else:
                if c3.button("Aktifkan", key=f"on_{idk}"):
                    c.execute("UPDATE kajian SET aktif = 0")
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (idk,))
                    conn.commit()
                    st.rerun()
            if c4.button("Hapus Kajian", key=f"delk_{idk}"):
                c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (idk,))
                c.execute("DELETE FROM kajian WHERE id = ?", (idk,))
                conn.commit()
                st.success("Kajian dan semua pertanyaan dihapus!")
                st.rerun()

    # TAB 2 — Moderasi (bisa hapus meski sudah approve)
    with tab2:
        c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if aktif:
            st.write(f"**Moderasi — {aktif[1]}**")
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
            for q in c.fetchall():
                qid, nama, isi, tgl, appr = q
                with st.expander(f"{nama} — {tgl} — {'Approved' if appr else 'Menunggu'}"):
                    st.write(isi)
                    ca, cb = st.columns(2)
                    if appr == 0:
                        if ca.button("Approve", key=f"a{qid}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (qid,))
                            conn.commit()
                            st.rerun()
                    if cb.button("Hapus", key=f"d{qid}"):
                        c.execute("DELETE FROM pertanyaan WHERE id = ?", (qid,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Belum ada kajian aktif.")

    # TAB 3 — QR Code Tetap 1 Selamanya
    with tab3:
        st.success("QR CODE TETAP 1 SELAMANYA")
        LINK_KAMU = "https://tanya-ustadz-dirj.streamlit.app"  # GANTI SETELAH DEPLOY
        qr_link = f"{LINK_KAMU}?penanya=yes"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={qr}", width=350)
        st.code(qr)
        st.info("Scan = langsung Penanya")
