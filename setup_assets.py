import os
import subprocess

def setup():
    # إنشاء مجلد للمتصفح والمكتبات
    os.makedirs("vendor/python", exist_ok=True)
    os.makedirs("vendor/browsers", exist_ok=True)
    
    # 1. تحميل المكتبات داخل المجلد
    subprocess.run(["pip", "install", "playwright", "camoufox", "--target", "vendor/python"])
    
    # 2. تحميل المتصفح داخل المجلد
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "vendor/browsers"
    subprocess.run(["python3", "-m", "playwright", "install", "chromium"])
    subprocess.run(["python3", "-m", "camoufox", "fetch"])

if __name__ == "__main__":
    setup()
