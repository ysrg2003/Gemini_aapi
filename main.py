import os
import sys
import json
import asyncio
import time

# استيراد محرك Camoufox
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل البيئة المحلية بنجاح.")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox.")
    sys.exit(1)

GEMINI_URL = "https://gemini.google.com/app"

async def run_gemini_automation(prompt):
    print(f"🧐 الطلب المستلم: {prompt}")
    output = {"status": "error", "message": "فشل التشغيل المبدئي"}

    try:
        # تشغيل المحرك بأقصى إعدادات السرعة
        async with AsyncCamoufox(
            headless=True,
            block_images=True,
            block_webrtc=True,
            i_know_what_im_doing=True,
            humanize=False, # التشغيل المباشر أسرع من محاكاة البشر
        ) as browser:
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
            )

            # استعادة الجلسة
            cookies_json = os.getenv("GEMINI_COOKIES")
            if cookies_json:
                await context.add_cookies(json.loads(cookies_json))
                print("🔑 تم حقن الجلسة.")

            page = await context.new_page()
            
            print("🌐 الإبحار السريع إلى Gemini...")
            # الانتقال فور "Commit" (بمجرد بدء وصول البيانات)
            await page.goto(GEMINI_URL, wait_until="commit", timeout=30000)

            # البحث عن مربع النص بأقصى سرعة
            input_selector = "div[contenteditable='true'], div[role='textbox']"
            await page.wait_for_selector(input_selector, timeout=15000)
            
            print("✍️ إرسال السؤال...")
            await page.fill(input_selector, prompt)
            await page.keyboard.press("Enter")
            
            print("📡 مراقبة تدفق الرد...")
            response_selector = ".model-response-text"
            
            # تحسين: الانتظار الذكي للرد دون إهدار ثوانٍ في sleep غير ضروري
            start_time = time.time()
            final_res = ""
            last_len = 0
            stable_ticks = 0
            
            # دورة الفحص السريع (كل 500ms بدلاً من 1s)
            while time.time() - start_time < 60:
                current_text = await page.evaluate(f'''() => {{
                    const nodes = document.querySelectorAll("{response_selector}");
                    return nodes.length > 0 ? nodes[nodes.length - 1].innerText : "";
                }}''')
                
                curr_len = len(current_text)
                if curr_len > 0 and curr_len == last_len:
                    stable_ticks += 1
                else:
                    stable_ticks = 0
                
                last_len = curr_len
                
                # إذا استقر النص لـ 3 دورات فحص (1.5 ثانية) نعتبره انتهى
                if curr_len > 0 and stable_ticks >= 3:
                    final_res = current_text
                    print(f"✅ تم استلام الرد بالكامل.")
                    break
                
                await asyncio.sleep(0.5) 

            if not final_res:
                final_res = "تجاوز الوقت المسموح دون استلام رد مستقر."

            output = {"status": "success", "response": final_res}

    except Exception as e:
        print(f"❌ خطأ تقني: {e}")
        output = {"status": "error", "message": str(e)}

    # حفظ النتيجة
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم حفظ النتيجة.")

if __name__ == "__main__":
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(run_gemini_automation(user_prompt))
