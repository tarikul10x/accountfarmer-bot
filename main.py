import asyncio
import os
import random
import string
import datetime
import pandas as pd
import aiofiles
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest
from io import BytesIO
import aiosqlite

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

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
    tracking_order = State()
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
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            lang = row[0] if row else 'bn'
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.executescript('''
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
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                sub_category TEXT,
                status TEXT DEFAULT 'pending',
                rate REAL,
                message_id INTEGER UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS rates (
                category TEXT PRIMARY KEY,
                rate_bdt REAL DEFAULT 5
            );
            CREATE TABLE IF NOT EXISTS toggles (
                item TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount_bdt REAL,
                currency TEXT,
                method TEXT,
                number TEXT,
                status TEXT DEFAULT 'pending'
            );
        ''')
                # রেফারেল কাউন্ট কলাম যোগ করা (যদি না থাকে)
                # রেফারেল কাউন্ট কলাম যোগ করা (পুরোনো ডাটাবেসের জন্য নিরাপদে)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
            await db.commit()
            print("referral_count কলাম সফলভাবে যোগ করা হয়েছে।")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass  # ইতিমধ্যে থাকলে কিছু করার দরকার নেই
            else:
                print(f"কলাম যোগ করতে সমস্যা: {e}")
                raise
        try:
            await db.execute("ALTER TABLE withdraw_requests ADD COLUMN reject_reason TEXT")
            await db.commit()
        except aiosqlite.OperationalError:
            pass  # ইতিমধ্যে থাকলে কিছু করবে না
 # নতুন কলাম যোগ করা (যদি আগে না থাকে)
        new_columns = [
            ("files", "order_id", "TEXT"),
            ("files", "username", "TEXT"),
            ("files", "data_count", "INTEGER DEFAULT 1"),
            ("withdraw_requests", "order_id", "TEXT")
        ]
        for table, col, col_type in new_columns:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                await db.commit()
            except aiosqlite.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
# ডিফল্ট রেট এবং টগল সেট করা
        for main in MAIN_CATEGORIES:
            for sub in SUB_CATEGORIES.get(main, []):
                full = f"{main}_{sub}"
                await db.execute("INSERT OR IGNORE INTO rates (category, rate_bdt) VALUES (?, 5)", (full,))
                await db.execute("INSERT OR IGNORE INTO toggles (item, enabled) VALUES (?, 1)", (full,))

        # রেট টেবিলে অতিরিক্ত কলাম যোগ (যদি না থাকে)
        try:
            await db.execute("ALTER TABLE rates ADD COLUMN display_name TEXT")
            await db.execute("ALTER TABLE rates ADD COLUMN format_text TEXT DEFAULT 'UID | Pass | 2FA'")
            await db.execute("ALTER TABLE rates ADD COLUMN last_time TEXT DEFAULT '11:00 PM BD'")
            await db.execute("ALTER TABLE rates ADD COLUMN report_time TEXT DEFAULT '24 Hours'")
            await db.commit()
            print("রেট টেবিলে অতিরিক্ত কলাম যোগ করা হয়েছে।")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass
            else:
                print(f"রেট কলাম যোগ করতে সমস্যা: {e}")
                raise

        await db.commit()
async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_user(user_id, username, full_name, referrer=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, referrer) VALUES (?, ?, ?, ?)", (user_id, username, full_name, referrer))
        await db.commit()
    if referrer:
        await give_refer_bonus(user_id)

async def get_rate(full_cat):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT rate_bdt FROM rates WHERE category = ?", (full_cat,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 5

async def is_enabled(full_cat):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT enabled FROM toggles WHERE item = ?", (full_cat,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1

async def get_coin_user():
    return "genzraiyaan"

def main_menu():
    kb = [
        [InlineKeyboardButton(text="📤 Send Files / Coins", callback_data="send_files")],
        [InlineKeyboardButton(text="💰 Today Rate", callback_data="today_rate")],
        [InlineKeyboardButton(text="📁 Files", callback_data="files_menu")],
        [InlineKeyboardButton(text="💳 Balance", callback_data="balance_menu")],
        [InlineKeyboardButton(text="👥 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="📋 Track Order", callback_data="track_order")],
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, call.from_user.id))
        await db.commit()
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
    full_cat = call.data.split("_", 1)[1]  # subcat_Facebook_Webmail → Facebook_Webmail
    await state.update_data(category=full_cat)

    # অটোমেটিক রেট টগল/ডিসপ্লে নামের জন্য ম্যাপিং (রেট সেট করার সময় কাজে লাগবে)
    # এটা শুধু রেফারেন্সের জন্য — কোনো ডাটাবেস চেঞ্জ লাগবে না

    if "PC Clone Cookies" in full_cat:
        # PC Clone সাব টাইপ সিলেক্ট
        kb = []
        for sub in PC_CLONE_SUB:
            kb.append([InlineKeyboardButton(text=sub, callback_data="ready_send")])
        kb.extend(back_home_kb())

        pc_prompt = await t(call.from_user.id, 'pc_clone_prompt')
        await call.message.edit_text(pc_prompt, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    elif "Random Gmail" in full_cat:
        # র‍্যান্ডম জিমেইল সাজেস্ট
        lowercase = string.ascii_lowercase
        digits = string.digits
        all_chars = string.ascii_letters + digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # র‍্যান্ডম ইউজারনেইম (১০-১৫ অক্ষর)
        username = ''.join(random.choices(lowercase + digits, k=random.randint(10, 15)))
        email = f"{username}@gmail.com"

        # শক্তিশালী পাসওয়ার্ড (১৮-২২ অক্ষর)
        password = ''.join(random.choices(all_chars, k=random.randint(18, 22)))

        suggestion_text = (
            f"<b>📧 সাজেস্টেড জিমেইল:</b>\n"
            f"<code>{email}</code>\n\n"
            f"<b>🔐 শক্তিশালী পাসওয়ার্ড:</b>\n"
            f"<code>{password}</code>\n\n"
            f"🔹 এই ইমেইল ও পাসওয়ার্ড দিয়ে জিমেইল তৈরি করুন।\n"
            f"🔹 তৈরি হয়ে গেলে <b>Done</b> চাপুন।"
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
        # সাধারণ ফাইল/কয়েন পাঠানোর প্রম্পট
        text = await t(call.from_user.id, 'send_file_prompt')
        if "Coin" in full_cat:
            text += f"\n\n{await t(call.from_user.id, 'coin_user_prompt')} {await get_coin_user()}"

        kb = [
            [InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu")]
        ]
        kb.extend(back_home_kb())

        # পুরোনো মেসেজ আইডি সেভ করে রাখি (পরে কীবোর্ড ক্লোজ করার জন্য)
        await state.update_data(prev_msg_id=call.message.message_id)

        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await state.set_state(States.waiting_file)

    await call.answer()

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

    # অর্ডার আইডি জেনারেট (১০ অক্ষর)
    order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # ডেটা কাউন্ট (XLSX/TXT ফাইলের জন্য)
    data_count = 1
    if message.document:
        try:
            file_info = await bot.get_file(message.document.file_id)
            file_bytes = await bot.download_file(file_info.file_path)
            file_stream = BytesIO(file_bytes)

            filename = message.document.file_name.lower()
            if filename.endswith('.xlsx'):
                df = pd.read_excel(file_stream)
                data_count = len(df)
            elif filename.endswith('.txt'):
                file_stream.seek(0)
                lines = file_stream.read().decode('utf-8', errors='ignore').splitlines()
                data_count = len([line for line in lines if line.strip()])
        except Exception as e:
            print(f"ফাইল কাউন্টে সমস্যা: {e}")
            data_count = 1

    total_amount = rate * data_count

    # ডাটাবেসে সেভ
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO files
            (user_id, category, sub_category, status, rate, message_id, order_id, username, data_count)
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?)
        """, (
            user.id,
            full_cat.split('_')[0],
            full_cat.split('_')[1],
            rate,
            message.message_id,
            order_id,
            user.username or "নেই",
            data_count
        ))
        await db.execute("UPDATE users SET pending = pending + 1 WHERE user_id = ?", (user.id,))
        await db.commit()

    # এডমিনের কাছে পাঠানো
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{order_id}")
        ],
        [InlineKeyboardButton(text="📋 কপি ইউজার আইডি", callback_data=f"copyid_{user.id}")]
    ])

    caption = (
        f"📥 <b>নতুন ফাইল এসেছে</b>\n\n"
        f"🆔 <b>অর্ডার আইডি:</b> <code>{order_id}</code>\n"
        f"🔹 ক্যাটাগরি: {full_cat.replace('_', ' ')}\n"
        f"💰 রেট: {rate} টাকা/ডেটা\n"
        f"📊 ডেটা সংখ্যা: {data_count}\n"
        f"💸 মোট: <b>{total_amount} টাকা</b>\n\n"
        f"👤 নাম: {user.full_name}\n"
        f"📛 ইউজারনেইম: @{user.username or 'নেই'}\n"
        f"🆔 আইডি: <code>{user.id}</code>"
    )

    if message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)
    else:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)

    # ইউজারকে সুন্দর সাকসেস মেসেজ + কপি বাটন
    file_sent_text = await t(message.from_user.id, 'file_sent')
    success_msg = (
        f"{file_sent_text}\n\n"
        f"🆔 <b>আপনার অর্ডার আইডি:</b> <code>{order_id}</code>\n"
        f"💸 <b>মোট টাকা:</b> {total_amount} টাকা (এপ্রুভ হলে)\n\n"
        f"স্ট্যাটাস দেখতে → মেইন মেনু → 📋 ট্র্যাক অর্ডার"
    )

    copy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")]
    ])

    await message.answer(success_msg, parse_mode="HTML", reply_markup=copy_kb)

    # পুরোনো ইনলাইন কীবোর্ড বন্ধ করা (prev_msg_id দিয়ে)
    prev_data = await state.get_data()
    prev_msg_id = prev_data.get('prev_msg_id')

    if prev_msg_id:
        try:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_msg_id, reply_markup=None)
        except TelegramBadRequest:
            pass
    else:
        # ফলব্যাক
        try:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id - 1, reply_markup=None)
        except TelegramBadRequest:
            pass

    await state.clear()
# Approve হ্যান্ডলার
@dp.callback_query(F.data.startswith("admin_approvewd_"))
async def admin_approve_withdraw(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[2])
    except:
        await call.answer("ভুল ডেটা।", show_alert=True)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT amount_bdt, order_id FROM withdraw_requests WHERE user_id = ? AND status = 'pending'", (target_user_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            await call.answer("কোনো পেন্ডিং উইথড্র নেই।", show_alert=True)
            return
        amount, order_id = row

        # টাকা কাটা + স্ট্যাটাস চেঞ্জ
        await db.execute("UPDATE users SET earnings_bdt = earnings_bdt - ? WHERE user_id = ?", (amount, target_user_id))
        await db.execute("UPDATE withdraw_requests SET status = 'approved' WHERE user_id = ? AND status = 'pending'", (target_user_id,))
        await db.commit()

    # ইউজারকে নোটিফিকেশন
    try:
        await bot.send_message(target_user_id, 
            f"✅ আপনার উইথড্র এপ্রুভ হয়েছে!\n"
            f"🆔 অর্ডার: <code>{order_id}</code>\n"
            f"💰 পরিমাণ: {amount} টাকা\n\n"
            f"পেমেন্টের স্ক্রিনশট পাঠান।",
            parse_mode="HTML"
        )
    except:
        pass

    await call.message.edit_text(
        call.message.text + f"\n\n✅ <b>উইথড্র এপ্রুভ করা হয়েছে ({amount} টাকা)</b>\n🆔 অর্ডার: <code>{order_id}</code>",
        parse_mode="HTML"
    )
    await call.answer("উইথড্র এপ্রুভ করা হয়েছে।")
# approve 
@dp.callback_query(F.data.startswith("approve_"))
async def approve_file(call: types.CallbackQuery):
    order_id = call.data.split("_")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, rate, data_count FROM files WHERE order_id = ?", (order_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            await call.answer("⚠️ ফাইল পাওয়া যায়নি।", show_alert=True)
            return
        user_id, rate, data_count = row
        amount = rate * data_count

        await db.execute("UPDATE files SET status = 'reported' WHERE order_id = ?", (order_id,))
        await db.execute("UPDATE users SET pending = pending - 1, reported = reported + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    # ইউজারকে নোটিফিকেশন + কপি বাটন
    approve_text = await t(user_id, 'approve_notification')
    notify_msg = (
        f"{approve_text}\n\n"
        f"🆔 <b>অর্ডার আইডি:</b> <code>{order_id}</code>\n"
        f"💰 <b>মোট:</b> {amount} টাকা\n"
        f"⏳ রিপোর্টের অপেক্ষায় (পেমেন্ট হবে শীঘ্রই)"
    )

    copy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")]
    ])

    try:
        await bot.send_message(user_id, notify_msg, parse_mode="HTML", reply_markup=copy_kb)
    except:
        pass

    # এডমিন মেসেজ আপডেট + বাটন ক্লোজ
    await call.message.edit_caption(
        caption=call.message.caption + "\n\n✅ <b>Approved! Waiting for report</b>",
        parse_mode="HTML",
        reply_markup=None  # বাটন সরিয়ে দেই
    )
    await call.answer("এপ্রুভ করা হয়েছে।")
# Reject with Reason (এডমিন থেকে কাজ করবে)
# Reject বাটন চাপলে (অর্ডার আইডি দিয়ে)
@dp.callback_query(F.data.startswith("reject_"))
async def reject_file(call: types.CallbackQuery, state: FSMContext):
    try:
        order_id = call.data.split("_")[1]  # reject_B2RBCOJPIY → B2RBCOJPIY

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT user_id, rate, data_count, category FROM files WHERE order_id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await call.answer("⚠️ ফাইল পাওয়া যায়নি বা ইতিমধ্যে প্রসেস করা হয়েছে।", show_alert=True)
                return
            user_id, rate, data_count, full_cat = row
            total_amount = rate * data_count

        # স্টেটে সেভ করা
        await state.update_data(
            reject_order_id=order_id,
            reject_user_id=user_id,
            reject_amount=total_amount,
            reject_category=full_cat.replace('_', ' ')
        )
        await state.set_state(States.reject_reason)

        # এডমিনকে কারণ চাওয়া
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel_reject")]
        ])

        await call.message.edit_caption(
            caption=call.message.caption + "\n\n❌ <b>রিজেক্ট করতে চান?</b>\n\nকারণ লিখুন:",
            parse_mode="HTML",
            reply_markup=kb
        )

        await call.answer()

    except Exception as e:
        await call.answer("সমস্যা হয়েছে।", show_alert=True)
        print(f"Reject error: {e}")


# কারণ রিসিভ + রিজেক্ট প্রসেস
@dp.message(States.reject_reason)
async def process_reject_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('reject_order_id')
    user_id = data.get('reject_user_id')
    total_amount = data.get('reject_amount', 0)
    category = data.get('reject_category', 'Unknown')

    reason = message.text.strip()
    if not reason:
        await message.answer("❌ কারণ লিখুন। অথবা Cancel করুন।")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE files SET status = 'rejected' WHERE order_id = ?", (order_id,))
        await db.execute("UPDATE users SET pending = pending - 1, rejected = rejected + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    # ইউজারকে নোটিফিকেশন + কপি বাটন
    reject_msg = (
        f"❌ আপনার ফাইল রিজেক্ট হয়েছে।\n\n"
        f"🆔 <b>অর্ডার আইডি:</b> <code>{order_id}</code>\n"
        f"🔹 ক্যাটাগরি: {category}\n"
        f"💸 মোট টাকা ছিল: {total_amount} টাকা\n"
        f"📛 <b>কারণ:</b> {reason}\n\n"
        f"দয়া করে সঠিক ফাইল পাঠান।"
    )

    copy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")]
    ])

    try:
        await bot.send_message(user_id, reject_msg, parse_mode="HTML", reply_markup=copy_kb)
    except:
        pass

    await message.answer("✅ রিজেক্ট করা হয়েছে। ইউজারকে কারণসহ জানানো হয়েছে।", reply_markup=main_menu())
    await state.clear()


# Cancel Reject
@dp.callback_query(F.data == "cancel_reject")
async def cancel_reject(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        original_caption = call.message.caption.split("\n\n❌ <b>রিজেক্ট করতে চান?</b>")[0]
        await call.message.edit_caption(
            caption=original_caption + "\n\n🔄 রিজেক্ট ক্যান্সেল করা হয়েছে।",
            parse_mode="HTML"
        )
    except:
        await call.message.edit_caption(caption=call.message.caption + "\n\n🔄 ক্যান্সেল করা হয়েছে।", parse_mode="HTML")
    await call.answer("রিজেক্ট ক্যান্সেল করা হয়েছে।")
@dp.message(States.reject_reason)
async def process_reject_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip()
    if not reason:
        await message.answer("❌ কারণ লিখুন। অথবা Cancel করুন।")
        return

    data = await state.get_data()
    order_id = data.get('reject_order_id')
    user_id = data.get('reject_user_id')
    total_amount = data.get('reject_amount', 0)
    category = data.get('reject_category', 'Unknown')

    if not order_id or not user_id:
        await message.answer("❌ সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        await state.clear()
        return

    # ডাটাবেস আপডেট
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE files SET status = 'rejected' WHERE order_id = ?", (order_id,))
        await db.execute("UPDATE users SET pending = pending - 1, rejected = rejected + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    # ইউজারকে সুন্দর রিজেক্ট মেসেজ + কপি বাটন
    reject_msg = (
        f"❌ আপনার ফাইল রিজেক্ট হয়েছে।\n\n"
        f"🆔 <b>অর্ডার আইডি:</b> <code>{order_id}</code>\n"
        f"🔹 ক্যাটাগরি: {category}\n"
        f"💸 মোট টাকা ছিল: {total_amount} টাকা\n"
        f"📛 <b>কারণ:</b> {reason}\n\n"
        f"দয়া করে সঠিক ফাইল পাঠান।"
    )

    copy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")]
    ])

    try:
        await bot.send_message(user_id, reject_msg, parse_mode="HTML", reply_markup=copy_kb)
    except:
        pass

    # এডমিনকে কনফার্ম + পুরোনো ইনলাইন বাটন ক্লোজ
    await message.answer(
        f"✅ রিজেক্ট করা হয়েছে।\n"
        f"🆔 অর্ডার: <code>{order_id}</code>\n"
        f"কারণ: {reason}",
        reply_markup=main_menu()
    )

    # এডমিনের পুরোনো মেসেজের ইনলাইন বাটন ক্লোজ করা (যদি সম্ভব হয়)
    try:
        # যদি reject চাপার সময় মেসেজ এডিট করা হয়ে থাকে
        await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id - 1, reply_markup=None)
    except:
        pass

    await state.clear()
# Withdraw সেকশন (সাকসেস হলে টাকা কাটবে + ট্রুটি ফ্রি)
# উইথড্র অ্যামাউন্ট ইনপুট
@dp.message(States.withdraw_amount)
async def wa(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())

        if amount < 100:
            kb = back_home_kb()
            await message.answer("❌ মিনিমাম ১০০ টাকা। আবার লিখুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            return

        user = await get_user(message.from_user.id)
        if not user or amount > user[8]:  # earnings_bdt
            kb = back_home_kb()
            await message.answer("❌ ব্যালেন্সের চেয়ে বেশি উইথড্র করা যাবে না। আবার লিখুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            return

        # অর্ডার আইডি জেনারেট (১০ অক্ষর)
        order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        data = await state.get_data()

        # ডাটাবেসে সেভ করা
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO withdraw_requests
                (user_id, amount_bdt, method, number, order_id, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (message.from_user.id, amount, data['method'], data['number'], order_id))
            await db.commit()

        # এডমিনকে নোটিফিকেশন
        user_info = await get_user(message.from_user.id)
        info_text = (
            f"💸 <b>নতুন উইথড্র রিকোয়েস্ট</b>\n\n"
            f"🆔 <b>অর্ডার আইডি:</b> <code>{order_id}</code>\n"
            f"👤 নাম: <b>{user_info[2]}</b>\n"
            f"🆔 আইডি: <code>{message.from_user.id}</code>\n"
            f"📛 ইউজারনেইম: @{user_info[1] or 'নেই'}\n"
            f"💰 ব্যালেন্স: {user_info[8]} টাকা\n"
            f"📁 ফাইল: পেন্ডিং {user_info[4]} | রিপোর্ট {user_info[5]} | এপ্রুভ {user_info[6]} | রিজেক্ট {user_info[7]}\n\n"
            f"🔹 অ্যামাউন্ট: <b>{amount} টাকা</b>\n"
            f"💳 মেথড: <b>{data['method'].upper()}</b>\n"
            f"🔢 নম্বর: <code>{data['number']}</code>\n\n"
            f"📅 সময়: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Approve", callback_data=f"wd_approve_{order_id}")],
            [InlineKeyboardButton(text="❌ Reject", callback_data=f"wd_reject_{order_id}")],
            [InlineKeyboardButton(text="📊 View Profile", callback_data=f"profile_{message.from_user.id}")]
        ])

        await bot.send_message(ADMIN_ID, info_text, parse_mode="HTML", reply_markup=admin_kb)

        # ইউজারকে সুন্দর সাকসেস মেসেজ + কপি বাটন
        success_text = await t(message.from_user.id, 'withdraw_success')
        success_msg = (
            f"{success_text}\n\n"
            f"🆔 <b>আপনার উইথড্র অর্ডার আইডি:</b> <code>{order_id}</code>\n"
            f"💰 <b>পরিমাণ:</b> {amount} টাকা\n"
            f"💳 <b>মেথড:</b> {data['method'].upper()}\n\n"
            f"স্ট্যাটাস দেখতে: মেইন মেনু → 📋 ট্র্যাক অর্ডার"
        )

        copy_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")]
        ])

        await message.answer(success_msg, parse_mode="HTML", reply_markup=copy_kb)

        # পুরোনো ইনলাইন বাটন বন্ধ করা
        try:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id - 1, reply_markup=None)
        except TelegramBadRequest:
            pass

        await state.clear()

    except ValueError:
        kb = back_home_kb()
        await message.answer("❌ সঠিক সংখ্যা লিখুন (যেমন: ১০০)।", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.message(Command("release"), F.from_user.id == ADMIN_ID)
async def admin_release(message: types.Message):
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ ব্যবহার: /release অর্ডার_আইডি কোয়ান্টিটি\nউদাহরণ: /release B2RBCOJPIY 20")
            return

        order_id = args[1].upper()
        try:
            quantity = int(args[2])
            if quantity <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ কোয়ান্টিটি সঠিক পূর্ণসংখ্যা হতে হবে।")
            return

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT user_id, rate, data_count, status FROM files WHERE order_id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await message.answer(f"❌ অর্ডার আইডি <code>{order_id}</code> পাওয়া যায়নি।")
                return
            user_id, rate, data_count_db, status = row

            if status != 'reported':
                await message.answer(f"❌ এই অর্ডার রিপোর্টের অপেক্ষায় নেই। স্ট্যাটাস: {status}")
                return

            # কোয়ান্টিটি অনুযায়ী টাকা হিসাব (যদি ইউজার কম দিতে চায়)
            amount = rate * quantity

            # ডাটাবেস আপডেট
            await db.execute("UPDATE users SET earnings_bdt = earnings_bdt + ?, reported = reported - 1, approved = approved + 1 WHERE user_id = ?", (amount, user_id))
            await db.execute("UPDATE files SET status = 'approved' WHERE order_id = ?", (order_id,))
            await db.commit()

        # ইউজারকে নোটিফিকেশন + কপি বাটন
        notify_msg = (
            f"🎉 অভিনন্দন! আপনার ফাইলের পেমেন্ট রিলিজ হয়েছে!\n\n"
            f"🆔 <b>অর্ডার আইডি:</b> <code>{order_id}</code>\n"
            f"📊 রিলিজকৃত কোয়ান্টিটি: {quantity}\n"
            f"💰 রেট: {rate} × {quantity} = <b>{amount} টাকা</b> যোগ হয়েছে\n\n"
            f"আপনার ব্যালেন্স চেক করুন → মেইন মেনু → 💳 Balance"
        )

        copy_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")]
        ])

        try:
            await bot.send_message(user_id, notify_msg, parse_mode="HTML", reply_markup=copy_kb)
        except:
            pass

        # এডমিনকে কনফার্ম
        await message.answer(
            f"✅ রিলিজ সফল!\n\n"
            f"🆔 অর্ডার: <code>{order_id}</code>\n"
            f"👤 ইউজার আইডি: <code>{user_id}</code>\n"
            f"📊 কোয়ান্টিটি: {quantity}\n"
            f"💰 যোগ করা হয়েছে: <b>{amount} টাকা</b>",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer("❌ কোনো সমস্যা হয়েছে।")
        print(f"Release error: {e}")

# উইথড্র এপ্রুভ (এডমিন)
@dp.callback_query(F.data.startswith("wd_approve_"))
async def withdraw_approve(call: types.CallbackQuery, state: FSMContext):
    order_id = call.data.split("_")[2]

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, amount_bdt, method, number FROM withdraw_requests WHERE order_id = ? AND status = 'pending'", (order_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await call.answer("❌ এই রিকোয়েস্ট আর পেন্ডিং নেই।", show_alert=True)
                return
            user_id, amount, method, number = row

        await db.execute("UPDATE withdraw_requests SET status = 'approved' WHERE order_id = ?", (order_id,))
        await db.commit()

    await bot.send_message(ADMIN_ID, f"✅ অর্ডার {order_id} এপ্রুভ করা হয়েছে। এখন স্ক্রিনশট পাঠান।")

    await state.update_data(pending_order_id=order_id, wd_user_id=user_id, wd_amount=amount, wd_method=method, wd_number=number)
    await state.set_state(AdminStates.screenshot_wait)

    await call.message.edit_text(call.message.text + "\n\n✅ <b>Approved! এখন স্ক্রিনশট পাঠান।</b>", parse_mode="HTML")
    await call.answer("এপ্রুভ হয়েছে।")


# স্ক্রিনশট রিসিভ + কমপ্লিট
@dp.message(AdminStates.screenshot_wait, F.photo)
async def admin_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("pending_order_id")
    user_id = data.get("wd_user_id")
    amount = data.get("wd_amount")

    if not order_id or not user_id:
        await message.answer("❌ সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        return

    # স্ক্রিনশট ইউজারকে পাঠানো (ফরওয়ার্ড না করে send_photo দিয়ে)
    photo_file_id = message.photo[-1].file_id
    caption = f"✅ আপনার {amount} টাকার উইথড্র কমপ্লিট হয়েছে!\n🆔 অর্ডার: <code>{order_id}</code>"

    try:
        await bot.send_photo(user_id, photo_file_id, caption=caption, parse_mode="HTML")
    except:
        await message.answer("❌ ইউজারকে পাঠানো যায়নি (হয়তো বট ব্লক করেছে)।")

    # এডমিনকে কনফার্ম
    await message.answer(f"✅ স্ক্রিনশট পাঠানো হয়েছে। অর্ডার {order_id} কমপ্লিট।")

    await state.clear()
# উইথড্র রিজেক্ট (এডমিন)

@dp.callback_query(F.data.startswith("profile_"))
async def admin_view_profile(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[1])

        user = await get_user(target_user_id)
        if not user:
            await call.answer("❌ ইউজার পাওয়া যায়নি।", show_alert=True)
            return

        username = user[1] or "নেই"
        full_name = user[2]
        language = user[3]
        pending = user[4]
        reported = user[5]
        approved = user[6]
        rejected = user[7]
        earnings = user[8] or 0
        referral_count = user[14] if len(user) > 14 else 0

        profile_text = (
            f"👤 <b>ইউজার প্রোফাইল (এডমিন ভিউ)</b>\n\n"
            f"🆔 <b>আইডি:</b> <code>{target_user_id}</code>\n"
            f"📛 <b>নাম:</b> {full_name}\n"
            f"📝 <b>ইউজারনেইম:</b> @{username}\n"
            f"🌍 <b>ভাষা:</b> {language.upper()}\n\n"
            f"💰 <b>ব্যালেন্স:</b> {earnings} টাকা\n\n"
            f"📁 <b>ফাইল স্ট্যাটাস</b>\n"
            f"⏳ পেন্ডিং: {pending}\n"
            f"⏳ রিপোর্ট অপেক্ষায়: {reported}\n"
            f"✅ এপ্রুভড: {approved}\n"
            f"❌ রিজেক্টেড: {rejected}\n\n"
            f"👥 রেফার করেছেন: {referral_count} জন"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 উইথড্র এপ্রুভ", callback_data=f"wd_approve_{target_user_id}")],
            [InlineKeyboardButton(text="❌ উইথড্র রিজেক্ট", callback_data=f"wd_reject_{target_user_id}")],
            [InlineKeyboardButton(text="🔙 ব্যাক", callback_data="main_menu")]
        ])

        await call.message.edit_text(profile_text, parse_mode="HTML", reply_markup=kb)
        await call.answer()

    except Exception as e:
        await call.answer("সমস্যা হয়েছে।", show_alert=True)
        print(f"Profile view error: {e}")

@dp.callback_query(F.data.startswith("wd_reject_"))
async def withdraw_reject(call: types.CallbackQuery, state: FSMContext):
    order_id = call.data.split("_")[2]

    await bot.send_message(call.from_user.id, "❌ রিজেক্টের কারণ লিখুন:")

    await state.update_data(reject_order_id=order_id)
    await state.set_state(AdminStates.reject_reason)

    await call.message.edit_text(call.message.text + "\n\n❌ <b>Rejected! কারণ লিখুন।</b>", parse_mode="HTML")
    await call.answer()


# রিজেক্ট কারণ রিসিভ + রিফান্ড
@dp.message(AdminStates.reject_reason)
async def admin_reject_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    order_id = data.get("reject_order_id")

    if not order_id or not reason:
        await message.answer("❌ কারণ লিখুন।")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, amount_bdt FROM withdraw_requests WHERE order_id = ? AND status = 'pending'", (order_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await message.answer("❌ রিকোয়েস্ট পাওয়া যায়নি।")
                return
            user_id, amount = row

        await db.execute("UPDATE withdraw_requests SET status = 'rejected', reject_reason = ? WHERE order_id = ?", (reason, order_id))
        await db.execute("UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?", (amount, user_id))  # রিফান্ড
        await db.commit()

    await bot.send_message(user_id, f"❌ আপনার উইথড্র রিকোয়েস্ট রিজেক্ট হয়েছে।\n🆔 অর্ডার: <code>{order_id}</code>\n📛 কারণ: {reason}")

    await message.answer(f"✅ অর্ডার {order_id} রিজেক্ট করা হয়েছে। টাকা রিফান্ড করা হয়েছে।")
    await state.clear()


# ইউজারের জন্য উইথড্র অর্ডার ট্র্যাক
@dp.callback_query(F.data == "track_order")
async def start_tracking(call: types.CallbackQuery, state: FSMContext):
    text = (
        "📋 <b>ট্র্যাক অর্ডার</b>\n\n"
        "আপনার অর্ডার আইডি লিখুন।\n\n"
        "উদাহরণ: <code>ABC123XYZ4</code>\n\n"
        "এটা হতে পারে ফাইলের অর্ডার বা উইথড্রের অর্ডার।"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_home())
    await state.set_state(States.tracking_order)
    await call.answer()

@dp.message(States.tracking_order)
async def process_tracking(message: types.Message, state: FSMContext):
    order_id = message.text.strip().upper()

    if len(order_id) < 8:
        await message.answer("❌ সঠিক অর্ডার আইডি লিখুন (কমপক্ষে ৮ অক্ষর)।", reply_markup=main_menu())
        await state.clear()
        return

    user_id = message.from_user.id
    found = False
    kb_rows = []  # কপি বাটনের জন্য

    async with aiosqlite.connect(DB_NAME) as db:
        # ফাইল চেক
        async with db.execute("""
            SELECT status, rate, data_count, category 
            FROM files 
            WHERE order_id = ? AND user_id = ?
        """, (order_id, user_id)) as cursor:
            file_row = await cursor.fetchone()

        if file_row:
            found = True
            status, rate, data_count, category = file_row
            total = rate * data_count

            status_text = {
                'pending': '⏳ পেন্ডিং',
                'reported': '⏳ রিপোর্টের অপেক্ষায়',
                'approved': '✅ এপ্রুভড (পেমেন্ট হয়েছে)',
                'rejected': '❌ রিজেক্টেড'
            }.get(status, status)

            text = (
                f"📁 <b>আপনার ফাইল অর্ডার</b>\n\n"
                f"🆔 অর্ডার আইডি: <code>{order_id}</code>\n"
                f"🔹 ক্যাটাগরি: {category.replace('_', ' ')}\n"
                f"📊 ডেটা সংখ্যা: {data_count}\n"
                f"💰 রেট: {rate} × {data_count} = <b>{total} টাকা</b>\n"
                f"📋 স্ট্যাটাস: <b>{status_text}</b>"
            )

            # কপি বাটন যোগ করা
            kb_rows.append([InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")])

        else:
            # উইথড্র চেক
            async with db.execute("""
                SELECT status, amount_bdt, method, reject_reason 
                FROM withdraw_requests 
                WHERE order_id = ? AND user_id = ?
            """, (order_id, user_id)) as cursor:
                wd_row = await cursor.fetchone()

            if wd_row:
                found = True
                status, amount, method, reason = wd_row

                status_text = {
                    'pending': '⏳ পেন্ডিং',
                    'approved': '✅ এপ্রুভড (পেমেন্ট হয়েছে)',
                    'rejected': '❌ রিজেক্টেড'
                }.get(status, status)

                text = (
                    f"💸 <b>আপনার উইথড্র অর্ডার</b>\n\n"
                    f"🆔 অর্ডার আইডি: <code>{order_id}</code>\n"
                    f"💳 মেথড: {method}\n"
                    f"💰 পরিমাণ: <b>{amount} টাকা</b>\n"
                    f"📋 স্ট্যাটাস: <b>{status_text}</b>"
                )
                if status == 'rejected' and reason:
                    text += f"\n📛 কারণ: {reason}"

                # কপি বাটন যোগ করা
                kb_rows.append([InlineKeyboardButton(text="📋 কপি অর্ডার আইডি", callback_data=f"copy_order_{order_id}")])

            else:
                text = f"❌ অর্ডার আইডি <code>{order_id}</code> পাওয়া যায়নি।\nদয়া করে সঠিক আইডি লিখুন।"

    # কীবোর্ড তৈরি
    if kb_rows:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    else:
        reply_markup = main_menu()

    await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
    await state.clear()
# উইথড্র স্টার্ট (মেনু থেকে)

@dp.callback_query(F.data.startswith("copy_order_"))
async def copy_order_id(call: types.CallbackQuery):
    order_id = call.data.split("_")[-1]
    await call.answer(order_id, show_alert=True)  # পপ-আপে দেখাবে + অটো কপি হবে

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

@dp.callback_query(F.data == "today_rate")
async def today_rate(call: types.CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT display_name, rate_bdt, format_text, last_time, report_time 
            FROM rates 
            WHERE display_name IS NOT NULL 
              AND display_name != 'None' 
              AND rate_bdt > 5 
            ORDER BY category
        """) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        text = "💰 <b>আজকের রেট</b>\n\nএখনো কোনো রেট আপডেট করা হয়নি। শীঘ্রই আপডেট করা হবে।"
    else:
        text = (
            "💎 <b>সবাই ID Submit শুরু করুন</b> 💎\n"
            "🌙 <b>সময়মতো Submit করতে থাকুন</b> 🌙\n\n"
            "   ⦅ <b>Submit Last Time : 11:00 PM</b> ⦆\n\n"
        )

        for name, rate, fmt, lt, rt in rows:
            usd = round(rate / 124, 2)
            # কয়েনের ক্ষেত্রে User: দেখানো
            if "Coin" in name:
                fmt = f"User: {fmt}"
            text += (
                f"<b>{name}</b>\n"
                f"💸 Members Rate: <b>{rate} BDT (${usd} USD)</b>\n"
                f"📄 Format: <b>{fmt}</b>\n"
                f"⏰ Last Time: <b>{lt}</b>\n"
                f"📊 Report Time: <b>{rt}</b>\n\n"
            )

        text += (
            "   《 <b>𝗔𝗹𝗹 𝗔𝗗𝗠𝗜𝗡 𝗥𝗔𝗧𝗘 𝗜𝗡𝗕𝗢𝗫</b> 》\n"
            "✅ Live Fresh ID Report 99+% 🔥 \n"
            "-------------------------------------------\n"
            "📛 কি ধরনের 𝐈𝐃 দিচ্ছেন তা অবশ্যই ফাইল নামে লিখে দিন ✅\n\n"
            "🚀 <b>সফলতার জন্য কঠোর পরিশ্রম করুন!</b>\n"
            "💪 <b>আমরা সবাই মিলে এগিয়ে যাই</b>\n\n"
            "📢 <b>আমাদের চ্যানেলে জয়েন করুন:</b>\n"
            "<b>https://t.me/genzinternational</b>"
        )

    kb = back_home_kb()
    await call.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data == "files_menu")
async def files_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    text = "📁 <b>আপনার ফাইল স্ট্যাটস</b>\n\n"
    async with aiosqlite.connect(DB_NAME) as db:
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
    async with aiosqlite.connect(DB_NAME) as db:
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
    async with aiosqlite.connect(DB_NAME) as db:
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, call.from_user.id))
        await db.commit()
    await call.message.edit_text(f"✅ ভাষা পরিবর্তন করা হয়েছে: {LANGUAGES[lang]['name']}", reply_markup=main_menu())
    await call.answer()

@dp.message(Command("pending"), F.from_user.id == ADMIN_ID)
async def list_pending(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT message_id, user_id, category, rate FROM files WHERE status = 'pending'") as cursor:
            rows = await cursor.fetchall()
    
    if not rows:
        await message.answer("কোনো পেন্ডিং ফাইল নেই।")
        return

    text = "⏳ <b>পেন্ডিং ফাইল লিস্ট</b>\n\n"
    for msg_id, user_id, cat, rate in rows:
        text += f"• আইডি: <code>{msg_id}</code> | ইউজার: <code>{user_id}</code> | ক্যাটাগরি: {cat} | রেট: {rate} টাকা\n"
        text += f"  /approve_{msg_id}  /reject_{msg_id}\n\n"

    await message.answer(text, parse_mode="HTML")

@dp.message(Command("reported"), F.from_user.id == ADMIN_ID)
async def list_reported(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT message_id, user_id, category, rate FROM files WHERE status = 'reported'") as cursor:
            rows = await cursor.fetchall()
    
    if not rows:
        await message.answer("কোনো রিপোর্ট অপেক্ষায় ফাইল নেই।")
        return

    text = "⏳ <b>রিপোর্ট অপেক্ষায় ফাইল লিস্ট</b>\n\n"
    for msg_id, user_id, cat, rate in rows:
        text += f"• আইডি: <code>{msg_id}</code> | ইউজার: <code>{user_id}</code> | ক্যাটাগরি: {cat} | রেট: {rate} টাকা\n\n"

    await message.answer(text, parse_mode="HTML")

# ম্যানুয়াল এপ্রুভ / রিজেক্ট (পরে করার জন্য)
@dp.message(Command("approve"))
async def manual_approve(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        msg_id = int(message.text.split()[1])
        # একই approve_file লজিক ব্যবহার করুন (কোড কপি করুন বা ফাংশন বানান)
        await message.answer("ম্যানুয়াল এপ্রুভ চালানো হয়েছে।")
    except:
        await message.answer("ব্যবহার: /approve message_id")

@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def broadcast(message: types.Message):
    if len(message.text.split(maxsplit=1)) < 2:
        await message.answer("❌ ব্যবহার: /broadcast আপনার মেসেজ")
        return
    text = message.text.split(maxsplit=1)[1]
    success = 0
    async with aiosqlite.connect(DB_NAME) as db:
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
    async with aiosqlite.connect(DB_NAME) as db:
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

    async with aiosqlite.connect(DB_NAME) as db:
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
# এডমিনের জন্য পাওয়ারফুল অর্ডার ট্র্যাক + একশন বাটন
@dp.message(Command("trackorder"), F.from_user.id == ADMIN_ID)
async def admin_track_order(message: types.Message):
    try:
        order_id = message.text.split()[1].upper()

        async with aiosqlite.connect(DB_NAME) as db:
            # প্রথমে ফাইল চেক
            async with db.execute("""
                SELECT f.order_id, f.user_id, f.category, f.rate, f.data_count, f.status,
                       u.full_name, u.username
                FROM files f
                JOIN users u ON f.user_id = u.user_id
                WHERE f.order_id = ?
            """, (order_id,)) as cursor:
                file_row = await cursor.fetchone()

            if file_row:
                order_id, user_id, category, rate, data_count, status, full_name, username = file_row
                total = rate * data_count

                status_text = {
                    'pending': '⏳ পেন্ডিং',
                    'reported': '⏳ রিপোর্টের অপেক্ষায়',
                    'approved': '✅ এপ্রুভড',
                    'rejected': '❌ রিজেক্টেড'
                }.get(status, status)

                text = (
                    f"📁 <b>ফাইল অর্ডার ডিটেইলস</b>\n\n"
                    f"🆔 অর্ডার: <code>{order_id}</code>\n"
                    f"👤 নাম: <b>{full_name}</b>\n"
                    f"📛 ইউজারনেইম: @{username or 'নেই'}\n"
                    f"🆔 আইডি: <code>{user_id}</code>\n"
                    f"🔹 ক্যাটাগরি: {category.replace('_', ' ')}\n"
                    f"📊 ডেটা: {data_count}\n"
                    f"💰 মোট: <b>{total} টাকা</b>\n"
                    f"📋 স্ট্যাটাস: <b>{status_text}</b>"
                )

                # বাটন যোগ করা — শুধু পেন্ডিং বা রিপোর্টেড হলে
                kb = []
                if status == 'pending':
                    kb.append([
                        InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve_file_{order_id}"),
                        InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject_file_{order_id}")
                    ])
                elif status == 'reported':
                    kb.append([InlineKeyboardButton(text="💸 Release (Pay)", callback_data=f"admin_release_file_{order_id}")])
                
                # সবসময় Deduct অপশন থাকবে (ভুল হলে টাকা কাটার জন্য)
                kb.append([InlineKeyboardButton(text="⚠️ Deduct Money", callback_data=f"admin_deduct_file_{order_id}")])

                reply_markup = InlineKeyboardMarkup(inline_keyboard=kb) if kb else None

                await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
                return

            # উইথড্র চেক
            async with db.execute("""
                SELECT w.order_id, w.user_id, w.amount_bdt, w.method, w.number, w.status,
                       u.full_name, u.username
                FROM withdraw_requests w
                JOIN users u ON w.user_id = u.user_id
                WHERE w.order_id = ?
            """, (order_id,)) as cursor:
                wd_row = await cursor.fetchone()

            if wd_row:
                order_id, user_id, amount, method, number, status, full_name, username = wd_row

                status_text = {
                    'pending': '⏳ পেন্ডিং',
                    'approved': '✅ এপ্রুভড',
                    'rejected': '❌ রিজেক্টেড'
                }.get(status, status)

                text = (
                    f"💸 <b>উইথড্র অর্ডার ডিটেইলস</b>\n\n"
                    f"🆔 অর্ডার: <code>{order_id}</code>\n"
                    f"👤 নাম: <b>{full_name}</b>\n"
                    f"📛 ইউজারনেইম: @{username or 'নেই'}\n"
                    f"🆔 আইডি: <code>{user_id}</code>\n"
                    f"💳 মেথড: {method}\n"
                    f"🔢 নম্বর: <code>{number}</code>\n"
                    f"💰 পরিমাণ: <b>{amount} টাকা</b>\n"
                    f"📋 স্ট্যাটাস: <b>{status_text}</b>"
                )

                kb = []
                if status == 'pending':
                    kb.append([
                        InlineKeyboardButton(text="✅ Approve Withdraw", callback_data=f"admin_approve_wd_{order_id}"),
                        InlineKeyboardButton(text="❌ Reject Withdraw", callback_data=f"admin_reject_wd_{order_id}")
                    ])

                reply_markup = InlineKeyboardMarkup(inline_keyboard=kb) if kb else None

                await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
                return

            # কিছুই পাওয়া গেল না
            await message.answer(f"❌ অর্ডার আইডি <code>{order_id}</code> পাওয়া যায়নি।")

    except IndexError:
        await message.answer("❌ ব্যবহার: /trackorder অর্ডার_আইডি\nউদাহরণ: /trackorder ABC123XYZ4")
    except Exception as e:
        await message.answer("❌ কোনো সমস্যা হয়েছে।")
        print(f"Admin Track Error: {e}")


# ফাইল এপ্রুভ (এডমিন থেকে)
@dp.callback_query(F.data.startswith("admin_approve_file_"))
async def admin_approve_file(call: types.CallbackQuery):
    order_id = call.data.split("_")[-1]
    # আপনার আগের approve_file লজিক ব্যবহার করুন বা এখানে সরাসরি
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, rate, data_count FROM files WHERE order_id = ?", (order_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id, rate, data_count = row
                await db.execute("UPDATE files SET status = 'reported' WHERE order_id = ?", (order_id,))
                await db.execute("UPDATE users SET pending = pending - 1, reported = reported + 1 WHERE user_id = ?", (user_id,))
                await db.commit()
                await bot.send_message(user_id, f"🎉 আপনার ফাইল এপ্রুভ হয়েছে! অর্ডার: {order_id}")
    await call.message.edit_text(call.message.text + "\n\n✅ এপ্রুভ করা হয়েছে।", parse_mode="HTML")
    await call.answer()

# ফাইল রিজেক্ট
@dp.callback_query(F.data.startswith("admin_reject_file_"))
async def admin_reject_file(call: types.CallbackQuery):
    order_id = call.data.split("_")[-1]
    # রিজেক্ট লজিক (কারণ চাইতে পারেন বা ডিফল্ট)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM files WHERE order_id = ?", (order_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id = row[0]
                await db.execute("UPDATE files SET status = 'rejected' WHERE order_id = ?", (order_id,))
                await db.execute("UPDATE users SET pending = pending - 1, rejected = rejected + 1 WHERE user_id = ?", (user_id,))
                await db.commit()
                await bot.send_message(user_id, f"❌ আপনার ফাইল রিজেক্ট হয়েছে। অর্ডার: {order_id}")
    await call.message.edit_text(call.message.text + "\n\n❌ রিজেক্ট করা হয়েছে।", parse_mode="HTML")
    await call.answer()

# রিলিজ (রিপোর্ট থেকে পে)
@dp.callback_query(F.data.startswith("admin_release_file_"))
async def admin_release_file(call: types.CallbackQuery):
    order_id = call.data.split("_")[-1]
    # আপনার release লজিক (যেমন আগের /release কমান্ড)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, rate, data_count FROM files WHERE order_id = ? AND status = 'reported'", (order_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id, rate, data_count = row
                amount = rate * data_count
                await db.execute("UPDATE users SET earnings_bdt = earnings_bdt + ?, reported = reported - 1, approved = approved + 1 WHERE user_id = ?", (amount, user_id))
                await db.execute("UPDATE files SET status = 'approved' WHERE order_id = ?", (order_id,))
                await db.commit()
                await bot.send_message(user_id, f"🎉 অর্ডার {order_id} রিলিজ হয়েছে! +{amount} টাকা যোগ হয়েছে।")
    await call.message.edit_text(call.message.text + "\n\n💸 রিলিজ করা হয়েছে।", parse_mode="HTML")
    await call.answer()

# উইথড্র এপ্রুভ ও রিজেক্ট (আগের লজিকের সাথে মিলিয়ে নিন)
@dp.callback_query(F.data.startswith("admin_approve_wd_"))
async def admin_approve_wd(call: types.CallbackQuery):
    order_id = call.data.split("_")[-1]
    # আপনার wd_approve লজিক কপি করুন
    await call.answer("এপ্রুভ করা হয়েছে।")

@dp.callback_query(F.data.startswith("admin_reject_wd_"))
async def admin_reject_wd(call: types.CallbackQuery):
    order_id = call.data.split("_")[-1]
    # রিজেক্ট + কারণ চাওয়া লজিক
    await call.answer("রিজেক্ট প্রক্রিয়া শুরু।")

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

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT full_name, earnings_bdt FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()

        if not user_row:
            await message.answer(f"❌ ইউজার আইডি <code>{user_id}</code> বটে পাওয়া যায়নি।", parse_mode="HTML")
            return

        user_name, current_balance = user_row
        new_balance = current_balance + amount

        await db.execute(
            "UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()

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


@dp.message(Command("deduct"), F.from_user.id == ADMIN_ID)
async def deduct_balance(message: types.Message):
    try:
        args = message.text.split(maxsplit=3)
        order_id = args[1]
        amount = float(args[2])
        reason = args[3] if len(args) > 3 else "ভুল রিলিজ"

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT user_id FROM files WHERE order_id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await message.answer("অর্ডার পাওয়া যায়নি।")
                return
            user_id = row[0]
            await db.execute("UPDATE users SET earnings_bdt = earnings_bdt - ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

        await bot.send_message(user_id, f"⚠️ অর্ডার {order_id} থেকে {amount} টাকা কাটা হয়েছে।\nকারণ: {reason}")
        await message.answer("টাকা কাটা হয়েছে।")

    except:
        await message.answer("ব্যবহার: /deduct অর্ডার_আইডি পরিমাণ [কারণ]")

@dp.message(Command("setrate"), F.from_user.id == ADMIN_ID)
async def set_rate(message: types.Message):
    lines = message.text.splitlines()[1:]  # /setrate এর পরের লাইনগুলো
    if not lines:
        await message.answer(
            "❌ সঠিক ব্যবহার:\n\n"
            "/setrate\n"
            "Webmail=7.70|UID - Pass - 2FA|11 PM BD|24 hours\n"
            "Niva Coin=5.00|User - Pass|11 PM BD|24 hours"
        )
        return

    updated = []
    cat_map = {
        "Webmail": "Facebook_Webmail",
        "Anymail": "Facebook_Anymail",
        "Number": "Facebook_Number",
        "PC Clone 1000x": "Facebook_PC Clone Cookies",
        "6155/56x Cookies": "Facebook_PC Clone Cookies",
        "Instagram Cookies": "Instagram_Instagram Cookies",
        "Instagram 2FA": "Instagram_Instagram 2FA",
        "Niva Coin": "Coins_Niva Coin",
        "NS Coin": "Coins_NS Coin",
        "Topfollow": "Coins_Topfollow",
        "Nitra Coin": "Coins_Nitra Coin",
        "Gmail Files": "Gmail_Gmail Files",
        "Random Gmail": "Gmail_Random Gmail",
        "Other Files": "Others_Other Files"
    }

    async with aiosqlite.connect(DB_NAME) as db:
        for line in lines:
            line = line.strip()
            if not line or '=' not in line:
                continue

            cat_name, value = line.split('=', 1)
            cat_name = cat_name.strip()
            db_cat = cat_map.get(cat_name)

            if not db_cat:
                continue  # যদি ম্যাপে না থাকে, স্কিপ করো

            parts = [p.strip() for p in value.split('|')]
            try:
                rate = float(parts[0])
            except:
                continue

            format_text = parts[1] if len(parts) > 1 else "UID | Pass | 2FA"
            last_time = parts[2] if len(parts) > 2 else "11:00 PM BD"
            report_time = parts[3] if len(parts) > 3 else "24 Hours"

            await db.execute("""
                INSERT OR REPLACE INTO rates
                (category, rate_bdt, display_name, format_text, last_time, report_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (db_cat, rate, cat_name, format_text, last_time, report_time))

            updated.append((cat_name, rate, format_text, last_time, report_time))

        await db.commit()

    # বাকি কোড (ব্রডকাস্ট ইত্যাদি) আগের মতোই থাকবে
    if not updated:
        await message.answer("কোনো রেট আপডেট হয়নি।")
        return

    # সুন্দর ব্রডকাস্ট
    broadcast_text = (
        "💎 <b>সবাই ID Submit শুরু করুন</b> 💎\n"
        "🌙 <b>সময়মতো Submit করতে থাকুন</b> 🌙\n\n"
        "   ⦅ <b>Submit Last Time : 11:00 PM</b> ⦆\n\n"
    )

    for cat, rate, fmt, lt, rt in updated:
        usd = round(rate / 124, 2)
        broadcast_text += (
            f"<b>{cat}</b>\n"
            f"💸 Members Rate: <b>{rate} BDT (${usd} USD)</b>\n"
            f"📄 Format: <b>{fmt}</b>\n"
            f"⏰ Last Time: <b>{lt}</b>\n"
            f"📊 Report Time: <b>{rt}</b>\n\n"
        )

    broadcast_text += (
        "   《 <b>𝗔𝗹𝗹 𝗔𝗗𝗠𝗜𝗡 𝗥𝗔𝗧𝗘 𝗜𝗡𝗕𝗢𝗫</b> 》\n"
        "✅ Live Fresh ID Report 99+% 🔥 \n"
        "-------------------------------------------\n"
        "📛 কি ধরনের 𝐈𝐃 দিচ্ছেন তা অবশ্যই ফাইল নামে লিখে দিন ✅\n\n"
        "🚀 <b>সফলতার জন্য কঠোর পরিশ্রম করুন!</b>\n"
        "💪 <b>আমরা সবাই মিলে এগিয়ে যাই</b>\n\n"
        "📢 <b>আমাদের চ্যানেলে জয়েন করুন:</b>\n"
        "<b>https://t.me/genzinternational</b>"
    )

    # সবাইকে ব্রডকাস্ট
    count = 0
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            for (uid,) in rows:
                try:
                    await bot.send_message(uid, broadcast_text, parse_mode="HTML", disable_web_page_preview=True)
                    count += 1
                except:
                    pass

    await message.answer(f"✅ রেট আপডেট + {count} জনকে ব্রডকাস্ট করা হয়েছে।")

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
    async with aiosqlite.connect(DB_NAME) as db:
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
    async with aiosqlite.connect(DB_NAME) as db:
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
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO toggles (item, enabled) VALUES (?, ?)", (full_cat, status))
        await db.commit()
    
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
    async with aiosqlite.connect(DB_NAME) as db:
        while current and level < 5:
            async with db.execute("SELECT referrer FROM users WHERE user_id = ?", (current,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    referrer = row[0]
                    bonus = bonuses[level]
                    await db.execute("UPDATE users SET earnings_bdt = earnings_bdt + ? WHERE user_id = ?", (bonus, referrer))
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
            async with aiosqlite.connect(DB_NAME) as db:
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
