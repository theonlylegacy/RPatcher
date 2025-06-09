import os
import sys
import subprocess
import winreg

try:
    import time
    import zipfile
    import shutil
    import winshell
    import psutil
    import inquirer
    from colorama import Fore, init
    from win32com.client import Dispatch
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.firefox.service import Service as FirefoxService

except ImportError as error:
    print(Fore.WHITE + "[PATCHER] Building \"requirements.bat\"..")

    path = os.path.join(os.path.dirname(__file__), "requirements.bat")

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("pip install selenium\n")
            f.write("pip install winshell\n")
            f.write("pip install colorama\n")
            f.write("pip install psutil\n")
            f.write("pip install inquirer\n")
    
    print(Fore.WHITE + "[PATCHER] Built \"requirements.bat\"!")
    print(Fore.WHITE + "[PATCHER] Extracting libraries..")
    subprocess.run(["cmd", "/c", path])
    print(Fore.WHITE + "[PATCHER] Extracted libraries!")
    os.execv(sys.executable, ["python"] + sys.argv)

init(autoreset = True)

def get_process(process_name):
    for entry in psutil.process_iter():
        if entry.name() == process_name:
            return entry

    return None

def get_roblox_directory():
    local_app_data = os.getenv("LOCALAPPDATA")

    return os.path.join(local_app_data, "Roblox", "Versions")

def configure_driver(download_path):
    options = FirefoxOptions()
    options.set_preference("browser.download.dir", download_path)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.add_argument("--headless")

    service = FirefoxService()
    driver = webdriver.Firefox(service = service, options = options)
    return driver

def get_log(driver, selector):
    wait = WebDriverWait(driver, 20)

    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

        return element
    except:
        driver.quit()
        sys.exit(0)

def stream_console(element):
    printed_lines = set()
    stream_finished = False

    for _ in range(60):
        text = element.text
        lines = text.splitlines()
        new_lines = [line for line in lines if line not in printed_lines]

        for line in new_lines:
            if "Exporting assembled zip file" in line:
                stream_finished = True
                break

            print(Fore.WHITE + line)

        printed_lines.update(new_lines)
        if stream_finished:
            break

        time.sleep(1)

def wait_for_zip(zip_path):
    start_time = time.time()

    while time.time() - start_time < 60:
        if os.path.exists(zip_path) and zip_path.endswith(".zip"):
            return
        
        time.sleep(0.5)

    print(Fore.WHITE + "[" + Fore.RED + "!" + Fore.WHITE + "] " + Fore.RED + f"Timed out waiting for assembled zip file \"{os.path.basename(zip_path)}\"!")
    time.sleep(5)
    os._exit(0)

def uninstall_previous_versions(roblox_directory):
    if not os.path.exists(roblox_directory):
        return

    for name in os.listdir(roblox_directory):
        path = os.path.join(roblox_directory, name)
        
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "RobloxPlayerBeta.exe")):
            print(Fore.WHITE + f"[+] Uninstalling version: \"{name}\"..")
            shutil.rmtree(path)
            print(Fore.WHITE + f"[+] Uninstalled version: \"{name}\"!")

def remove_previous_shortcuts():
    start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")
    
    for name in os.listdir(start_menu):
        path = os.path.join(start_menu, name)
        
        if name == "Roblox Player.lnk" and os.path.isfile(path):
            print(Fore.WHITE + f"[+] Removing shortcut: \"{name}\"..")
            os.remove(path)
            print(Fore.WHITE + f"[+] Removed shortcut \"{name}\"!")

def unzip_file(zip_filename, zip_path, extract_to):
    print(Fore.WHITE + f"[+] Extracting \"{zip_filename}\"..")

    with zipfile.ZipFile(zip_path, "r") as zip_reference:
        zip_reference.extractall(extract_to)
    
    os.remove(zip_path)
    
    print(Fore.WHITE + f"[+] Extracted \"{zip_filename}\"!")

def build_shortcut(path, name):
    start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")
    os.makedirs(start_menu, exist_ok=True)
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(os.path.join(start_menu, f"{name}.lnk"))
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.IconLocation = path
    shortcut.save()

def main():
    binary_type = inquirer.prompt([inquirer.List("choice", message = Fore.YELLOW + "BinaryType", choices = ["WindowsPlayer", "WindowsStudio64", "MacPlayer", "MacStudio"])])
    version_hash = input(Fore.WHITE + "[" + Fore.YELLOW + "?" + Fore.WHITE + "] " + Fore.YELLOW + "Version: " + Fore.WHITE)

    roblox_process = get_process("RobloxPlayerBeta.exe")
    if roblox_process:
        print(Fore.WHITE + "[" + Fore.RED + "!" + Fore.WHITE + "] " + Fore.RED + "\"RobloxPlayerBeta.exe\" is running!")
        
        close_process = input(Fore.WHITE + "[" + Fore.YELLOW + "?" + Fore.WHITE + "] " + Fore.YELLOW + "Terminate \"RobloxPlayerBeta.exe\": " + Fore.WHITE)
        if close_process.upper() != "Y":
            os._exit(0)
        
        print(Fore.WHITE + "[+] Terminating \"RobloxPlayerBeta.exe\"..")
        
        roblox_process.terminate()
        time.sleep(5)
        
        print(Fore.WHITE + "[+] Terminated \"RobloxPlayerBeta.exe\"!")

    print("")
    print(Fore.WHITE + "[+] Configuring driver..")

    roblox_directory = get_roblox_directory()
    api_url = f"https://rdd.fuckass.site/?channel=LIVE&binaryType={binary_type["choice"]}&version={version_hash}"
    driver = configure_driver(roblox_directory)
    driver.get(api_url)
    
    print(Fore.WHITE + "[+] Configured driver!")
    print("")

    stream_console(get_log(driver, "#consoleText"))
    zip_path = os.path.join(roblox_directory, f"LIVE-{binary_type["choice"]}-version-{version_hash}.zip")

    print(Fore.WHITE + f"[+] Exporting assembled zip file \"{os.path.basename(zip_path)}\"..")
    
    wait_for_zip(zip_path)
    zip_directory = os.path.join(roblox_directory, f"version-{version_hash}")

    print(Fore.WHITE + f"[+] Exported assembled zip file \"{os.path.basename(zip_path)}\"!")
    print("")

    uninstall_previous_versions(roblox_directory)
    print(Fore.WHITE + f"[+] Building version folder \"{os.path.basename(zip_directory)}\"..")
    os.makedirs(zip_directory, exist_ok=True)
    print(Fore.WHITE + f"[+] Built version folder \"{os.path.basename(zip_directory)}\"!")
    unzip_file(os.path.basename(zip_path), zip_path, zip_directory)

    roblox_player = None
    for folder_name in os.listdir(roblox_directory):
        folder_path = os.path.join(roblox_directory, folder_name)
        exe_path = os.path.join(folder_path, "RobloxPlayerBeta.exe")
        
        if os.path.isdir(folder_path) and os.path.isfile(exe_path):
            roblox_player = exe_path
            break

    if roblox_player:
        remove_previous_shortcuts()
        print(Fore.WHITE + "[+] Building shortcut \"Roblox Player.lnk\"..")
        build_shortcut(roblox_player, "Roblox Player")
        print(Fore.WHITE + "[+] Built shortcut \"Roblox Player.lnk\"!")
    else:
        print(Fore.WHITE + "[" + Fore.RED + "!" + Fore.WHITE + "] " + Fore.RED + "Error building shortcut \"Roblox Player.lnk\"!")

    print(Fore.WHITE + "[+] Building registry details..")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "URL:Roblox Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player\shell")
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player\shell\open")

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player\shell\open\command") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"\"{roblox_player}\" %1")

    print(Fore.WHITE + "[+] Built registry details!")
    print("")

    print(Fore.WHITE + "[" + Fore.GREEN + "!" + Fore.WHITE + "] " + Fore.GREEN + "Successfully patched Roblox!")

    driver.quit()
    sys.exit(0)

main()
