import os
import platform
import random
from srt_equalizer import srt_equalizer
from src.utils.config import ROOT_DIR
from src.utils.status import *


def close_running_selenium_instances() -> None:
    try:
        info(" => Closing running Selenium instances...")
        if platform.system() == "Windows":
            os.system("taskkill /f /im firefox.exe")
        else:
            os.system("pkill firefox")
        success(" => Closed running Selenium instances.")
    except Exception as e:
        error(f"Error occurred while closing running Selenium instances: {str(e)}")


def build_url(youtube_video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={youtube_video_id}"


def rem_temp_files() -> None:
    mp_dir = os.path.join(ROOT_DIR, "temp")
    files = os.listdir(mp_dir)
    for file in files:
        if not file.endswith(".json"):
            os.remove(os.path.join(mp_dir, file))


def choose_random_song() -> str:
    try:
        songs = os.listdir(os.path.join(ROOT_DIR, "assets/songs"))
        song = random.choice(songs)
        success(f" => Chose song: {song}")
        return os.path.join(ROOT_DIR, "assets/songs", song)
    except Exception as e:
        error(f"Error occurred while choosing random song: {str(e)}")


def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
    srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)
