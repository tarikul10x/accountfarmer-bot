import aiosqlite

DB_NAME = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                referrer INTEGER,
                pending_files INTEGER DEFAULT 0,
                approved_files INTEGER DEFAULT 0,
                total_earnings_bdt REAL DEFAULT 0,
                total_earnings_usd REAL DEFAULT 0,
                language TEXT DEFAULT 'bn',
                payment_method TEXT,
                payment_number TEXT,
                is_premium INTEGER DEFAULT 0,
                referral_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS rates (
                date TEXT PRIMARY KEY,
                rate_bdt REAL DEFAULT 5,
                rate_usd REAL DEFAULT 0.04
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        ''')
        # Default settings
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('refer_bonus_bdt', '10')")
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_user(user_id, username, full_name, referrer=None, lang='bn'):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, username, full_name, referrer, language, referral_count)
            VALUES (?, ?, ?, ?, ?, 
                COALESCE((SELECT referral_count FROM users WHERE user_id = ?), 0))
        """, (user_id, username, full_name, referrer, lang, user_id))
        await db.commit()
        # Update referrer count and bonus
        if referrer:
            await update_referral_chain(referrer, user_id)

async def update_referral_chain(new_user_id, referred_by_chain):
    # Simple 5 level 20% decreasing bonus (example: 100%, 50%, 25%, 12.5%, 6.25%)
    bonuses = [10, 5, 2.5, 1.25, 0.625]  # BDT
    current = new_user_id
    level = 0
    async with aiosqlite.connect(DB_NAME) as db:
        while current and level < 5:
            async with db.execute("SELECT referrer FROM users WHERE user_id = ?", (current,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    referrer = row[0]
                    bonus_bdt = bonuses[level]
                    await db.execute("UPDATE users SET total_earnings_bdt = total_earnings_bdt + ? WHERE user_id = ?", (bonus_bdt, referrer))
                    await db.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (referrer,))
                    # Check premium
                    await db.execute("UPDATE users SET is_premium = 1 WHERE user_id = ? AND referral_count >= 100", (referrer,))
                    current = referrer
                    level += 1
                else:
                    break
        await db.commit()
