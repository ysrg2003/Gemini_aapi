import os
import subprocess
import shutil
import sys

def setup():
    vendor_dir = "vendor"
    if os.path.exists(vendor_dir):
        shutil.rmtree(vendor_dir)
    
    python_dir = os.path.abspath(os.path.join(vendor_dir, "python"))
    browsers_dir = os.path.abspath(os.path.join(vendor_dir, "browsers"))
    # --- المسار الجديد لكاش كاموفوكس ---
    camou_cache_dir = os.path.abspath(os.path.join(vendor_dir, "camoufox_cache"))
    
    os.makedirs(python_dir, exist_ok=True)
    os.makedirs(browsers_dir, exist_ok=True)
    os.makedirs(camou_cache_dir, exist_ok=True)
    
    print("⏳ بدأت عملية بناء الترسانة الشاملة...")

    # 1. تثبيت المكتبات
    libs = ["playwright", "camoufox", "wheel", "setuptools"]
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        *libs, 
        "--target", python_dir,
        "--no-cache-dir"
    ], check=True)

    # إعداد البيئة لتوجيه كل التحميلات داخل مجلد vendor
    env = os.environ.copy()
    env["PYTHONPATH"] = python_dir + os.pathsep + env.get("PYTHONPATH", "")
    env["PLAYWRIGHT_BROWSERS_PATH"] = browsers_dir
    # --- توجيه الكاش للمجلد الذي سيتم ضغطه ---
    env["CAMOUFOX_CACHE_DIR"] = camou_cache_dir

    print("🌐 تحميل محركات المتصفح (Chromium)...")
    subprocess.run([
        sys.executable, "-m", "playwright", "install", "chromium"
    ], env=env, check=True)
    
    print("🦊 جاري سحب محرك Camoufox المتخفي (700MB+) إلى المجلد المحلي...")
    # الآن سيتم تحميل المتصفح داخل vendor/camoufox_cache
    subprocess.run([
        sys.executable, "-m", "camoufox", "fetch"
    ], env=env, check=True)

    # 4. تنظيف وضغط
    print("🧹 تنظيف الملفات المؤقتة...")
    for root, dirs, files in os.walk(python_dir):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))

    print(f"🗜️ جاري ضغط الترسانة (حجم كبير متوقع)...")
    shutil.make_archive("vendor_assets", 'zip', vendor_dir)
    shutil.rmtree(vendor_dir)
    print("✅ تم إنشاء vendor_assets.zip بنجاح شاملة المتصفح والمكتبات!")

if __name__ == "__main__":
    setup()
