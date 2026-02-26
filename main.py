import asyncio
import sys
import json
import os

# ==========================================================
# 1. إعداد المسارات والبيئة (يجب أن يتم قبل استيراد المكتبات)
# ==========================================================
# تحديد المسار الذي تم فك ضغط الترسانة (vendor_assets.zip) فيه
extract_path = os.path.join(os.getcwd(), "vendor_extracted")

# إخبار النظام أين يجد المكتبات المثبتة
vendor_python = os.path.join(extract_path, "python")
if os.path.exists(vendor_python):
    sys.path.insert(0, vendor_python)
else:
    print(f"⚠️ تحذير: لم يتم العثور على مجلد المكتبات في {vendor_python}")

# إخبار Camoufox و Playwright بمكان المحركات محلياً (No-Download Mode)
os.environ["CAMOUFOX_CACHE_DIR"] = os.path.join(extract_path, "camoufox_cache")
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(extract_path, "browsers")

# ==========================================================
# 2. الاستيراد الآمن
# ==========================================================
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل وضع الطيران المحلي (Offline Engine).")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox. تأكد من نجاح خطوة فك الضغط.")
    sys.exit(1)

GEMINI_URL = "https://gemini.google.com/app"

# ==========================================================
# 3. محرك الأتمتة (The Core Engine)
# ==========================================================
async def run_gemini_automation(prompt):
    print(f"🧐 الطلب: {prompt}")
    
    # إعدادات المتصفح للسرعة القصوى
    async with AsyncCamoufox(
        headless=True,
        block_images=True,  # حظر الصور لتسريع التحميل
        block_fonts=True    # حظر الخطوط الخارجية
    ) as browser:
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )

        # حقن الجلسة (Cookies)
        cookies_json = os.getenv("GEMINI_COOKIES")
        if cookies_json:
            try:
                await context.add_cookies(json.loads(cookies_json))
                print("🔑 تم استعادة الجلسة بنجاح.")
            except Exception as e:
                print(f"⚠️ خطأ في الكوكيز: {e}")

        page = await context.new_page()
        
        try:
            print("🌐 الإبحار إلى Gemini...")
            # الانتظار حتى يتم تحميل الهيكل الأساسي فقط للسرعة
            await page.goto(GEMINI_URL, wait_until="commit", timeout=60000)

            # تحديد مربع الإدخال
            input_selector = "div[role='textbox'], [contenteditable='true']"
            await page.wait_for_selector(input_selector, timeout=30000)
            
            print("✍️ إرسال السؤال...")
            await page.fill(input_selector, prompt)
            await page.keyboard.press("Enter")
            
            # --- مراقبة استجابة Gemini (High-Speed Monitor) ---
            print("📡 بانتظار الرد...")
            response_selector = ".model-response-text"
            
            # الانتظار حتى يبدأ النص بالظهور
            await page.wait_for_selector(response_selector, timeout=60000)
            
            previous_length = 0
            stable_count = 0
            
            # فحص نمو النص كل ثانية واحدة (أسرع من الإصدار السابق)
            for _ in range(90): 
                current_text = await page.evaluate(f'''() => {{
                    const els = document.querySelectorAll("{response_selector}");
                    return els.length > 0 ? els[els.length - 1].innerText : "";
                }}''')
                
                current_length = len(current_text)
                
                if current_length > previous_length:
                    previous_length = current_length
                    stable_count = 0
                elif current_length > 0:
                    stable_count += 1
                
                # إذا استقر النص لـ 4 ثوانٍ نعتبره انتهى
                if stable_count >= 4:
                    print(f"✅ اكتمل الرد ({current_length} حرف).")
                    break
                
                await asyncio.sleep(1) 

            # استخراج النتيجة النهائية
            final_res = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll("{response_selector}");
                return els.length > 0 ? els[els.length - 1].innerText : "فشل استخراج الرد.";
            }}''')

            output = {"status": "success", "response": final_res}

        except Exception as e:
            print(f"❌ خطأ: {e}")
            output = {"status": "error", "message": str(e)}

        # حفظ النتيجة
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        print("💾 تم تحديث result.json")

if __name__ == "__main__":
    # قراءة المدخل من سطر الأوامر (الذي يرسله الـ Workflow)
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(run_gemini_automation(user_prompt))
