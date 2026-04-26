"""
setup_group.py — Jalankan SEKALI untuk daftarkan grup internal ke database.

Cara pakai:
1. Pastikan kedua bot sudah dimasukkan ke grup internal Telegram
2. Jalankan: python setup_group.py
3. Masukkan ID grup saat diminta (lihat cara dapat ID di bawah)

Cara dapat Group ID:
- Tambahkan @userinfobot ke grup, lalu kirim pesan sembarang
- Atau forward pesan dari grup ke @userinfobot
- ID grup biasanya diawali tanda minus, contoh: -1001234567890
"""

import asyncio
import aiosqlite

PM_DB = "/tmp/kotakaipm.db"
SALES_DB = "/tmp/kotakai.db"

async def set_setting(db_path, key, value):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()
    print(f"  Tersimpan di {db_path}: {key} = {value}")

async def main():
    print("=" * 50)
    print("SETUP GRUP INTERNAL KOTAKCODE BOTS")
    print("=" * 50)
    print()

    group_id = input("Masukkan Group ID (contoh: -1001234567890): ").strip()
    if not group_id:
        print("Group ID tidak boleh kosong!")
        return

    if not group_id.startswith("-"):
        print("Peringatan: Group ID biasanya diawali tanda minus (-)")
        konfirm = input("Lanjutkan? (y/n): ").strip().lower()
        if konfirm != "y":
            return

    print()
    print("Menyimpan ke database PM Bot...")
    await set_setting(PM_DB, "internal_group_id", group_id)

    print("Menyimpan ke database Sales Bot...")
    await set_setting(SALES_DB, "internal_group_id", group_id)

    print()
    print("=" * 50)
    print("SELESAI! Grup internal berhasil didaftarkan.")
    print()
    print("Sekarang kedua bot bisa:")
    print("- Kirim notif lead/support ke grup otomatis")
    print("- Auto reply satu sama lain jika konteksnya relevan")
    print()
    print("Pastikan kedua bot sudah ada di grup dan punya izin kirim pesan!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
