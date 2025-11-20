import streamlit as st
import sqlite3
from datetime import datetime

# === DATABASE ===
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

# Tabel kajian (versi lama)
c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT,
                aktif INTEGER DEFAULT 0
             )''')

# Tambah kolom baru jika belum ada (biar tidak error)
try:
    c.execute("ALTER TABLE kajian ADD COLUMN nama_ustadz TEXT")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE kajian ADD COLUMN tanggal_kajian TEXT")
except sqlite3.OperationalError:
    pass

# Tabel pertanyaan
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

    c.execute("SELECT nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()
    if not aktif:
        st.error("Belum ada kajian aktif. Silakan hubungi panitia.")
        st.stop()

    nama_kajian, ustadz, tgl_kajian = aktif
    st.success(f"**{nama_kajian}**")
    st.info(f"Ustadz: **{ustadz or 'Ustadz'}** • Tanggal: **{tgl_kajian or 'Belum ditentukan'}**")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda (wajib)", placeholder="Ahmad / Ummu Aisyah")
        pertanyaan = st.text_area("Pertanyaan Anda", height=150, placeholder="Tuliskan dengan jelas dan sopan...")
        kirim = st.form_submit_button("Kirim Pertanyaan", use_container_width=True, type="primary")

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                tgl = datetime.now().strftime("%d/%m/%Y %H:%M")
                c.execute("SELECT id FROM kajian WHERE aktif = 1")
                kajian_id = c.fetchone()[0]
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, pertanyaan, tanggal, approved) VALUES (?, ?, ?, ?, 0)",
                          (kajian_id, nama.strip(), pertanyaan.strip(), tgl))
                conn.commit()
                st.success(f"**Jawaban Anda sudah ditampung. Terima kasih, {nama.split()[0]}!**")
                st.info("Pertanyaan akan dimoderasi sebelum ditampilkan kepada Ustadz.")
    st.stop()

# ===================================
# PANEL OPERATOR & USTADZ
# ===================================
st.set_page_config(page_title="Panel Kajian", layout="wide")
st.title("Panel Operator & Ustadz")

# Info kajian aktif
c.execute("SELECT nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
aktif_info = c.fetchone()
if aktif_info:
    col1, col2 = st.columns([3, 1])
    col1.success(f"KAJIAN AKTIF: {aktif_info[0]}")
    col2.info(f"Ustadz: {aktif_info[1] or '-'} • {aktif_info[2] or ''}")

# Pilih Role
role = st.sidebar.selectbox("Pilih Role", ["Operator", "Ustadz"])

# ==================== LOGIN DENGAN TOMBOL MASUK ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.header(f"Login sebagai {role}")
    password = st.sidebar.text_input("Password", type="password", key=f"pwd_{role}")
    login_btn = st.sidebar.button("Masuk", type="primary", use_container_width=True)

    if login_btn:
        if role == "Operator" and password == PASS_OPERATOR:
            st.session_state.logged_in = True
            st.session_state.role = "Operator"
            st.success("Login Operator berhasil!")
            st.rerun()
        elif role == "Ustadz" and password == PASS_USTADZ:
            st.session_state.logged_in = True
            st.session_state.role = "Ustadz"
            st.success("Login Ustadz berhasil!")
            st.rerun()
        else:
            st.sidebar.error("Password salah!")
    st.stop()

# ==================== JIKA SUDAH LOGIN ====================
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")

    if not aktif_info:
        st.info("Belum ada kajian aktif.")
    else:
        st.success(f"**{aktif_info[0]}**")
        st.write(f"Ustadz: **{aktif_info[1] or 'Anda'}** • Tanggal: **{aktif_info[2] or '-'}**")
        c.execute("SELECT id FROM kajian WHERE aktif = 1")
        kajian_id = c.fetchone()[0]
        c.execute("SELECT nama_penanya, pertanyaan, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 1 ORDER BY tanggal ASC", (kajian_id,))
        data = c.fetchall()
        if not data:
            st.info("Belum ada pertanyaan yang di-approve.")
        else:
            for i, (n, q, t) in enumerate(data, 1):
                st.markdown(f"**{i}. {n}** — _{t}_")
                st.write(q)
                st.divider()

else:  # OPERATOR
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Code Tetap"])

    with tab1:
        st.subheader("Buat Kajian Baru")
        nama_kajian = st.text_input("Nama Kajian")
        nama_ustadz = st.text_input("Nama Ustadz")
        tgl_kajian = st.date_input("Tanggal Kajian", datetime.now())
        if st.button("Buat Kajian Baru", type="primary"):
            if nama_kajian:
                c.execute("""INSERT INTO kajian (nama, nama_ustadz, tanggal_kajian, tanggal_dibuat)
                             VALUES (?, ?, ?, ?)""",
                          (nama_kajian, nama_ustadz or "-", str(tgl_kajian), datetime.now().strftime("%d/%m/%Y %H:%M")))
                conn.commit()
                st.success("Kajian berhasil dibuat!")
                st.rerun()

        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian, aktif FROM kajian ORDER BY id DESC")
        for row in c.fetchall():
            idk, nama, ust, tgl, stat = row
            c1, c2, c3, c4, c5 = st.columns([4, 2, 1.5, 1.5, 1.5])
            c1.write(f"**{nama}**")
            c2.write(f"Ustadz: *{ust or '-'}* • {tgl or '-'}")
            if stat:
                c3.success("AKTIF")
                if c4.button("Nonaktifkan", key=f"off_{idk}", type="secondary"):
                    c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (idk,))
                    conn.commit()
                    st.rerun()
            else:
                if c3.button("Aktifkan", key=f"on_{idk}", type="primary"):
                    c.execute("UPDATE kajian SET aktif = 0")
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (idk,))
                    conn.commit()
                    st.rerun()
            if c5.button("Hapus", key=f"del_{idk}"):
                c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (idk,))
                c.execute("DELETE FROM kajian WHERE id = ?", (idk,))
                conn.commit()
                st.success("Kajian dihapus!")
                st.rerun()

    with tab2:
        if aktif_info:
            st.write(f"**Moderasi — {aktif_info[0]}**")
            st.caption(f"Ustadz: {aktif_info[1] or '-'} • {aktif_info[2] or '-'}")
            c.execute("SELECT id FROM kajian WHERE aktif = 1")
            kajian_id = c.fetchone()[0]
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (kajian_id,))
            for q in c.fetchall():
                qid, nama, isi, tgl, appr = q
                with st.expander(f"{nama} — {tgl} — {'Approved' if appr else 'Menunggu'}"):
                    st.write(isi)
                    ca, cb = st.columns(2)
                    if appr == 0:
                        if ca.button("Approve", key=f"a{qid}", type="primary"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (qid,))
                            conn.commit()
                            st.rerun()
                    if cb.button("Hapus", key=f"d{qid}"):
                        c.execute("DELETE FROM pertanyaan WHERE id = ?", (qid,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Belum ada kajian aktif.")

    with tab3:
        st.success("QR CODE TETAP 1 SELAMANYA")
        st.write("Cetak sekali → pakai selamanya!")

        LINK_KAMU = "https://tanya-ustadz-dirj.streamlit.app"  # GANTI SETELAH DEPLOY
        qr_link = f"{LINK_KAMU}?penanya=yes"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={qr_link}"

        st.image(qr_url, width=350)
        st.code(qr_link)
        st.markdown("**Scan QR ini → langsung masuk mode Penanya**")

# Tombol Logout
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    del st.session_state.role
    st.rerun()
