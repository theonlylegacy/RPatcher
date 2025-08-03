import subprocess
import sys
import importlib

subprocess.check_call([sys.executable, "installer.py"])
imports = importlib.import_module("imports")

win32com = imports.win32com
selenium = imports.selenium
colorama = imports.colorama
inquirer = imports.inquirer
zipfile = imports.zipfile
psutil = imports.psutil
shutil = imports.shutil
time = imports.time
os = imports.os
sys = imports.sys
winreg = imports.winreg

def message(type, message, choices = []):
    if type == "i":
        return print(colorama.Fore.WHITE + f"[+] {message}")

    if type == "l":
        return inquirer.prompt([inquirer.List("choice", message = colorama.Fore.YELLOW + message, choices = choices)])

    if type == "q":
        return input(colorama.Fore.WHITE + "[" + colorama.Fore.YELLOW + "?" + colorama.Fore.WHITE + "] " + colorama.Fore.YELLOW + f"{message}: " + colorama.Fore.WHITE)

    if type == "a":
        print(colorama.Fore.WHITE + "[" + colorama.Fore.RED + "!" + colorama.Fore.WHITE + "] " + colorama.Fore.RED + message)

        time.sleep(5)
        sys.exit(0)

    if type == "s":
        print(colorama.Fore.WHITE + "[" + colorama.Fore.GREEN + "!" + colorama.Fore.WHITE + "] " + colorama.Fore.GREEN + message)

def fetch_process(name):
    for entry in psutil.process_iter():
        if entry.name() == name:
            return entry

def fetch_versions_directory():
    localappdata = os.getenv("LOCALAPPDATA")

    return os.path.join(localappdata, "Roblox", "Versions")

def build_webdriver(path):
    options = selenium.webdriver.firefox.options.Options()
    service = selenium.webdriver.firefox.service.Service()

    options.set_preference("browser.download.dir", path)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.add_argument("--headless")

    return selenium.webdriver.Firefox(service = service, options = options)

def build_shortcut(path, name):
    start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")
    os.makedirs(start_menu, exist_ok = True)

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(os.path.join(start_menu, f"{name}.lnk"))
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.IconLocation = path
    shortcut.save()

def fetch_console(webdriver, selector):
    timeout = selenium.webdriver.support.ui.WebDriverWait(webdriver, 20)

    try:
        return timeout.until(selenium.webdriver.support.expected_conditions.presence_of_element_located((selenium.webdriver.common.by.By.CSS_SELECTOR, selector)))
    except:
        webdriver.quit()
        sys.exit(0)

def iterate_console(console, timeout = 40, delay = 1):
    seen_lines = set()

    for iteration in range(timeout):
        lines = console.text.splitlines()
        new_lines = []

        for line in lines:
            if line not in seen_lines:
                new_lines.append(line)

        for line in new_lines:
            if "Exporting assembled zip file" in line:
                return
            
            print(colorama.Fore.WHITE + line.replace("..", "").replace("!", ""))

        seen_lines.update(new_lines)
        time.sleep(delay)

def await_package(path, type, timeout = 40):
    await_start = time.perf_counter()
    await_result = False

    while (time.perf_counter() - await_start) < timeout:
        if os.path.exists(path) and path.endswith(type):
            await_result = True
            break
        
        time.sleep(0.5)
    
    if not await_result:
        message("a", f"Timed out awaiting package {os.path.basename(path)} of type {type}")

        time.sleep(5)
        sys.exit(0)

def patch():
    colorama.init(autoreset = True)

    binary_type = message("l", "BinaryType", ["WindowsPlayer", "WindowsStudio64"])
    version_hash = message("q", "Version")
    process_name = binary_type["choice"] == "WindowsPlayer" and "RobloxPlayerBeta.exe" or binary_type["choice"] == "WindowsStudio64" and "RobloxStudioBeta.exe"
    shortcut_name = binary_type["choice"] == "WindowsPlayer" and "Roblox Player" or binary_type["choice"] == "WindowsStudio64" and "Roblox Studio"
    process = fetch_process(process_name)

    print("")

    if process:
        message("a", f"\"{process_name}\" is running")
        terminate_process = message("q", f"Close \"{process_name}\"")

        if terminate_process.upper() != "Y":
            sys.exit(0)

        process.terminate()

    message("i", "Configuring webdriver")

    versions_directory = fetch_versions_directory()
    webdriver = build_webdriver(versions_directory)
    webdriver.get(f"https://rdd.fuckass.site/?channel=LIVE&binaryType={binary_type["choice"]}&version={version_hash}")

    message("i", "Configured webdriver")
    iterate_console(fetch_console(webdriver, "#consoleText"))

    package_path = os.path.join(versions_directory, f"LIVE-{binary_type["choice"]}-version-{version_hash}.zip")
    message("i", f"Exporting assembled package \"{os.path.basename(package_path)}\"")

    await_package(package_path, "zip")
    package_directory = os.path.join(versions_directory, f"version-{version_hash}")

    message("i", f"Exported assembled package \"{os.path.basename(package_path)}\"")

    for name in os.listdir(versions_directory):
        path = os.path.join(versions_directory, name)

        if os.path.isdir(path) and os.path.isfile(os.path.join(path, process_name)):
            shutil.rmtree(path)

    message("i", f"Building version directory \"{os.path.basename(package_directory)}\"")
    os.makedirs(package_directory, exist_ok = True)

    message("i", f"Extracting package \"{os.path.basename(package_path)}\"")

    with zipfile.ZipFile(package_path, "r") as package:
        package.extractall(package_directory)

    message("i", f"Extracted package \"{os.path.basename(package_path)}\"")
    os.remove(package_path)

    roblox_path = None

    for directory in os.listdir(versions_directory):
        path = os.path.join(versions_directory, directory)
        executable_path = os.path.join(path, process_name)

        if os.path.isdir(path) and os.path.isfile(executable_path):
            roblox_path = executable_path
            break

    if roblox_path:
        start_menu = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Roblox")
    
        for shortcut in os.listdir(start_menu):
            path = os.path.join(start_menu, shortcut)
            
            if shortcut == f"{shortcut_name}.lnk" and os.path.isfile(path):
                os.remove(path)

        build_shortcut(roblox_path, shortcut_name)
    else:
        message("a", f"Could not build shortcut \"{shortcut_name}\" for \"{process_name}\" because it does not exist")

    message("i", "Editing registry details")

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "URL:Roblox Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player\shell")
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player\shell\open")

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\roblox-player\shell\open\command") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"\"{roblox_path}\" %1")

    message("i", "Edited registry details")
    message("s", f"Successfully patched {process_name} to version {version_hash}")

    webdriver.quit()
    sys.exit(0)

patch()