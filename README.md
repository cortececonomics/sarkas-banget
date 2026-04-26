# Kotakcode Bots — Panduan Setup & Deploy

Dua bot Telegram untuk Kotakcode:
- main_pm.py   -> KotakAI (Technical Support Bot)
- main.py      -> Kira (Sales & Customer Service Bot)

Keduanya bisa saling reply di grup internal secara otomatis.

---

## STRUKTUR FILE

kotakcode_bots/
|-- main_pm.py       Bot teknis (KotakAI)
|-- main.py          Bot sales (Kira)
|-- requirements.txt Library yang dibutuhkan
|-- setup_group.py   Script setup grup internal (jalankan sekali)
|-- README.md        File ini

---

## CARA INSTALL

1. Install Python 3.10 atau lebih baru

2. Install dependencies:
   pip install -r requirements.txt

3. Jalankan kedua bot di terminal terpisah:
   python main_pm.py
   python main.py

---

## SETUP GRUP INTERNAL

Grup internal adalah grup Telegram khusus tim Kotakcode
tempat kedua bot berinteraksi satu sama lain.

Langkah-langkah:
1. Buat grup Telegram baru (contoh: "Kotakcode Internal")
2. Masukkan @NgabRizal, @kotakcode, dan kedua bot ke grup
3. Berikan izin bot untuk kirim pesan di grup
4. Pastikan kedua bot sudah berjalan
5. Jalankan: python setup_group.py
6. Masukkan Group ID saat diminta

Cara dapat Group ID:
- Tambahkan @userinfobot ke grup, kirim pesan sembarang
- Group ID biasanya diawali minus, contoh: -1001234567890

---

## CARA DAPAT GROUP ID ALTERNATIF

1. Buka Telegram Web (web.telegram.org)
2. Klik grup internal
3. Lihat URL: https://web.telegram.org/k/#-1001234567890
4. Angka setelah # adalah Group ID (tambahkan minus di depan)

---

## CARA KERJA CROSS-BOT DI GRUP

Skenario 1 — Lead masuk ke Sales Bot:
  Klien chat Kira -> Kira detect lead HOT
  -> Kira kirim notif ke grup internal
  -> PM Bot (KotakAI) baca notif
  -> Jika ada kata kunci teknis, PM Bot auto reply di grup
  -> Tim bisa langsung diskusi

Skenario 2 — Support teknis eskalasi ke PM Bot:
  Klien chat KotakAI -> masalah kompleks
  -> KotakAI kirim laporan ke grup internal
  -> Kira baca laporan
  -> Jika ada kata kunci sales/bisnis, Kira auto reply di grup
  -> Tim bisa koordinasi tindak lanjut

Skenario 3 — Tag manual di grup:
  Anggota tim ketik @namabot [pesan]
  -> Bot yang di-tag langsung reply
  -> Bot lain tidak ikut campur kecuali ada trigger relevan

---

## FITUR TIAP BOT

KotakAI (main_pm.py) — Technical Support:
  - Jawab pertanyaan teknis: error, bug, kode, arsitektur
  - Analisis file kode yang dikirim klien
  - Eskalasi ke founder jika butuh pair programming
  - Ingat konteks percakapan (60 pesan terakhir)

Kira (main.py) — Sales & CS:
  - Handle inquiry klien dengan teknik sales natural
  - Track lead otomatis (WARM -> HOT)
  - /clients  -> lihat daftar klien yang pernah chat
  - /leads    -> lihat daftar leads dan statusnya
  - Cek "ada klien?" untuk lihat aktivitas 24 jam terakhir
  - Ingat konteks percakapan per klien

---

## DEPLOY KE VPS (Opsional)

Agar bot jalan terus 24/7 di VPS:

Install PM2:
  npm install -g pm2

Jalankan bot dengan PM2:
  pm2 start main_pm.py --name kotakai-pm --interpreter python3
  pm2 start main.py --name kotakai-sales --interpreter python3

Auto start saat server reboot:
  pm2 startup
  pm2 save

Cek status:
  pm2 status

Lihat log:
  pm2 logs kotakai-pm
  pm2 logs kotakai-sales

---

## CATATAN PENTING

- Jangan ubah BOT_TOKEN dan DEEPSEEK_KEYS
- Kedua bot pakai database terpisah (/tmp/kotakaipm.db dan /tmp/kotakai.db)
- Folder /tmp akan reset saat server restart — pindahkan DB_FILE ke folder permanen jika perlu
- Untuk production: ganti /tmp/kotakaipm.db -> /home/user/kotakaipm.db

Contoh ganti lokasi database (opsional):
  Di main_pm.py baris DB_FILE: ubah "/tmp/kotakaipm.db" -> "/home/user/kotakaipm.db"
  Di main.py baris DB_FILE: ubah "/tmp/kotakai.db" -> "/home/user/kotakai.db"
  Lakukan hal yang sama di setup_group.py

---

Dibuat untuk Kotakcode oleh KotakAI
