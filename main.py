import os
import sys
import json
import asyncio

# التحقق من وجود المكتبة
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل البيئة المحلية.")
except ImportError:
    print("❌ خطأ: مكتبة Camoufox غير مثبتة. نفذ: pip install camoufox")
    sys.exit(1)

# الإعدادات العامة
GEMINI_URL = "https://gemini.google.com/app"
# محددات العناصر (Selectors) - تم تحديثها لتكون أكثر دقة
INPUT_SELECTOR = "div[role='textbox']"
RESPONSE_SELECTOR = ".model-response-text"
# الأزرار التي تظهر فقط عند اكتمال الرد تماماً
FINISH_INDICATOR = "button[aria-label*='Read aloud'], .action-buttons-container"

async def run_gemini_automation(prompt):
    print(f"🧐 جاري المعالجة: {prompt[:50]}...")
    
    output = {"status": "error", "message": "فشل التشغيل المبدئي"}

    try:
        # 1. تشغيل المتصفح مع معالجة التنبيهات والسرعة
        async with AsyncCamoufox(
            headless=True,
            block_images=True,
            i_know_what_im_doing=True, # لتجاوز LeakWarning الخاص بحظر الصور
            humanize=True,
        ) as browser:
            
            # 2. إعداد السياق (Context)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # 3. حقن الكوكيز لاستعادة الجلسة
            cookies_json = os.getenv("GEMINI_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم حقن الجلسة.")
                except Exception as e:
                    print(f"⚠️ خطأ في الكوكيز: {e}")

            page = await context.new_page()

            # 4. تسريع التحميل عبر حظر الخطوط والملفات غير الضرورية (يدوياً لضمان التوافق)
            async def block_assets(route):
                if route.request.resource_type in ["font", "media"]:
                    await route.abort()
                else:
                    await route.continue_()
            await page.route("**/*", block_assets)
            
            # 5. الدخول السريع (wait_until='commit' لتوفير الوقت)
            print("🌐 الإبحار إلى Gemini...")
            await page.goto(GEMINI_URL, wait_until="commit", timeout=45000)

            # 6. إرسال السؤال
            print("✍️ كتابة السؤال...")
            await page.wait_for_selector(INPUT_SELECTOR, timeout=20000)
            await page.fill(INPUT_SELECTOR, prompt)
            await asyncio.sleep(0.5) # مهلة بسيطة لضمان استقرار النص
            await page.keyboard.press("Enter")
            
            # 7. المراقبة الذكية لانتهاء الرد (بدل الـ 8 ثوانٍ الثابتة)
            print("📡 بانتظار رد الذكاء الاصطناعي...")
            await page.wait_for_selector(RESPONSE_SELECTOR, timeout=30000)
            
            # فحص ذكي كل نصف ثانية: هل ظهرت أزرار "النسخ" أو "القراءة الصوتية"؟
            # هذا يعني أن Gemini انتهى من الكتابة (Streaming Finished)
            is_finished = False
            for _ in range(60): # حد أقصى 30 ثانية انتظار إضافي
                indicators = await page.locator(FINISH_INDICATOR).count()
                if indicators > 0:
                    is_finished = True
                    break
                await asyncio.sleep(0.5)

            if not is_finished:
                print("⚠️ تنبيه: تم استخراج الرد قبل ظهور مؤشر الاكتمال (قد يكون الرد طويلاً).")

            # 8. استخراج النتيجة النهائية بـ HTML
            final_res_html = await page.locator(RESPONSE_SELECTOR).last.inner_html()
            output = {"status": "success", "response": final_res_html.strip()}

    except Exception as e:
        print(f"❌ حدث خطأ: {e}")
        output = {"status": "error", "message": str(e)}

    # 9. حفظ النتيجة
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم تحديث result.json بنجاح.")

if __name__ == "__main__":
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(run_gemini_automation(user_prompt))
