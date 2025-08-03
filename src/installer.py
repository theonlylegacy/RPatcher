import json
import subprocess
import sys
import os
import importlib

def package_installed(import_name):
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

with open("dependencies.json") as file:
    dependencies_list = json.load(file)

missing_packages = []

for package in dependencies_list:
    if not package_installed(package["import_name"]):
        missing_packages.append(package["package_name"])

if missing_packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
    os.system("cls")
    os.execv(sys.executable, [sys.executable] + sys.argv)
