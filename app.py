import telebot
from telebot import types
import json
import os
import importlib.util
from flask import Flask, render_template, send_from_directory
import threading

# --- إعدادات البوت الأصلية ---
spec = importlib.util.spec_from_file_location("config", ".config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
bot = telebot.TeleBot(config.API_TOKEN)

if not os.path.exists(config.PHOTOS_DIR): os.makedirs(config.PHOTOS_DIR)
waiting_for_images = {}

# --- إعدادات Flask (سيرفر الويب) ---
app = Flask(__name__, template_folder='.')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin-page') # رابط لوحة التحكم الجديد
def admin_page():
    return render_template('admin.html')

@app.route('/products.json')
def serve_json():
    return send_from_directory('.', 'products.json')

@app.route('/photos/<path:filename>')
def serve_photos(filename):
    return send_from_directory(config.PHOTOS_DIR, filename)

# --- وظائف البوت الأصلية (بدون تغيير) ---
def update_json(products):
    with open(config.JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=4, ensure_ascii=False)

# ... (باقي دوال البوت: handle_data, get_main_img, get_gallery كما هي في كودك) ...
# ملاحظة: تأكد من نسخ الدوال كاملة من ملفك الأصلي هنا

# --- تشغيل النظام المزدوج ---
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # تشغيل البوت في خيط منفصل
    threading.Thread(target=run_bot).start()
    # تشغيل السيرفر
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

