# DASAR APLIKASI
Tujuan utama dari aplikasi ini adalah untuk membantu mencatat, mengelola, dan menampilkan berbagai kegiatan yang dilakukan di lingkungan Departemen Elektro dan Informatika. Kegiatan yang dimaksud bisa berupa seminar, kuliah tamu, praktikum, lomba, rapat dosen, dan kegiatan lainnya.
Saya memilih menggunakan Python karena bahasanya cukup mudah dipahami dan sangat cocok untuk membangun aplikasi semacam ini, apalagi kalau dikombinasikan dengan database seperti MySQL atau SQLite.

**Fitur-Fitur Utama**

1. Manajemen Data Kegiatan
Di sini pengguna bisa:
Menambahkan kegiatan baru, lengkap dengan informasi nama kegiatan, tanggal pelaksanaan, tempat, penanggung jawab, dan jenis kegiatan.
Melakukan perubahan (edit) atau menghapus kegiatan jika diperlukan.
Melihat daftar kegiatan, yang bisa di filter berdasarkan kategori atau tanggal tertentu.

2. Manajemen Pengguna
Pengguna sistem ini terdiri dari tiga jenis: mahasiswa, dosen, dan staf.
Ketiganya akan ditangani menggunakan prinsip inheritance di OOP (Object Oriented Programming)
Untuk keamanan, sistem ini juga bisa dilengkapi login atau autentikasi sederhana (fitur ini opsional, tapi direkomendasikan).

4. Koneksi Database
Semua data kegiatan dan pengguna akan disimpan dalam sebuah database, dan aplikasinya bisa diatur untuk menggunakan MySQL atau SQLite, tergantung kebutuhan.
Kita juga akan mengambil dan menampilkan data dari database menggunakan query SQL.

**Penerapan Konsep OOP (Object-Oriented Programming)**

1. Encapsulation
Setiap atribut dan method dalam class akan disembunyikan (menggunakan teknik seperti atribut privat), supaya tidak sembarang bagian program bisa mengaksesnya. Ini penting untuk menjaga integritas data.

2. Inheritance
Kita punya class induk bernama Pengguna, lalu dari class ini diturunkan tiga class turunan: Mahasiswa, Dosen, dan Staf. Dengan cara ini, kita tidak perlu menulis ulang kode yang sama untuk setiap jenis pengguna.

3. Polymorphism
Method seperti tampilkan_info() akan diimplementasikan berbeda tergantung jenis penggunanya. Jadi meskipun method-nya sama, output-nya bisa disesuaikan.

4. Overriding
Di subclass seperti Dosen atau Staf, kita bisa memodifikasi method dari class induk agar sesuai kebutuhan masing-masing.

5. Composition
Class Kegiatan akan memiliki atribut yang menyimpan referensi ke objek Pengguna, karena setiap kegiatan pasti punya penanggung jawab. Jadi, hubungan antar class ini sangat relevan dengan dunia nyata.
