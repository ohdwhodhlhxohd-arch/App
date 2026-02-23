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

def load_settings():
    """وظيفة لإعادة تحميل الإعدادات من الملف الفعلي على القرص"""
    global current_config, bot
    try:
        spec = importlib.util.spec_from_file_location("config", ".config.py")
        new_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(new_config)
        
        # إذا تغير التوكن، نحتاج لإعادة تعريف كائن البوت
        if current_config is None or current_config.API_TOKEN != new_config.API_TOKEN:
            bot = telebot.TeleBot(new_config.API_TOKEN)
            print(f"✅ تم تحديث توكن البوت: {new_config.API_TOKEN[:10]}...")
        
        current_config = new_config
        if not os.path.exists(current_config.PHOTOS_DIR): 
            os.makedirs(current_config.PHOTOS_DIR)
        return True
    except Exception as e:
        print(f"❌ خطأ في تحميل الإعدادات: {e}")
        return False

# تحميل الإعدادات لأول مرة عند تشغيل التطبيق
load_settings()

def config_refresher():
    """خيط خلفي يفحص المتغيرات كل 30 ثانية كما اقترحت يا محمد"""
    while True:
        time.sleep(60)
        load_settings()
        print("🔄 تم فحص وتحديث المتغيرات تلقائياً...")

# تشغيل خيط التحديث التلقائي
threading.Thread(target=config_refresher, daemon=True).start()

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

# --- تشغيل النظام المزدوج ---
def run_bot():
    while True:
        try:
            if bot:
                print("🤖 البوت يعمل الآن...")
                bot.remove_webhook()
                bot.polling(none_stop=True, interval=3)
        except Exception as e:
            print(f"⚠️ خطأ في البوت، سيعيد المحاولة: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل البوت في خيط منفصل
    threading.Thread(target=run_bot, daemon=True).start()
    
    # تشغيل السيرفر (Render يستخدم المنفذ 10000 افتراضياً)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
