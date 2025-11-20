import streamlit as st
import sqlite3
from datetime import datetime

# === SETUP DATABASE ===
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

# === PASSWORD (ganti sesuai keinginan) ===
PASS_OPERATOR = "operator123"
PASS_USTADZ = "ustadz123"

# === APLIKASI ===
st.set_page_config(page_title="Q&A Kajian Ustadz", layout="centered")
st.title("📖 Aplikasi Q&A Kajian Ustadz")

# Sidebar untuk pilih role
role = st.sidebar.selectbox("Pilih Role Anda", ["Penanya", "Ustadz", "Operator"])

# ===================================
# 1. ROLE PENANYA (scan QR dulu → langsung ke halaman ini)
# ===================================
if role == "Penanya":
    st.header("Ajukan Pertanyaan Anda")
    st.info("Anda masuk melalui scan QR kode kajian. Pertanyaan Anda akan dimoderasi oleh operator sebelum ditampilkan kepada Ustadz.")

    # Ambil kajian yang aktif (hanya boleh ada 1 yang aktif)
    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    kajian_aktif = c.fetchone()

    if not kajian_aktif:
        st.warning("❌ Saat ini belum ada kajian yang aktif. Silakan tunggu operator mengaktifkan kajian.")
        st.stop()

    kajian_id, nama_kajian = kajian_aktif

    st.success(f"📌 Kajian aktif: **{nama_kajian}**")

    with st.form("form_pertanyaan"):
        nama = st.text_input("Nama Anda (boleh nama panggilan)", placeholder="Misal: Ahmad S. / Ibu Fatimah")
        pertanyaan = st.text_area("Pertanyaan Anda", placeholder="Tuliskan pertanyaan Anda dengan sopan...", height=150)

        submitted = st.form_submit_button("Kirim Pertanyaan")

        if submitted:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                tanggal = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, pertanyaan, tanggal, approved) VALUES (?, ?, ?, ?, 0)",
                          (kajian_id, nama.strip(), pertanyaan.strip(), tanggal))
                conn.commit()
                st.success("✅ Pertanyaan berhasil dikirim! Tunggu moderasi operator.")
                st.balloons()

# ===================================
# 2. ROLE USTADZ
# ===================================
elif role == "Ustadz":
    st.header("👳‍♂️ Dashboard Ustadz")

    password = st.sidebar.text_input("Password Ustadz", type="password")
    if password != PASS_USTADZ:
        st.error("Password salah!")
        st.stop()

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    kajian_aktif = c.fetchone()

    if not kajian_aktif:
        st.info("Tidak ada kajian aktif saat ini.")
    else:
        kajian_id, nama_kajian = kajian_aktif
        st.success(f"Kajian aktif: **{nama_kajian}**")

        c.execute("""SELECT nama_penanya, pertanyaan, tanggal 
                     FROM pertanyaan 
                     WHERE kajian_id = ? AND approved = 1 
                     ORDER BY tanggal ASC""", (kajian_id,))
        pertanyaan_approved = c.fetchall()

        if not pertanyaan_approved:
            st.info("Belum ada pertanyaan yang di-approve.")
        else:
            for i, (nama, isi, tgl) in enumerate(pertanyaan_approved, 1):
                with st.container():
                    st.markdown(f"**{i}. {nama}** — _{tgl}_")
                    st.markdown(f"> {isi}")
                    st.divider()

# ===================================
# 3. ROLE OPERATOR
# ===================================
else:  # Operator
    st.header("⚙️ Dashboard Operator")

    password = st.sidebar.text_input("Password Operator", type="password")
    if password != PASS_OPERATOR:
        st.error("Password salah!")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Buat & Kelola Kajian", "Moderasi Pertanyaan", "QR Code Kajian Aktif"])

    # Tab 1: Buat & Kelola Kajian
    with tab1:
        st.subheader("Buat Kajian Baru")
        nama_baru = st.text_input("Nama kajian baru", placeholder="Misal: Kajian Kitab Riyadhus Shalihin - 20 Nov 2025")
        if st.button("Buat Kajian Baru"):
            if nama_baru:
                tanggal = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO kajian (nama, tanggal_dibuat, aktif) VALUES (?, ?, 0)", (nama_baru, tanggal))
                conn.commit()
                st.success("Kajian berhasil dibuat!")
                st.rerun()
            else:
                st.error("Nama kajian wajib diisi")

        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, tanggal_dibuat, aktif FROM kajian ORDER BY id DESC")
        daftar_kajian = c.fetchall()

        for kj in daftar_kajian:
            col1, col2 = st.columns([4,1])
            status = "🟢 Aktif" if kj[3] else "⚪ Tidak Aktif"
            col1.write(f"**{kj[1]}**  \n_{kj[2]}_  \n{status}")
            if col2.button("Jadikan Aktif", key=f"aktif_{kj[0]}"):
                c.execute("UPDATE kajian SET aktif = 0")  # matikan semua dulu
                c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (kj[0],))
                conn.commit()
                st.success(f"Kajian **{kj[1]}** sekarang aktif!")
                st.rerun()

    # Tab 2: Moderasi Pertanyaan
    with tab2:
        c.execute("SELECT id, nama FROM kajian ORDER BY id DESC")
        semua_kajian = c.fetchall()
        pilihan_kajian = st.selectbox("Pilih kajian untuk dimoderasi", [f"{k[1]} (ID: {k[0]})" for k in semua_kajian])

        if pilihan_kajian:
            kj_id = int(pilihan_kajian.split("ID: ")[1][:-1])
            c.execute("""SELECT id, nama_penanya, pertanyaan, tanggal, approved 
                         FROM pertanyaan 
                         WHERE kajian_id = ? 
                         ORDER BY tanggal DESC""", (kj_id,))
            daftar_pertanyaan = c.fetchall()

            if not daftar_pertanyaan:
                st.info("Belum ada pertanyaan untuk kajian ini.")
            else:
                for p in daftar_pertanyaan:
                    pid, nama, isi, tgl, appr = p
                    status = "✅ Approved" if appr else "⏳ Menunggu"
                    with st.expander(f"{nama} — {tgl} — {status}"):
                        st.write(isi)
                        col1, col2 = st.columns(2)
                        if appr == 0:
                            if col1.button("Approve", key=f"app_{pid}"):
                                c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (pid,))
                                conn.commit()
                                st.success("Di-approve!")
                                st.rerun()
                            if col2.button("Tolak/Hapus", key=f"del_{pid}"):
                                c.execute("DELETE FROM pertanyaan WHERE id = ?", (pid,))
                                conn.commit()
                                st.error("Dihapus!")
                                st.rerun()

    # Tab 3: QR Code Kajian Aktif (untuk dicetak & dipasang di masjid)
    with tab3:
        c.execute("SELECT nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if aktif:
            url_penanya = st.text_input("URL aplikasi Anda (wajib diisi untuk QR)", 
                                        value="https://nama-app-anda.streamlit.app")  # ganti dengan link Streamlit Anda
            if url_penanya:
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url_penanya}"
                st.image(qr_url, caption=f"QR Code untuk kajian: {aktif[0]}")
                st.code(url_penanya)
                st.success("Cetak QR ini dan tempel di lokasi kajian agar jamaah bisa scan & bertanya!")
        else:
            st.info("Belum ada kajian yang aktif → QR code akan muncul otomatis setelah ada kajian aktif.")

