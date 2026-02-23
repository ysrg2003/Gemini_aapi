import asyncio
import sys
import json
import os
import shutil
import zipfile
import stat  # ميزة: التحكم في نظام ملفات لينكس لإصلاح الصلاحيات

# ==========================================================
# 1. إدارة البيئة الدائمة (Persistence Layer)
# ==========================================================
current_dir = os.getcwd()
zip_path = os.path.join(current_dir, "vendor_assets.zip")
extract_path = os.path.join(current_dir, "vendor_extracted")

# ميزة: فك الضغط التلقائي والذكي
if os.path.exists(zip_path) and not os.path.exists(extract_path):
    print("📦 جاري فك ضغط المحرك الدائم (Libraries & Browsers)...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # ميزة: إصلاح الصلاحيات (التي منعت التشغيل سابقاً)
    print("🔑 جاري إصلاح صلاحيات الملفات التنفيذية...")
    for root, dirs, files in os.walk(extract_path):
        for name in files:
            # منح صلاحية التنفيذ لـ Node.js ومحركات المتصفح
            if name == "node" or "chrome" in name or "firefox" in name or name.endswith(".sh"):
                file_path = os.path.join(root, name)
                st = os.stat(file_path)
                os.chmod(file_path, st.st_mode | stat.S_IEXEC)
    print("✅ تم تجهيز البيئة ومنح الصلاحيات بنجاح.")

# ==========================================================
# 2. حقن المسارات (Path Injection)
# ==========================================================
# ميزة: استخدام المكتبات المرفوعة دون الحاجة لـ pip install في كل مرة
vendor_python = os.path.join(extract_path, "python")
sys.path.insert(0, vendor_python) 
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(extract_path, "browsers")

# ==========================================================
# 3. الاستيراد الآمن (Safe Import)
# ==========================================================
try:
    from camoufox.async_api import AsyncCamoufox
    print("✅ تم تحميل محرك Camoufox بنجاح.")
except ImportError as e:
    print(f"❌ خطأ فادح: لم يتم العثور على المكتبة. التفاصيل: {e}")
    sys.exit(1)

GEMINI_URL = "https://gemini.google.com/app"

# ==========================================================
# 4. المحرك الأساسي للأتمتة (Automation Engine)
# ==========================================================
async def run_gemini_automation(prompt):
    print(f"🚀 بدء العملية... السؤال: {prompt}")
    
    # ميزة: التخفي الكامل (Full Stealth) عبر Camoufox
    async with AsyncCamoufox(headless=True) as browser:
        
        # ميزة: سياق متصفح مع بصمة حقيقية (Fingerprinting)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # ميزة: تجاوز تسجيل الدخول عبر الكوكيز (Session Persistence)
        cookies_json = os.getenv("GEMINI_COOKIES")
        if cookies_json:
            try:
                await context.add_cookies(json.loads(cookies_json))
                print("✅ تم تحميل الجلسة (Cookies) بنجاح.")
            except Exception as e:
                print(f"⚠️ فشل تحميل الكوكيز: {e}")

        page = await context.new_page()

        # ميزة صواريخ السرعة (Turbo Speed) - [معدلة للاستقرار]
        # نحظر الصور والخطوط فقط، ونترك الـ CSS لضمان عدم اختفاء العناصر
        await page.route("**/*.{png,jpg,jpeg,svg,gif,webp,woff,woff2,ttf}", lambda route: route.abort())
        
        try:
            print("⏳ جاري فتح Gemini...")
            # ميزة: الانتظار السريع (Fast Navigation) عبر domcontentloaded
            await page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=60000)

            # ميزة: المحدد الذكي (Smart Selector) لمربع النص
            input_selector = "div[role='textbox'], [contenteditable='true']"
            print("🔍 في انتظار ظهور مربع النص...")
            await page.wait_for_selector(input_selector, timeout=30000)
            
            print("✍️ كتابة السؤال...")
            await page.fill(input_selector, prompt)
            await page.keyboard.press("Enter")
            
            print("📡 تم الإرسال، بانتظار الرد...")

            # ميزة: استخراج الرد بذكاء (Smart Extraction)
            # ننتظر ظهور حاوية النص مباشرة بدلاً من الأزرار المتقلبة
            response_selector = ".model-response-text"
            try:
                await page.wait_for_selector(response_selector, timeout=60000)
                # مهلة 5 ثوانٍ لضمان اكتمال "تدفق" النص (Streaming) من السيرفر
                await asyncio.sleep(5)
            except:
                print("⚠️ تنبيه: استغرق الرد وقتاً طويلاً، سأحاول جلب ما ظهر.")

            # ميزة: الكشط البرمجي العميق (Deep Scrape) لاستخراج النص الصافي
            result_text = await page.evaluate('''() => {
                const responses = document.querySelectorAll(".model-response-text");
                if (responses.length > 0) {
                    return responses[responses.length - 1].innerText;
                }
                const fallback = document.querySelector(".message-content");
                return fallback ? fallback.innerText : "لم يتم العثور على نص الرد.";
            }''')

            output = {
                "status": "success",
                "prompt": prompt,
                "response": result_text
            }
            print("✅ تم استلام الرد بنجاح.")

        except Exception as e:
            print(f"❌ حدث خطأ أثناء التشغيل: {str(e)}")
            # ميزة: لقطة شاشة للخطأ لتشخيص المشاكل البصرية
            await page.screenshot(path="error_debug.png")
            output = {"status": "error", "message": str(e)}

        # ميزة: حفظ النتيجة في ملف JSON مهيكل
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hi"
    asyncio.run(run_gemini_automation(user_prompt))
