from datetime import datetime
from termcolor import colored

def error(message: str, show_emoji: bool = True) -> None:
    emoji = "❌" if show_emoji else ""
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(colored(f"{date} - {emoji} {message}", "red"))


def success(message: str, show_emoji: bool = True) -> None:
    emoji = "✅" if show_emoji else ""
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(colored(f"{date} - {emoji} {message}", "green"))


def info(message: str, show_emoji: bool = True) -> None:
    emoji = "ℹ️" if show_emoji else ""
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(colored(f"{date} - {emoji} {message}", "magenta"))


def warning(message: str, show_emoji: bool = True) -> None:
    emoji = "⚠️" if show_emoji else ""
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(colored(f"{date} - {emoji} {message}", "yellow"))

def question(message: str, show_emoji: bool = True) -> str:
    emoji = "❓" if show_emoji else ""
    return input(colored(f"{emoji} {message}", "magenta"))
