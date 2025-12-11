#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kapan Bayar Bot - Telegram Debt Tracker Bot
Bot untuk mencatat dan mengingatkan utang dengan fitur lengkap
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile,
    Message,
    ChatMember
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

# Load environment variables
load_dotenv()

# Konfigurasi
TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))
BOT_USERNAME = "KapanBayarBot"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Direktori database
DATABASE_DIR = Path("database")
DATABASE_DIR.mkdir(exist_ok=True)

# File users.json
USERS_FILE = Path("users.json")
# File join groups
JOIN_FILE = Path("join_groups.json")
# File join users tracking
JOIN_USERS_FILE = Path("join_users.json")

# Inisialisasi file join
if not JOIN_FILE.exists():
    with open(JOIN_FILE, 'w', encoding='utf-8') as f:
        json.dump({"groups": []}, f, indent=2)

if not JOIN_USERS_FILE.exists():
    with open(JOIN_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"users": {}}, f, indent=2)

# Class untuk mengelola utang
class DebtManager:
    @staticmethod
    def get_user_file(user_id: int) -> Path:
        """Mendapatkan file JSON untuk user tertentu"""
        return DATABASE_DIR / f"{user_id}.json"
    
    @staticmethod
    def load_user_debts(user_id: int) -> Dict:
        """Memuat data utang user"""
        user_file = DebtManager.get_user_file(user_id)
        if user_file.exists():
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"debts": [], "notification_interval": 5, "is_notification_paused": False}
    
    @staticmethod
    def save_user_debts(user_id: int, data: Dict):
        """Menyimpan data utang user"""
        user_file = DebtManager.get_user_file(user_id)
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def add_debt(user_id: int, debt_data: Dict):
        """Menambahkan utang baru"""
        data = DebtManager.load_user_debts(user_id)
        debt_data["id"] = len(data["debts"]) + 1
        debt_data["created_at"] = datetime.now().isoformat()
        data["debts"].append(debt_data)
        DebtManager.save_user_debts(user_id, data)
        return debt_data["id"]
    
    @staticmethod
    def delete_debt(user_id: int, debt_id: int) -> bool:
        """Menghapus utang berdasarkan ID"""
        data = DebtManager.load_user_debts(user_id)
        original_length = len(data["debts"])
        data["debts"] = [d for d in data["debts"] if d["id"] != debt_id]
        
        # Update ID setelah penghapusan
        for i, debt in enumerate(data["debts"], 1):
            debt["id"] = i
        
        DebtManager.save_user_debts(user_id, data)
        return len(data["debts"]) != original_length
    
    @staticmethod
    def get_debt(user_id: int, debt_id: int) -> Optional[Dict]:
        """Mendapatkan utang berdasarkan ID"""
        data = DebtManager.load_user_debts(user_id)
        for debt in data["debts"]:
            if debt["id"] == debt_id:
                return debt
        return None
    
    @staticmethod
    def get_all_debts(user_id: int) -> List[Dict]:
        """Mendapatkan semua utang user"""
        data = DebtManager.load_user_debts(user_id)
        return data["debts"]
    
    @staticmethod
    def get_total_debt_amount(user_id: int) -> float:
        """Menghitung total jumlah utang"""
        debts = DebtManager.get_all_debts(user_id)
        total = 0
        for debt in debts:
            try:
                # Remove currency symbols and convert to float
                amount_str = str(debt["amount"]).replace('k', '000').replace('K', '000')
                amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                total += float(amount_str)
            except:
                continue
        return total
    
    @staticmethod
    def update_notification_interval(user_id: int, interval: int):
        """Memperbarui interval notifikasi"""
        data = DebtManager.load_user_debts(user_id)
        data["notification_interval"] = interval
        DebtManager.save_user_debts(user_id, data)
    
    @staticmethod
    def toggle_notification_pause(user_id: int, pause: bool):
        """Mengaktifkan/menonaktifkan notifikasi"""
        data = DebtManager.load_user_debts(user_id)
        data["is_notification_paused"] = pause
        DebtManager.save_user_debts(user_id, data)

# Class untuk mengelola user
class UserManager:
    @staticmethod
    def load_users() -> Dict:
        """Memuat data semua user"""
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"users": {}}
    
    @staticmethod
    def save_users(data: Dict):
        """Menyimpan data user"""
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def add_user(user_id: int, username: str, first_name: str):
        """Menambahkan user baru"""
        data = UserManager.load_users()
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "username": username,
                "first_name": first_name,
                "joined_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            UserManager.save_users(data)
    
    @staticmethod
    def update_last_active(user_id: int):
        """Memperbarui waktu aktif terakhir user"""
        data = UserManager.load_users()
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["last_active"] = datetime.now().isoformat()
            UserManager.save_users(data)
    
    @staticmethod
    def get_total_users() -> int:
        """Mendapatkan total jumlah user"""
        data = UserManager.load_users()
        return len(data["users"])
    
    @staticmethod
    def get_all_user_ids() -> List[int]:
        """Mendapatkan semua ID user"""
        data = UserManager.load_users()
        return [int(user_id) for user_id in data["users"].keys()]

# Class untuk mengelola join groups
class JoinGroupManager:
    @staticmethod
    def load_groups() -> Dict:
        """Memuat data groups yang wajib diikuti"""
        if JOIN_FILE.exists():
            with open(JOIN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"groups": []}
    
    @staticmethod
    def save_groups(data: Dict):
        """Menyimpan data groups"""
        with open(JOIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def add_group(group_username: str):
        """Menambahkan group baru"""
        data = JoinGroupManager.load_groups()
        
        # Hapus @ jika ada
        if group_username.startswith('@'):
            group_username = group_username[1:]
        
        if group_username not in data["groups"]:
            data["groups"].append(group_username)
            JoinGroupManager.save_groups(data)
            return True
        return False
    
    @staticmethod
    def remove_group(index: int) -> bool:
        """Menghapus group berdasarkan index"""
        data = JoinGroupManager.load_groups()
        if 0 <= index < len(data["groups"]):
            removed = data["groups"].pop(index)
            JoinGroupManager.save_groups(data)
            return removed
        return False
    
    @staticmethod
    def get_all_groups() -> List[str]:
        """Mendapatkan semua groups"""
        data = JoinGroupManager.load_groups()
        return data["groups"]
    
    @staticmethod
    def get_groups_count() -> int:
        """Mendapatkan jumlah groups"""
        data = JoinGroupManager.load_groups()
        return len(data["groups"])
    
    @staticmethod
    def load_join_users() -> Dict:
        """Memuat data user yang sudah join"""
        if JOIN_USERS_FILE.exists():
            with open(JOIN_USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"users": {}}
    
    @staticmethod
    def save_join_users(data: Dict):
        """Menyimpan data user yang sudah join"""
        with open(JOIN_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def update_user_join_status(user_id: int, groups_status: Dict):
        """Memperbarui status join user"""
        data = JoinGroupManager.load_join_users()
        data["users"][str(user_id)] = {
            "groups_status": groups_status,
            "last_checked": datetime.now().isoformat()
        }
        JoinGroupManager.save_join_users(data)
    
    @staticmethod
    def get_user_join_status(user_id: int) -> Dict:
        """Mendapatkan status join user"""
        data = JoinGroupManager.load_join_users()
        return data["users"].get(str(user_id), {"groups_status": {}})
    
    @staticmethod
    def check_all_users_joined() -> Dict:
        """Memeriksa semua user yang sudah join"""
        groups = JoinGroupManager.get_all_groups()
        user_data = JoinGroupManager.load_join_users()
        
        result = {}
        for group in groups:
            result[group] = []
        
        for user_id_str, user_info in user_data["users"].items():
            user_id = int(user_id_str)
            user_status = user_info.get("groups_status", {})
            
            for group in groups:
                if user_status.get(group, False):
                    result[group].append(user_id)
        
        return result

# Notifikasi Manager
class NotificationManager:
    _instance = None
    _active_notifications = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._running = True
            cls._instance._thread = threading.Thread(target=cls._instance._check_notifications, daemon=True)
            cls._instance._thread.start()
        return cls._instance
    
    def _check_notifications(self):
        """Thread untuk memeriksa dan mengirim notifikasi"""
        while self._running:
            try:
                user_files = list(DATABASE_DIR.glob("*.json"))
                
                for user_file in user_files:
                    try:
                        user_id = int(user_file.stem)
                        with open(user_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if data.get("is_notification_paused", False):
                            continue
                        
                        notification_interval = data.get("notification_interval", 5)
                        
                        for debt in data.get("debts", []):
                            if debt.get("payment_date") and debt.get("notification_time"):
                                try:
                                    payment_date_str = debt["payment_date"]
                                    notification_time_str = debt["notification_time"]
                                    
                                    # Parse tanggal dan waktu
                                    payment_date = datetime.strptime(payment_date_str, "%Y/%m/%d").date()
                                    notification_time = datetime.strptime(notification_time_str, "%H:%M").time()
                                    
                                    # Buat datetime lengkap
                                    notification_datetime = datetime.combine(payment_date, notification_time)
                                    
                                    # Jika sudah lewat waktu notifikasi hari ini
                                    now = datetime.now()
                                    if now >= notification_datetime:
                                        # Periksa apakah sudah mengirim notifikasi hari ini
                                        last_notified = debt.get("last_notified")
                                        if last_notified:
                                            last_notified_date = datetime.fromisoformat(last_notified).date()
                                            if last_notified_date == now.date():
                                                continue
                                        
                                        # Update last_notified
                                        debt["last_notified"] = now.isoformat()
                                        DebtManager.save_debts(user_id, data)
                                        
                                except Exception as e:
                                    logger.error(f"Error processing notification: {e}")
                                    continue
                    
                    except Exception as e:
                        logger.error(f"Error checking notifications for {user_file}: {e}")
                
                time.sleep(60)  # Cek setiap menit
            
            except Exception as e:
                logger.error(f"Error in notification thread: {e}")
                time.sleep(60)
    
    def stop(self):
        """Menghentikan thread notifikasi"""
        self._running = False
        if self._thread:
            self._thread.join()

# Fungsi untuk mengecek apakah user sudah join semua group
async def check_user_joined_all_groups(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Mengecek apakah user sudah join semua group yang diwajibkan"""
    groups = JoinGroupManager.get_all_groups()
    
    if not groups:
        return True  # Tidak ada group yang diwajibkan
    
    user_status = JoinGroupManager.get_user_join_status(user_id)
    groups_status = user_status.get("groups_status", {})
    
    # Jika belum pernah dicek atau perlu dicek ulang
    last_checked = user_status.get("last_checked")
    if last_checked:
        last_checked_time = datetime.fromisoformat(last_checked)
        if (datetime.now() - last_checked_time).seconds < 300:  # Cache 5 menit
            # Gunakan data cache
            return all(groups_status.get(group, False) for group in groups)
    
    # Cek status join untuk setiap group
    new_status = {}
    all_joined = True
    
    for group in groups:
        try:
            chat_member = await context.bot.get_chat_member(f"@{group}", user_id)
            is_member = chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
            new_status[group] = is_member
            
            if not is_member:
                all_joined = False
        except Exception as e:
            logger.error(f"Error checking membership for {user_id} in @{group}: {e}")
            new_status[group] = False
            all_joined = False
    
    # Update status user
    JoinGroupManager.update_user_join_status(user_id, new_status)
    
    return all_joined

# Fungsi untuk membuat keyboard utama
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Membuat keyboard utama"""
    keyboard = [
        [KeyboardButton("➕ Tambah Utang"), KeyboardButton("🗑️ Hapus Utang")],
        [KeyboardButton("📋 Daftar Utang"), KeyboardButton("⏸️ Jeda Notifikasi")],
        [KeyboardButton("❓ Panduan"), KeyboardButton("💝 Support Developer")],
        [KeyboardButton("⬅️ Kembali ke Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_join_keyboard(groups: List[str]) -> InlineKeyboardMarkup:
    """Membuat keyboard untuk join group"""
    keyboard = []
    
    for group in groups:
        keyboard.append([
            InlineKeyboardButton(f"🔗 Join @{group}", url=f"https://t.me/{group}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ Sudah Join", callback_data="check_join")
    ])
    
    return InlineKeyboardMarkup(keyboard)

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user = update.effective_user
    user_id = user.id
    
    # Tambah user ke database
    UserManager.add_user(user_id, user.username, user.first_name)
    UserManager.update_last_active(user_id)
    
    # Cek apakah user harus join group
    groups = JoinGroupManager.get_all_groups()
    if groups:
        all_joined = await check_user_joined_all_groups(user_id, context)
        
        if not all_joined:
            # Tampilkan pesan untuk join group
            group_list = "\n".join([f"• @{group}" for group in groups])
            
            await update.message.reply_text(
                f"👋 **Halo {user.first_name}!**\n\n"
                f"📢 **Untuk menggunakan bot ini, Anda harus bergabung dengan group/channel berikut:**\n\n"
                f"{group_list}\n\n"
                f"✅ **Setelah bergabung, klik tombol 'Sudah Join' di bawah.**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_join_keyboard(groups)
            )
            return
    
    # Kirim foto jika ada
    try:
        if os.path.exists("icon.png"):
            with open("icon.png", 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"✨ **Selamat datang di Kapan Bayar Bot!** ✨\n\n"
                           f"Halo {user.first_name}! 👋\n\n"
                           f"Saya adalah asisten pribadi Anda untuk mencatat dan mengingatkan utang. "
                           f"Dengan saya, Anda tidak akan lupa menagih utang lagi! 💼\n\n"
                           f"📊 **Fitur Utama:**\n"
                           f"• ✅ Catat utang dengan detail lengkap\n"
                           f"• 🔔 Pengingat otomatis\n"
                           f"• 📋 Daftar utang terorganisir\n"
                           f"• ⏸️ Kontrol notifikasi fleksibel\n\n"
                           f"Gunakan tombol di bawah untuk mulai! 🚀",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_keyboard()
                )
        else:
            await update.message.reply_text(
                f"✨ **Selamat datang di Kapan Bayar Bot!** ✨\n\n"
                f"Halo {user.first_name}! 👋\n\n"
                f"Saya adalah asisten pribadi Anda untuk mencatat dan mengingatkan utang. "
                f"Dengan saya, Anda tidak akan lupa menagih utang lagi! 💼\n\n"
                f"📊 **Fitur Utama:**\n"
                f"• ✅ Catat utang dengan detail lengkap\n"
                f"• 🔔 Pengingat otomatis\n"
                f"• 📋 Daftar utang terorganisir\n"
                f"• ⏸️ Kontrol notifikasi fleksibel\n\n"
                f"Gunakan tombol di bawah untuk mulai! 🚀",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        await update.message.reply_text(
            f"Halo {user.first_name}! Selamat datang di Kapan Bayar Bot!",
            reply_markup=get_main_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help"""
    help_text = (
        "📚 **Panduan Penggunaan Kapan Bayar Bot** 📚\n\n"
        
        "✨ **Fitur Utama:**\n"
        "1. ➕ **Tambah Utang** - Catat utang baru dengan detail lengkap\n"
        "2. 🗑️ **Hapus Utang** - Hapus utang yang sudah selesai\n"
        "3. 📋 **Daftar Utang** - Lihat semua utang yang tercatat\n"
        "4. ⏸️ **Jeda Notifikasi** - Atur interval pengingat\n"
        "5. 💝 **Support Developer** - Dukung pengembangan bot\n\n"
        
        "📝 **Cara Mencatat Utang:**\n"
        "1. Klik '➕ Tambah Utang'\n"
        "2. Isi format: Nama | Jumlah | Tanggal | Jam | Catatan\n"
        "   Contoh: `John | 100k | 2025/12/20 | 12:30 | Utang makan siang`\n"
        "3. Tanggal dan jam bisa dikosongkan\n\n"
        
        "🔔 **Sistem Notifikasi:**\n"
        "• Bot akan mengingatkan saat jatuh tempo\n"
        "• Bisa atur interval pengingat\n"
        "• Bisa pause/tunda notifikasi\n\n"
        
        "💡 **Tips:**\n"
        "• Gunakan format yang benar untuk hasil terbaik\n"
        "• Update status utang setelah ditagih/dibayar\n"
        "• Gunakan fitur jeda jika butuh waktu\n\n"
        "📞 **Butuh bantuan?** Hubungi developer melalui menu Support!"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# Handler untuk tombol
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol inline"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "check_join":
        # Cek apakah user sudah join semua group
        groups = JoinGroupManager.get_all_groups()
        all_joined = await check_user_joined_all_groups(user_id, context)
        
        if all_joined:
            await query.edit_message_text(
                "✅ **Verifikasi berhasil!**\n\n"
                "Anda telah bergabung dengan semua group yang diwajibkan.\n\n"
                "Sekarang Anda dapat menggunakan bot ini sepenuhnya!",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Kirim menu utama
            await query.message.reply_text(
                "🎉 **Selamat!** Anda sekarang dapat menggunakan semua fitur bot.\n"
                "Pilih menu di bawah:",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ **Anda belum bergabung dengan semua group!**\n\n"
                "Silakan bergabung dengan semua group yang tertera di atas, "
                "kemudian klik 'Sudah Join' lagi.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_join_keyboard(groups)
            )
    
    elif data.startswith("paid_"):
        debt_id = int(data.split("_")[1])
        if DebtManager.delete_debt(user_id, debt_id):
            await query.edit_message_text(
                "✅ **Utang berhasil ditandai sebagai sudah dibayar!**\n"
                "Data telah dihapus dari catatan.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                "❌ **Gagal menandai utang.**\n"
                "Silakan coba lagi atau hubungi developer.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("snooze_"):
        debt_id = int(data.split("_")[1])
        debt = DebtManager.get_debt(user_id, debt_id)
        if debt:
            # Update notification time untuk 1 jam lagi
            new_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
            await query.edit_message_text(
                f"⏸️ **Notifikasi ditunda 1 jam.**\n"
                f"Pengingat berikutnya: {new_time}",
                parse_mode=ParseMode.MARKDOWN
            )

# Handler untuk pesan teks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan teks"""
    user = update.effective_user
    user_id = user.id
    text = update.message.text
    
    # Update last active
    UserManager.update_last_active(user_id)
    
    # Cek apakah user harus join group/channel
    groups = JoinGroupManager.get_all_groups()
    if groups:
        all_joined = await check_user_joined_all_groups(user_id, context)
        
        if not all_joined:
            # Cek apakah ini perintah khusus yang diizinkan
            allowed_commands = ['/start', '/help']
            if text.startswith(tuple(allowed_commands)):
                pass  # Izinkan perintah ini
            elif text == "⬅️ Kembali ke Menu":
                # Tampilkan pesan join lagi
                group_list = "\n".join([f"• @{group}" for group in groups])
                
                await update.message.reply_text(
                    f"📢 **Untuk menggunakan bot ini, Anda harus bergabung dengan group/channel berikut:**\n\n"
                    f"{group_list}\n\n"
                    f"✅ **Setelah bergabung, klik tombol 'Sudah Join'.**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_join_keyboard(groups)
                )
                return
            else:
                # Tampilkan pesan untuk join group
                group_list = "\n".join([f"• @{group}" for group in groups])
                
                await update.message.reply_text(
                    f"⛔ **Akses Dibatasi**\n\n"
                    f"Anda harus bergabung dengan group/channel berikut terlebih dahulu:\n\n"
                    f"{group_list}\n\n"
                    f"Setelah bergabung, gunakan /start untuk verifikasi.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_join_keyboard(groups)
                )
                return
    
    # Handler untuk menu
    if text == "➕ Tambah Utang":
        await update.message.reply_text(
            "📝 **Tambahkan Utang Baru**\n\n"
            "Silakan kirim data utang dengan format:\n"
            "`Nama | Jumlah | Tanggal Bayar | Jam Notif | Catatan`\n\n"
            "🔸 **Contoh:**\n"
            "`John | 100k | 2025/12/20 | 12:30 | Utang makan siang`\n\n"
            "💡 **Catatan:**\n"
            "• Tanggal format: YYYY/MM/DD\n"
            "• Jam format: HH:MM (24 jam)\n"
            "• Tanggal dan jam bisa dikosongkan\n"
            "• Pisahkan dengan tanda pipe (|)",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["state"] = "adding_debt"
    
    elif text == "🗑️ Hapus Utang":
        debts = DebtManager.get_all_debts(user_id)
        if not debts:
            await update.message.reply_text(
                "📭 **Tidak ada utang yang tercatat.**\n"
                "Tambahkan utang terlebih dahulu.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
            return
        
        # Buat daftar utang
        debt_list = "📋 **Daftar Utang:**\n\n"
        for debt in debts:
            debt_list += (
                f"{debt['id']}. **{debt.get('debtor_name', 'Tidak diketahui')}**\n"
                f"   💰 {debt.get('amount', '0')}\n"
                f"   📅 {debt.get('payment_date', 'Tidak ditentukan')}\n\n"
            )
        
        debt_list += "Ketik nomor utang yang ingin dihapus:"
        
        await update.message.reply_text(
            debt_list,
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["state"] = "deleting_debt"
    
    elif text == "📋 Daftar Utang":
        debts = DebtManager.get_all_debts(user_id)
        if not debts:
            await update.message.reply_text(
                "📭 **Tidak ada utang yang tercatat.**\n"
                "Tambahkan utang terlebih dahulu.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
            return
        
        # Buat daftar utang
        debt_list = "📊 **Daftar Utang Anda:**\n\n"
        total_amount = 0
        
        for debt in debts:
            debt_list += (
                f"🔸 **{debt.get('debtor_name', 'Tidak diketahui')}**\n"
                f"   💰 **Jumlah:** {debt.get('amount', '0')}\n"
                f"   📅 **Jatuh tempo:** {debt.get('payment_date', 'Tidak ditentukan')}\n"
                f"   ⏰ **Notif:** {debt.get('notification_time', 'Tidak diatur')}\n"
                f"   📝 **Catatan:** {debt.get('notes', 'Tidak ada')}\n\n"
            )
            
            # Hitung total
            try:
                amount_str = str(debt.get('amount', '0')).replace('k', '000').replace('K', '000')
                amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                total_amount += float(amount_str)
            except:
                continue
        
        # Format total amount
        if total_amount >= 1000000:
            total_str = f"{total_amount/1000000:.1f}M"
        elif total_amount >= 1000:
            total_str = f"{total_amount/1000:.0f}k"
        else:
            total_str = str(int(total_amount))
        
        debt_list += f"💰 **Total Utang:** Rp {total_str}"
        
        await update.message.reply_text(
            debt_list,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    
    elif text == "⏸️ Jeda Notifikasi":
        await update.message.reply_text(
            "⏸️ **Atur Interval Notifikasi**\n\n"
            "Kirim jumlah menit untuk interval notifikasi:\n"
            "Contoh: `5` (untuk setiap 5 menit)\n"
            "Contoh: `0` (untuk menonaktifkan)\n\n"
            "💡 **Default:** 5 menit",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["state"] = "setting_interval"
    
    elif text == "❓ Panduan":
        await help_command(update, context)
    
    elif text == "💝 Support Developer":
        try:
            if os.path.exists("qris.jpeg"):
                with open("qris.jpeg", 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=(
                            "💖 **Support Developer** 💖\n\n"
                            "Dukung pengembangan bot ini agar terus berkembang!\n\n"
                            "💳 **Donasi via QRIS:**\n"
                            "Scan QR code di atas\n\n"
                            "🌎 **Cryptocurrency:**\n"
                            "• **BTC:** `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`\n"
                            "• **ETH/USDT (ERC20):** `0x742d35Cc6634C0532925a3b844Bc9e0F4Bf5aC32`\n\n"
                            "💝 **Terima kasih atas supportnya!**\n"
                            "Setiap donasi sangat berarti untuk pengembangan bot."
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_main_keyboard()
                    )
            else:
                await update.message.reply_text(
                    "💖 **Support Developer** 💖\n\n"
                    "Dukung pengembangan bot ini agar terus berkembang!\n\n"
                    "🌎 **Cryptocurrency:**\n"
                    "• **BTC:** `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`\n"
                    "• **ETH/USDT (ERC20):** `0x742d35Cc6634C0532925a3b844Bc9e0F4Bf5aC32`\n\n"
                    "💝 **Terima kasih atas supportnya!**\n"
                    "Setiap donasi sangat berarti untuk pengembangan bot.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_keyboard()
                )
        except Exception as e:
            logger.error(f"Error sending support info: {e}")
            await update.message.reply_text(
                "💖 Terima kasih minat untuk support developer!",
                reply_markup=get_main_keyboard()
            )
    
    elif text == "⬅️ Kembali ke Menu":
        await update.message.reply_text(
            "🏠 **Kembali ke Menu Utama**\n"
            "Pilih opsi di bawah:",
            reply_markup=get_main_keyboard()
        )
    
    else:
        # Handle state-based messages
        state = context.user_data.get("state")
        
        if state == "adding_debt":
            # Parse debt data
            parts = [part.strip() for part in text.split('|')]
            
            if len(parts) < 2:
                await update.message.reply_text(
                    "❌ **Format salah!**\n"
                    "Minimal: Nama | Jumlah\n"
                    "Contoh: `John | 100k`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            debtor_name = parts[0]
            amount = parts[1]
            payment_date = parts[2] if len(parts) > 2 else None
            notification_time = parts[3] if len(parts) > 3 else None
            notes = parts[4] if len(parts) > 4 else ""
            
            # Validate date format
            if payment_date:
                try:
                    datetime.strptime(payment_date, "%Y/%m/%d")
                except ValueError:
                    await update.message.reply_text(
                        "❌ **Format tanggal salah!**\n"
                        "Gunakan format: YYYY/MM/DD\n"
                        "Contoh: 2025/12/20",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            
            # Validate time format
            if notification_time:
                try:
                    datetime.strptime(notification_time, "%H:%M")
                except ValueError:
                    await update.message.reply_text(
                        "❌ **Format waktu salah!**\n"
                        "Gunakan format: HH:MM (24 jam)\n"
                        "Contoh: 14:30",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            
            # Save debt
            debt_data = {
                "debtor_name": debtor_name,
                "amount": amount,
                "payment_date": payment_date,
                "notification_time": notification_time,
                "notes": notes
            }
            
            debt_id = DebtManager.add_debt(user_id, debt_data)
            
            await update.message.reply_text(
                f"✅ **Utang berhasil ditambahkan!**\n\n"
                f"📌 **ID:** {debt_id}\n"
                f"👤 **Nama:** {debtor_name}\n"
                f"💰 **Jumlah:** {amount}\n"
                f"📅 **Tanggal:** {payment_date or 'Tidak ditentukan'}\n"
                f"⏰ **Notif:** {notification_time or 'Tidak diatur'}\n"
                f"📝 **Catatan:** {notes or 'Tidak ada'}\n\n"
                f"💡 Bot akan mengingatkan saat jatuh tempo!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
            
            context.user_data["state"] = None
        
        elif state == "deleting_debt":
            try:
                debt_id = int(text)
                if DebtManager.delete_debt(user_id, debt_id):
                    await update.message.reply_text(
                        f"✅ **Utang #{debt_id} berhasil dihapus!**",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_main_keyboard()
                    )
                else:
                    await update.message.reply_text(
                        f"❌ **Utang #{debt_id} tidak ditemukan!**",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_main_keyboard()
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ **Input tidak valid!**\n"
                    "Ketik nomor utang yang ingin dihapus.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            context.user_data["state"] = None
        
        elif state == "setting_interval":
            try:
                interval = int(text)
                if interval < 0:
                    await update.message.reply_text(
                        "❌ **Interval tidak valid!**\n"
                        "Gunakan angka positif.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                DebtManager.update_notification_interval(user_id, interval)
                
                if interval == 0:
                    message = "🔕 **Notifikasi dinonaktifkan.**"
                else:
                    message = f"⏰ **Interval notifikasi diatur ke {interval} menit.**"
                
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_keyboard()
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ **Input tidak valid!**\n"
                    "Gunakan angka (dalam menit).",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            context.user_data["state"] = None
        
        else:
            # Default response
            await update.message.reply_text(
                "🤖 **Kapan Bayar Bot**\n\n"
                "Gunakan menu di bawah untuk mengelola utang Anda!",
                reply_markup=get_main_keyboard()
            )

# Owner commands
async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /owner"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    owner_help = (
        "👑 **Owner Commands** 👑\n\n"
        
        "📊 **Stats & Management:**\n"
        "• /stats - Lihat statistik bot\n"
        "• /backupuser - Backup data user\n"
        "• /broadcast - Kirim pesan ke semua user\n"
        "• /addjoin @group - Tambah group wajib join\n"
        "• /listjoin - List group wajib join\n"
        "• /deljoin - Hapus group wajib join\n"
        "• /statsjoin - Statistik user join\n\n"
        
        "📈 **Statistik:**\n"
        "• Total user aktif\n"
        "• Total utang tercatat\n"
        "• Aktivitas terakhir\n\n"
        
        "📤 **Broadcast:**\n"
        "Reply pesan dengan /broadcast\n"
        "Support teks dan media\n\n"
        
        "🔒 **Group Wajib Join:**\n"
        "User harus join group/channel\n"
        "Untuk menggunakan bot"
    )
    
    await update.message.reply_text(
        owner_help,
        parse_mode=ParseMode.MARKDOWN
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /stats"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    total_users = UserManager.get_total_users()
    
    # Hitung total utang dari semua user
    total_debts = 0
    total_amount = 0
    user_files = list(DATABASE_DIR.glob("*.json"))
    
    for user_file in user_files:
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_debts += len(data.get("debts", []))
                
                # Hitung total amount
                for debt in data.get("debts", []):
                    try:
                        amount_str = str(debt.get("amount", "0")).replace('k', '000').replace('K', '000')
                        amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                        total_amount += float(amount_str)
                    except:
                        continue
        except:
            continue
    
    # Format total amount
    if total_amount >= 1000000:
        amount_str = f"Rp {total_amount/1000000:.2f}M"
    elif total_amount >= 1000:
        amount_str = f"Rp {total_amount/1000:.0f}k"
    else:
        amount_str = f"Rp {int(total_amount)}"
    
    stats_text = (
        f"📊 **Statistik Bot** 📊\n\n"
        f"👥 **Total User:** {total_users}\n"
        f"📝 **Total Utang:** {total_debts}\n"
        f"💰 **Total Nilai:** {amount_str}\n"
        f"📁 **Database:** {len(user_files)} file\n"
        f"🔗 **Group Wajib Join:** {JoinGroupManager.get_groups_count()}\n\n"
        f"🔄 **Terakhir Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

async def backupuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /backupuser"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    if USERS_FILE.exists():
        with open(USERS_FILE, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename="users_backup.json",
                caption=f"📁 **Backup Data User**\nTotal User: {UserManager.get_total_users()}"
            )
    else:
        await update.message.reply_text("❌ File backup tidak ditemukan!")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /broadcast - PERBAIKAN ERROR"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    # Cek apakah ini reply message
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ **Reply pesan yang ingin di-broadcast!**\n"
            "Contoh: Reply pesan ini dengan /broadcast",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    message_to_forward = update.message.reply_to_message
    user_ids = UserManager.get_all_user_ids()
    
    await update.message.reply_text(f"📢 **Mulai broadcast ke {len(user_ids)} user...**")
    
    success_count = 0
    fail_count = 0
    
    for uid in user_ids:
        try:
            # Kirim pesan berdasarkan tipe
            if message_to_forward.text:
                # Perbaikan: Gunakan parse_mode yang benar
                parse_mode = None
                if message_to_forward.entities or message_to_forward.caption_entities:
                    # Jika ada entities, gunakan MARKDOWN
                    parse_mode = ParseMode.MARKDOWN
                
                await context.bot.send_message(
                    chat_id=uid,
                    text=message_to_forward.text,
                    parse_mode=parse_mode,
                    entities=message_to_forward.entities
                )
                
            elif message_to_forward.photo:
                await context.bot.send_photo(
                    chat_id=uid,
                    photo=message_to_forward.photo[-1].file_id,
                    caption=message_to_forward.caption,
                    parse_mode=ParseMode.MARKDOWN if message_to_forward.caption_entities else None,
                    caption_entities=message_to_forward.caption_entities
                )
                
            elif message_to_forward.video:
                await context.bot.send_video(
                    chat_id=uid,
                    video=message_to_forward.video.file_id,
                    caption=message_to_forward.caption,
                    parse_mode=ParseMode.MARKDOWN if message_to_forward.caption_entities else None,
                    caption_entities=message_to_forward.caption_entities
                )
                
            elif message_to_forward.document:
                await context.bot.send_document(
                    chat_id=uid,
                    document=message_to_forward.document.file_id,
                    caption=message_to_forward.caption,
                    parse_mode=ParseMode.MARKDOWN if message_to_forward.caption_entities else None,
                    caption_entities=message_to_forward.caption_entities
                )
                
            else:
                # Try to forward as-is
                await message_to_forward.forward(chat_id=uid)
            
            success_count += 1
            time.sleep(0.1)  # Delay untuk menghindari limit
            
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"✅ **Broadcast selesai!**\n\n"
        f"📤 Berhasil: {success_count}\n"
        f"❌ Gagal: {fail_count}\n"
        f"📊 Total: {len(user_ids)}",
        parse_mode=ParseMode.MARKDOWN
    )

async def addjoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /addjoin"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Format salah!**\n"
            "Gunakan: /addjoin @username_group\n"
            "Contoh: /addjoin @testchannel",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    group_username = ' '.join(context.args)
    
    # Validasi format
    if not group_username.startswith('@'):
        group_username = '@' + group_username
    
    if JoinGroupManager.add_group(group_username):
        await update.message.reply_text(
            f"✅ **Group berhasil ditambahkan!**\n\n"
            f"Group: {group_username}\n"
            f"User wajib join group ini sebelum menggunakan bot.\n\n"
            f"📊 Total group: {JoinGroupManager.get_groups_count()}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            f"❌ **Group sudah ada dalam daftar!**\n"
            f"Group: {group_username}",
            parse_mode=ParseMode.MARKDOWN
        )

async def listjoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /listjoin"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    groups = JoinGroupManager.get_all_groups()
    
    if not groups:
        await update.message.reply_text(
            "📭 **Tidak ada group yang diwajibkan.**\n"
            "Gunakan /addjoin @namagroup untuk menambahkan.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    groups_list = "📋 **Daftar Group Wajib Join:**\n\n"
    for i, group in enumerate(groups, 1):
        groups_list += f"{i}. {group}\n"
    
    groups_list += f"\n📊 **Total:** {len(groups)} group"
    
    await update.message.reply_text(
        groups_list,
        parse_mode=ParseMode.MARKDOWN
    )

async def deljoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /deljoin"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    groups = JoinGroupManager.get_all_groups()
    
    if not groups:
        await update.message.reply_text(
            "📭 **Tidak ada group yang diwajibkan.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Tampilkan daftar group
    groups_list = "🗑️ **Pilih group untuk dihapus:**\n\n"
    for i, group in enumerate(groups, 1):
        groups_list += f"{i}. {group}\n"
    
    groups_list += "\nKetik nomor group yang ingin dihapus:"
    
    await update.message.reply_text(
        groups_list,
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data["state"] = "deleting_group"

async def statsjoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /statsjoin"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Akses ditolak!")
        return
    
    groups = JoinGroupManager.get_all_groups()
    
    if not groups:
        await update.message.reply_text(
            "📭 **Tidak ada group yang diwajibkan.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Dapatkan statistik join
    join_stats = JoinGroupManager.check_all_users_joined()
    total_users = UserManager.get_total_users()
    
    stats_text = "📊 **Statistik Join Group**\n\n"
    
    for group, user_ids in join_stats.items():
        joined_count = len(user_ids)
        percentage = (joined_count / total_users * 100) if total_users > 0 else 0
        
        stats_text += (
            f"🔗 **{group}**\n"
            f"   ✅ Bergabung: {joined_count} user\n"
            f"   📈 Persentase: {percentage:.1f}%\n\n"
        )
    
    stats_text += f"👥 **Total User Bot:** {total_users} user"
    
    # Kirim file join_users.json
    if JOIN_USERS_FILE.exists():
        with open(JOIN_USERS_FILE, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename="join_users.json",
                caption=stats_text
            )
    else:
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk error"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Handle parse error khusus
    if "Can't parse entities" in str(context.error):
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ **Terjadi kesalahan parsing!**\n"
                "Pastikan format Markdown/HTML Anda benar.\n\n"
                "💡 **Tips:** Hindari karakter khusus atau gunakan format plain text.",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        if update and update.effective_user:
            try:
                await update.effective_message.reply_text(
                    "❌ **Terjadi kesalahan!**\n"
                    "Silakan coba lagi atau hubungi developer.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass

# Main function
def main():
    """Fungsi utama untuk menjalankan bot"""
    # Buat aplikasi
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("backupuser", backupuser_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("addjoin", addjoin_command))
    application.add_handler(CommandHandler("listjoin", listjoin_command))
    application.add_handler(CommandHandler("deljoin", deljoin_command))
    application.add_handler(CommandHandler("statsjoin", statsjoin_command))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Jalankan bot
    print("🤖 Kapan Bayar Bot sedang berjalan...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print("📊 Bot siap menerima perintah!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Inisialisasi Notification Manager
    notification_manager = NotificationManager()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot dihentikan.")
        notification_manager.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        notification_manager.stop()
