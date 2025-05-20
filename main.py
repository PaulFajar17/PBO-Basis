import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from login import login_window

# Warna & gaya
BG_COLOR = "#f0f8ff"
BTN_COLOR = "#4a90e2"
BTN_HOVER = "#357ABD"
FONT = ("Segoe UI", 10)

def buat_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ManajemenKegiatanDTEI"
        )
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Role (
        Role_ID INT PRIMARY KEY,
        Nama_Role VARCHAR(100)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pengguna (
        ID_Pengguna INT PRIMARY KEY,
        Nama VARCHAR(100),
        Role_ID INT,
        NIM_NIP VARCHAR(50),
        Username VARCHAR(50),
        Password VARCHAR(50),
        FOREIGN KEY (Role_ID) REFERENCES Role(Role_ID)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Kegiatan (
        ID_Kegiatan VARCHAR(10) PRIMARY KEY,
        Nama_Kegiatan VARCHAR(100),
        Tanggal VARCHAR(20),
        Tempat VARCHAR(100),
        Jenis_Kegiatan VARCHAR(50),
        ID_Penanggung_Jawab INT,
        FOREIGN KEY (ID_Penanggung_Jawab) REFERENCES Pengguna(ID_Pengguna)
    )""")

    # Data Role
    cursor.execute("SELECT COUNT(*) FROM Role")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO Role (Role_ID, Nama_Role) VALUES (%s, %s)",
                           [(1, 'Mahasiswa'), (2, 'Dosen'), (3, 'Staff')])

    # Data Pengguna
    cursor.execute("SELECT COUNT(*) FROM Pengguna")
    if cursor.fetchone()[0] == 0:
        pengguna = [
            (101, "Paul Fajar", 1, "2025", "Paul_mhs", "PAULPASS"),
            (102, "Dr. Zhafier", 2, "705", "Zhafier_dsn", "ZHAFPASS"),
            (103, "Vijaypal Singh", 3, "2252", "Jay_staff", "JAYPASS"),
        ]
        cursor.executemany("INSERT INTO Pengguna VALUES (%s, %s, %s, %s, %s, %s)", pengguna)

    # Data Kegiatan Awal
    cursor.execute("SELECT COUNT(*) FROM Kegiatan")
    if cursor.fetchone()[0] == 0:
        kegiatan_awal = [
            ("K001", "Seminar AI", "10-05-2025", "Aula FT", "Seminar", 101),
            ("K002", "Praktikum IoT", "15-05-2025", "Lab Jaringan Komputer", "Praktikum", 102),
            ("K003", "Rapat Dosen Bulanan", "20-05-2025", "Ruang Dosen", "Rapat Dosen", 103),
        ]
        cursor.executemany("""
            INSERT INTO Kegiatan (ID_Kegiatan, Nama_Kegiatan, Tanggal, Tempat, Jenis_Kegiatan, ID_Penanggung_Jawab)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, kegiatan_awal)

    conn.commit()
    conn.close()

class KegiatanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🗂️ Aplikasi Manajemen Kegiatan")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("950x600")

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", font=("Segoe UI", 9))

        self.build_ui()

    def build_ui(self):
        input_frame = tk.LabelFrame(self.root, text="Form Tambah Kegiatan", bg=BG_COLOR, font=FONT)
        input_frame.pack(fill='x', padx=20, pady=10)

        labels = ["ID Kegiatan", "Nama Kegiatan", "Tanggal (DD-MM-YYYY)", "Tempat", "Jenis Kegiatan", "Penanggung Jawab"]
        
        self.entries = {}

        for i, label in enumerate(labels[:-1]):
            tk.Label(input_frame, text=label, bg=BG_COLOR, font=FONT).grid(row=i, column=0, sticky="w", pady=3)
            ent = tk.Entry(input_frame, font=FONT, width=30)
            ent.grid(row=i, column=1, padx=10, pady=3, sticky="w")
            self.entries[label] = ent

        tk.Label(input_frame, text=labels[-1], bg=BG_COLOR, font=FONT).grid(row=5, column=0, sticky="w", pady=3)
        self.combo_pj = ttk.Combobox(input_frame, state="readonly", width=28)
        self.combo_pj.grid(row=5, column=1, padx=10, pady=3, sticky="w")

        # Tombol
        self.btn_simpan = self.styled_button(input_frame, "➕ Tambah", self.tambah_kegiatan)
        self.btn_simpan.grid(row=6, column=0, padx=10, pady=10)

        self.btn_hapus = self.styled_button(input_frame, "❌ Hapus", self.hapus_kegiatan)
        self.btn_hapus.grid(row=6, column=1, pady=10, sticky="w")

        self.btn_refresh = self.styled_button(input_frame, "🔄 Tampilkan Semua", self.tampilkan_kegiatan)
        self.btn_refresh.grid(row=6, column=2, padx=10)

        # Frame Tabel
        tabel_frame = tk.LabelFrame(self.root, text="📋 Daftar Kegiatan", bg=BG_COLOR, font=FONT)
        tabel_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(tabel_frame, columns=("id", "nama", "tanggal", "tempat", "jenis", "pj"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, anchor="center", width=140)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tabel_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load_pengguna()
        self.tampilkan_kegiatan()

    def styled_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, font=FONT, bg=BTN_COLOR, fg="white", relief="flat", command=command)
        btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=BTN_COLOR))
        return btn

    def load_pengguna(self):
        conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ManajemenKegiatanDTEI"
        )
        cursor = conn.cursor()
        cursor = conn.cursor()
        cursor.execute("SELECT ID_Pengguna, Nama FROM Pengguna")
        self.pengguna_data = cursor.fetchall()
        self.combo_pj["values"] = [f"{nama} (ID {idp})" for idp, nama in self.pengguna_data]
        conn.close()

    def tambah_kegiatan(self):
        try:
            id_keg = self.entries["ID Kegiatan"].get()
            nama = self.entries["Nama Kegiatan"].get()
            # Ambil tanggal dari Calendar widget
            tanggal = self.cal_tanggal.get_date()
            # Ambil tanggal dari widget kalender (DateEntry)
            tanggal = self.cal_tanggal.get_date().strftime("%d-%m-%Y")
            tempat = self.entries["Tempat"].get()
            jenis = self.entries["Jenis Kegiatan"].get()
            pj_index = self.combo_pj.current()

            if not all([id_keg, nama, tanggal, tempat, jenis]):
                raise ValueError("Semua kolom harus diisi.")
            if pj_index == -1:
                raise ValueError("Pilih penanggung jawab.")

            # Validasi tanggal dari DateEntry
            try:
                tanggal = self.cal_tanggal.get_date().strftime("%d-%m-%Y")
            except Exception:
                raise ValueError("Pilih tanggal kegiatan.")

            id_pj = self.pengguna_data[pj_index][0]

            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="ManajemenKegiatanDTEI"
                )
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Kegiatan (ID_Kegiatan, Nama_Kegiatan, Tanggal, Tempat, Jenis_Kegiatan, ID_Penanggung_Jawab)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_keg, nama, tanggal, tempat, jenis, id_pj))
            conn.commit()
            conn.close()

            messagebox.showinfo("✅ Sukses", "Kegiatan berhasil ditambahkan.")
            self.tampilkan_kegiatan()
        except mysql.connector.IntegrityError:
            messagebox.showerror("❌ Error", "ID kegiatan sudah digunakan.")
        except ValueError as e:
            messagebox.showwarning("⚠️ Peringatan", str(e))

    def hapus_kegiatan(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Peringatan", "Pilih kegiatan yang ingin dihapus.")
            return
        id_keg = self.tree.item(selected, "values")[0]
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ManajemenKegiatanDTEI"
            )
        cursor = conn.cursor()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Kegiatan WHERE ID_Kegiatan = %s", (id_keg,))
        conn.commit()
        conn.close()
        messagebox.showinfo("🗑️ Sukses", "Kegiatan berhasil dihapus.")
        self.tampilkan_kegiatan()
    def tampilkan_kegiatan(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ManajemenKegiatanDTEI"
            )
        cursor = conn.cursor()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT K.ID_Kegiatan, K.Nama_Kegiatan, K.Tanggal, K.Tempat, K.Jenis_Kegiatan, P.Nama
            FROM Kegiatan K
            JOIN Pengguna P ON K.ID_Penanggung_Jawab = P.ID_Pengguna
        """)
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)
        conn.close()

if __name__ == "__main__":
    buat_database()
    login_window()  # Panggil fungsi login sebelum membuka aplikasi utama
    root = tk.Tk()
    app = KegiatanApp(root)
    root.mainloop()