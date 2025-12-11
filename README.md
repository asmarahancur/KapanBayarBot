# Kapan Bayar Bot 🤖💸

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Telegram-Bot_API-26a5e4.svg" alt="Telegram Bot API">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen.svg" alt="Status">
</p>

<p align="center">
  <strong>Telegram Bot untuk Mencatat, Mengelola, dan Mengingatkan Utang dengan Fitur Lengkap</strong>
</p>

<p align="center">
  <img src="https://i.imgur.com/3JZQ6X2.png" alt="Kapan Bayar Bot Preview" width="500">
</p>

## 📋 Daftar Isi
- [✨ Fitur Utama](#-fitur-utama)
- [🚀 Demo](#-demo)
- [⚙️ Instalasi](#️-instalasi)
- [🔧 Konfigurasi](#-konfigurasi)
- [📁 Struktur Proyek](#-struktur-proyek)
- [🎯 Cara Penggunaan](#-cara-penggunaan)
- [👑 Fitur Owner](#-fitur-owner)
- [🛠️ Teknologi](#️-teknologi)
- [🤝 Berkontribusi](#-berkontribusi)
- [📄 Lisensi](#-lisensi)
- [🙏 Penghargaan](#-penghargaan)

## ✨ Fitur Utama

### 💼 **Untuk Semua User**
- ✅ **Tambah Utang** - Catat utang dengan detail lengkap (nama, jumlah, tanggal, jam notifikasi, catatan)
- 🗑️ **Hapus Utang** - Hapus utang yang sudah lunas atau tidak berlaku
- 📋 **Daftar Utang** - Lihat semua utang yang tercatat dengan total keseluruhan
- ⏸️ **Jeda Notifikasi** - Atur interval pengingat (5 menit, 10 menit, dll.)
- 🔔 **Pengingat Otomatis** - Notifikasi saat jatuh tempo dengan konfirmasi pembayaran
- ❓ **Panduan Lengkap** - Petunjuk penggunaan yang mudah dipahami
- 💝 **Support Developer** - Dukung pengembangan bot melalui QRIS dan cryptocurrency

### 👑 **Fitur Khusus Owner**
- 📊 **Statistik Lengkap** - Lihat jumlah user, total utang, dan aktivitas
- 📤 **Broadcast Message** - Kirim pesan/media ke semua user sekaligus
- 🔒 **Group Wajib Join** - Atur group/channel yang harus diikuti user
- 📁 **Backup Data** - Ekspor data user dan utang dalam format JSON
- 👥 **Manajemen User** - Pantau dan kelola semua user bot

### 🔒 **Sistem Keamanan**
- ✅ **Verifikasi Membership** - Pastikan user sudah join group/channel tertentu
- 🔐 **Owner-Only Commands** - Perintah khusus hanya untuk owner
- 💾 **Database Terpisah** - Data user disimpan aman di file terpisah
- 🔄 **Auto-Save** - Data tersimpan otomatis setiap perubahan

## 🚀 Demo

### 📸 Screenshot Fitur

| Menu Utama | Tambah Utang | Daftar Utang |
|------------|--------------|--------------|
| <img src="https://i.imgur.com/X9Q7t8a.png" width="250"> | <img src="https://i.imgur.com/Y8s9R7r.png" width="250"> | <img src="https://i.imgur.com/zQ3Wc9L.png" width="250"> |

| Notifikasi | Owner Stats | Broadcast |
|------------|-------------|-----------|
| <img src="https://i.imgur.com/6T0KpVv.png" width="250"> | <img src="https://i.imgur.com/M8fFhN5.png" width="250"> | <img src="https://i.imgur.com/P9rJzWk.png" width="250"> |

## ⚙️ Instalasi

### Prasyarat
- Python 3.8 atau lebih tinggi
- Akun Telegram
- Bot Token dari [@BotFather](https://t.me/BotFather)

### Langkah-langkah Instalasi

1. **Clone Repository**
```bash
git clone https://github.com/asmarahancur/KapanBayarBot.git
cd KapanBayarBot
```

2. **Buat Virtual Environment (Opsional tapi Direkomendasikan)**
```bash
# Untuk Windows
python -m venv venv
venv\Scripts\activate

# Untuk Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Konfigurasi Environment**
```bash
cp .env.example .env
# Edit file .env dengan editor teks favorit Anda
```

## 🔧 Konfigurasi

### File `.env`
```env
# Bot Configuration
TOKEN=your_bot_token_here_123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
OWNER_ID=your_telegram_id_here_123456789

# Optional Settings (default values)
NOTIFICATION_INTERVAL=5  # dalam menit
TIMEZONE=Asia/Jakarta
```

### Cara Mendapatkan Bot Token
1. Buka [@BotFather](https://t.me/BotFather) di Telegram
2. Ketik `/newbot` dan ikuti instruksi
3. Salin token yang diberikan (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Cara Mendapatkan Owner ID
1. Buka [@userinfobot](https://t.me/userinfobot) di Telegram
2. Kirim pesan apa saja
3. Salin ID Anda (format angka)

### Menyiapkan Gambar (Opsional)
```bash
# Tambahkan icon untuk welcome message
cp icon-example.png icon.png

# Tambahkan QRIS untuk donasi
cp qris-example.jpeg qris.jpeg
```

## 📁 Struktur Proyek

```
kapan-bayar-bot/
├── 📂 database/              # Folder database per user
│   ├── 123456789.json       # Data utang user 123456789
│   └── 987654321.json       # Data utang user 987654321
│
├── 📜 main.py               # File utama bot
├── 📜 requirements.txt       # Dependencies Python
├── 📜 .env                  # Konfigurasi environment
├── 📜 .gitignore            # File yang diabaikan Git
│
├── 📜 users.json            # Data semua user
├── 📜 join_groups.json      # Daftar group wajib join
├── 📜 join_users.json       # Tracking status join user
│
├── 📂 assets/               # Folder aset (opsional)
│   ├── icon.png             # Gambar welcome
│   └── qris.jpeg            # QRIS untuk donasi
│
├── 📜 README.md             # Dokumentasi ini
└── 📜 LICENSE               # Lisensi MIT
```

## 🎯 Cara Penggunaan

### 1. Memulai Bot
1. Cari bot Anda di Telegram: `@YourBotUsername`
2. Klik `/start` atau tombol "Start"
3. Jika ada group wajib join, bergabunglah terlebih dahulu
4. Klik "✅ Sudah Join" setelah bergabung

### 2. Menambahkan Utang
Format: `Nama | Jumlah | Tanggal | Jam | Catatan`

**Contoh:**
```
John Doe | 100k | 2025/12/20 | 12:30 | Utang makan siang
```

**Penjelasan:**
- **Nama**: Nama penghutang
- **Jumlah**: Jumlah utang (contoh: 100k, 50000, 1.5jt)
- **Tanggal**: Tanggal jatuh tempo (format: YYYY/MM/DD) *opsional*
- **Jam**: Waktu notifikasi (format: HH:MM) *opsional*
- **Catatan**: Keterangan tambahan *opsional*

### 3. Menu Utama
```
➕ Tambah Utang     - Tambahkan utang baru
🗑️ Hapus Utang     - Hapus utang yang sudah lunas
📋 Daftar Utang    - Lihat semua utang yang tercatat
⏸️ Jeda Notifikasi - Atur interval pengingat
❓ Panduan         - Petunjuk penggunaan
💝 Support Dev     - Dukung pengembangan bot
⬅️ Kembali         - Kembali ke menu utama
```

### 4. Sistem Notifikasi
- 🔔 Notifikasi akan dikirim saat jatuh tempo
- ⏰ Interval bisa diatur (default: 5 menit)
- ✅ Konfirmasi dengan tombol "Sudah Dibayar" atau "Tunda 1 Jam"
- 🔕 Bisa dimatikan dengan mengatur interval ke 0

## 👑 Fitur Owner

### Perintah Owner
```bash
/owner         - Menu perintah owner
/stats         - Statistik bot lengkap
/backupuser    - Backup data semua user
/broadcast     - Broadcast pesan ke semua user (reply pesan)
/addjoin       - Tambah group wajib join
/listjoin      - Lihat daftar group wajib join
/deljoin       - Hapus group wajib join
/statsjoin     - Statistik user yang sudah join
```

### Contoh Penggunaan Owner
```bash
# Broadcast pesan
1. Kirim pesan ke bot
2. Reply pesan tersebut dengan /broadcast

# Menambahkan group wajib join
/addjoin @testchannel

# Melihat statistik
/stats
```

## 🛠️ Teknologi

### **Backend**
- ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) - Bahasa pemrograman utama
- ![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20.7+-orange) - Library Telegram Bot API
- ![JSON](https://img.shields.io/badge/JSON-Database-lightgrey) - Penyimpanan data

### **Libraries Utama**
- `python-telegram-bot` - Interface untuk Telegram Bot API
- `python-dotenv` - Manajemen environment variables
- `schedule` - Penjadwalan notifikasi

### **Fitur Teknis**
- ✅ **Multi-user Support** - Support ribuan user sekaligus
- 🔄 **Background Processing** - Notifikasi berjalan di background thread
- 💾 **File-based Database** - Tidak perlu setup database server
- 🔒 **Error Handling** - Sistem error handling yang robust
- 📱 **Responsive Design** - Antarmuka yang optimal untuk mobile

## 🤝 Berkontribusi

Kontribusi sangat diterima! Berikut cara berkontribusi:

1. **Fork** repository ini
2. **Clone** fork Anda:
   ```bash
   git clone https://github.com/your-username/kapan-bayar-bot.git
   ```
3. **Buat branch** untuk fitur baru:
   ```bash
   git checkout -b feature/namafitur
   ```
4. **Commit** perubahan Anda:
   ```bash
   git commit -m 'Tambahkan fitur baru'
   ```
5. **Push** ke branch:
   ```bash
   git push origin feature/namafitur
   ```
6. **Buat Pull Request**

### Area yang Membutuhkan Kontribusi
- 🌐 **Translations** - Terjemahan ke bahasa lain
- 🐛 **Bug Fixes** - Perbaikan bug yang ditemukan
- ✨ **New Features** - Fitur-fitur baru yang berguna
- 📚 **Documentation** - Perbaikan dan penambahan dokumentasi
- 🎨 **UI/UX Improvements** - Perbaikan antarmuka pengguna

### Pedoman Kontribusi
1. Ikuti standar kode Python (PEP 8)
2. Tambahkan komentar yang jelas pada kode baru
3. Update dokumentasi jika diperlukan
4. Test kode Anda sebelum submit
5. Gunakan commit message yang deskriptif

## 📄 Lisensi

Proyek ini dilisensikan di bawah **Lisensi MIT** - lihat file [LICENSE](LICENSE) untuk detail lengkap.

```
MIT License

Copyright (c) 2024 [Nama Anda]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Penghargaan

### Terima Kasih Kepada
- **Telegram** untuk platform Bot API yang luar biasa
- **Komunitas Python-Telegram-Bot** untuk library yang powerful
- **Semua Kontributor** yang telah membantu pengembangan bot ini
- **Pengguna Bot** untuk feedback dan dukungannya

### Dukung Pengembangan
Jika Anda merasa bot ini berguna, pertimbangkan untuk:
- ⭐ **Star** repository ini di GitHub
- 🐛 **Report bugs** atau beri saran fitur
- 💝 **Donasi** melalui menu Support dalam bot
- 📢 **Share** dengan teman dan komunitas

### Kontak Developer
- 📧 Email: developer@example.com
- 💬 Telegram: [@username](https://t.me/username)
- 🐙 GitHub: [@username](https://github.com/username)

---

<p align="center">
  <strong>Dibuat dengan ❤️ untuk membantu mengelola keuangan dengan lebih baik</strong>
  <br>
  <sub>Jangan lupa bayar utang tepat waktu! 💸</sub>
</p>

<p align="center">
  <a href="https://github.com/username/kapan-bayar-bot/stargazers">
    <img src="https://img.shields.io/github/stars/username/kapan-bayar-bot?style=social" alt="GitHub Stars">
  </a>
  <a href="https://github.com/username/kapan-bayar-bot/forks">
    <img src="https://img.shields.io/github/forks/username/kapan-bayar-bot?style=social" alt="GitHub Forks">
  </a>
  <a href="https://github.com/username/kapan-bayar-bot/issues">
    <img src="https://img.shields.io/github/issues/username/kapan-bayar-bot?color=blue" alt="GitHub Issues">
  </a>
  <a href="https://github.com/username/kapan-bayar-bot/pulls">
    <img src="https://img.shields.io/github/issues-pr/username/kapan-bayar-bot?color=blue" alt="GitHub Pull Requests">
  </a>
</p>

---

**Disclaimer**: Bot ini dibuat untuk membantu mengingatkan pembayaran utang. Developer tidak bertanggung jawab atas kerugian finansial atau masalah lainnya yang timbul dari penggunaan bot ini. Gunakan dengan bijak dan sesuai kebutuhan.
