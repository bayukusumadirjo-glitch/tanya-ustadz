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
                nama_penanya TEXT NOT NOT NULL,
                pertanyaan TEXT NOT NULL,
                tanggal TEXT,
                approved INTEGER DEFAULT 0,
                FOREIGN KEY (kajian_id) REFERENCES kajian (id)
             )''')
conn.commit()

# === PASSWORD (ganti kalau mau) ===
PASS_OPERATOR = "operator123"
PASS_USTADZ   = "ustadz123"

# === DETEKSI: dari QR atau bukan ===
if st.query_params.get("penanya") == "yes":
    is_penanya = True
else:
    is_penanya = False

# ===================================
# MODE PENANYA (langsung dari QR)
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
# PANEL USTADZ & OPERATOR
# ===================================
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

else:  # ==================== OPERATOR ====================
    st.header("Dashboard Operator")
    pwd = st.sidebar.text_input("Password Operator", type="password")
    if pwd != PASS_OPERATOR:
        st.error("Password salah!")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi Pertanyaan", "QR Code Tetap"])

    # ==================== TAB 1: Kelola Kajian ====================
    with tab1:
        st.subheader("Buat Kajian Baru")
        nama_baru = st.text_input("Nama kajian baru", placeholder="Misal: Kajian Bulanan November 2025")
        if st.button("Buat Kajian Baru") and nama_baru:
            tgl = datetime.now().strftime("%d/%m/%Y %H:%M")
            c.execute("INSERT INTO kajian (nama, tanggal_dibuat, aktif) VALUES (?, ?, 0)", (nama_baru, tgl))
            conn.commit()
            st.success("Kajian berhasil dibuat!")
            st.rerun()

        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, tanggal_dibuat, aktif FROM kajian ORDER BY id DESC")
        daftar = c.fetchall()

        for kj in daftar:
            id_kj, nama_kj, tgl_kj, status = kj
            col1, col2, col3, col4 = st.columns([4, 1.5, 1.5, 1.5])
            col1.write(f"**{nama_kj}**  \n_{tgl_kj}_")
            
            if status == 1:
                col2.success("AKTIF")
            else:
                col2.write("Tidak aktif")

            # Tombol Toggle Aktif/Nonaktif
            if status == 1:
                if col3.button("Nonaktifkan", key=f"off_{id_kj}"):
                    c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (id_kj,))
                    conn.commit()
                    st.rerun()
            else:
                if col3.button("Aktifkan", key=f"on_{id_kj}"):
                    c.execute("UPDATE kajian SET aktif = 0")  # matikan semua dulu
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (id_kj,))
                    conn.commit()
                    st.rerun()

            # Tombol Hapus Kajian
            if col4.button("Hapus Kajian", key=f"delkajian_{id_kj}"):
                if st.session_state.get(f"confirm_{id_kj}") != True:
                    st.session_state[f"confirm_{id_kj}"] = True
                    st.warning(f"Yakin hapus kajian **{nama_kj}** dan semua pertanyaannya?")
                else:
                    c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (id_kj,))
                    c.execute("DELETE FROM kajian WHERE id = ?", (id_kj,))
                    conn.commit()
                    del st.session_state[f"confirm_{id_kj}"]
                    st.success("Kajian dan semua pertanyaan dihapus!")
                    st.rerun()

    # ==================== TAB 2: Moderasi Pertanyaan ====================
    with tab2:
        c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.write(f"**Moderasi — {aktif[1]}**")
            c.execute("""SELECT id, nama_penanya, pertanyaan, tanggal, approved 
                         FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC""", (aktif[0],))
            for q in c.fetchall():
                qid, nama, isi, tgl, appr = q
                status = "Approved" if appr else "Menunggu"
                with st.expander(f"{nama} — {tgl} — {status}"):
                    st.write(isi)
                    col_a, col_b = st.columns(2)
                    if appr == 0:
                        if col_a.button("Approve", key=f"app_{qid}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (qid,))
                            conn.commit()
                            st.rerun()
                    else:
                        col_a.write("Sudah di-approve")

                    # BISA HAPUS MESKIPUN SUDAH DI-APPROVE
                    if col_b.button("Hapus Pertanyaan", key=f"delq_{qid}"):
                        c.execute("DELETE FROM pertanyaan WHERE id = ?", (qid,))
                        conn.commit()
                        st.error("Pertanyaan dihapus!")
                        st.rerun()

    # ==================== TAB 3: QR Code Tetap ====================
    with tab3:
        st.success("QR CODE INI TETAP 1 SELAMANYA")
        st.write("Cetak sekali → pakai untuk semua kajian!")

        # GANTI DENGAN LINK STREAMLIT KAMU NANTI
        LINK_KAMU = "https://tanya-ustadz-dirj.streamlit.app"  # ← ubah setelah deploy
        qr_data = f"{LINK_KAMU}?penanya=yes"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={qr_data}"

        st.image(qr_url, width=350)
        st.code(qr_data)
        st.info("Scan QR ini → langsung masuk mode Penanya (tanpa sidebar)")
