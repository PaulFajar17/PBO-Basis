import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar 
import datetime
from PIL import Image, ImageTk, ImageFilter # Ditambahkan untuk login window

# --- Warna & Gaya Global ---
BG_COLOR = "#f0f8ff"
FONT_STYLE = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
BTN_COLOR = "#4a90e2" # Digunakan untuk styling Calendar
BTN_HOVER = "#357ABD" # Digunakan untuk styling Calendar

# --- Kelas untuk Manajemen Database ---
class DatabaseManager:
    def __init__(self, host, user, password, database_name):
        self.host = host
        self.user = user
        self.password = password
        self.database_name = database_name

    def _get_connection(self):
        """Membuat dan mengembalikan koneksi database."""
        try:
            return mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database_name
            )
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                try: 
                    temp_conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
                    temp_cursor = temp_conn.cursor()
                    temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    temp_conn.commit()
                    temp_cursor.close()
                    temp_conn.close()
                    return mysql.connector.connect(
                        host=self.host, user=self.user, password=self.password, database=self.database_name
                    )
                except mysql.connector.Error as create_err:
                    raise mysql.connector.Error(f"Gagal membuat atau terhubung ke database '{self.database_name}': {create_err}") from create_err
            else:
                raise mysql.connector.Error(f"Koneksi database gagal: {err}") from err

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, is_many=False, is_ddl_multi=False):
        """Mengeksekusi query SQL dan mengelola koneksi."""
        conn = None
        try:
            conn = self._get_connection()
            if is_ddl_multi:
                if isinstance(query, list): 
                    for q_part in query:
                        cursor = conn.cursor()
                        cursor.execute(q_part)
                        cursor.close()
                else: 
                    cursor = conn.cursor()
                    for result in cursor.execute(query, multi=True if ";" in query else False):
                        pass 
                    cursor.close()
            elif is_many and params:
                cursor = conn.cursor()
                cursor.executemany(query, params)
                cursor.close()
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    conn.commit()
                
                if fetch_one:
                    result = cursor.fetchone()
                    cursor.close()
                    return result
                if fetch_all:
                    result = cursor.fetchall()
                    cursor.close()
                    return result
                if cursor.lastrowid and query.strip().upper().startswith("INSERT"): 
                    last_id = cursor.lastrowid
                    cursor.close()
                    return last_id
                rowcount = cursor.rowcount 
                cursor.close()
                return rowcount
            conn.commit() 
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            raise err
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def call_stored_procedure(self, proc_name, args=()):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.callproc(proc_name, args)
            conn.commit()
            rowcount = cursor.rowcount 
            return rowcount 
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            raise err
        finally:
            if conn and conn.is_connected():
                if 'cursor' in locals() and cursor: 
                    cursor.close()
                conn.close()

    def _execute_ddl_block(self, ddl_string):
        try:
            ddl_string = ddl_string.strip()
            self.execute_query(ddl_string) 
        except mysql.connector.Error as e:
            if e.errno == mysql.connector.errorcode.ER_TABLE_EXISTS_ERROR or \
               e.errno == mysql.connector.errorcode.ER_VIEW_EXISTS or \
               e.errno == mysql.connector.errorcode.ER_SP_ALREADY_EXISTS or \
               e.errno == mysql.connector.errorcode.ER_TRG_ALREADY_EXISTS:
                print(f"Info: Objek DDL sudah ada, dilewati. {str(e)[:100]}")
            else:
                print(f"Error saat eksekusi DDL block: {e} \nQuery: {ddl_string[:200]}")
                raise

    def initialize_database(self):
        """Membuat tabel, view, trigger, dan stored procedure."""
        base_tables_ddl = [
            """CREATE TABLE IF NOT EXISTS Role (
                Role_ID INT PRIMARY KEY,
                Nama_Role VARCHAR(100) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
            """CREATE TABLE IF NOT EXISTS Pengguna (
                ID_Pengguna INT PRIMARY KEY,
                Nama VARCHAR(100) NOT NULL,
                Role_ID INT,
                NIM_NIP VARCHAR(50) UNIQUE,
                Username VARCHAR(50) UNIQUE NOT NULL,
                Password VARCHAR(255) NOT NULL,
                FOREIGN KEY (Role_ID) REFERENCES Role(Role_ID) ON DELETE SET NULL ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
            """CREATE TABLE IF NOT EXISTS Kegiatan (
                ID_Kegiatan VARCHAR(10) PRIMARY KEY,
                Nama_Kegiatan VARCHAR(100) NOT NULL,
                Tanggal VARCHAR(20), 
                Tempat VARCHAR(100),
                Jenis_Kegiatan VARCHAR(50),
                ID_Penanggung_Jawab INT,
                FOREIGN KEY (ID_Penanggung_Jawab) REFERENCES Pengguna(ID_Pengguna) ON DELETE SET NULL ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"""
        ]
        for ddl in base_tables_ddl:
            self._execute_ddl_block(ddl)

        log_table_ddl = """
        CREATE TABLE IF NOT EXISTS Log_Perubahan_Kegiatan (
            ID_Log INT AUTO_INCREMENT PRIMARY KEY,
            ID_Kegiatan_Ref VARCHAR(10),
            Aksi VARCHAR(50) NOT NULL,
            Timestamp_Aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            Detail_Lama TEXT,
            Detail_Baru TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"""
        self._execute_ddl_block(log_table_ddl)

        view_ddl = """
        CREATE OR REPLACE VIEW View_Detail_Kegiatan AS
        SELECT
            K.ID_Kegiatan, K.Nama_Kegiatan, K.Tanggal, K.Tempat, K.Jenis_Kegiatan,
            P.Nama AS Nama_Penanggung_Jawab, R.Nama_Role AS Role_Penanggung_Jawab,
            K.ID_Penanggung_Jawab
        FROM Kegiatan K
        LEFT JOIN Pengguna P ON K.ID_Penanggung_Jawab = P.ID_Pengguna
        LEFT JOIN Role R ON P.Role_ID = R.Role_ID
        """
        self._execute_ddl_block(view_ddl)

        trigger_insert_ddl = """
        CREATE TRIGGER IF NOT EXISTS TRG_Kegiatan_After_Insert
        AFTER INSERT ON Kegiatan
        FOR EACH ROW
        BEGIN
            INSERT INTO Log_Perubahan_Kegiatan (ID_Kegiatan_Ref, Aksi, Detail_Baru)
            VALUES (NEW.ID_Kegiatan, 'INSERT',
                    CONCAT('ID: ', NEW.ID_Kegiatan,
                           ', Nama: ', NEW.Nama_Kegiatan,
                           ', Tanggal: ', NEW.Tanggal,
                           ', Tempat: ', NEW.Tempat,
                           ', Jenis: ', NEW.Jenis_Kegiatan,
                           ', PJ_ID: ', IFNULL(NEW.ID_Penanggung_Jawab, 'NULL'))
                   );
        END
        """
        self._execute_ddl_block(trigger_insert_ddl)

        trigger_update_ddl = """
        CREATE TRIGGER IF NOT EXISTS TRG_Kegiatan_After_Update
        AFTER UPDATE ON Kegiatan
        FOR EACH ROW
        BEGIN
            DECLARE detail_lama_str TEXT;
            DECLARE detail_baru_str TEXT;
            SET detail_lama_str = CONCAT('ID: ', OLD.ID_Kegiatan, ', Nama: ', OLD.Nama_Kegiatan, ', Tanggal: ', OLD.Tanggal, ', Tempat: ', OLD.Tempat, ', Jenis: ', OLD.Jenis_Kegiatan, ', PJ_ID: ', IFNULL(OLD.ID_Penanggung_Jawab, 'NULL'));
            SET detail_baru_str = CONCAT('ID: ', NEW.ID_Kegiatan, ', Nama: ', NEW.Nama_Kegiatan, ', Tanggal: ', NEW.Tanggal, ', Tempat: ', NEW.Tempat, ', Jenis: ', NEW.Jenis_Kegiatan, ', PJ_ID: ', IFNULL(NEW.ID_Penanggung_Jawab, 'NULL'));
            IF detail_lama_str <> detail_baru_str THEN
                INSERT INTO Log_Perubahan_Kegiatan (ID_Kegiatan_Ref, Aksi, Detail_Lama, Detail_Baru)
                VALUES (NEW.ID_Kegiatan, 'UPDATE', detail_lama_str, detail_baru_str);
            END IF;
        END
        """
        self._execute_ddl_block(trigger_update_ddl)

        trigger_delete_ddl = """
        CREATE TRIGGER IF NOT EXISTS TRG_Kegiatan_Before_Delete
        BEFORE DELETE ON Kegiatan
        FOR EACH ROW
        BEGIN
            INSERT INTO Log_Perubahan_Kegiatan (ID_Kegiatan_Ref, Aksi, Detail_Lama)
            VALUES (OLD.ID_Kegiatan, 'DELETE',
                    CONCAT('ID: ', OLD.ID_Kegiatan,
                           ', Nama: ', OLD.Nama_Kegiatan,
                           ', Tanggal: ', OLD.Tanggal,
                           ', Tempat: ', OLD.Tempat,
                           ', Jenis: ', OLD.Jenis_Kegiatan,
                           ', PJ_ID: ', IFNULL(OLD.ID_Penanggung_Jawab, 'NULL'))
                   );
        END
        """
        self._execute_ddl_block(trigger_delete_ddl)

        sp_tambah_ddl = """
        CREATE PROCEDURE IF NOT EXISTS SP_TambahKegiatan (
            IN p_ID_Kegiatan VARCHAR(10), IN p_Nama_Kegiatan VARCHAR(100), IN p_Tanggal VARCHAR(20),
            IN p_Tempat VARCHAR(100), IN p_Jenis_Kegiatan VARCHAR(50), IN p_ID_Penanggung_Jawab INT
        )
        BEGIN
            INSERT INTO Kegiatan (ID_Kegiatan, Nama_Kegiatan, Tanggal, Tempat, Jenis_Kegiatan, ID_Penanggung_Jawab)
            VALUES (p_ID_Kegiatan, p_Nama_Kegiatan, p_Tanggal, p_Tempat, p_Jenis_Kegiatan, p_ID_Penanggung_Jawab);
        END
        """
        self._execute_ddl_block(sp_tambah_ddl)

        sp_update_ddl = """
        CREATE PROCEDURE IF NOT EXISTS SP_UpdateKegiatan (
            IN p_ID_Kegiatan_Target VARCHAR(10), IN p_Nama_Kegiatan_Baru VARCHAR(100), IN p_Tanggal_Baru VARCHAR(20),
            IN p_Tempat_Baru VARCHAR(100), IN p_Jenis_Kegiatan_Baru VARCHAR(50), IN p_ID_Penanggung_Jawab_Baru INT
        )
        BEGIN
            UPDATE Kegiatan
            SET Nama_Kegiatan = p_Nama_Kegiatan_Baru, Tanggal = p_Tanggal_Baru, Tempat = p_Tempat_Baru,
                Jenis_Kegiatan = p_Jenis_Kegiatan_Baru, ID_Penanggung_Jawab = p_ID_Penanggung_Jawab_Baru
            WHERE ID_Kegiatan = p_ID_Kegiatan_Target;
        END
        """
        self._execute_ddl_block(sp_update_ddl)

        sp_hapus_ddl = """
        CREATE PROCEDURE IF NOT EXISTS SP_HapusKegiatan (
            IN p_ID_Kegiatan VARCHAR(10)
        )
        BEGIN
            DELETE FROM Kegiatan WHERE ID_Kegiatan = p_ID_Kegiatan;
        END
        """
        self._execute_ddl_block(sp_hapus_ddl)

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM Role")
            if cursor.fetchone()[0] == 0:
                roles = [(1, 'Mahasiswa'), (2, 'Dosen'), (3, 'Staff')]
                cursor.executemany("INSERT INTO Role (Role_ID, Nama_Role) VALUES (%s, %s)", roles)

            cursor.execute("SELECT COUNT(*) FROM Pengguna")
            if cursor.fetchone()[0] == 0:
                pengguna = [
                    (101, "Paul Fajar", 1, "2025", "Paul_mhs", "PAULPASS"),
                    (102, "Dr. Zhafier", 2, "705", "Zhafier_dsn", "ZHAFPASS"),
                    (103, "Vijaypal Singh", 3, "2252", "Jay_staff", "JAYPASS"),
                ]
                cursor.executemany("INSERT INTO Pengguna (ID_Pengguna, Nama, Role_ID, NIM_NIP, Username, Password) VALUES (%s, %s, %s, %s, %s, %s)", pengguna)

            cursor.execute("SELECT COUNT(*) FROM Kegiatan")
            if cursor.fetchone()[0] == 0:
                kegiatan_awal = [
                    ("K001", "Seminar AI", "10-05-2025", "Aula FT", "Seminar", 101),
                    ("K002", "Praktikum IoT", "15-05-2025", "Lab Jaringan Komputer", "Praktikum", 102),
                    ("K003", "Rapat Dosen Bulanan", "20-05-2025", "Ruang Dosen", "Rapat Dosen", 103),
                ]
                for keg in kegiatan_awal:
                    cursor.callproc("SP_TambahKegiatan", keg)
            conn.commit()
            print("Database berhasil diinisialisasi dengan data awal jika diperlukan.")
        except mysql.connector.Error as err_init_data:
            print(f"Error saat mengisi data awal: {err_init_data}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def tambah_kegiatan_db(self, id_keg, nama, tanggal, tempat, jenis, id_pj):
        self.call_stored_procedure("SP_TambahKegiatan", 
                                   (id_keg, nama, tanggal, tempat, jenis, id_pj))

    def update_kegiatan_db(self, id_keg_target, nama_keg, tanggal, tempat, jenis_keg, id_pj):
        return self.call_stored_procedure("SP_UpdateKegiatan", 
                                   (id_keg_target, nama_keg, tanggal, tempat, jenis_keg, id_pj))

    def hapus_kegiatan_db(self, id_keg):
        return self.call_stored_procedure("SP_HapusKegiatan", (id_keg,))

    def get_semua_kegiatan_db(self):
        query = """
            SELECT ID_Kegiatan, Nama_Kegiatan, Tanggal, Tempat, Jenis_Kegiatan, 
                   Nama_Penanggung_Jawab, ID_Penanggung_Jawab 
            FROM View_Detail_Kegiatan
            ORDER BY STR_TO_DATE(Tanggal, '%d-%m-%Y') DESC, Nama_Kegiatan ASC 
        """
        return self.execute_query(query, fetch_all=True)

    def get_semua_pengguna_db(self):
        query = "SELECT ID_Pengguna, Nama FROM Pengguna ORDER BY Nama"
        return self.execute_query(query, fetch_all=True)

    def verify_user_credentials(self, username, password):
        """Memverifikasi kredensial pengguna."""
        query = "SELECT * FROM Pengguna WHERE Username = %s AND Password = %s"
        result = self.execute_query(query, (username, password), fetch_one=True)
        return result is not None

    def get_roles_db(self):
        """Mengambil semua role dari database."""
        query = "SELECT Role_ID, Nama_Role FROM Role ORDER BY Nama_Role"
        return self.execute_query(query, fetch_all=True)

    def check_username_exists(self, username):
        """Memeriksa apakah username sudah ada."""
        query = "SELECT 1 FROM Pengguna WHERE Username = %s"
        return self.execute_query(query, (username,), fetch_one=True) is not None

    def check_nimid_exists(self, nim_nip):
        """Memeriksa apakah NIM/NIP sudah ada."""
        query = "SELECT 1 FROM Pengguna WHERE NIM_NIP = %s"
        return self.execute_query(query, (nim_nip,), fetch_one=True) is not None
    
    def get_max_pengguna_id(self):
        """Mendapatkan ID_Pengguna maksimum saat ini."""
        query = "SELECT MAX(ID_Pengguna) FROM Pengguna"
        result = self.execute_query(query, fetch_one=True)
        return result[0] if result and result[0] is not None else 0


    def add_user_db(self, id_pengguna, nama, role_id, nim_nip, username, password):
        """Menambahkan pengguna baru ke database."""
        query = """
            INSERT INTO Pengguna (ID_Pengguna, Nama, Role_ID, NIM_NIP, Username, Password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, (id_pengguna, nama, role_id, nim_nip, username, password))

    def get_activity_log_db(self):
        """Mengambil semua riwayat aktivitas dari Log_Perubahan_Kegiatan."""
        query = """
            SELECT ID_Log, Timestamp_Aksi, Aksi, ID_Kegiatan_Ref, Detail_Lama, Detail_Baru 
            FROM Log_Perubahan_Kegiatan 
            ORDER BY Timestamp_Aksi DESC
        """
        return self.execute_query(query, fetch_all=True)


# --- Kelas untuk Jendela Login ---
class LoginDialog:
    def __init__(self, parent_root, db_manager, open_signup_callback):
        self.parent_root = parent_root 
        self.db_manager = db_manager
        self.open_signup_callback = open_signup_callback 
        self.login_successful = False

        self.top = tk.Toplevel(parent_root)
        self.top.title("Login Aplikasi Manajemen Kegiatan")
        self.top.geometry("1080x720")
        self.top.resizable(False, False)
        self.top.grab_set() 

        try:
            img = Image.open("./assets/LOGIN (1).png")
            img = img.resize((1080, 720), Image.LANCZOS) 
            self.bg_image = ImageTk.PhotoImage(img)
            bg_label = ttk.Label(self.top, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            print("Peringatan: Gambar latar login './assets/LOGIN (1).png' tidak ditemukan.")
            self.top.configure(bg="lightgray") 
        except Exception as e:
            print(f"Error memuat gambar latar: {e}")
            self.top.configure(bg="lightgray")

        s = ttk.Style()
        s.configure("Login.TLabel", background="#FFFFFF", font=(FONT_STYLE[0], 12), padding=5) 
        s.configure("Login.TEntry", font=(FONT_STYLE[0], 12), padding=5)
        s.configure("Login.TButton", font=(FONT_STYLE[0], 12, "bold"), padding=10)
        s.configure("Link.TLabel", foreground="blue", font=(FONT_STYLE[0], 10, "underline"))
        
        center_frame = ttk.Frame(self.top) 
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Label(center_frame, text="Username", font=(FONT_STYLE[0], 14)).grid(row=0, column=0, pady=(0,5), sticky="w")
        self.username_entry = ttk.Entry(center_frame, font=(FONT_STYLE[0], 14), width=30)
        self.username_entry.grid(row=1, column=0, pady=(0,10))

        ttk.Label(center_frame, text="Password", font=(FONT_STYLE[0], 14)).grid(row=2, column=0, pady=(0,5), sticky="w")
        self.password_entry = ttk.Entry(center_frame, show="*", font=(FONT_STYLE[0], 14), width=30)
        self.password_entry.grid(row=3, column=0, pady=(0,20))
        
        self.password_entry.bind("<Return>", self._attempt_login) 

        login_button = ttk.Button(center_frame, text="Login", command=self._attempt_login, style="Login.TButton")
        login_button.grid(row=4, column=0, pady=10, sticky="ew")

        signup_label = ttk.Label(center_frame, text="Belum punya akun? Daftar di sini", style="Link.TLabel", cursor="hand2")
        signup_label.grid(row=5, column=0, pady=(10,0))
        signup_label.bind("<Button-1>", lambda e: self.open_signup_callback())
        
        self.username_entry.focus_set() 
        self.top.protocol("WM_DELETE_WINDOW", self._on_close_dialog) 

    def _on_close_dialog(self):
        print("Jendela login ditutup oleh pengguna.")
        self.login_successful = False 
        self.top.destroy()
        if not self.login_successful:
            self.parent_root.destroy()


    def _attempt_login(self, event=None): 
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Login Gagal", "Username dan Password harus diisi.", parent=self.top)
            return

        try:
            if self.db_manager.verify_user_credentials(username, password):
                messagebox.showinfo("Login Berhasil", "Login berhasil!", parent=self.top)
                self.login_successful = True
                self.top.destroy() 
            else:
                messagebox.showerror("Login Gagal", "Username atau password salah.", parent=self.top)
        except mysql.connector.Error as db_err:
            messagebox.showerror("Error Database", f"Tidak dapat terhubung ke database: {db_err}", parent=self.top)
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}", parent=self.top)

# --- Kelas untuk Jendela Signup ---
class SignupDialog:
    def __init__(self, parent_root, db_manager):
        self.parent_root = parent_root
        self.db_manager = db_manager
        self.signup_successful = False

        self.top = tk.Toplevel(parent_root)
        self.top.title("Pendaftaran Pengguna Baru")
        self.top.geometry("500x650") 
        self.top.resizable(False, False)
        self.top.grab_set()
        self.top.configure(bg=BG_COLOR)

        s = ttk.Style()
        s.configure("Signup.TLabel", background=BG_COLOR, font=(FONT_STYLE[0], 11))
        s.configure("Signup.TEntry", font=(FONT_STYLE[0], 11))
        s.configure("Signup.TButton", font=(FONT_STYLE[0], 11, "bold"))
        s.configure("Signup.TCombobox", font=(FONT_STYLE[0], 11))


        form_frame = ttk.Frame(self.top, padding="20 20 20 20", style="TFrame")
        form_frame.pack(expand=True, fill=tk.BOTH)
        
        ttk.Label(form_frame, text="Nama Lengkap:", style="Signup.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.nama_entry = ttk.Entry(form_frame, width=40, style="Signup.TEntry")
        self.nama_entry.grid(row=0, column=1, pady=5, sticky="ew")

        ttk.Label(form_frame, text="NIM/NIP:", style="Signup.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.nimid_entry = ttk.Entry(form_frame, width=40, style="Signup.TEntry")
        self.nimid_entry.grid(row=1, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Username:", style="Signup.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form_frame, width=40, style="Signup.TEntry")
        self.username_entry.grid(row=2, column=1, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Password:", style="Signup.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form_frame, show="*", width=40, style="Signup.TEntry")
        self.password_entry.grid(row=3, column=1, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Konfirmasi Password:", style="Signup.TLabel").grid(row=4, column=0, sticky="w", pady=5)
        self.confirm_password_entry = ttk.Entry(form_frame, show="*", width=40, style="Signup.TEntry")
        self.confirm_password_entry.grid(row=4, column=1, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Role:", style="Signup.TLabel").grid(row=5, column=0, sticky="w", pady=5)
        self.role_combo = ttk.Combobox(form_frame, state="readonly", width=38, style="Signup.TCombobox")
        self.role_combo.grid(row=5, column=1, pady=5, sticky="ew")
        self._load_roles()

        self.confirm_password_entry.bind("<Return>", self._attempt_signup)

        button_frame = ttk.Frame(form_frame, style="TFrame")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        signup_button = ttk.Button(button_frame, text="Daftar", command=self._attempt_signup, style="Signup.TButton")
        signup_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = ttk.Button(button_frame, text="Batal", command=self.top.destroy, style="Signup.TButton")
        cancel_button.pack(side=tk.LEFT, padx=10)

        self.nama_entry.focus_set()
        self.top.protocol("WM_DELETE_WINDOW", self.top.destroy)


    def _load_roles(self):
        try:
            roles_data = self.db_manager.get_roles_db() 
            if roles_data:
                self.role_map = {nama_role: role_id for role_id, nama_role in roles_data}
                self.role_combo["values"] = list(self.role_map.keys())
            else:
                self.role_combo["values"] = []
                self.role_map = {}
        except mysql.connector.Error as db_err:
            messagebox.showerror("Error Database", f"Gagal memuat role: {db_err}", parent=self.top)
            self.role_combo["values"] = []
            self.role_map = {}


    def _attempt_signup(self, event=None):
        nama = self.nama_entry.get().strip()
        nim_nip = self.nimid_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get() 
        confirm_password = self.confirm_password_entry.get()
        role_nama = self.role_combo.get()

        if not all([nama, nim_nip, username, password, confirm_password, role_nama]):
            messagebox.showerror("Pendaftaran Gagal", "Semua field harus diisi.", parent=self.top)
            return

        if password != confirm_password:
            messagebox.showerror("Pendaftaran Gagal", "Password dan Konfirmasi Password tidak cocok.", parent=self.top)
            return
        
        if len(password) < 6: 
            messagebox.showerror("Pendaftaran Gagal", "Password minimal harus 6 karakter.", parent=self.top)
            return

        role_id = self.role_map.get(role_nama)
        if role_id is None:
            messagebox.showerror("Pendaftaran Gagal", "Role tidak valid.", parent=self.top)
            return

        try:
            if self.db_manager.check_username_exists(username):
                messagebox.showerror("Pendaftaran Gagal", f"Username '{username}' sudah digunakan.", parent=self.top)
                return
            if self.db_manager.check_nimid_exists(nim_nip):
                messagebox.showerror("Pendaftaran Gagal", f"NIM/NIP '{nim_nip}' sudah terdaftar.", parent=self.top)
                return
            
            max_id = self.db_manager.get_max_pengguna_id()
            new_id_pengguna = max_id + 1

            self.db_manager.add_user_db(new_id_pengguna, nama, role_id, nim_nip, username, password)
            messagebox.showinfo("Pendaftaran Berhasil", "Pengguna baru berhasil didaftarkan! Silakan login.", parent=self.top)
            self.signup_successful = True
            self.top.destroy()

        except mysql.connector.Error as db_err:
            messagebox.showerror("Error Database", f"Gagal mendaftarkan pengguna: {db_err}", parent=self.top)
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}", parent=self.top)

# --- Kelas untuk Jendela Riwayat Aktivitas ---
class ActivityLogDialog:
    def __init__(self, parent, db_manager):
        self.top = tk.Toplevel(parent)
        self.top.title("📜 Riwayat Aktivitas Kegiatan")
        self.top.geometry("950x500")
        self.top.resizable(True, True)
        self.top.grab_set() # Modal
        self.top.configure(bg=BG_COLOR)
        self.db_manager = db_manager

        # Frame untuk Treeview dan Scrollbar
        log_frame = ttk.LabelFrame(self.top, text="Log Perubahan Data Kegiatan", padding="10")
        log_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Treeview untuk menampilkan log
        columns = ("id_log", "timestamp", "aksi", "id_keg_ref", "detail_lama", "detail_baru")
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show="headings")
        
        self.log_tree.heading("id_log", text="ID Log")
        self.log_tree.heading("timestamp", text="Waktu")
        self.log_tree.heading("aksi", text="Aksi")
        self.log_tree.heading("id_keg_ref", text="ID Kegiatan")
        self.log_tree.heading("detail_lama", text="Data Lama")
        self.log_tree.heading("detail_baru", text="Data Baru")

        self.log_tree.column("id_log", width=60, anchor="center")
        self.log_tree.column("timestamp", width=150, anchor="w")
        self.log_tree.column("aksi", width=80, anchor="w")
        self.log_tree.column("id_keg_ref", width=100, anchor="center")
        self.log_tree.column("detail_lama", width=250, anchor="w")
        self.log_tree.column("detail_baru", width=250, anchor="w")

        # Scrollbar
        scrollbar_y = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        scrollbar_x = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.log_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Tombol Refresh dan Tutup
        button_frame = ttk.Frame(self.top)
        button_frame.pack(pady=10)

        refresh_button = ttk.Button(button_frame, text="🔄 Muat Ulang", command=self._load_log_data)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        close_button = ttk.Button(button_frame, text="Tutup", command=self.top.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

        self._load_log_data()
        self.top.protocol("WM_DELETE_WINDOW", self.top.destroy)


    def _load_log_data(self):
        """Memuat dan menampilkan data log ke Treeview."""
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        try:
            log_data = self.db_manager.get_activity_log_db()
            if log_data:
                for row in log_data:
                    # Format timestamp jika perlu (misalnya, jika dari DB adalah objek datetime)
                    formatted_row = list(row)
                    if isinstance(row[1], datetime.datetime):
                        formatted_row[1] = row[1].strftime("%Y-%m-%d %H:%M:%S")
                    self.log_tree.insert("", tk.END, values=formatted_row)
            else:
                self.log_tree.insert("", tk.END, values=("", "Tidak ada data log.", "", "", "", ""))
        except mysql.connector.Error as db_err:
            messagebox.showerror("Error Database", f"Gagal memuat riwayat aktivitas: {db_err}", parent=self.top)
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat memuat log: {e}", parent=self.top)


# --- Kelas Aplikasi Utama ---
class KegiatanApp:
    def __init__(self, root, db_manager):
        self.root = root
        self.db_manager = db_manager
        self.selected_kegiatan_id_for_update = None 
        self.root.title("🗂️ Aplikasi Manajemen Kegiatan DTEI (VTS)")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1050x850") 

        style = ttk.Style()
        style.theme_use('clam') 
        style.configure("Treeview.Heading", font=FONT_BOLD)
        style.configure("Treeview", font=FONT_STYLE, rowheight=25) 
        style.configure("TLabel", background=BG_COLOR, font=FONT_STYLE)
        style.configure("TEntry", font=FONT_STYLE)
        style.configure("TCombobox", font=FONT_STYLE)
        style.map("TCombobox", fieldbackground=[("readonly", "white")]) 
        style.configure("TButton", font=FONT_STYLE, padding=5)
        style.configure("TLabelframe.Label", font=FONT_BOLD, background=BG_COLOR)


        self.pengguna_data_map = {} 
        self.pengguna_id_to_display_map = {} 
        self._build_ui()

    def _styled_button(self, parent, text, command, style_name="TButton"):
        btn = ttk.Button(parent, text=text, command=command, style=style_name)
        return btn

    def _build_ui(self):
        input_frame = ttk.LabelFrame(self.root, text="Formulir Kegiatan")
        input_frame.pack(fill='x', padx=15, pady=10)

        self.labels_texts_map = {
            "id_kegiatan": "ID Kegiatan:",
            "nama_kegiatan": "Nama Kegiatan:",
            "tanggal": "Tanggal:", 
            "tempat": "Tempat:",
            "jenis_kegiatan": "Jenis Kegiatan:",
            "pj": "Penanggung Jawab:"
        }
        self.entries = {} 

        form_fields_frame = ttk.Frame(input_frame)
        form_fields_frame.pack(padx=10, pady=10)

        tanggal_idx = list(self.labels_texts_map.keys()).index("tanggal")
        
        self.tempat_options = ["Aula B11", "Auditorium B12", "Labkom1-B11", "Kelas1", "Kelas2", 
                               "Kelas3", "Kelas4", "Kelas5", "Kelas6", "Kelas7", "Kelas8", 
                               "Kelas9", "Kelas10"]


        for i, (key, text) in enumerate(self.labels_texts_map.items()):
            label = ttk.Label(form_fields_frame, text=text)
            
            current_row_for_label = i
            current_row_for_widget = i

            if key == "tanggal":
                label.grid(row=current_row_for_label, column=0, sticky="nw", padx=5, pady=5)
                self.cal_tanggal = Calendar(form_fields_frame, selectmode='day',
                                            date_pattern='dd-mm-yyyy', 
                                            font=FONT_STYLE,
                                            showweeknumbers=False,
                                            locale='id_ID', 
                                            background=BTN_COLOR, 
                                            foreground='white',   
                                            bordercolor=BTN_COLOR,
                                            headersbackground=BTN_COLOR,
                                            headersforeground='white',
                                            selectbackground=BTN_HOVER, 
                                            selectforeground='white',
                                            normalbackground='white', 
                                            normalforeground='black',
                                            weekendbackground='white',
                                            weekendforeground='black',
                                            othermonthbackground='lightgray', 
                                            othermonthforeground='darkgray',
                                            othermonthwebackground='lightgray',
                                            othermonthweforeground='darkgray'
                                           )
                self.cal_tanggal.grid(row=current_row_for_widget, column=1, sticky="ew", padx=5, pady=5, rowspan=3)
                self.entries[key] = self.cal_tanggal
                self.cal_tanggal.bind("<<CalendarSelected>>", self._on_calendar_selected_debug)
            
            elif i > tanggal_idx : 
                current_row_for_label = tanggal_idx + 3 + (i - tanggal_idx - 1)
                current_row_for_widget = current_row_for_label
                label.grid(row=current_row_for_label, column=0, sticky="w", padx=5, pady=5)

                if key == "tempat": 
                    self.combo_tempat = ttk.Combobox(form_fields_frame, values=self.tempat_options, state="readonly", width=37, font=FONT_STYLE)
                    self.combo_tempat.grid(row=current_row_for_widget, column=1, sticky="ew", padx=5, pady=5)
                    self.entries[key] = self.combo_tempat
                elif key == "pj":
                    self.combo_pj = ttk.Combobox(form_fields_frame, state="readonly", width=37, font=FONT_STYLE)
                    self.combo_pj.grid(row=current_row_for_widget, column=1, sticky="ew", padx=5, pady=5)
                    self.entries[key] = self.combo_pj
                else: 
                    entry = ttk.Entry(form_fields_frame, font=FONT_STYLE, width=40)
                    entry.grid(row=current_row_for_widget, column=1, sticky="ew", padx=5, pady=5)
                    self.entries[key] = entry
            
            else: 
                label.grid(row=current_row_for_label, column=0, sticky="w", padx=5, pady=5)
                entry = ttk.Entry(form_fields_frame, font=FONT_STYLE, width=40)
                entry.grid(row=current_row_for_widget, column=1, sticky="ew", padx=5, pady=5)
                self.entries[key] = entry
        
        if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
            self.combo_pj = self.entries["pj"]
        if "tempat" in self.entries and isinstance(self.entries["tempat"], ttk.Combobox):
            self.combo_tempat = self.entries["tempat"] 


        action_buttons_frame = ttk.Frame(input_frame)
        action_buttons_frame.pack(pady=20) 

        self.btn_simpan = self._styled_button(action_buttons_frame, "➕ Tambah", self._tambah_kegiatan)
        self.btn_simpan.pack(side=tk.LEFT, padx=5)

        self.btn_update = self._styled_button(action_buttons_frame, "✏️ Update", self._update_kegiatan)
        self.btn_update.pack(side=tk.LEFT, padx=5)
        self.btn_update.config(state="disabled") 

        self.btn_hapus = self._styled_button(action_buttons_frame, "❌ Hapus", self._hapus_kegiatan)
        self.btn_hapus.pack(side=tk.LEFT, padx=5)

        self.btn_clear_form = self._styled_button(action_buttons_frame, "🧹 Bersihkan Form", self._clear_form_action)
        self.btn_clear_form.pack(side=tk.LEFT, padx=5)
        
        self.btn_refresh_data = self._styled_button(action_buttons_frame, "🔄 Muat Ulang Data", self._tampilkan_semua_kegiatan_ui) # Teks diubah
        self.btn_refresh_data.pack(side=tk.LEFT, padx=5)

        self.btn_activity_log = self._styled_button(action_buttons_frame, "📜 Riwayat Aktivitas", self._open_activity_log_dialog)
        self.btn_activity_log.pack(side=tk.LEFT, padx=5)


        tabel_frame = ttk.LabelFrame(self.root, text="📋 Daftar Kegiatan (dari View)") 
        tabel_frame.pack(fill='both', expand=True, padx=15, pady=10)

        columns_info = {
            "id": {"text": "ID Keg.", "width": 80, "anchor": "w"},
            "nama": {"text": "Nama Kegiatan", "width": 250, "anchor": "w"},
            "tanggal": {"text": "Tanggal", "width": 100, "anchor": "center"},
            "tempat": {"text": "Tempat", "width": 180, "anchor": "w"},
            "jenis": {"text": "Jenis Keg.", "width": 120, "anchor": "w"},
            "pj_nama": {"text": "P. Jawab", "width": 150, "anchor": "w"},
            "pj_id": {"text": "ID PJ", "width": 0, "anchor": "w"} 
        }
        self.tree = ttk.Treeview(tabel_frame, columns=list(columns_info.keys()), show="headings")
        
        for col_id, info in columns_info.items():
            self.tree.heading(col_id, text=info["text"])
            if info["width"] == 0: 
                 self.tree.column(col_id, width=0, stretch=tk.NO)
            else:
                self.tree.column(col_id, anchor=info["anchor"], width=info["width"], minwidth=info["width"] if info["width"] > 50 else 50)
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)


        scrollbar = ttk.Scrollbar(tabel_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill="y") 

        self._load_pengguna_ui()
        self._tampilkan_semua_kegiatan_ui()

    def _on_calendar_selected_debug(self, event=None):
        try:
            selected_date = self.cal_tanggal.get_date()
            print(f"DEBUG: <<CalendarSelected>> event. Tanggal terpilih: {selected_date}")
            self.root.update_idletasks()
        except Exception as e:
            print(f"DEBUG: Terjadi error di _on_calendar_selected_debug: {e}")


    def _clear_form_fields(self):
        self.entries["id_kegiatan"].config(state="normal")
        self.entries["id_kegiatan"].delete(0, tk.END)
        self.entries["nama_kegiatan"].delete(0, tk.END)
        
        if "tempat" in self.entries and isinstance(self.entries["tempat"], ttk.Combobox):
            self.entries["tempat"].set('') 
        elif "tempat" in self.entries: 
             self.entries["tempat"].delete(0, tk.END)

        if "jenis_kegiatan" in self.entries: 
            self.entries["jenis_kegiatan"].delete(0, tk.END)

        if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
            self.entries["pj"].set('') 
        self.selected_kegiatan_id_for_update = None

    def _clear_form_action(self):
        self._clear_form_fields()
        self.entries["id_kegiatan"].config(state="normal") 
        self.btn_simpan.config(state="normal")
        self.btn_update.config(state="disabled")
        if self.tree.selection(): 
            self.tree.selection_remove(self.tree.selection()[0])


    def _on_tree_select(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            self._clear_form_action()
            return

        item_values = self.tree.item(selected_items[0], "values")
        if not item_values or len(item_values) < 7:  
            print("Error: Data item tidak lengkap dari treeview.")
            self._clear_form_action()
            return

        self._clear_form_fields() 

        id_keg_val, nama_keg_val, tgl_val, tempat_val, jenis_val, pj_nama_val, pj_id_val_hidden = item_values
        
        self.selected_kegiatan_id_for_update = id_keg_val

        self.entries["id_kegiatan"].insert(0, id_keg_val)
        self.entries["id_kegiatan"].config(state="readonly") 

        self.entries["nama_kegiatan"].insert(0, nama_keg_val)
        try:
            if tgl_val:
                date_obj = datetime.datetime.strptime(tgl_val, "%d-%m-%Y").date()
                self.cal_tanggal.selection_set(date_obj)
                self.cal_tanggal.focus_set() 
                self.cal_tanggal.event_generate("<<CalendarSelected>>") 
            else:
                self.cal_tanggal.selection_set(datetime.date.today())
        except ValueError:
            print(f"Format tanggal salah dari tree: {tgl_val}")
            self.cal_tanggal.selection_set(datetime.date.today())

        if "tempat" in self.entries and isinstance(self.entries["tempat"], ttk.Combobox):
            if tempat_val in self.tempat_options:
                self.entries["tempat"].set(tempat_val)
            else:
                self.entries["tempat"].set('') 
                print(f"Warning: Nilai tempat '{tempat_val}' dari DB tidak ada di opsi dropdown.")
        elif "tempat" in self.entries: 
             self.entries["tempat"].insert(0, tempat_val)

        if "jenis_kegiatan" in self.entries: 
            self.entries["jenis_kegiatan"].insert(0, jenis_val)

        if pj_id_val_hidden and pj_id_val_hidden != 'None' and pj_id_val_hidden.strip():
            try:
                pj_id_int = int(pj_id_val_hidden)
                pj_display_text = self.pengguna_id_to_display_map.get(pj_id_int)
                if pj_display_text and "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                    self.entries["pj"].set(pj_display_text)
                else:
                    if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                        self.entries["pj"].set('') 
            except ValueError:
                if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                    self.entries["pj"].set('')
                print(f"ID PJ tidak valid: {pj_id_val_hidden}")
        else:
            if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                 self.entries["pj"].set('')

        self.btn_simpan.config(state="disabled")
        self.btn_update.config(state="normal")


    def _load_pengguna_ui(self):
        try:
            pengguna_list = self.db_manager.get_semua_pengguna_db()
            if pengguna_list:
                self.pengguna_data_map = {f"{nama} (ID: {idp})": idp for idp, nama in pengguna_list}
                self.pengguna_id_to_display_map = {idp: f"{nama} (ID: {idp})" for idp, nama in pengguna_list}
                if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                    self.entries["pj"]["values"] = list(self.pengguna_data_map.keys())
            else:
                if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                    self.entries["pj"]["values"] = []
                self.pengguna_data_map = {}
                self.pengguna_id_to_display_map = {}
        except mysql.connector.Error as err:
            messagebox.showerror("Error Database", f"Gagal memuat data pengguna: {err}")

    def _tambah_kegiatan(self):
        try:
            id_keg = self.entries["id_kegiatan"].get().strip()
            nama = self.entries["nama_kegiatan"].get().strip()
            
            tanggal_obj = self.cal_tanggal.get_date() 
            tanggal_str = ""

            if tanggal_obj is None: # Jika tidak ada tanggal yang dipilih
                messagebox.showwarning("Validasi Gagal", "Tanggal harus dipilih.", parent=self.root)
                return
            
            # Pastikan tanggal_obj adalah datetime.date sebelum memanggil strftime
            if not isinstance(tanggal_obj, datetime.date):
                 # Ini seharusnya tidak terjadi jika Calendar.get_date() bekerja sesuai dokumentasi
                messagebox.showerror("Error Tipe Tanggal",
                                     f"Tipe data tidak terduga untuk tanggal: {type(tanggal_obj)}.\nNilai: '{tanggal_obj}'.\nHarap laporkan bug ini.",
                                     parent=self.root)
                print(f"DEBUG: Unexpected type from cal_tanggal.get_date(): {type(tanggal_obj)}, value: {tanggal_obj}")
                return
            
            try:
                tanggal_str = tanggal_obj.strftime("%d-%m-%Y")
            except AttributeError: # Menangkap jika tanggal_obj adalah string (seharusnya tidak terjadi di sini)
                 messagebox.showerror("Error Tipe Tanggal",
                                     f"Kesalahan internal: Objek tanggal adalah string '{tanggal_obj}' bukan objek date.",
                                     parent=self.root)
                 return
            except Exception as e: # Menangkap error strftime lainnya
                 messagebox.showerror("Error Format Tanggal",
                                     f"Gagal memformat tanggal: {e}",
                                     parent=self.root)
                 return

            
            tempat = ""
            if "tempat" in self.entries and isinstance(self.entries["tempat"], ttk.Combobox):
                tempat = self.entries["tempat"].get().strip()
            elif "tempat" in self.entries: 
                tempat = self.entries["tempat"].get().strip()

            jenis = ""
            if "jenis_kegiatan" in self.entries: 
                jenis = self.entries["jenis_kegiatan"].get().strip()
            
            pj_display_name = ""
            if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                pj_display_name = self.entries["pj"].get()
            else:
                messagebox.showerror("Error Internal", "Widget Penanggung Jawab tidak terdefinisi.")
                return

            if not all([id_keg, nama, tanggal_str, tempat, jenis, pj_display_name]):
                messagebox.showwarning("⚠️ Validasi Gagal", "Semua kolom formulir harus diisi.")
                return

            id_pj = self.pengguna_data_map.get(pj_display_name)
            if id_pj is None:
                messagebox.showerror("Error Internal", "Penanggung jawab tidak valid.")
                return

            self.db_manager.tambah_kegiatan_db(id_keg, nama, tanggal_str, tempat, jenis, id_pj)
            messagebox.showinfo("✅ Sukses", f"Kegiatan '{nama}' berhasil ditambahkan.")
            self._tampilkan_semua_kegiatan_ui()
            self._clear_form_action()

        except mysql.connector.Error as db_err:
            if db_err.errno == 1062 : 
                 messagebox.showerror("❌ Error Duplikasi", f"ID Kegiatan '{id_keg}' sudah terdaftar. Gunakan ID lain.")
            elif hasattr(db_err, 'msg') and 'ID Kegiatan sudah ada.' in db_err.msg : 
                 messagebox.showerror("❌ Error Duplikasi SP", db_err.msg)
            else:
                 messagebox.showerror("❌ Error Database", f"Gagal menambah kegiatan: {db_err}")
        except Exception as e:
            messagebox.showerror("❌ Kesalahan Umum", f"Terjadi kesalahan tak terduga: {e}")

    def _update_kegiatan(self):
        if not self.selected_kegiatan_id_for_update:
            messagebox.showwarning("⚠️ Peringatan", "Tidak ada kegiatan yang dipilih untuk diupdate.")
            return
        
        try:
            id_keg_target = self.selected_kegiatan_id_for_update
            nama_baru = self.entries["nama_kegiatan"].get().strip()
            
            tanggal_obj = self.cal_tanggal.get_date()
            tanggal_str_baru = ""

            if tanggal_obj is None:
                messagebox.showwarning("Validasi Gagal", "Tanggal harus dipilih untuk update.", parent=self.root)
                return

            if not isinstance(tanggal_obj, datetime.date):
                messagebox.showerror("Error Tipe Tanggal",
                                     f"Tipe data tidak terduga untuk tanggal: {type(tanggal_obj)}.\nNilai: '{tanggal_obj}'.\nHarap laporkan bug ini.",
                                     parent=self.root)
                print(f"DEBUG: Unexpected type from cal_tanggal.get_date() for update: {type(tanggal_obj)}, value: {tanggal_obj}")
                return
            
            try:
                tanggal_str_baru = tanggal_obj.strftime("%d-%m-%Y")
            except AttributeError:
                 messagebox.showerror("Error Tipe Tanggal",
                                     f"Kesalahan internal: Objek tanggal adalah string '{tanggal_obj}' bukan objek date saat update.",
                                     parent=self.root)
                 return
            except Exception as e:
                 messagebox.showerror("Error Format Tanggal",
                                     f"Gagal memformat tanggal saat update: {e}",
                                     parent=self.root)
                 return
            
            tempat_baru = ""
            if "tempat" in self.entries and isinstance(self.entries["tempat"], ttk.Combobox):
                tempat_baru = self.entries["tempat"].get().strip()
            elif "tempat" in self.entries: 
                tempat_baru = self.entries["tempat"].get().strip()

            jenis_baru = ""
            if "jenis_kegiatan" in self.entries: 
                jenis_baru = self.entries["jenis_kegiatan"].get().strip()
            
            pj_display_name_baru = ""
            if "pj" in self.entries and isinstance(self.entries["pj"], ttk.Combobox):
                 pj_display_name_baru = self.entries["pj"].get()
            else:
                messagebox.showerror("Error Internal", "Widget Penanggung Jawab tidak terdefinisi.")
                return

            if not all([nama_baru, tanggal_str_baru, tempat_baru, jenis_baru, pj_display_name_baru]):
                messagebox.showwarning("⚠️ Validasi Gagal", "Semua kolom (kecuali ID) harus diisi untuk update.")
                return

            id_pj_baru = self.pengguna_data_map.get(pj_display_name_baru)
            if id_pj_baru is None:
                messagebox.showerror("Error Internal", "Penanggung jawab baru tidak valid.")
                return

            self.db_manager.update_kegiatan_db(
                id_keg_target, nama_baru, tanggal_str_baru, tempat_baru, jenis_baru, id_pj_baru
            )
            messagebox.showinfo("✅ Sukses", f"Kegiatan (ID: {id_keg_target}) berhasil diperbarui.")
            self._tampilkan_semua_kegiatan_ui()
            self._clear_form_action()

        except mysql.connector.Error as db_err:
             messagebox.showerror("❌ Error Database", f"Gagal memperbarui kegiatan: {db_err}")
        except Exception as e:
            messagebox.showerror("❌ Kesalahan Umum", f"Terjadi kesalahan tak terduga saat update: {e}")


    def _hapus_kegiatan(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("⚠️ Peringatan", "Pilih satu kegiatan yang ingin dihapus.")
            return
        
        if len(selected_items) > 1:
            messagebox.showwarning("⚠️ Peringatan", "Hanya bisa menghapus satu kegiatan dalam satu waktu.")
            return

        id_keg = self.tree.item(selected_items[0], "values")[0]
        
        if not messagebox.askyesno("❓ Konfirmasi Hapus", f"Anda yakin ingin menghapus kegiatan ID: {id_keg}?"):
            return
        
        try:
            self.db_manager.hapus_kegiatan_db(id_keg)
            messagebox.showinfo("🗑️ Sukses", f"Kegiatan ID: {id_keg} berhasil dihapus.")
            self._tampilkan_semua_kegiatan_ui()
            self._clear_form_action() 
        except mysql.connector.Error as err:
            messagebox.showerror("❌ Error Database", f"Gagal menghapus ID {id_keg}: {err}")
        

    def _tampilkan_semua_kegiatan_ui(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            kegiatan_list = self.db_manager.get_semua_kegiatan_db()
            if kegiatan_list:
                for row_data in kegiatan_list: 
                    if len(row_data) == 7:
                         self.tree.insert("", "end", values=row_data)
                    else:
                        print(f"Peringatan: Data tidak lengkap diterima dari DB: {row_data}")
        except mysql.connector.Error as err:
            messagebox.showerror("Error Database", f"Gagal memuat daftar kegiatan: {err}")

    def _open_activity_log_dialog(self):
        """Membuka dialog riwayat aktivitas."""
        log_dialog = ActivityLogDialog(self.root, self.db_manager)
        # self.root.wait_window(log_dialog.top) # Tidak perlu jika grab_set() digunakan


# --- Titik Masuk Aplikasi ---
def open_signup_dialog(parent_root, db_manager):
    """Fungsi untuk membuka dialog signup."""
    signup_dialog = SignupDialog(parent_root, db_manager)
    parent_root.wait_window(signup_dialog.top)


if __name__ == "__main__":
    DB_HOST = "localhost"
    DB_USER = "root" 
    DB_PASS = ""  
    DB_NAME = "ManajemenKegiatanDTEI_VTS" 

    main_root = tk.Tk()
    main_root.withdraw() 

    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)

    try:
        print(f"Menginisialisasi database '{DB_NAME}'...")
        db_manager.initialize_database() 
        print("Inisialisasi database selesai.")
    except Exception as e:
        messagebox.showerror("Kritikal: Inisialisasi Database Gagal", f"Aplikasi tidak dapat dimulai.\nError: {e}")
        print(f"Kritikal: Inisialisasi Database Gagal - {e}")
        main_root.destroy()
        exit() 
    
    def do_open_signup():
        open_signup_dialog(main_root, db_manager)

    login_dialog = LoginDialog(main_root, db_manager, do_open_signup)
    main_root.wait_window(login_dialog.top) 

    if hasattr(login_dialog, 'login_successful') and login_dialog.login_successful:
        main_root.deiconify() 
        app = KegiatanApp(main_root, db_manager)
        main_root.mainloop()
    else:
        print("Login gagal atau jendela login ditutup. Aplikasi keluar.")
        main_root.destroy() 
