import os
import sys
import json
import asyncio
from camoufox.async_api import AsyncCamoufox

# إعدادات الرابط والمحددات (Selectors)
GEMINI_URL = "https://gemini.google.com/app"
INPUT_SELECTOR = "div[role='textbox']"
RESPONSE_SELECTOR = ".model-response-text"
# الأزرار التي تظهر فقط عند انتهاء الرد (مثل زر القراءة الصوتية أو النسخ)
FINISH_INDICATOR = "button[aria-label*='Read aloud'], .action-buttons-container"

async def run_gemini_automation(prompt):
    print(f"🚀 بدء المحرك... الطلب: {prompt[:50]}...")
    
    result = {"status": "error", "response": ""}

    try:
        # 1. إعداد المتصفح بأقصى سرعة وأفضل تخفي
        async with AsyncCamoufox(
            headless=True,
            block_images=True,
            # حظر الموارد غير الضرورية لتسريع التحميل
            exclude_resources=["font", "media", "eventsource", "websocket"],
            humanize=True,
        ) as browser:
            
            # 2. إنشاء سياق المتصفح مع User-Agent حديث
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            # 3. إدارة الجلسة عبر الكوكيز (للحفاظ على تسجيل الدخول)
            cookies_env = os.getenv("GEMINI_COOKIES")
            if cookies_env:
                try:
                    await context.add_cookies(json.loads(cookies_env))
                    print("🔑 تم استيراد الجلسة بنجاح.")
                except Exception as e:
                    print(f"⚠️ خطأ في تنسيق الكوكيز: {e}")

            page = await context.new_page()
            
            # 4. الإبحار الذكي
            # ننتظر فقط حتى يتم إرسال الصفحة (commit) لبدء التفاعل فوراً
            print("🌐 جاري الدخول إلى Gemini...")
            await page.goto(GEMINI_URL, wait_until="commit", timeout=45000)

            # 5. التفاعل مع صندوق الإدخال
            print("⌨️ إدخال النص...")
            await page.wait_for_selector(INPUT_SELECTOR, timeout=20000)
            
            # استخدام fill ثم محاكاة الضغط للإرسال لضمان السرعة والتخفي
            await page.fill(INPUT_SELECTOR, prompt)
            await asyncio.sleep(0.2) 
            await page.keyboard.press("Enter")
            
            # 6. مراقبة الرد (الانتظار الذكي المبني على الحدث)
            print("📡 بانتظار اكتمال الرد...")
            
            # ننتظر ظهور حاوية الرد أولاً
            await page.wait_for_selector(RESPONSE_SELECTOR, timeout=20000)
            
            # حلقة فحص سريعة (Polling) للتأكد من انتهاء الكتابة
            # بدلاً من 8 ثوانٍ ثابتة، نتحقق كل نصف ثانية من ظهور أزرار التحكم
            is_done = False
            for attempt in range(60): # حد أقصى 30 ثانية
                # إذا ظهرت أزرار "أعجبني/لم يعجبني/نسخ"، فالرد اكتمل
                done_elements = await page.locator(FINISH_INDICATOR).count()
                if done_elements > 0:
                    is_done = True
                    break
                await asyncio.sleep(0.5)

            if not is_done:
                print("⚠️ تنبيه: قد لا يكون الرد قد اكتمل تماماً، لكن سيتم الاستخراج الآن.")

            # 7. استخراج آخر رد في المحادثة
            final_html = await page.locator(RESPONSE_SELECTOR).last.inner_html()
            
            result = {
                "status": "success",
                "response": final_html.strip()
            }
            print("✅ تم استخراج الرد بنجاح.")

    except Exception as e:
        error_msg = f"حدث خطأ: {str(e)}"
        print(f"❌ {error_msg}")
        result["response"] = error_msg

    # 8. حفظ المخرجات بصيغة JSON
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("💾 تم حفظ النتيجة في result.json")

if __name__ == "__main__":
    # قراءة الطلب من سطر الأوامر
    prompt_arg = sys.argv[1] if len(sys.argv) > 1 else "اكتب لي نصيحة قصيرة عن البرمجة"
    asyncio.run(run_gemini_automation(prompt_arg))
