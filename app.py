import telebot
from telebot import types
import json
import os
import importlib.util
from flask import Flask, render_template, send_from_directory
import threading
import time

# --- المتغيرات العالمية للتحكم في الإعدادات ---
current_config = None
bot = None
bot_thread = None
bot_token = None
stop_bot_event = threading.Event()

def load_settings():
    """وظيفة لإعادة تحميل الإعدادات من الملف الفعلي على القرص"""
    global current_config, bot, bot_token, bot_thread, stop_bot_event
    try:
        spec = importlib.util.spec_from_file_location("config", ".config.py")
        new_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(new_config)
        
        # إذا تغير التوكن، أعد تشغيل البوت بشكل آمن
        if bot_token != new_config.API_TOKEN:
            bot_token = new_config.API_TOKEN
            print(f"✅ تم تحديث توكن البوت: {bot_token[:10]}...")
            # إيقاف الخيط القديم إذا كان يعمل
            if bot_thread and bot_thread.is_alive():
                stop_bot_event.set()
                bot_thread.join(timeout=5)
                stop_bot_event.clear()
            bot = telebot.TeleBot(bot_token)
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
        else:
            if bot is None:
                bot = telebot.TeleBot(bot_token)
                bot_thread = threading.Thread(target=run_bot, daemon=True)
                bot_thread.start()

        current_config = new_config
        if not os.path.exists(current_config.PHOTOS_DIR): 
            os.makedirs(current_config.PHOTOS_DIR)
        return True
    except Exception as e:
        print(f"❌ خطأ في تحميل الإعدادات: {e}")
        return False

def config_refresher():
    """خيط خلفي يفحص المتغيرات كل 60 ثانية كما اقترحت يا محمد"""
    while True:
        time.sleep(60)
        load_settings()
        print("🔄 تم فحص وتحديث المتغيرات تلقائياً...")

def run_bot():
    global bot
    while not stop_bot_event.is_set():
        try:
            if bot:
                print("🤖 البوت يعمل الآن...")
                bot.remove_webhook()
                bot.polling(none_stop=True, interval=3)
        except Exception as e:
            print(f"⚠️ خطأ في البوت، سيعيد المحاولة: {e}")
            time.sleep(5)

# --- إعدادات Flask ---
app = Flask(__name__, template_folder='.')
waiting_for_images = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin-page')
def admin_page():
    # سيستخدم القوالب أحدث BASE_URL موجود في current_config تلقائياً
    return render_template('admin.html', config=current_config)

@app.route('/products.json')
def serve_json():
    return send_from_directory('.', 'products.json')

@app.route('/photos/<path:filename>')
def serve_photos(filename):
    return send_from_directory(current_config.PHOTOS_DIR, filename)

# --- وظائف البوت المحدثة لتستخدم current_config ---
def update_json(products):
    with open(current_config.JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=4, ensure_ascii=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك في نظام المتجر المحدث تلقائياً!")

# يمكنك إضافة باقي دوال معالجة البيانات (handle_data) هنا 
# مع التأكد من استخدام current_config.VARIABLE بدلاً من config.VARIABLE

if __name__ == "__main__":
    # تحميل الإعدادات لأول مرة عند تشغيل التطبيق - يقوم بتشغيل البوت أيضاً
    load_settings()
    # تشغيل خيط التحديث التلقائي
    threading.Thread(target=config_refresher, daemon=True).start()
    # تشغيل السيرفر (Render يستخدم المنفذ 10000 افتراضياً)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
