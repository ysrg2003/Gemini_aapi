import os
import sys
import json
import asyncio

# 1. التحقق من البيئة والمحرك
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل البيئة المحلية بنجاح.")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox. تأكد من تثبيتها عبر pip install camoufox.")
    sys.exit(1)

# الرابط الأساسي لجيمناي
GEMINI_URL = "https://gemini.google.com/app"

async def run_gemini_automation(prompt):
    print(f"🧐 جاري معالجة الطلب: {prompt}")
    
    # هيكل افتراضي للمخرجات في حال حدث خطأ
    output = {"status": "error", "message": "فشل التشغيل المبدئي"}

    try:
        # 2. إعداد المتصفح بتقنيات التخفي (Anti-Bot)
        async with AsyncCamoufox(
            headless=True,            # تشغيل في الخلفية لتوفير الموارد
            block_images=True,        # منع الصور لتسريع التحميل وتوفير البيانات
            i_know_what_im_doing=True, # تخطي تحذيرات الحماية المتقدمة
            humanize=True,            # محاكاة حركة الماوس والكيبورد لتجنب الحظر
        ) as browser:
            
            # 3. إعداد سياق المتصفح (Context)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # 4. إدارة الجلسة (Session) عبر الكوكيز
            cookies_json = os.getenv("GEMINI_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم حقن كوكيز الجلسة بنجاح.")
                except Exception as e:
                    print(f"⚠️ خطأ في الكوكيز (تأكد من صيغة الـ JSON): {e}")

            page = await context.new_page()
            
            # 5. الدخول إلى الموقع وانتظار الهيكل الأساسي
            print("🌐 الإبحار إلى Gemini...")
            await page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=60000)

            # 6. البحث عن صندوق الإدخال (Selector)
            input_selector = "div[role='textbox'], [contenteditable='true'], #input-area"
            await page.wait_for_selector(input_selector, timeout=30000)
            
            # 7. كتابة السؤال وإرساله
            print("✍️ كتابة السؤال وإرساله...")
            await page.fill(input_selector, prompt)
            await page.keyboard.press("Enter")
            
            # 8. مراقبة "تدفق" الرد (Streaming Response)
            print("📡 بانتظار رد الذكاء الاصطناعي...")
            response_selector = ".model-response-text"
            
            # ننتظر أول ظهور للرد
            await page.wait_for_selector(response_selector, timeout=60000)
            
            previous_html = ""
            stable_count = 0
            
            # فحص استقرار الرد (90 محاولة كحد أقصى)
            # نستخدم HTML هنا لأن التغيير قد يكون في "تنسيق الكود" وليس النص فقط
            for attempt in range(90): 
                current_html = await page.evaluate(f'''() => {{
                    const els = document.querySelectorAll("{response_selector}");
                    return els.length > 0 ? els[els.length - 1].innerHTML : "";
                }}''')
                
                # إذا زاد طول الـ HTML، يعني أن الرد لا يزال يُكتب
                if len(current_html) > len(previous_html):
                    previous_html = current_html
                    stable_count = 0
                elif len(current_html) > 0:
                    stable_count += 1
                
                # إذا استقر الرد لـ 8 ثوانٍ، نعتبره اكتمل
                if stable_count >= 10:
                    print(f"✅ تم التقاط الرد المنسق بالكامل.")
                    break
                
                await asyncio.sleep(1)

            # 9. استخراج النتيجة النهائية بـ HTML للحفاظ على القوالب (Templates)
            final_res_html = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll("{response_selector}");
                if (els.length > 0) {{
                    // نأخذ آخر عنصر لضمان جلب الرد الأخير في المحادثة
                    return els[els.length - 1].innerHTML; 
                }}
                return "خطأ: لم نتمكن من العثور على محتوى الرد.";
            }}''')

            output = {"status": "success", "response": final_res_html}

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")
        output = {"status": "error", "message": str(e)}

    # 10. حفظ النتيجة النهائية بتنسيق UTF-8 لضمان سلامة اللغة العربية
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم حفظ الرد في result.json")

if __name__ == "__main__":
    # قراءة السؤال من سطر الأوامر (Command Line Argument)
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(run_gemini_automation(user_prompt))
