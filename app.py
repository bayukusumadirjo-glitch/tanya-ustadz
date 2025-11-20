import streamlit as st
import sqlite3
from datetime import datetime

# === DATABASE ===
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

# Tabel kajian (sudah ada kolom nama_ustadz & tanggal_kajian)
c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                nama_ustadz TEXT,
                tanggal_kajian TEXT,
                tanggal_dibuat TEXT,
                aktif INTEGER DEFAULT 0
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS pertanyaan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kajian_id INTEGER,
                nama_penanya
