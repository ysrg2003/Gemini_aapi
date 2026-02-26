import os
import subprocess
import shutil
import sys

def setup():
    # 1. إعداد المسارات الأساسية
    vendor_dir = "vendor"
    current_path = os.getcwd()
    
    python_dir = os.path.join(current_path, vendor_dir, "python")
    browsers_dir = os.path.join(current_path, vendor_dir, "browsers")
    camou_cache_dir = os.path.join(current_path, vendor_dir, "camoufox_cache")

    # تنظيف أي مخلفات سابقة
    if os.path.exists(vendor_dir):
        shutil.rmtree(vendor_dir)
    
    os.makedirs(python_dir, exist_ok=True)
    os.makedirs(browsers_dir, exist_ok=True)
    os.makedirs(camou_cache_dir, exist_ok=True)
    
    print("⏳ بدأت عملية بناء الترسانة الشاملة...")
    print(f"📂 مسار الكاش المستهدف: {camou_cache_dir}")

    # 2. إعداد بيئة التنفيذ المؤقتة لعملية التحميل
    env = os.environ.copy()
    env["PYTHONPATH"] = python_dir + os.pathsep + env.get("PYTHONPATH", "")
    env["PLAYWRIGHT_BROWSERS_PATH"] = browsers_dir
    env["CAMOUFOX_CACHE_DIR"] = camou_cache_dir  # إجبار المكتبة على التحميل هنا

    # 3. تثبيت المكتبات البرمجية داخل مجلد vendor
    print("📦 تثبيت المكتبات (Playwright & Camoufox)...")
    libs = ["playwright", "camoufox", "wheel", "setuptools"]
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        *libs, 
        "--target", python_dir,
        "--no-cache-dir"
    ], check=True)

    # 4. تحميل متصفح Chromium الخاص بـ Playwright
    print("🌐 تحميل محرك Chromium...")
    subprocess.run([
        sys.executable, "-m", "playwright", "install", "chromium"
    ], env=env, check=True)
    
    # 5. تحميل محرك Camoufox (الأهم: الـ 713MB)
    print("🦊 سحب محرك Camoufox الثقيل إلى المجلد المحلي...")
    # ملاحظة: نستخدم sys.executable مع PYTHONPATH للوصول للمكتبة التي ثبتناها للتو
    result = subprocess.run([
        sys.executable, "-m", "camoufox", "fetch"
    ], env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ خطأ في تحميل Camoufox: {result.stderr}")
        sys.exit(1)
    else:
        print("✅ تم تحميل المحرك بنجاح.")

    # 6. تنظيف الملفات الزائدة لتقليل حجم الـ ZIP
    print("🧹 تنظيف الملفات المؤقتة والزائدة...")
    for root, dirs, files in os.walk(vendor_dir):
        for d in ["__pycache__", "tests", "test", "docs"]:
            if d in dirs:
                shutil.rmtree(os.path.join(root, d))

    # 7. عملية الضغط النهائي
    print(f"🗜️ جاري ضغط الترسانة (حوالي 800MB+)... قد يستغرق هذا دقائق...")
    # نضغط محتويات مجلد vendor ليكون الاستخراج سهلاً
    shutil.make_archive("vendor_assets", 'zip', vendor_dir)
    
    if os.path.exists("vendor_assets.zip"):
        size_mb = os.path.getsize("vendor_assets.zip") / (1024 * 1024)
        print(f"✅ تم إنشاء الترسانة بنجاح!")
        print(f"📦 حجم الملف النهائي: {size_mb:.2f} MB")
        # اختيارياً: حذف مجلد vendor لتوفير مساحة على محرك الأقراص في GitHub
        shutil.rmtree(vendor_dir)
    else:
        print("❌ فشل إنشاء ملف الـ ZIP!")
        sys.exit(1)

if __name__ == "__main__":
    setup()
