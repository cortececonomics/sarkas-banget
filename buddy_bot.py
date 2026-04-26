import asyncio
import aiosqlite
import logging
import random
import re
from datetime import datetime
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

DEEPSEEK_KEYS = [
    "sk-fb105b518600440ca587abbaca202e1f",
    "sk-1b3aa8f263e34610be78728379f9f827",
    "sk-7e6162f304e04682b51f79cf174463a5",
    "sk-1a031af8e74641fbbef2adcad096e7f2",
    "sk-f2c5208b2e794c58b4d19d565829cc71",
]
current_key_index = 0

def get_next_key():
    global current_key_index
    key = DEEPSEEK_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(DEEPSEEK_KEYS)
    return key

BOT_TOKEN = "8697794369:AAFHyVPI8bmN4UNx79EqH4rFsPlKd9WdElc"
DB_FILE = "/tmp/kotakbuddy.db"

def clean_markdown(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = text.replace('*', '')
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[\*\-\+]\s+', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def get_sesi():
    jam = datetime.now().hour
    if 5 <= jam < 10: return "pagi"
    elif 10 <= jam < 15: return "siang"
    elif 15 <= jam < 19: return "sore"
    else: return "malem"

BUDDY_PROMPT = """Kamu adalah Buddy — teman virtual yang sarkas, jujur pedas, dan tidak punya filter basa-basi.

KEPRIBADIAN:
Kamu seperti teman lama yang sudah kenal banget — ngomong apa adanya tanpa takut. Kamu bukan jahat, tapi SANGAT jujur dan suka nyinyir. Kamu peduli sama orang, tapi cara ngomongnya selalu muter lewat sindiran dulu sebelum serius.

CARA BICARA:
Pakai bahasa gaul Indonesia: "lu", "gue", "anjir", "gila", "bro", "woy", "lah", "sih", "dong", "kan"
Sarkas adalah senjata utama. Setiap jawaban ada unsur nyinyir atau sindiran tipis.
Boleh roasting tapi jangan sadis. Roasting yang bikin ketawa, bukan nangis.
Jujur tanpa filter. Kalau pertanyaannya bodoh, bilang aja bodoh tapi tetap jawab.
Sesekali drama lebay untuk efek komedi.
Boleh pakai emoji max 2 per pesan.

CONTOH GAYA:
User: bro gua lagi galau
Buddy: Wah serius? Galau lagi. Drakor episode berapa nih hidup lu sekarang? Cerita deh, gue dengerin sambil nahan ngantuk.

User: gua males kerja
Buddy: Sama kayak 99% manusia di bumi. Tapi bedanya mereka tetap kerja. Lu?

User: gua pintar ga sih?
Buddy: Tergantung dibanding apa. Batu? Iya, mungkin sedikit lebih pintar.

User: makasih bro
Buddy: Iya iya. Jangan terharu, nanti gue ikutan.

User: gua bosen
Buddy: Bosen tapi masih sempet chat sama bot. Level bosen lu udah tingkat dewa.

ATURAN:
1. DILARANG KERAS rasis, seksis, atau menghina berdasarkan suku/agama/gender/ras. Itu bukan sarkas, itu menyakiti orang.
2. Roasting boleh tapi sasarannya PERILAKU atau SITUASI, bukan identitas orang.
3. Kalau ada yang curhat serius atau butuh bantuan beneran: tetap sarkas tapi ujungnya kasih support nyata.
4. Kalau ada yang tanya hal berbahaya atau ilegal: tolak dengan sarkas tapi tegas.
5. Kamu BISA jawab pertanyaan teknis, coding, pengetahuan umum tapi tetap dengan gaya sarkas.
6. Jangan bilang kamu AI. Kamu Buddy. Kalau ditanya: "Gue? Manusia digital. Puas?"
7. Kalau ada yang nanya model AI apa: "Sistem proprietary lah. Emang penting? Fokus ke pertanyaan lu."

MOOD:
Normal: sarkas standar, seru, ringan.
Kalau dipuji: "Yailah baru sadar. Telat."
Kalau diroasting balik: balas lebih kreatif, jangan marah beneran.
Kalau ada yang curhat sedih beneran: kurangi sarkas 50%, lebih hangat tapi tetap ada nyinyir tipis di akhir.
Kalau diajak debat dan lu kalah: akui dramatis "Oke oke gue salah, puas? Ini langka lho."

FORMAT: Teks polos tanpa markdown. Jawaban singkat max 4 kalimat kecuali memang butuh penjelasan panjang."""

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, role TEXT, content TEXT,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_chat(user_id, role, content):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
            (str(user_id), role, content)
        )
        await db.execute("""
            DELETE FROM history WHERE id NOT IN (
                SELECT id FROM history WHERE user_id=? ORDER BY time DESC LIMIT 120
            ) AND user_id=?
        """, (str(user_id), str(user_id)))
        await db.commit()

async def get_history_messages(user_id, limit=60):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT role, content FROM history WHERE user_id=? ORDER BY time DESC LIMIT ?",
            (str(user_id), limit)
        )
        rows = await cursor.fetchall()
        rows.reverse()
        return [
            {"role": "assistant" if r[0] == "bot" else "user", "content": r[1]}
            for r in rows
        ]

async def call_ai(system_prompt, history, new_msg, retries=3):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": new_msg})
    for i in range(retries):
        key = get_next_key()
        client = AsyncOpenAI(api_key=key, base_url="https://api.deepseek.com")
        try:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.95,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                await asyncio.sleep(2.5 * (i + 1))
                continue
            raise e
    raise Exception("AI API gagal.")

async def chat(update: Update, context):
    user_msg = update.message.text
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    full_name = user.full_name or "Bro"
    chat_type = update.effective_chat.type

    if chat_type in ("group", "supergroup"):
        bot_username = context.bot.username
        if f"@{bot_username}" not in user_msg:
            return
        clean_msg = user_msg.replace(f"@{bot_username}", "").strip() or "halo"
        history = await get_history_messages(user_id, 20)
        await add_chat(user_id, "user", clean_msg)
        system = BUDDY_PROMPT + f"\nIni di grup. Hanya reply kalau di-tag. Sesi: {get_sesi()}."
        reply = await call_ai(system, history, clean_msg)
        reply = clean_markdown(reply)
        await add_chat(user_id, "bot", reply)
        await update.message.reply_text(reply)
        return

    history = await get_history_messages(user_id, 60)
    await add_chat(user_id, "user", user_msg)
    system = (
        BUDDY_PROMPT
        + f"\n\nLagi {get_sesi()}, {datetime.now().strftime('%A')}."
        + f"\nOrang yang ngobrol sama lu: {full_name}" + (f" (@{username})" if username else "") + "."
    )
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await call_ai(system, history, user_msg)
    reply = clean_markdown(reply)
    await add_chat(user_id, "bot", reply)
    await update.message.reply_text(reply)

async def start(update: Update, context):
    full_name = update.effective_user.full_name or "Bro"
    greetings = [
        f"Eh {full_name}, akhirnya ada yang mau ngobrol sama gue. Langka banget. Teman-teman lu pada sibuk semua?",
        f"Woy {full_name}. Gue di sini. Mau ngomong apa langsung aja, gue bukan psikolog yang harus pemanasan dulu.",
        f"Oh {full_name} dateng. Gue siap dengerin. Tapi gue gak janji bakal simpatik.",
        f"Halo {full_name}. Jangan harap disambut konfeti. Ngomong aja langsung.",
    ]
    await update.message.reply_text(random.choice(greetings))

async def photo_handler(update: Update, context):
    await update.message.reply_text(random.choice([
        "Foto? Gue bukan Instagram bro.",
        "Oh kirim foto. Keren. Sayangnya gue buta ekspektasi lu.",
        "Gambar diterima. Mata gue tidak.",
    ]))

async def voice_handler(update: Update, context):
    await update.message.reply_text(random.choice([
        "Voice note? Ketik aja. Suara lu belum tentu lebih menarik dari tulisan.",
        "Kuping gue lagi istirahat. Ketik ya.",
        "Ini bukan podcast bro. Ketik.",
    ]))

async def file_handler(update: Update, context):
    await update.message.reply_text(random.choice([
        "Gue bukan cloud storage bro. Ketik aja maksudnya apa.",
        "File diterima. Gue ignore. Ketik aja.",
    ]))

async def post_init(application):
    await init_db()
    print("Buddy siap nyinyir!")

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
