def tambah(a, b):
    return a + b

def kurang(a, b):
    return a - b

def kali(a, b):
    return a * b

def bagi(a, b):
    if b != 0:
        return a / b
    else:
        return "Error: Tidak bisa membagi dengan nol!"

print("Kalkulator Sederhana")
print("1. Tambah")
print("2. Kurang")
print("3. Kali")
print("4. Bagi")

pilih = input("Pilih operasi (1/2/3/4): ")

angka1 = float(input("Masukkan angka pertama: "))
angka2 = float(input("Masukkan angka kedua: "))

if pilih == '1':
    print("Hasil:", tambah(angka1, angka2))
elif pilih == '2':
    print("Hasil:", kurang(angka1, angka2))
elif pilih == '3':
    print("Hasil:", kali(angka1, angka2))
elif pilih == '4':
    print("Hasil:", bagi(angka1, angka2))
else:
    print("Pilihan tidak valid.")
