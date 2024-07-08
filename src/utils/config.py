import json
import os
import sys

from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])

def assert_folder_structure() -> None:
    if not os.path.exists(os.path.join(ROOT_DIR, "temp")):
        if get_verbose():
            print(colored(f"=> Creating temp folder at {os.path.join(ROOT_DIR, 'temp')}", "green"))
        os.makedirs(os.path.join(ROOT_DIR, "temp"))


def get_first_time_running() -> bool:
def get_verbose() -> bool:
    with open(os.path.join(ROOT_DIR, "config/config.json"), "r") as file:
        return json.load(file)["verbose"]


def get_headless() -> bool:
    with open(os.path.join(ROOT_DIR, "config/config.json"), "r") as file:
        return json.load(file)["headless"]


def get_generators() -> list:
    with open(os.path.join(ROOT_DIR, "config/config.json"), "r") as file:
        return json.load(file)["generators"]


def get_threads() -> int:
    with open(os.path.join(ROOT_DIR, "config/config.json"), "r") as file:
        return json.load(file)["threads"]


def get_assemblyai_api_key() -> str:
    with open(os.path.join(ROOT_DIR, "config/config.json"), "r") as file:
        return json.load(file)["assembly_ai_api_key"]


def get_fonts_dir() -> str:
    return os.path.join(ROOT_DIR, "assets/fonts")


def get_imagemagick_path() -> str:
    with open(os.path.join(ROOT_DIR, "config/config.json"), "r") as file:
        return json.load(file)["imagemagick_path"]
