import os
import sys
import subprocess

try:
    import time
    import zipfile
    import shutil
    import winshell
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service

except ImportError as error:
    print("[PATCHER] Creating \"requirements.bat\"..")

    bat_path = os.path.join(os.path.dirname(__file__), "requirements.bat")

    if not os.path.exists(bat_path):
        with open(bat_path, "w") as f:
            f.write("pip install selenium\n")
            f.write("pip install winshell\n")
    
    print("[PATCHER] Created \"requirements.bat\"!")

    print("[PATCHER] Extracting libraries..")
    subprocess.run(["cmd", "/c", bat_path])
    print("[PATCHER] Extracted libraries!")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def get_roblox_directory():
    local_app_data = os.getenv("LOCALAPPDATA")
    directory = os.path.join(local_app_data, "Roblox", "Versions")
    return directory

def configure_driver(download_path, headless=True):
    options = Options()
    service = Service(log_path=os.devnull)
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }

    options.add_experimental_option("prefs", prefs)

    if headless:
        options.add_argument("--headless")

    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_log_element(driver, selector, timeout=20):
    wait = WebDriverWait(driver, timeout)

    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        return element
    except:
        print("[PATCHER] Timed out")
        driver.quit()
        exit(1)

def stream_console_log(element, exclude_phrase="Thank you for using WEAO RDD!", poll_duration=30, poll_interval=1):
    printed_lines = set()

    for _ in range(poll_duration):
        text = element.text
        lines = text.splitlines()
        new_lines = [line for line in lines if line not in printed_lines]

        for line in new_lines:
            if line.strip().startswith(exclude_phrase) or line.strip().endswith("done!"):
                continue

            print(line)

        printed_lines.update(new_lines)
        time.sleep(poll_interval)

def cleanup_previous_versions(roblox_directory):
    if not os.path.exists(roblox_directory):
        return

    for folder_name in os.listdir(roblox_directory):
        folder_path = os.path.join(roblox_directory, folder_name)

        if os.path.isdir(folder_path) and os.path.isfile(os.path.join(folder_path, "RobloxPlayerBeta.exe")):
            print(f"[PATCHER] Removing previous version: \"{folder_name}\"..")
            shutil.rmtree(folder_path)
            print(f"[PATCHER] Removed previous version: \"{folder_name}\"!")

def unzip_file(zip_filename, zip_path, extract_to):
    print(f"[PATCHER] Extracting \"{zip_filename}\"..")

    with zipfile.ZipFile(zip_path, "r") as zip_reference:
        zip_reference.extractall(extract_to)
    
    os.remove(zip_path)
    print(f"[PATCHER] Extracted \"{zip_filename}\"!")

def create_shortcut(target_path, shortcut_name):
    import winshell
    from win32com.client import Dispatch

    start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")
    os.makedirs(start_menu, exist_ok=True)

    shortcut_path = os.path.join(start_menu, f"{shortcut_name}.lnk")

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.IconLocation = target_path
    shortcut.save()

def main():
    binary_type = input("[PATCHER] BinaryType: ")  # e.g. WindowsPlayer
    version_hash = input("[PATCHER] Version: ")  # e.g. ad3ee47cdc5e44f6

    roblox_directory = get_roblox_directory()
    cleanup_previous_versions(roblox_directory)

    api_url = f"https://rdd.weao.xyz/?channel=LIVE&binaryType={binary_type}&version={version_hash}"
    driver = configure_driver(roblox_directory)
    driver.get(api_url)
    log_element = wait_for_log_element(driver, "#consoleText")
    stream_console_log(log_element)
    driver.quit()

    zip_filename = f"WEAO-LIVE-{binary_type}-version-{version_hash}.zip"
    zip_path = os.path.join(roblox_directory, zip_filename)
    zip_directory = os.path.join(roblox_directory, f"version-{version_hash}")

    print(f"[+] Exported assembled zip file \"{zip_filename}\"!")

    print("[PATCHER] Creating version folder..")
    os.makedirs(zip_directory, exist_ok=True)
    print("[PATCHER] Created version folder!")

    unzip_file(zip_filename, zip_path, zip_directory)
    roblox_player = None

    for folder_name in os.listdir(roblox_directory):
        folder_path = os.path.join(roblox_directory, folder_name)
        exe_path = os.path.join(folder_path, "RobloxPlayerBeta.exe")

        if os.path.isdir(folder_path) and os.path.isfile(exe_path):
            roblox_player = exe_path
            break

    if roblox_player:
        print("[PATCHER] Creating shortcut..")
        create_shortcut(roblox_player, "Roblox Player")
        print("[PATCHER] Created shortcut!")
    else:
        print("[PATCHER] Error creating shortcut!")

    print("[PATCHER] Complete!")
    input("[PATCHER] Exit:")

main()
