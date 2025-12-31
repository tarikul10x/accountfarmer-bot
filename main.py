import asyncio
import os
import random
import string
import datetime
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest
import aiosqlite
import sqlite3

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))


db_lock = asyncio.Lock()

async def get_db_connection():
    def connect():
        conn = sqlite3.connect(DB_NAME, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    return await asyncio.to_thread(connect)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

DB_NAME = "bot.db"
BACKUP_NAME = "bot_backup.db"
USD_RATE = 124

class States(StatesGroup):
    waiting_file = State()
    withdraw_method = State()
    withdraw_number = State()
    withdraw_amount = State()
    random_gmail_done = State()
    reject_reason = State()
    support_ticket = State()

class AdminStates(StatesGroup):
    screenshot_wait = State()   # এপ্রুভ করার পর স্ক্রিনশট চাইবে
    reject_reason = State()     # রিজেক্ট করার পর রিজন চাইবে
# ট্রান্সলেশন ডিকশনারি (সকল ভাষায় টেক্সট)

LANGUAGES = {
    'bn': {'name': '🇧🇩 বাংলা', 'welcome': '🌟 স্বাগতম! ফাইল শেয়ার করে আয় করুন।'},
    'en': {'name': '🇺🇸 English', 'welcome': '🌟 Welcome! Earn by sharing files.'},
    'ur': {'name': '🇵🇰 اردو', 'welcome': '🌟 خوش آمدید!'},
    'vi': {'name': '🇻🇳 Tiếng Việt', 'welcome': '🌟 Chào mừng!'}
}

TEXTS = {
    'welcome': {
        'bn': '🌟 স্বাগতম! ফাইল শেয়ার করে আয় করুন।',
        'en': '🌟 Welcome! Earn by sharing files.',
        'ur': '🌟 خوش آمدید! فائلز شیئر کرکے کمائیں۔',
        'vi': '🌟 Chào mừng! Kiếm tiền bằng chia sẻ file.'
    },
    'select_language': {
        'bn': 'ভাষা সিলেক্ট করুন:',
        'en': 'Select Language:',
        'ur': 'زبان منتخب کریں:',
        'vi': 'Chọn ngôn ngữ:'
    },
    'main_menu_title': {
        'bn': '🏠 মেইন মেনু',
        'en': '🏠 Main Menu',
        'ur': '🏠 مین مینو',
        'vi': '🏠 Menu chính'
    },
    'send_files': {
        'bn': '📤 Send Files / Coins',
        'en': '📤 Send Files / Coins',
        'ur': '📤 فائلیں / کوائنز بھیجیں',
        'vi': '📤 Gửi Files / Coins'
    },
    'today_rate': {
        'bn': '💰 আজকের রেট',
        'en': '💰 Today\'s Rate',
        'ur': '💰 آج کی ریٹ',
        'vi': '💰 Tỷ giá hôm nay'
    },
    'files': {
        'bn': '📁 Files',
        'en': '📁 Files',
        'ur': '📁 فائلیں',
        'vi': '📁 Files'
    },
    'balance': {
        'bn': '💳 Balance',
        'en': '💳 Balance',
        'ur': '💳 بیلنس',
        'vi': '💳 Số dư'
    },
    'referral': {
        'bn': '👥 Referral',
        'en': '👥 Referral',
        'ur': '👥 ریفرل',
        'vi': '👥 Giới thiệu'
    },
    'withdraw': {
        'bn': '💸 Withdraw',
        'en': '💸 Withdraw',
        'ur': '💸 ودرو',
        'vi': '💸 Rút tiền'
    },
    'settings': {
        'bn': '⚙️ Settings',
        'en': '⚙️ Settings',
        'ur': '⚙️ سیٹنگز',
        'vi': '⚙️ Cài đặt'
    },
    'leaderboard': {
        'bn': '🏆 Leaderboard',
        'en': '🏆 Leaderboard',
        'ur': '🏆 لیڈربورڈ',
        'vi': '🏆 Bảng xếp hạng'
    },
    'support': {
        'bn': '🆘 Support',
        'en': '🆘 Support',
        'ur': '🆘 سپورٹ',
        'vi': '🆘 Hỗ trợ'
    },
    'home': {
        'bn': '🏠 Home',
        'en': '🏠 Home',
        'ur': '🏠 ہوم',
        'vi': '🏠 Trang chủ'
    },
    'back': {
        'bn': '🔙 Back',
        'en': '🔙 Back',
        'ur': '🔙 واپس',
        'vi': '🔙 Quay lại'
    },
    'select_category': {
        'bn': 'ক্যাটাগরি সিলেক্ট করুন:',
        'en': 'Select Category:',
        'ur': 'زمرہ منتخب کریں:',
        'vi': 'Chọn danh mục:'
    },
    'send_file_prompt': {
        'bn': 'ফাইল বা স্ক্রিনশট পাঠান।',
        'en': 'Send file or screenshot.',
        'ur': 'فائل یا اسکرین شاٹ بھیجیں۔',
        'vi': 'Gửi file hoặc ảnh chụp màn hình.'
    },
    'coin_user_prompt': {
        'bn': 'ইউজার:',
        'en': 'User:',
        'ur': 'یوزر:',
        'vi': 'Người dùng:'
    },
    'random_gmail_title': {
        'bn': '🔐 র‍্যান্ডম জিমেইল সাজেস্ট',
        'en': '🔐 Random Gmail Suggestions',
        'ur': '🔐 رینڈم جی میل تجاویز',
        'vi': '🔐 Gợi ý Gmail ngẫu nhiên'
    },
    'random_gmail_desc': {
        'bn': 'এগুলো দিয়ে জিমেইল তৈরি করুন। তৈরি হয়ে গেলে <b>Done</b> ক্লিক করুন।',
        'en': 'Use these to create Gmail. Click <b>Done</b> when finished.',
        'ur': 'ان کو استعمال کرکے جی میل بنائیں۔ مکمل ہونے پر <b>Done</b> کلک کریں۔',
        'vi': 'Sử dụng những cái này để tạo Gmail. Khi hoàn tất, nhấn <b>Done</b>.'
    },
    'pc_clone_prompt': {
        'bn': 'PC Clone টাইপ সিলেক্ট করুন:',
        'en': 'Select PC Clone Type:',
        'ur': 'پی سی کلون ٹائپ منتخب کریں:',
        'vi': 'Chọn loại PC Clone:'
    },
    'file_sent': {
        'bn': '✅ ফাইল সফলভাবে এডমিনের কাছে পাঠানো হয়েছে।',
        'en': '✅ File successfully sent to admin.',
        'ur': '✅ فائل کامیابی سے ایڈمن کو بھیج دی گئی۔',
        'vi': '✅ File đã được gửi thành công đến admin.'
    },
    'approve_notification': {
        'bn': '🎉 আপনার ফাইল এপ্রুভ হয়েছে। Waiting for report।',
        'en': '🎉 Your file has been approved. Waiting for report.',
        'ur': '🎉 آپ کی فائل منظور ہوگئی۔ رپورٹ کا انتظار ہے۔',
        'vi': '🎉 File của bạn đã được duyệt. Đang chờ báo cáo.'
    },
    'reject_notification': {
        'bn': '❌ আপনার ফাইল রিজেক্ট হয়েছে। কারণ:',
        'en': '❌ Your file has been rejected. Reason:',
        'ur': '❌ آپ کی فائل مسترد ہوگئی۔ وجہ:',
        'vi': '❌ File của bạn đã bị từ chối. Lý do:'
    },
    'withdraw_method': {
        'bn': 'মেথড সিলেক্ট করুন:',
        'en': 'Select Method:',
        'ur': 'طریقہ منتخب کریں:',
        'vi': 'Chọn phương thức:'
    },
    'withdraw_number': {
        'bn': 'নম্বর দিন:',
        'en': 'Enter Number:',
        'ur': 'نمبر درج کریں:',
        'vi': 'Nhập số:'
    },
    'withdraw_amount': {
        'bn': 'অ্যামাউন্ট লিখুন (মিনিমাম ৫০ টাকা):',
        'en': 'Enter Amount (Minimum 50 BDT):',
        'ur': 'رقم درج کریں (کم از کم 50 ٹکا):',
        'vi': 'Nhập số tiền (Tối thiểu 50 BDT):'
    },
    'withdraw_success': {
        'bn': '✅ রিকোয়েস্ট পাঠানো হয়েছে।',
        'en': '✅ Request sent successfully.',
        'ur': '✅ درخواست کامیابی سے بھیج دی گئی۔',
        'vi': '✅ Yêu cầu đã được gửi thành công.'
    }
}

# ট্রান্সলেশন ফাংশন

async def t(user_id, key):
    db = await get_db_connection()
    try:
        cursor = await asyncio.to_thread(db.execute, "SELECT language FROM users WHERE user_id = ?", (user_id,))
        row = await asyncio.to_thread(cursor.fetchone)
        lang = row[0] if row else 'bn'
    except Exception:
        lang = 'bn'  # যদি ডাটাবেস এরর হয় তাহলে ডিফল্ট bn
    finally:
        db.close()

    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get('bn', key))

MAIN_CATEGORIES = ["Facebook", "Instagram", "Coins", "Gmail", "Others"]

SUB_CATEGORIES = {
    "Facebook": ["Webmail", "Anymail", "Number", "PC Clone Cookies", "Others"],
    "Instagram": ["Instagram Cookies", "Instagram 2FA"],
    "Coins": ["Niva Coin", "NS Coin", "Topfollow", "Nitra Coin", "Others"],
    "Gmail": ["Gmail Files", "Random Gmail"],
    "Others": ["Other Files"]
}

PC_CLONE_SUB = ["PC Clone 1000x", "6155/56x Cookies"]

async def init_db():
    def setup_db():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'bn',
                pending INTEGER DEFAULT 0,
                reported INTEGER DEFAULT 0,
                approved INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0,
                earnings_bdt REAL DEFAULT 0,
                earnings_usd REAL DEFAULT 0,
                payment_method TEXT,
                payment_number TEXT,
                referrer INTEGER,
                last_login DATE
            );
            -- বাকি টেবিলগুলো...
        ''')

        try:
            conn.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # ইতিমধ্যে থাকলে ইগনোর

        for main in MAIN_CATEGORIES:
            for sub in SUB_CATEGORIES.get(main, []):
                full = f"{main}_{sub}"
                conn.execute("INSERT OR IGNORE INTO rates (category, rate_bdt) VALUES (?, 5)", (full,))
                conn.execute("INSERT OR IGNORE INTO toggles (item, enabled) VALUES (?, 1)", (full,))

        conn.commit()
        conn.close()

    await asyncio.to_thread(setup_db)

async def get_user(user_id):
    db = await get_db_connection()
    try:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_user(user_id, username, full_name, referrer=None):
    db = await get_db_connection()
    try:
        await asyncio.to_thread(db.execute,"INSERT OR IGNORE INTO users (user_id, username, full_name, referrer) VALUES (?, ?, ?, ?)", (user_id, username, full_name, referrer))
        asyncio.to_thread(db.commit)
    if referrer:
        await give_refer_bonus(user_id)
    finally:
        db.close()
async def get_rate(full_cat):
    db = await get_db_connection()
    try:
        async with db.execute("SELECT rate_bdt FROM rates WHERE category = ?", (full_cat,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 5
    finally:
        db.close()
async def is_enabled(full_cat):
    db = await get_db_connection()
    try:
        async with db.execute("SELECT enabled FROM toggles WHERE item = ?", (full_cat,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1
    finally:
        db.close()
async def get_coin_user():
    return "genzraiyaan"

def main_menu():
    kb = [
        [InlineKeyboardButton(text="📤 Send Files / Coins", callback_data="send_files")],
        [InlineKeyboardButton(text="💰 Today Rate", callback_data="today_rate")],
        [InlineKeyboardButton(text="📁 Files", callback_data="files_menu")],
        [InlineKeyboardButton(text="💳 Balance", callback_data="balance_menu")],
        [InlineKeyboardButton(text="👥 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="💸 Withdraw", callback_data="withdraw_start")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton(text="🆘 Support", url="https://t.me/teamraiyaan")],
        [InlineKeyboardButton(text="📊 My Stats", callback_data="mystats")],
        [InlineKeyboardButton(text="🏠 Home", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_home_kb():
    return [
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")],
        [InlineKeyboardButton(text="🏠 Home", callback_data="main_menu")]
    ]

def back_home():
    return InlineKeyboardMarkup(inline_keyboard=back_home_kb())

@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    referrer = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    await add_user(message.from_user.id, message.from_user.username, message.from_user.full_name, referrer)
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    welcome_text = await t(message.from_user.id, 'welcome')
    ref_text = f"""
আপনার রেফার লিঙ্ক:
{ref_link}

রেফার করে প্রতি জনে ৫ টাকা + ৫ লেভেল MLM বোনাস পান!
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v['name'], callback_data=f"lang_{k}")] for k, v in LANGUAGES.items()
    ])
    select_lang_text = await t(message.from_user.id, 'select_language')
    await message.answer(welcome_text + "\n\n" + ref_text + "\n" + select_lang_text, reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    db = await get_db_connection() try:
        await asyncio.to_thread(db.execute,"UPDATE users SET language = ? WHERE user_id = ?", (lang, call.from_user.id))
        asyncio.to_thread(db.commit)
    welcome = await t(call.from_user.id, 'welcome')
    await call.message.edit_text(welcome, reply_markup=main_menu())
    await call.answer()

@dp.callback_query(F.data == "main_menu")
async def home(call: types.CallbackQuery):
    title = await t(call.from_user.id, 'main_menu_title')
    await call.message.edit_text(title, reply_markup=main_menu())
    await call.answer()

@dp.callback_query(F.data == "send_files")
async def send_files(call: types.CallbackQuery):
    kb = []
    for cat in MAIN_CATEGORIES:
        kb.append([InlineKeyboardButton(text=cat, callback_data=f"maincat_{cat}")])
    kb.extend(back_home_kb())
    select_cat = await t(call.from_user.id, 'select_category')
    await call.message.edit_text(select_cat, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data.startswith("maincat_"))
async def main_cat_selected(call: types.CallbackQuery):
    cat = call.data.split("_")[1]
    kb = []
    for sub in SUB_CATEGORIES.get(cat, []):
        full = f"{cat}_{sub}"
        if await is_enabled(full):
            kb.append([InlineKeyboardButton(text=sub, callback_data=f"subcat_{full}")])
    kb.extend(back_home_kb())
    await call.message.edit_text(f"{cat} সাবক্যাটাগরি:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data.startswith("subcat_"))
async def sub_cat_selected(call: types.CallbackQuery, state: FSMContext):
    full_cat = call.data.split("_", 1)[1]
    await state.update_data(category=full_cat)

    if "PC Clone Cookies" in full_cat:
        kb = []
        for sub in PC_CLONE_SUB:
            kb.append([InlineKeyboardButton(text=sub, callback_data="ready_send")])
        kb.extend(back_home_kb())
        pc_prompt = await t(call.from_user.id, 'pc_clone_prompt')
        await call.message.edit_text(pc_prompt, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    elif "Random Gmail" in full_cat:
        # শক্তিশালী পাসওয়ার্ডের জন্য ক্যারেক্টার সেট
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        all_chars = lowercase + uppercase + digits + special

        # ১টা র‍্যান্ডম জিমেইল ইউজারনেম (১০-১৫ অক্ষর)
        username_length = random.randint(10, 15)
        username = ''.join(random.choices(lowercase + digits, k=username_length))
        email = f"{username}@gmail.com"

        # খুবই শক্তিশালী পাসওয়ার্ড (১৮-২২ অক্ষর)
        password_length = random.randint(18, 22)
        password = ''.join(random.choices(all_chars, k=password_length))

        # সুন্দর ফরম্যাটে দেখানো
        suggestion_text = (
            f"<b>📧 সাজেস্টেড জিমেইল:</b>\n"
            f"<code>{email}</code>\n\n"
            f"<b>🔐 শক্তিশালী পাসওয়ার্ড:</b>\n"
            f"<code>{password}</code>\n\n"
            f"🔹 এই ইমেইল ও পাসওয়ার্ড দিয়ে জিমেইল তৈরি করুন।\n"
            f"🔹 তৈরি হয়ে গেলে নিচের <b>Done</b> বাটন চাপুন।"
        )

        kb = [
            [InlineKeyboardButton(text="✅ Done", callback_data="gmail_done")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu")]
        ]

        title = await t(call.from_user.id, 'random_gmail_title')
        desc = await t(call.from_user.id, 'random_gmail_desc')

        final_text = f"<b>{title}</b>\n\n{suggestion_text}\n\n{desc}"

        await call.message.edit_text(
            final_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )

    else:
        text = await t(call.from_user.id, 'send_file_prompt')
        if "Coin" in full_cat:
            text += f"\n\n{await t(call.from_user.id, 'coin_user_prompt')} {await get_coin_user()}"
        
        kb = [[InlineKeyboardButton(text="Cancel", callback_data="main_menu")]]
        kb.extend(back_home_kb())
        
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await state.set_state(States.waiting_file)
@dp.callback_query(F.data == "ready_send")
async def ready_send(call: types.CallbackQuery, state: FSMContext):
    text = await t(call.from_user.id, 'send_file_prompt')
    kb = [[InlineKeyboardButton(text="Cancel", callback_data="main_menu")]]
    kb.extend(back_home_kb())
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(States.waiting_file)
    await call.answer()

# কপি ইউজার আইডি বাটন কাজ করবে
@dp.callback_query(F.data.startswith("copyid_"))
async def copy_user_id(call: types.CallbackQuery):
    user_id = call.data.split("_")[1]
    await call.answer(user_id, show_alert=True)

# র‍্যান্ডম জিমেইল Done বাটন কাজ করবে
@dp.callback_query(F.data == "gmail_done")
async def gmail_random_done(call: types.CallbackQuery, state: FSMContext):
    user = call.from_user

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"gmail_approve_{user.id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"gmail_reject_{user.id}")
        ]
    ])

    caption = f"""
📧 <b>র‍্যান্ডম জিমেইল তৈরির রিকোয়েস্ট</b>

👤 ইউজার: {user.full_name}
🆔 আইডি: <code>{user.id}</code>
📛 ইউজারনেম: @{user.username if user.username else 'নেই'}
    """

    await bot.send_message(ADMIN_ID, caption, parse_mode="HTML", reply_markup=admin_kb)

    await call.message.edit_text(
        "✅ আপনার রিকোয়েস্ট এডমিনের কাছে পাঠানো হয়েছে।\n"
        "এপ্রুভ হলে নোটিফিকেশন পাবেন।",
        reply_markup=main_menu()
    )
    await state.clear()
    await call.answer()

from aiogram.exceptions import TelegramBadRequest  # উপরে import যোগ করুন (যদি না থাকে)

@dp.callback_query(F.data.startswith("gmail_approve_"))
async def gmail_approve(call: types.CallbackQuery):
    try:
        user_id = int(call.data.split("_")[2])
    except (IndexError, ValueError):
        await call.answer("ভুল ডেটা।", show_alert=True)
        return

    # ইউজারকে নোটিফিকেশন
    try:
        await bot.send_message(
            user_id,
            "🎉 অভিনন্দন!\n\n"
            "আপনার র‍্যান্ডম জিমেইল রিকোয়েস্ট <b>এপ্রুভ</b> হয়েছে!\n"
            "এখন আপনি ফাইল পাঠাতে পারবেন। ধন্যবাদ! 🌟",
            parse_mode="HTML"
        )
    except:
        pass

    # এডমিন মেসেজে Approved দেখানো (caption থাকলে)
    if call.message.caption:
        current_caption = call.message.caption
        new_caption = current_caption + "\n\n✅ <b>Approved</b>"

        try:
            await call.message.edit_caption(caption=new_caption, parse_mode="HTML")
        except TelegramBadRequest as e:
            if "not modified" not in str(e).lower() and "no caption" not in str(e).lower():
                print(f"Edit caption error: {e}")
    else:
        # caption না থাকলে শুধু টেক্সট edit করুন বা কিছু না করুন
        try:
            await call.message.edit_text(
                (call.message.text or "") + "\n\n✅ <b>Approved</b>",
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "not modified" not in str(e).lower():
                print(f"Edit text error: {e}")

    await call.answer("এপ্রুভ করা হয়েছে। ✅")


@dp.callback_query(F.data.startswith("gmail_reject_"))
async def gmail_reject(call: types.CallbackQuery):
    try:
        user_id = int(call.data.split("_")[2])
    except (IndexError, ValueError):
        await call.answer("ভুল ডেটা।", show_alert=True)
        return

    # ইউজারকে নোটিফিকেশন
    try:
        await bot.send_message(
            user_id,
            "❌ দুঃখিত!\n\n"
            "আপনার র‍্যান্ডম জিমেইল রিকোয়েস্ট <b>রিজেক্ট</b> হয়েছে।\n"
            "আবার চেষ্টা করুন।",
            parse_mode="HTML"
        )
    except:
        pass

    # এডমিন মেসেজে Rejected দেখানো
    if call.message.caption:
        current_caption = call.message.caption
        new_caption = current_caption + "\n\n❌ <b>Rejected</b>"

        try:
            await call.message.edit_caption(caption=new_caption, parse_mode="HTML")
        except TelegramBadRequest as e:
            if "not modified" not in str(e).lower() and "no caption" not in str(e).lower():
                print(f"Edit caption error: {e}")
    else:
        try:
            await call.message.edit_text(
                (call.message.text or "") + "\n\n❌ <b>Rejected</b>",
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "not modified" not in str(e).lower():
                print(f"Edit text error: {e}")

    await call.answer("রিজেক্ট করা হয়েছে। ❌")
@dp.message(States.waiting_file, F.document | F.photo)
async def receive_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    full_cat = data.get("category", "Unknown")
    rate = await get_rate(full_cat)
    user = message.from_user

    # ডাটাবেসে message_id সহ সেভ করা
    db = await get_db_connection() try:
        await asyncio.to_thread(db.execute,"""
            INSERT INTO files 
            (user_id, category, sub_category, status, rate, message_id) 
            VALUES (?, ?, ?, 'pending', ?, ?)
        """, (
            user.id,
            full_cat.split('_')[0],
            full_cat.split('_')[1],
            rate,
            message.message_id
        ))
        await asyncio.to_thread(db.execute,"UPDATE users SET pending = pending + 1 WHERE user_id = ?", (user.id,))
        asyncio.to_thread(db.commit)

    # এডমিনের কাছে বাটন সহ ফরওয়ার্ড
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{message.message_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{message.message_id}")
        ],
        [
            InlineKeyboardButton(text="📋 কপি ইউজার আইডি", callback_data=f"copyid_{user.id}")
        ]
    ])

    caption = f"""
📥 <b>নতুন ফাইল এসেছে</b>

🔹 ক্যাটাগরি: {full_cat}
💰 রেট: {rate} টাকা

👤 ইউজার: {user.full_name}
🆔 আইডি: <code>{user.id}</code>
    """

    if message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)
    else:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)

    file_sent_text = await t(message.from_user.id, 'file_sent')
    await message.answer(file_sent_text, reply_markup=main_menu())
    await state.clear()

# Approve হ্যান্ডলার
@dp.callback_query(F.data.startswith("admin_approvewd_"))
async def admin_approve_withdraw(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[2])
    except:
        await call.answer("ভুল ডেটা।")
        return

    # এখানে আপনার উইথড্র এপ্রুভ লজিক (যেমন /approvewd কমান্ডের মতো)
    db = await get_db_connection()
    try:
        async with db.execute("SELECT amount_bdt FROM withdraw_requests WHERE user_id = ? AND status = 'pending'", (target_user_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            await call.answer("কোনো পেন্ডিং উইথড্র নেই।", show_alert=True)
            return
        amount = row[0]

        # টাকা কাটা + স্ট্যাটাস চেঞ্জ
        await asyncio.to_thread(db.execute,"UPDATE users SET earnings_bdt = earnings_bdt - ? WHERE user_id = ?", (amount, target_user_id))
        await asyncio.to_thread(db.execute,"UPDATE withdraw_requests SET status = 'approved' WHERE user_id = ? AND status = 'pending'", (target_user_id,))
        asyncio.to_thread(db.commit)
       finally:
        db.close()
    # ইউজারকে নোটিফিকেশন
    try:
        await bot.send_message(target_user_id, "✅ আপনার উইথড্র এপ্রুভ হয়েছে। পেমেন্টের স্ক্রিনশট পাঠান।")
    except:
        pass

    await call.message.edit_text(
        call.message.text + f"\n\n✅ <b>উইথড্র এপ্রুভ করা হয়েছে ({amount} টাকা)</b>",
        parse_mode="HTML"
    )
    await call.answer("উইথড্র এপ্রুভ করা হয়েছে।")
    finally:
        db.close()
@dp.callback_query(F.data.startswith("back_to_userstats_"))
async def back_to_userstats(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[3])
    except:
        await call.answer("ভুল ডেটা।")
        return

    # আবার /userstats এর মতো টেক্সট + বাটন দেখানো
    # আপনার পুরোনো /userstats কোডের টেক্সট + বাটন এখানে কপি করুন
    # অথবা সরাসরি /userstats ফাংশন কল করুন (কিন্তু callback থেকে)

    # সিম্পল উপায়: আবার userstats টেক্সট দেখানো
    user = await get_user(target_user_id)
    if not user:
        await call.answer("ইউজার পাওয়া যায়নি।")
        return

    # আপনার /userstats এর টেক্সট + বাটন কপি করুন
    stats_text = f"""
🔍 <b>ইউজার স্ট্যাটাস (এডমিন ভিউ)</b>

🆔 <b>আইডি:</b> <code>{target_user_id}</code>
📛 <b>নাম:</b> {user[2]}
... (বাকি টেক্সট)
    """

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 উইথড্র এপ্রুভ", callback_data=f"admin_approvewd_{target_user_id}")],
        [InlineKeyboardButton(text="📊 ফাইল স্ট্যাটাস", callback_data=f"admin_files_{target_user_id}")],
        [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
    ])

    await call.message.edit_text(stats_text, parse_mode="HTML", reply_markup=kb)
    await call.answer()
@dp.callback_query(F.data.startswith("back_to_userstats_"))
async def back_to_userstats(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[3])
    except:
        await call.answer("ভুল ডেটা।")
        return

    # আবার /userstats এর মতো টেক্সট + বাটন দেখানো
    # আপনার পুরোনো /userstats কোডের টেক্সট + বাটন এখানে কপি করুন
    # অথবা সরাসরি /userstats ফাংশন কল করুন (কিন্তু callback থেকে)

    # সিম্পল উপায়: আবার userstats টেক্সট দেখানো
    user = await get_user(target_user_id)
    if not user:
        await call.answer("ইউজার পাওয়া যায়নি।")
        return

    # আপনার /userstats এর টেক্সট + বাটন কপি করুন
    stats_text = f"""
🔍 <b>ইউজার স্ট্যাটাস (এডমিন ভিউ)</b>

🆔 <b>আইডি:</b> <code>{target_user_id}</code>
📛 <b>নাম:</b> {user[2]}
... (বাকি টেক্সট)
    """

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 উইথড্র এপ্রুভ", callback_data=f"admin_approvewd_{target_user_id}")],
        [InlineKeyboardButton(text="📊 ফাইল স্ট্যাটাস", callback_data=f"admin_files_{target_user_id}")],
        [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
    ])

    await call.message.edit_text(stats_text, parse_mode="HTML", reply_markup=kb)
    await call.answer()
@dp.callback_query(F.data.startswith("approve_"))
async def approve_file(call: types.CallbackQuery):
    try:
        msg_id = int(call.data.split("_")[1])

        db = await get_db_connection() try:
            async with db.execute("SELECT user_id, rate FROM files WHERE message_id = ?", (msg_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await call.answer("⚠️ ফাইল পাওয়া যায়নি।", show_alert=True)
                return
            user_id, rate = row

            await asyncio.to_thread(db.execute,"UPDATE files SET status = 'reported' WHERE message_id = ?", (msg_id,))
            await asyncio.to_thread(db.execute,"UPDATE users SET pending = pending - 1, reported = reported + 1 WHERE user_id = ?", (user_id,))
            asyncio.to_thread(db.commit)

        approve_text = await t(user_id, 'approve_notification')
        await bot.send_message(user_id, approve_text + f" রেট: {rate} টাকা")
        await call.message.edit_caption(caption=call.message.caption + "\n\n✅ <b>Approved!</b>", parse_mode="HTML")
        await call.answer("এপ্রুভ করা হয়েছে।")

    except Exception as e:
        await call.answer("সমস্যা হয়েছে।", show_alert=True)
        print(f"Approve Error: {e}")

# Reject হ্যান্ডলার (কারণ সহ)
@dp.callback_query(F.data.startswith("reject_"))
async def reject_file(call: types.CallbackQuery, state: FSMContext):
    try:
        msg_id = int(call.data.split("_")[1])

        db = await get_db_connection() try:
            async with db.execute("SELECT user_id FROM files WHERE message_id = ?", (msg_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await call.answer("⚠️ ফাইল পাওয়া যায়নি।", show_alert=True)
                return
            user_id = row[0]

        await state.update_data(reject_msg_id=msg_id, reject_user_id=user_id)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Cancel Reject", callback_data="cancel_reject")]
        ])

        await call.message.edit_text("❌ রিজেক্টের কারণ লিখুন:\n\n(লিখে Send করুন)", reply_markup=kb)
        await state.set_state(States.reject_reason)

    except Exception as e:
        await call.answer("সমস্যা হয়েছে।", show_alert=True)

@dp.callback_query(F.data == "cancel_reject")
async def cancel_reject(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("রিজেক্ট ক্যান্সেল করা হয়েছে।")
    await call.answer()

@dp.message(States.reject_reason)
async def reject_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("reject_msg_id")
    user_id = data.get("reject_user_id")
    reason = message.text.strip()

    if not reason:
        await message.answer("কারণ লিখুন।")
        return

    db = await get_db_connection() try:
        await asyncio.to_thread(db.execute,"UPDATE files SET status = 'rejected' WHERE message_id = ?", (msg_id,))
        await asyncio.to_thread(db.execute,"UPDATE users SET pending = pending - 1, rejected = rejected + 1 WHERE user_id = ?", (user_id,))
        asyncio.to_thread(db.commit)

    reject_text = await t(user_id, 'reject_notification')
    await bot.send_message(user_id, reject_text + f" {reason}\nআবার চেষ্টা করুন।")
    await message.answer("রিজেক্ট করা হয়েছে।", reply_markup=main_menu())
    await state.clear()

# Withdraw সেকশন (সাকসেস হলে টাকা কাটবে + ট্রুটি ফ্রি)

# উইথড্র স্টার্ট (মেনু থেকে)
@dp.callback_query(F.data == "withdraw_start")
async def withdraw_start(call: types.CallbackQuery, state: FSMContext):
    kb = [
        [InlineKeyboardButton(text="Bkash", callback_data="wm_bkash")],
        [InlineKeyboardButton(text="Nagad", callback_data="wm_nagad")],
        [InlineKeyboardButton(text="Rocket", callback_data="wm_rocket")],
        [InlineKeyboardButton(text="Binance", callback_data="wm_binance")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]  # ব্যাক বাটন যোগ
    ]
    method_text = await t(call.from_user.id, 'withdraw_method')
    await call.message.edit_text(method_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(States.withdraw_method)
    await call.answer()

# মেথড সিলেক্ট (wm)
@dp.callback_query(F.data.startswith("wm_"))
async def wm(call: types.CallbackQuery, state: FSMContext):
    method = call.data[3:]
    await state.update_data(method=method)
    number_text = await t(call.from_user.id, 'withdraw_number')
    kb = [
        [InlineKeyboardButton(text="🔙 Back to Methods", callback_data="withdraw_start")]  # ব্যাক টু মেথডস
    ]
    kb.extend(back_home_kb())
    await call.message.edit_text(f"{method} {number_text}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(States.withdraw_number)
    await call.answer()

# নম্বর ইনপুট (wn)
@dp.message(States.withdraw_number)
async def wn(message: types.Message, state: FSMContext):
    number = message.text.strip()
    if not number:
        await message.answer("নম্বর লিখুন।")
        return
    await state.update_data(number=number)
    amount_text = await t(message.from_user.id, 'withdraw_amount')
    kb = [
        [InlineKeyboardButton(text="🔙 Back to Number", callback_data="withdraw_start")]  # ব্যাক টু মেথডস (অথবা নম্বর চেঞ্জ)
    ]
    kb.extend(back_home_kb())
    await message.answer(amount_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(States.withdraw_amount)

# অ্যামাউন্ট ইনপুট (wa) — ভ্যালিডেশন + অ্যাডমিন নোটিফিকেশন
@dp.message(States.withdraw_amount)
async def wa(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount < 100:
            amount_text = await t(message.from_user.id, 'withdraw_amount')
            kb = back_home_kb()
            await message.answer("মিনিমাম ১০০ টাকা। আবার লিখুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            return

        user = await get_user(message.from_user.id)
        if not user or amount > user[8]:  # earnings_bdt
            kb = back_home_kb()
            await message.answer("ব্যালেন্সের চেয়ে বেশি নয়। আবার লিখুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            return

        data = await state.get_data()
        db = await get_db_connection() try:
            # রিকোয়েস্ট সেভ
            await asyncio.to_thread(db.execute,"INSERT INTO withdraw_requests (user_id, amount_bdt, method, number) VALUES (?, ?, ?, ?)",
                             (message.from_user.id, amount, data['method'], data['number']))
            asyncio.to_thread(db.commit)

        # এডমিনকে রিকোয়েস্ট + ইউজারের সকল তথ্য + এপ্রুভ/রিজেক্ট বাটন
        user_info = await get_user(message.from_user.id)
        info_text = (
            f"💸 <b>নতুন উইথড্র রিকোয়েস্ট</b>\n\n"
            f"👤 নাম: <b>{user_info[2]}</b>\n"
            f"🆔 আইডি: <code>{message.from_user.id}</code>\n"
            f"📛 ইউজারনেম: @{user_info[1] or 'নেই'}\n"
            f"🌍 ভাষা: {user_info[3].upper()}\n"
            f"💰 ব্যালেন্স: {user_info[8]} টাকা\n"
            f"📁 ফাইল স্ট্যাটাস: পেন্ডিং {user_info[4]}, রিপোর্ট {user_info[5]}, এপ্রুভ {user_info[6]}, রিজেক্ট {user_info[7]}\n\n"
            f"🔹 অ্যামাউন্ট: <b>{amount} টাকা</b>\n"
            f"💳 মেথড: <b>{data['method']}</b>\n"
            f"🔢 নম্বর: <code>{data['number']}</code>\n\n"
            f"ফিচার: রিকোয়েস্ট টাইম {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        admin_kb = [
            [InlineKeyboardButton(text="✅ Approve", callback_data=f"wd_approve_{message.from_user.id}")],
            [InlineKeyboardButton(text="❌ Reject", callback_data=f"wd_reject_{message.from_user.id}")],
            [InlineKeyboardButton(text="📊 View Profile", callback_data=f"profile_{message.from_user.id}")]
        ]

        await bot.send_message(ADMIN_ID, info_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=admin_kb))

        success_text = await t(message.from_user.id, 'withdraw_success')
        await message.answer(success_text, reply_markup=main_menu())
        await state.clear()

    except ValueError:
        kb = back_home_kb()
        await message.answer("সঠিক সংখ্যা লিখুন।", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# Approve হ্যান্ডলার — স্ক্রিনশট চাইবে
@dp.callback_query(F.data.startswith("wd_approve_"))
async def withdraw_approve(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.data.split("_")[2])
    db = await get_db_connection() try:
        async with db.execute("SELECT amount_bdt, method, number FROM withdraw_requests WHERE user_id = ? AND status = 'pending'", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await call.answer("কোনো পেন্ডিং রিকোয়েস্ট নেই।")
                return
            amount, method, number = row

        await asyncio.to_thread(db.execute,"UPDATE withdraw_requests SET status = 'approved' WHERE user_id = ? AND status = 'pending'", (user_id,))
        asyncio.to_thread(db.commit)

    await bot.send_message(call.from_user.id, f"পেমেন্টের স্ক্রিনশট পাঠান ({method}: {number}, {amount} টাকা)")

    await state.update_data(pending_user_id=user_id, wd_amount=amount, wd_method=method, wd_number=number)
    await state.set_state(AdminStates.screenshot_wait)

    await call.message.edit_text(call.message.text + "\n\n✅ <b>Approved! স্ক্রিনশট পাঠান।</b>", parse_mode="HTML")
    await call.answer("এপ্রুভ হয়েছে। স্ক্রিনশট পাঠান।")

# অ্যাডমিন স্ক্রিনশট পেলে ফরওয়ার্ড + কমপ্লিট
@dp.message(AdminStates.screenshot_wait, F.photo)
async def admin_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("pending_user_id")
    amount = data.get("wd_amount")
    if not user_id:
        await message.answer("সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        return

    # স্ক্রিনশট ফরওয়ার্ড
    await bot.forward_message(user_id, message.chat.id, message.message_id)
    await bot.send_message(user_id, f"✅ আপনার {amount} টাকার উইথড্র কমপ্লিট হয়েছে! স্ক্রিনশট দেখুন।")

    # এডমিনকে কনফার্ম
    await message.answer("✅ স্ক্রিনশট ফরওয়ার্ড করা হয়েছে। উইথড্র কমপ্লিট।")

    await state.clear()

# রিজেক্ট হ্যান্ডলার — রিজন চাইবে
@dp.callback_query(F.data.startswith("wd_reject_"))
async def withdraw_reject(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.data.split("_")[2])
    await bot.send_message(call.from_user.id, "রিজেক্টের কারণ লিখুন:")

    await state.update_data(reject_user_id=user_id)
    await state.set_state(AdminStates.reject_reason)

    await call.message.edit_text(call.message.text + "\n\n❌ <b>Rejected! কারণ লিখুন।</b>", parse_mode="HTML")
    await call.answer("রিজেক্ট হয়েছে। কারণ লিখুন।")

# অ্যাডমিন রিজন দিলে ইউজারকে পাঠানো + রিফান্ড (যদি চান)
@dp.message(AdminStates.reject_reason)
async def admin_reject_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    user_id = data.get("reject_user_id")
    if not user_id or not reason:
        await message.answer("কারণ লিখুন।")
        return

    db = await get_db_connection() try:
        async with db.execute("SELECT amount_bdt FROM withdraw_requests WHERE user_id = ? AND status = 'pending'", (user_id,)) as cursor:
            row = await cursor.fetchone()
            amount = row[0] if row else 0

        await asyncio.to_thread(db.execute,"UPDATE withdraw_requests SET status = 'rejected' WHERE user_id = ? AND status = 'pending'", (user_id,))
        # রিফান্ড (টাকা ফিরিয়ে দিন)
        await asyncio.to_thread(db.execute,"UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?", (amount, user_id))
        asyncio.to_thread(db.commit)

    # ইউজারকে রিজন পাঠানো
    await bot.send_message(user_id, f"❌ আপনার উইথড্র রিকোয়েস্ট রিজেক্ট হয়েছে।\nকারণ: {reason}")

    await message.answer("✅ রিজেক্ট + কারণ পাঠানো হয়েছে।")

    await state.clear()

# Withdraw Approve (এডমিন) + টাকা কাটা (পুরোনো কমান্ড — রাখুন যদি চান)
@dp.message(Command("approvewd"), F.from_user.id == ADMIN_ID)
async def approve_wd(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        db = await get_db_connection() try:
            async with db.execute("SELECT amount_bdt FROM withdraw_requests WHERE user_id = ? AND status = 'pending'", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await message.answer("রিকোয়েস্ট পাওয়া যায়নি।")
                return
            amount = row[0]

            # টাকা কাটা + স্ট্যাটাস চেঞ্জ
            await asyncio.to_thread(db.execute,"UPDATE users SET earnings_bdt = earnings_bdt - ? WHERE user_id = ?", (amount, user_id))
            await asyncio.to_thread(db.execute,"UPDATE withdraw_requests SET status = 'approved' WHERE user_id = ? AND status = 'pending'", (user_id,))
            asyncio.to_thread(db.commit)

        await bot.send_message(user_id, "✅ আপনার উইথড্র এপ্রুভ হয়েছে। পেমেন্টের স্ক্রিনশট পাঠান।")
        await message.answer("এপ্রুভ করা হয়েছে + ব্যালেন্স থেকে টাকা কাটা হয়েছে।")
    except:
        await message.answer("ভুল ইউজার আইডি। উদাহরণ: /approvewd 123456789") 
@dp.callback_query(F.data == "today_rate")
async def today_rate(call: types.CallbackQuery):
    db = await get_db_connection() try:
        async with db.execute("SELECT category, rate_bdt FROM rates WHERE rate_bdt > 0 ORDER BY category") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        text = "💰 <b>আজকের রেট</b>\n\nকোনো রেট এখনো সেট করা হয়নি।"
    else:
        text = "💰 <b>আজকের রেট</b>\n\n"
        for cat, rate in rows:
            # শুধু যেগুলোর রেট ৫ এর বেশি বা আপনি আপডেট করেছেন (ডিফল্ট ৫ না)
            if rate > 5:  # আপনি যদি ডিফল্ট ৫ রাখেন, তাহলে >5 মানে আপডেট করা
                text += f"• <b>{cat.replace('_', ' ')}</b>: <b>{rate} টাকা</b>\n"

    # যদি কোনো আপডেটেড রেট না থাকে
    if "কোনো রেট এখনো" in text or len(text.split('\n')) <= 3:
        text = "💰 <b>আজকের রেট</b>\n\nএখনো কোনো রেট আপডেট করা হয়নি।"

    kb = back_home_kb()
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()
@dp.callback_query(F.data == "files_menu")
async def files_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    text = "📁 <b>আপনার ফাইল স্ট্যাটস</b>\n\n"
    db = await get_db_connection() try:
        async with db.execute("SELECT pending, reported, approved, rejected FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                pending, reported, approved, rejected = row
                text += f"⏳ পেন্ডিং: {pending}\n"
                text += f"⏳ রিপোর্ট অপেক্ষায়: {reported}\n"
                text += f"✅ এপ্রুভড: {approved}\n"
                text += f"❌ রিজেক্টেড: {rejected}\n"
    kb = back_home_kb()
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data == "balance_menu")
async def balance_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    db = await get_db_connection() try:
        async with db.execute("SELECT earnings_bdt FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            earnings = row[0] if row else 0
    text = f"💳 <b>আপনার ব্যালেন্স</b>\n\n"
    text += f"মোট আয়: <b>{earnings} টাকা</b>\n\n"
    text += "উইথড্র করতে Withdraw বাটন ক্লিক করুন।"
    kb = back_home_kb()
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data == "referral")
async def referral(call: types.CallbackQuery):
    user_id = call.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    db = await get_db_connection() try:
        async with db.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            count = row[0] if row else 0
    text = f"👥 <b>রেফারেল সিস্টেম</b>\n\n"
    text += f"আপনার রেফার লিঙ্ক:\n<code>{ref_link}</code>\n\n"
    text += f"মোট রেফার করেছেন: {count} জন\n"
    text += "প্রতি রেফারে ৫ টাকা + ৫ লেভেল MLM বোনাস!"
    kb = back_home_kb()
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data == "settings")
async def settings_menu(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🌐 ভাষা পরিবর্তন", callback_data="change_lang")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    await call.message.edit_text("⚙️ <b>সেটিংস</b>\n\nভাষা পরিবর্তন করুন:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data == "change_lang")
async def change_lang(call: types.CallbackQuery):
    kb = []
    for k, v in LANGUAGES.items():
        kb.append([InlineKeyboardButton(text=v['name'], callback_data=f"set_lang_{k}")])
    kb.append([InlineKeyboardButton(text="🔙 Back", callback_data="settings")])
    await call.message.edit_text("🌍 ভাষা সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(call: types.CallbackQuery):
    lang = call.data.split("_")[2]
    db = await get_db_connection() try:
        await asyncio.to_thread(db.execute,"UPDATE users SET language = ? WHERE user_id = ?", (lang, call.from_user.id))
        asyncio.to_thread(db.commit)
    await call.message.edit_text(f"✅ ভাষা পরিবর্তন করা হয়েছে: {LANGUAGES[lang]['name']}", reply_markup=main_menu())
    await call.answer()

@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def broadcast(message: types.Message):
    if len(message.text.split(maxsplit=1)) < 2:
        await message.answer("❌ ব্যবহার: /broadcast আপনার মেসেজ")
        return
    text = message.text.split(maxsplit=1)[1]
    success = 0
    db = await get_db_connection() try:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            for (uid,) in rows:
                try:
                    await bot.send_message(uid, text)
                    success += 1
                except:
                    pass
    await message.answer(f"✅ {success} জনকে মেসেজ পাঠানো হয়েছে।")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Send Files", callback_data="send_files")],
        [InlineKeyboardButton(text="💰 Today Rate", callback_data="today_rate")],
        [InlineKeyboardButton(text="📁 My Files", callback_data="files_menu")],
        [InlineKeyboardButton(text="💳 Balance", callback_data="balance_menu")],
        [InlineKeyboardButton(text="👥 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="💸 Withdraw", callback_data="withdraw_start")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton(text="🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton(text="🆘 Support", callback_data="support")],
        [InlineKeyboardButton(text="🏠 Home", callback_data="main_menu")]
    ])

    help_text = """
🤖 <b>বটের সাহায্য মেনু</b>

নিচের বাটনগুলো ক্লিক করে আপনি যা চান তা করতে পারবেন:

📤 ফাইল পাঠিয়ে আয় করুন
💰 আজকের রেট দেখুন
📁 আপনার ফাইলের স্ট্যাটাস দেখুন
💳 ব্যালেন্স চেক করুন
👥 রেফার করে বোনাস পান
💸 টাকা তুলুন
⚙️ ভাষা চেঞ্জ করুন
🏆 টপ আর্নার দেখুন
🆘 সমস্যা হলে সাপোর্টে যান

ধন্যবাদ বট ব্যবহার করার জন্য! 🌟
    """

    await message.answer(help_text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("myrate"))
async def my_rate(message: types.Message):
    text = "💰 <b>আপনার রেট লিস্ট</b>\n\n"
    db = await get_db_connection() try:
        async with db.execute("SELECT category, rate_bdt FROM rates ORDER BY category") as cursor:
            rows = await cursor.fetchall()
            for cat, rate in rows:
                text += f"• {cat.replace('_', ' ')}: <b>{rate} টাকা</b>\n"
    kb = back_home_kb()
    await message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.message(Command("mystats"))
@dp.callback_query(F.data == "mystats")
async def my_stats(event: types.Message | types.CallbackQuery):
    # কমান্ড বা কলব্যাক — দুইটাই হ্যান্ডেল করবে
    if isinstance(event, types.CallbackQuery):
        message = event.message
        user_id = event.from_user.id
        await event.answer()  # লোডিং বন্ধ করতে
    else:
        message = event
        user_id = event.from_user.id

    user = await get_user(user_id)
    if not user:
        text = "❌ আপনার তথ্য পাওয়া যায়নি। /start দিয়ে আবার চেষ্টা করুন।"
        if isinstance(event, types.CallbackQuery):
            await message.edit_text(text, reply_markup=back_home())
        else:
            await message.answer(text, reply_markup=back_home())
        return

    # ইনডেক্স অনুযায়ী ডেটা নেওয়া
    pending = user[4]
    reported = user[5]
    approved = user[6]
    rejected = user[7]
    earnings = user[8] or 0

    # রেফারেল কাউন্ট — যদি কলাম না থাকে তাহলে IndexError এড়ানো
    referral_count = 0
    if len(user) > 14:  # referral_count ইনডেক্স ধরে (যদি থাকে)
        referral_count = user[14] or 0

    text = f"📊 <b>আপনার স্ট্যাটাস</b>\n\n"
    text += f"💰 ব্যালেন্স: <b>{earnings} টাকা</b>\n\n"
    text += f"📁 ফাইল স্ট্যাটাস:\n"
    text += f"⏳ পেন্ডিং: <b>{pending}</b>\n"
    text += f"⏳ রিপোর্ট অপেক্ষায়: <b>{reported}</b>\n"
    text += f"✅ এপ্রুভড: <b>{approved}</b>\n"
    text += f"❌ রিজেক্টেড: <b>{rejected}</b>\n\n"
    text += f"👥 রেফার করেছেন: <b>{referral_count} জন</b>"

    # কীবোর্ড — রিফ্রেশ + হোম
    kb = [
        [InlineKeyboardButton(text="🔄 রিফ্রেশ", callback_data="mystats")],
        [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)

    # কলব্যাক হলে edit, কমান্ড হলে answer
    if isinstance(event, types.CallbackQuery):
        await message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=markup)
@dp.message(Command("userstats"), F.from_user.id == ADMIN_ID)
async def admin_user_stats(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ ব্যবহার: /userstats 123456789\n(ইউজারের আইডি দিন)")
            return
        
        target_id = int(args[1])
        user = await get_user(target_id)
        
        if not user:
            await message.answer("❌ এই আইডির কোনো ইউজার পাওয়া যায়নি।")
            return

        username = user[1] or "নেই"
        full_name = user[2]
        language = user[3]
        pending = user[4]
        reported = user[5]
        approved = user[6]
        rejected = user[7]
        earnings = user[8] or 0
        referrer = user[13] if len(user) > 13 else "নেই"
        referral_count = user[14] if len(user) > 14 else 0

        stats_text = f"""
🔍 <b>ইউজার স্ট্যাটাস (এডমিন ভিউ)</b>

🆔 <b>আইডি:</b> <code>{target_id}</code>
📛 <b>নাম:</b> {full_name}
📝 <b>ইউজারনেম:</b> @{username}
🌍 <b>ভাষা:</b> {language.upper()}

💰 <b>ব্যালেন্স:</b> {earnings} টাকা

📁 <b>ফাইল স্ট্যাটাস</b>
⏳ পেন্ডিং: {pending}
⏳ রিপোর্ট অপেক্ষায়: {reported}
✅ এপ্রুভড: {approved}
❌ রিজেক্টেড: {rejected}

👥 <b>রেফারেল</b>
রেফার করেছেন: {referral_count} জন
রেফারার আইডি: {referrer}

🔧 এডমিন থেকে দেখা হচ্ছে
        """

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 উইথড্র এপ্রুভ", callback_data=f"admin_approvewd_{target_id}")],
            [InlineKeyboardButton(text="📊 ফাইল স্ট্যাটাস", callback_data=f"admin_files_{target_id}")],
            [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
        ])

        await message.answer(stats_text, parse_mode="HTML", reply_markup=kb)

    except ValueError:
        await message.answer("❌ সঠিক ইউজার আইডি দিন (শুধু সংখ্যা)।")
    except Exception as e:
        await message.answer("কোনো সমস্যা হয়েছে।")
        print(f"UserStats Error: {e}")

@dp.message(Command("rules"))
async def rules(message: types.Message):
    rules_text = """
📜 <b>বটের নিয়মাবলী</b>

✅ যা করতে পারবেন:
• সঠিক ক্যাটাগরিতে ফাইল পাঠান
• রেফার করে বোনাস পান
• প্রতিদিন লগইন করে বোনাস নিন

❌ যা করবেন না:
• ডুপ্লিকেট/ফেক ফাইল পাঠাবেন না
• স্প্যাম করবেন না
• বটের বাইরে পেমেন্ট চাইবেন না

ভায়োলেশন করলে ব্যান করা হবে।
    """
    kb = back_home_kb()
    await message.answer(rules_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    
@dp.message(Command("invite"))
async def invite_command(message: types.Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    db = await get_db_connection() try:
        async with db.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            count = row[0] if row else 0

    invite_text = f"""
👥 <b>আপনার রেফারেল লিঙ্ক</b>

🔗 <code>{ref_link}</code>

📊 মোট রেফার করেছেন: <b>{count} জন</b>

প্রতি রেফারে ৫ টাকা + ৫ লেভেল MLM বোনাস পান!

বন্ধুদের আমন্ত্রণ জানান এবং বোনাস উপভোগ করুন 🌟
    """

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 লিঙ্ক শেয়ার করুন", url=f"https://t.me/share/url?url={ref_link}")],
        [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
    ])

    await message.answer(invite_text, parse_mode="HTML", reply_markup=kb)



# এডমিন কমান্ডস
@dp.message(Command("addbalance"), F.from_user.id == ADMIN_ID)
async def manual_add_balance(message: types.Message):
    args = message.text.split()
    
    if len(args) != 3 or not args[1].isdigit():
        await message.answer(
            "❌ ভুল ফরম্যাট!\n\n"
            "<b>সঠিক ব্যবহার:</b>\n"
            "/addbalance <user_id> <amount>\n\n"
            "<b>উদাহরণ:</b>\n"
            "/addbalance 8143512878 500",
            parse_mode="HTML"
        )
        return

    user_id = int(args[1])
    
    try:
        amount = float(args[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ অ্যামাউন্ট পজিটিভ সংখ্যা হতে হবে (যেমন: 100, 250.5)")
        return

    db = await get_db_connection() try:
        async with db.execute("SELECT full_name, earnings_bdt FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()

        if not user_row:
            await message.answer(f"❌ ইউজার আইডি <code>{user_id}</code> বটে পাওয়া যায়নি।", parse_mode="HTML")
            return

        user_name, current_balance = user_row
        new_balance = current_balance + amount

        await asyncio.to_thread(db.execute,
            "UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?",
            (amount, user_id)
        )
        asyncio.to_thread(db.commit)

    # ইউজারকে নোটিফিকেশন
    try:
        await bot.send_message(
            user_id,
            f"🎉 অ্যাডমিন থেকে বোনাস/পেমেন্ট!\n\n"
            f"💰 <b>+{amount} টাকা</b> যোগ হয়েছে\n"
            f"📊 নতুন ব্যালেন্স: <b>{new_balance} টাকা</b>\n\n"
            f"ধন্যবাদ! 🌟",
            parse_mode="HTML"
        )
    except:
        pass  # ব্লক করলে ইগনোর

    # এডমিনকে কনফার্মেশন (রিটার্ন লাইন সহ সুন্দর ফরম্যাট)
    await message.answer(
        f"✅ সফলভাবে যোগ করা হয়েছে!\n\n"
        f"👤 ইউজার: <a href='tg://user?id={user_id}'>{user_name}</a>\n"
        f"🆔 আইডি: <code>{user_id}</code>\n"
        f"💰 যোগ করা হয়েছে: <b>{amount} টাকা</b>\n"
        f"📊 নতুন ব্যালেন্স: <b>{new_balance} টাকা</b>",
        parse_mode="HTML"
    )
@dp.message(Command("release"), F.from_user.id == ADMIN_ID)
async def manual_release_payment(message: types.Message):
    args = message.text.split()
    
    # সঠিক ফরম্যাট চেক
    if len(args) != 3:
        await message.answer(
            "❌ ভুল ফরম্যাট!\n\n"
            "<b>সঠিক ব্যবহার:</b>\n"
            "/release <user_id> <amount>\n\n"
            "<b>উদাহরণ:</b>\n"
            "/release 8143512878 500\n"
            "/release 123456789 250",
            parse_mode="HTML"
        )
        return

    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ ইউজার আইডি সঠিক সংখ্যা হতে হবে।")
        return

    try:
        amount = float(args[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ অ্যামাউন্ট পজিটিভ সংখ্যা হতে হবে (যেমন: 100, 250.5)")
        return

    db = await get_db_connection() try:
        # ইউজার আছে কিনা চেক করা (অপশনাল, কিন্তু ভালো)
        async with db.execute("SELECT full_name, earnings_bdt FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()

        if not user_row:
            await message.answer(f"❌ ইউজার আইডি <code>{user_id}</code> বটে পাওয়া যায়নি।", parse_mode="HTML")
            return

        user_name, current_balance = user_row

        # টাকা যোগ করা
        new_balance = current_balance + amount
        await asyncio.to_thread(db.execute,
            "UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?",
            (amount, user_id)
        )
        asyncio.to_thread(db.commit)

    # ইউজারকে নোটিফিকেশন
    try:
        await bot.send_message(
            user_id,
            f"🎉 অ্যাডমিন থেকে পেমেন্ট রিলিজ হয়েছে!\n\n"
            f"💰 <b>+{amount} টাকা</b> যোগ হয়েছে\n"
            f"📊 নতুন ব্যালেন্স: <b>{new_balance} টাকা</b>\n\n"
            f"এখন উইথড্র করতে পারবেন। ধন্যবাদ! 🌟",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"⚠️ ইউজারকে মেসেজ পাঠানো যায়নি (হয়তো ব্লক করেছে)। কিন্তু টাকা যোগ হয়েছে।")

    # এডমিনকে কনফার্মেশন
    await message.answer(
        f"✅ সফলভাবে রিলিজ করা হয়েছে!\n\n"
        f"👤 ইউজার: <b>{user_name}</b>\n"
        f"🆔 আইডি: <code>{user_id}</code>\n"
        f"💰 যোগ করা হয়েছে: <b>{amount} টাকা</b>\n"
        f"📊 নতুন ব্যালেন্স: <b>{new_balance} টাকা</b>",
        parse_mode="HTML"
    )
@dp.message(Command("setrate"), F.from_user.id == ADMIN_ID)
async def set_rate(message: types.Message):
    args = message.text.split()[1:]  # /setrate এর পরের সব

    if not args:
        await message.answer(
            "❌ কোনো রেট দেওয়া হয়নি!\n\n"
            "<b>ব্যবহার:</b>\n"
            "/setrate Facebook_Webmail=10 Coins_Niva=7 Others_Other=15\n\n"
            "একাধিক রেট একসাথে চেঞ্জ করতে পারবেন।",
            parse_mode="HTML"
        )
        return

    updated = []
    failed = []

    db = await get_db_connection() try:
        for arg in args:
            if '=' not in arg:
                failed.append(f"❌ {arg} (ফরম্যাট ভুল)")
                continue

            cat, rate_str = arg.split('=', 1)
            cat = cat.strip()
            rate_str = rate_str.strip()

            if not cat:
                failed.append("❌ খালি ক্যাটাগরি")
                continue

            try:
                rate = float(rate_str)
                if rate < 0:
                    raise ValueError
            except ValueError:
                failed.append(f"❌ {cat} = {rate_str} (সংখ্যা হতে হবে)")
                continue

            # রেট আপডেট (INSERT OR REPLACE = UPSERT)
            await asyncio.to_thread(db.execute,
                "INSERT OR REPLACE INTO rates (category, rate_bdt) VALUES (?, ?)",
                (cat, rate)
            )
            updated.append(f"✅ <b>{cat.replace('_', ' ')}</b> → <b>{rate} টাকা</b>")

        asyncio.to_thread(db.commit)

    # ফিডব্যাক তৈরি
    response = "<b>📢 রেট আপডেট সম্পন্ন!</b>\n\n"

    if updated:
        response += "<b>সফলভাবে চেঞ্জ হয়েছে:</b>\n" + "\n".join(updated) + "\n\n"
    if failed:
        response += "<b>ফেইলড:</b>\n" + "\n".join(failed) + "\n\n"

    # ব্রডকাস্ট শুধু যদি কিছু আপডেট হয়
    if updated:
        broadcast_text = "📢 <b>নতুন রেট আপডেট!</b>\n\n" + "\n".join(updated)
        broadcast_count = 0

        db = await get_db_connection() try:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                for (uid,) in rows:
                    try:
                        await bot.send_message(uid, broadcast_text, parse_mode="HTML")
                        broadcast_count += 1
                    except:
                        pass  # ব্লক করলে স্কিপ

        response += f"📩 <b>{broadcast_count}</b> জন ইউজারকে নোটিফিকেশন পাঠানো হয়েছে।"

    await message.answer(response, parse_mode="HTML")

@dp.message(Command("profile"))
async def profile_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("প্রোফাইল পাওয়া যায়নি।")
        return

    # ডাটা আনপ্যাক
    username = user[1] or "নেই"
    full_name = user[2]
    language = user[3]
    pending = user[4]
    reported = user[5]
    approved = user[6]
    rejected = user[7]
    earnings = user[8] or 0
    referrer = user[13] or "নেই"
    referral_count = user[14] if len(user) > 14 else 0  # যদি কলাম থাকে

    # প্রোফাইল টেক্সট
    profile_text = f"""
👤 <b>আপনার প্রোফাইল</b>

🆔 <b>আইডি:</b> <code>{user_id}</code>
📛 <b>নাম:</b> {full_name}
📝 <b>ইউজারনেম:</b> @{username}
🌍 <b>ভাষা:</b> {language.upper()}

💰 <b>ব্যালেন্স:</b> {earnings} টাকা

📁 <b>ফাইল স্ট্যাটাস</b>
⏳ পেন্ডিং: {pending}
⏳ রিপোর্ট অপেক্ষায়: {reported}
✅ এপ্রুভড: {approved}
❌ রিজেক্টেড: {rejected}

👥 <b>রেফারেল</b>
রেফার করেছেন: {referral_count} জন
রেফারার আইডি: {referrer}

ধন্যবাদ বট ব্যবহার করার জন্য! 🌟
    """

    # ইনলাইন বাটন
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 ব্যালেন্স দেখুন", callback_data="balance_menu")],
        [InlineKeyboardButton(text="📁 ফাইল স্ট্যাটাস", callback_data="files_menu")],
        [InlineKeyboardButton(text="👥 রেফারেল", callback_data="referral")],
        [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
    ])

    await message.answer(profile_text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("profile"), F.from_user.id == ADMIN_ID)
async def admin_profile(message: types.Message):
    try:
        # কমান্ড থেকে ইউজার আইডি নেওয়া
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ ব্যবহার: /profile 123456789\n(ইউজারের আইডি দিন)")
            return
        
        target_id = int(args[1])
        user = await get_user(target_id)
        
        if not user:
            await message.answer("❌ এই আইডির কোনো ইউজার পাওয়া যায়নি।")
            return

        # ডাটা আনপ্যাক
        username = user[1] or "নেই"
        full_name = user[2]
        language = user[3]
        pending = user[4]
        reported = user[5]
        approved = user[6]
        rejected = user[7]
        earnings = user[8] or 0
        referrer = user[13] or "নেই"
        referral_count = user[14] if len(user) > 14 else 0

        profile_text = f"""
👤 <b>ইউজার প্রোফাইল (এডমিন ভিউ)</b>

🆔 <b>আইডি:</b> <code>{target_id}</code>
📛 <b>নাম:</b> {full_name}
📝 <b>ইউজারনেম:</b> @{username}
🌍 <b>ভাষা:</b> {language.upper()}

💰 <b>ব্যালেন্স:</b> {earnings} টাকা

📁 <b>ফাইল স্ট্যাটাস</b>
⏳ পেন্ডিং: {pending}
⏳ রিপোর্ট অপেক্ষায়: {reported}
✅ এপ্রুভড: {approved}
❌ রিজেক্টেড: {rejected}

👥 <b>রেফারেল</b>
রেফার করেছেন: {referral_count} জন
রেফারার আইডি: {referrer}

🔍 এডমিন থেকে দেখা হচ্ছে
        """

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 ব্যালেন্স দেখুন", callback_data=f"admin_balance_{target_id}")],
            [InlineKeyboardButton(text="📁 ফাইল স্ট্যাটাস", callback_data=f"admin_files_{target_id}")],
            [InlineKeyboardButton(text="💸 উইথড্র এপ্রুভ", url=f"tg://user?id={target_id}")],
            [InlineKeyboardButton(text="🏠 হোম", callback_data="main_menu")]
        ])

        await message.answer(profile_text, parse_mode="HTML", reply_markup=kb)

    except ValueError:
        await message.answer("❌ সঠিক ইউজার আইডি দিন (শুধু সংখ্যা)।")
    except Exception as e:
        await message.answer("কোনো সমস্যা হয়েছে।")
        print(f"Admin Profile Error: {e}")

@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def bot_stats(message: types.Message):
    db = await get_db_connection() try:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
        async with db.execute("SELECT SUM(earnings_bdt) FROM users") as cursor:
            total_earnings = (await cursor.fetchone())[0] or 0
        async with db.execute("SELECT COUNT(*) FROM files WHERE status = 'pending'") as cursor:
            pending_files = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM files WHERE status = 'reported'") as cursor:
            reported_files = (await cursor.fetchone())[0]
        text = f"""
🤖 বট স্ট্যাটস

👥 মোট ইউজার: {total_users}
📁 পেন্ডিং ফাইল: {pending_files}
⏳ রিপোর্ট অপেক্ষায়: {reported_files}
💰 মোট বিতরণকৃত আয়: {total_earnings} টাকা
        """
        await message.answer(text)

@dp.message(Command("notice"), F.from_user.id == ADMIN_ID)
async def broadcast_notice(message: types.Message):
    if len(message.text.split(maxsplit=1)) < 2:
        await message.answer("❌ ব্যবহার: /notice আপনার নোটিশ মেসেজ")
        return
    
    notice_text = message.text.split(maxsplit=1)[1]
    success_count = 0
    db = await get_db_connection() try:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            for (uid,) in rows:
                try:
                    await bot.send_message(uid, f"📢 <b>গুরুত্বপূর্ণ নোটিশ</b>\n\n{notice_text}", parse_mode="HTML")
                    success_count += 1
                except:
                    pass
    
    await message.answer(f"✅ নোটিশ সফলভাবে {success_count} জন ইউজারের কাছে পাঠানো হয়েছে।")

@dp.message(Command("toggle"), F.from_user.id == ADMIN_ID)
async def toggle_category(message: types.Message):
    args = message.text.split()[1:]
    if len(args) != 2:
        await message.answer("❌ ব্যবহার: /toggle Facebook_Webmail on\nঅথবা /toggle Coins_Niva off")
        return
    
    full_cat = args[0]
    status_str = args[1].lower()
    if status_str not in ["on", "off"]:
        await message.answer("❌ শুধু 'on' অথবা 'off' লিখুন।")
        return
    
    status = 1 if status_str == "on" else 0
    
    db = await get_db_connection() try:
        await asyncio.to_thread(db.execute,"INSERT OR REPLACE INTO toggles (item, enabled) VALUES (?, ?)", (full_cat, status))
        asyncio.to_thread(db.commit)
    
    status_text = "চালু" if status else "বন্ধ"
    await message.answer(f"✅ {full_cat} ক্যাটাগরি {status_text} করা হয়েছে।")

@dp.callback_query(F.data == "support")
async def support(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("🆘 আপনার সমস্যা লিখুন। এডমিনের কাছে পাঠানো হবে।", reply_markup=back_home_kb())
    await state.set_state(States.support_ticket)

@dp.message(States.support_ticket)
async def receive_ticket(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"🆘 নতুন সাপোর্ট টিকেট\nইউজার: {message.from_user.id}\nমেসেজ: {message.text}")
    await message.answer("✅ আপনার সমস্যা এডমিনের কাছে পাঠানো হয়েছে। শীঘ্রই রিপ্লাই পাবেন।", reply_markup=main_menu())
    await state.clear()

## রেফার বোনাস ফাংশন (আগে ছিল, আবার দিলাম যাতে কোনো ফিচার বাদ না যায়)
async def give_refer_bonus(new_user_id):
    bonuses = [5, 2, 2, 2, 2]  # Level 1: 5 Tk, Level 2-5: 2 Tk each
    current = new_user_id
    level = 0
    db = await get_db_connection() try:
        while current and level < 5:
            async with db.execute("SELECT referrer FROM users WHERE user_id = ?", (current,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    referrer = row[0]
                    bonus = bonuses[level]
                    await asyncio.to_thread(db.execute,"UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?", (bonus, referrer))
                    try:
                        await bot.send_message(referrer, f"🎉 রেফার বোনাস! +{bonus} টাকা (Level {level+1})")
                    except:
                        pass
                    current = referrer
                    level += 1

# ডেইলি মোটিভেশন
async def daily_motivation():
    while True:
        if datetime.datetime.now().hour == 8:
            db = await get_db_connection() try:
                async with db.execute("SELECT user_id FROM users") as cursor:
                    rows = await cursor.fetchall()
                    for (uid,) in rows:
                        try:
                            await bot.send_message(uid, "🤲 ইনশাআল্লাহ আজকের দিন সফল হোক। সৎ থাকুন, পরিশ্রম করুন।")
                        except:
                            pass
        await asyncio.sleep(3600)

# ডেইলি ব্যাকআপ
async def daily_backup():
    while True:
        if datetime.datetime.now().hour == 0:
            if os.path.exists(DB_NAME):
                shutil.copy(DB_NAME, f"{BACKUP_NAME}_{datetime.date.today()}.db")
        await asyncio.sleep(3600)

# মেইন ফাংশন
async def main():
    await init_db()
    asyncio.create_task(daily_motivation())
    asyncio.create_task(daily_backup())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
