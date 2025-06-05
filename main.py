import os
import sys
import subprocess

try:
    import time
    import zipfile
    import shutil
    import winshell
    import colorama
    import psutil
    from win32com.client import Dispatch
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service

except ImportError as error:
    print("[PATCHER] Building \"requirements.bat\"..")

    bat_path = os.path.join(os.path.dirname(__file__), "requirements.bat")

    if not os.path.exists(bat_path):
        with open(bat_path, "w") as f:
            f.write("pip install selenium\n")
            f.write("pip install winshell\n")
            f.write("pip install colorama\n")
            f.write("pip install psutil\n")
    
    print("[PATCHER] Built \"requirements.bat\"!")

    print("[PATCHER] Extracting libraries..")
    subprocess.run(["cmd", "/c", bat_path])
    print("[PATCHER] Extracted libraries!")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def get_process(process_name):
    process_entry = None

    for entry in psutil.process_iter():
        if entry.name() == process_name:
            process_entry = entry
            break

    return process_entry 

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

def stream_console_log(element, poll_duration=30, poll_interval=1):
    printed_lines = set()

    for _ in range(poll_duration):
        text = element.text
        lines = text.splitlines()
        new_lines = [line for line in lines if line not in printed_lines]

        for line in new_lines:
            if line.strip().endswith("done!"):
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
            print(f"[PATCHER] Clearing previous version: \"{folder_name}\"..")
            shutil.rmtree(folder_path)
            print(f"[PATCHER] Cleared previous version: \"{folder_name}\"!")

def cleanup_previous_shortcuts():
    start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")

    for name in os.listdir(start_menu):
        path = os.path.join(start_menu, name)

        if name == "Roblox Player.lnk" and os.path.isfile(path):
            print(f"[PATCHER] Clearing previous shortcut: \"{name}\"..")
            os.remove(path)
            print(f"[PATCHER] Cleared previous shortcut \"{name}\"!")

def unzip_file(zip_filename, zip_path, extract_to):
    print(f"[PATCHER] Extracting \"{zip_filename}\"..")

    with zipfile.ZipFile(zip_path, "r") as zip_reference:
        zip_reference.extractall(extract_to)
    
    os.remove(zip_path)
    print(f"[PATCHER] Extracted \"{zip_filename}\"!")

def build_shortcut(path, name):
    start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")
    os.makedirs(start_menu, exist_ok=True)

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(os.path.join(start_menu, f"{name}.lnk"))
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.IconLocation = path
    shortcut.save()

def main():
    binary_type = input("[PATCHER] BinaryType: ")  # e.g. WindowsPlayer
    version_hash = input("[PATCHER] Version: ")  # e.g. ad3ee47cdc5e44f6

    roblox_process = get_process("RobloxPlayerBeta.exe")

    if roblox_process:
        print("[PATCHER] \"RobloxPlayerBeta.exe\" is running!")
        close_process = input("[PATCHER] Do you wish to terminate \"RobloxPlayerBeta.exe\"? (Y/N): ")

        if close_process.upper() != "Y":
            os._exit(0)
        
        roblox_process.terminate()
        time.sleep(5)

    roblox_directory = get_roblox_directory()

    api_url = f"https://rdd.fuckass.site/?channel=LIVE&binaryType={binary_type}&version={version_hash}"
    driver = configure_driver(roblox_directory)
    driver.get(api_url)
    log_element = wait_for_log_element(driver, "#consoleText")
    stream_console_log(log_element)
    driver.quit()

    zip_filename = f"LIVE-{binary_type}-version-{version_hash}.zip"
    zip_path = os.path.join(roblox_directory, zip_filename)
    zip_directory = os.path.join(roblox_directory, f"version-{version_hash}")

    print(f"[+] Exported assembled zip file \"{zip_filename}\"!")

    cleanup_previous_versions(roblox_directory)

    print("[PATCHER] Building version folder..")
    os.makedirs(zip_directory, exist_ok=True)
    print("[PATCHER] Built version folder!")

    unzip_file(zip_filename, zip_path, zip_directory)
    roblox_player = None

    for folder_name in os.listdir(roblox_directory):
        folder_path = os.path.join(roblox_directory, folder_name)
        exe_path = os.path.join(folder_path, "RobloxPlayerBeta.exe")

        if os.path.isdir(folder_path) and os.path.isfile(exe_path):
            roblox_player = exe_path
            break

    if roblox_player:
        cleanup_previous_shortcuts()

        print("[PATCHER] Building shortcut \"Roblox Player.lnk\"..")
        build_shortcut(roblox_player, "Roblox Player")
        print("[PATCHER] Built shortcut \"Roblox Player.lnk\"!")
    else:
        print("[PATCHER] Error building shortcut \"Roblox Player.lnk\"!")

    print("[PATCHER] Successfully patched!")
    time.sleep(5)
    os._exit(0)

main()
