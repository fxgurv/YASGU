import os
import json
import random
import re
import time
from datetime import datetime
from typing import List
from uuid import uuid4
import assemblyai as aai
import g4f
import requests
from moviepy.config import change_settings
from moviepy.editor import *
from moviepy.video.fx.all import crop
from moviepy.video.tools.subtitles import SubtitlesClip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from termcolor import colored
from webdriver_manager.firefox import GeckoDriverManager

# Constants
ROOT_DIR = os.getcwd()
YOUTUBE_TEXTBOX_ID = "textbox"
YOUTUBE_MADE_FOR_KIDS_NAME = "VIDEO_MADE_FOR_KIDS_MFK"
YOUTUBE_NOT_MADE_FOR_KIDS_NAME = "VIDEO_MADE_FOR_KIDS_NOT_MFK"
YOUTUBE_NEXT_BUTTON_ID = "next-button"
YOUTUBE_RADIO_BUTTON_XPATH = "//*[@id=\"radioLabel\"]"
YOUTUBE_DONE_BUTTON_ID = "done-button"

# Utility Functions
def assert_folder_structure() -> None:
    if not os.path.exists(os.path.join(ROOT_DIR, "temp")):
        if get_verbose():
            print(colored(f"=> Creating temp folder at {os.path.join(ROOT_DIR, 'temp')}", "green"))
        os.makedirs(os.path.join(ROOT_DIR, "temp"))

def get_first_time_running() -> bool:
    return not os.path.exists(os.path.join(ROOT_DIR, "temp"))

def get_verbose() -> bool:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["verbose"]

def get_headless() -> bool:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["headless"]

def get_generators() -> list:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["generators"]

def get_threads() -> int:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["threads"]

def get_assemblyai_api_key() -> str:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["assembly_ai_api_key"]

def get_fonts_dir() -> str:
    return os.path.join(ROOT_DIR, "Fonts")

def get_imagemagick_path() -> str:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["imagemagick_path"]

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

def rem_temp_files() -> None:
    mp_dir = os.path.join(ROOT_DIR, "temp")
    files = os.listdir(mp_dir)
    for file in files:
        if not file.endswith(".json"):
            os.remove(os.path.join(mp_dir, file))

def choose_random_song() -> str:
    try:
        songs = os.listdir(os.path.join(ROOT_DIR, "Music"))
        song = random.choice(songs)
        success(f" => Chose song: {song}")
        return os.path.join(ROOT_DIR, "Music", song)
    except Exception as e:
        error(f"Error occurred while choosing random song: {str(e)}")

def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
    from srt_equalizer import srt_equalizer
    srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)

def build_is_topic_already_covered_prompt(already_covered: str, subject: str) -> str:
    return (f"Here is a list of already covered subject : {already_covered}. "
            f"Tell me if the following subject looks like one we already covered :  {subject}. "
            f"Just answer with 'yes' or 'no', nothing else.")

def build_generate_topic_prompt(subject: str) -> str:
    return (f"Please generate a specific video idea that takes about the following topic: {subject}. "
            f"Make it exactly one sentence. "
            f"Be creative! Find a unique angle or perspective on the topic."
            f"Only return the topic, nothing else.")

def build_generate_script_prompt(topic: str, language: str) -> str:
    return (f"""
        Generate a script for a video in 4 sentences, depending on the subject of the video.

        The script is to be returned as a string with the specified number of paragraphs.

        Here is an example of a string:
        "This is an example string."

        Do not under any circumstance reference this prompt in your response.

        Get straight to the point, don't start with unnecessary things like, "welcome to this video" or "Sure here is a script".

        Obviously, the script should be related to the subject of the video.

        YOU MUST NOT EXCEED THE 4 SENTENCES LIMIT. MAKE SURE THE 4 SENTENCES ARE SHORT. LESS THAN 5000 CHARACTER IN TOTAL BUT MORE THAN 2000 CHARACTERS IN TOTAL.
        YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE SCRIPT, NEVER USE A TITLE.
        YOU MUST WRITE THE SCRIPT IN THE LANGUAGE SPECIFIED IN [LANGUAGE].
        ONLY RETURN THE RAW CONTENT OF THE SCRIPT. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE SCRIPT ITSELF. ALSO, NEVER TALK ABOUT THE AMOUNT OF PARAGRAPHS OR LINES. JUST WRITE THE SCRIPT

        Subject: {topic}
        Language: {language}
        """)

def build_generate_title_prompt(subject: str, language: str) -> str:
    return (f"Please generate a YouTube Short Video Title for the following subject, including hashtags: {subject}. "
    f"Only return the title, nothing else. "
    f"Limit the title under 80 characters. "
    f"YOU MUST WRITE THE TITLE IN THE {language} LANGUAGE.")

def build_generate_description_prompt(script: str, language: str) -> str:
    return (f"Please generate a YouTube Short Video Description for the following script: {script}. "
            f"Only return the description, nothing else."
             f"Limit the description under 300 characters. "
            f"YOU MUST WRITE THE DESCRIPTION IN THE {language} LANGUAGE.")

def build_generate_image_prompts(script: str, subject: str, n_prompts) -> str:
    return (f"""
        Generate {n_prompts} Image Prompts for AI Image Generation,
        depending on the subject of a video.
        Subject: {subject}

        The image prompts are to be returned as
        a JSON-Array of strings.

        Each search term should consist of a full sentence,
        always add the main subject of the video.

        Be emotional and use interesting adjectives to make the
        Image Prompt as detailed as possible.

        YOU MUST ONLY RETURN THE JSON-ARRAY OF STRINGS.
        YOU MUST NOT RETURN ANYTHING ELSE. 
        YOU MUST NOT RETURN THE SCRIPT.

        The search terms must be related to the subject of the video.
        Here is an example of a JSON-Array of strings:
        ["image prompt 1", "image prompt 2", "image prompt 3"]

        For context, here is the full text:
        {script}
        """)

def parse_model(model_name: str) -> any:
    if model_name == "gpt4":
        return g4f.models.gpt_4
    elif model_name == "gpt35_turbo":
        return g4f.models.gpt_35_turbo
    elif model_name == "llama2_7b":
        return g4f.models.llama2_7b
    elif model_name == "llama2_13b":
        return g4f.models.llama2_13b
    elif model_name == "llama2_70b":
        return g4f.models.llama2_70b
    elif model_name == "mixtral_8x7b":
        return g4f.models.mixtral_8x7b
    elif model_name == "dolphin_mixtral_8x7b":
        return g4f.models.dolphin_mixtral_8x7b
    elif model_name == "airoboros_70b":
        return g4f.models.airoboros_70b
    elif model_name == "airoboros_l2_70b":
        return g4f.models.airoboros_l2_70b
    elif model_name == "gemini":
        return g4f.models.gemini
    elif model_name == "claude_v2":
        return g4f.models.claude_v2
    elif model_name == "claude_3_sonnet":
        return g4f.models.claude_3_sonnet
    elif model_name == "claude_3_opus":
        return g4f.models.claude_3_opus
    else:
        return g4f.models.gpt_35_turbo

def generate_response(prompt: str, model: any, max_retry = 10) -> str:
    response = ""
    retry = 0
    while not response:
        if retry > max_retry:
            error("Failed to generate response.")
            return ""
        response = g4f.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        retry += 1
    return response

def generate_image(prompt: str, image_model: str, generation_path: str) -> str:
    ok = False
    while not ok:
        url = f"https://hercai.onrender.com/{image_model}/text2image?prompt={prompt}"
        r = requests.get(url)
        parsed = r.json()
        if "url" not in parsed or not parsed.get("url"):
            if get_verbose():
                info(f" => Failed to generate Image for Prompt: {prompt}. Retrying...")
            ok = False
        else:
            ok = True
            image_url = parsed["url"]
            image_path = os.path.join(generation_path, str(uuid4()) + ".png")
            with open(image_path, "wb") as image_file:
                image_r = requests.get(image_url)
                image_file.write(image_r.content)
            if get_verbose():
                info(f" => Wrote Image to \"{image_path}\"\n")
            return image_path

def generate_script_to_speech(script) -> str:
    path = os.path.join(ROOT_DIR, "temp", str(uuid4()) + ".wav")
    script = re.sub(r'[^\w\s.?!]', '', script)
    TTS().synthesize(script, path)
    if get_verbose():
        info(f" => Wrote TTS to \"{path}\"")
    return path

def generate_subtitles(audio_path: str) -> str:
    aai.settings.api_key = get_assemblyai_api_key()
    config = aai.TranscriptionConfig()
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)
    subtitles = transcript.export_subtitles_srt()
    srt_path = os.path.join(ROOT_DIR, "temp", str(uuid4()) + ".srt")
    with open(srt_path, "w") as file:
        file.write(subtitles)
    return srt_path

def generate_video(images, tts_path, subtitles_path, font, subtitles_max_chars, subtitles_size, subtitles_color, subtitles_stroke_color, subtitles_stroke_thickness, audio_volume) -> str:
    combined_image_path = os.path.join(ROOT_DIR, "temp", str(uuid4()) + ".mp4")
    threads = get_threads()
    tts_clip = AudioFileClip(tts_path)
    max_duration = tts_clip.duration
    req_dur = max_duration / len(images)
    generator = lambda txt: TextClip(
        txt,
        font=os.path.join(get_fonts_dir(), font),
        fontsize=subtitles_size,
        color=subtitles_color,
        stroke_color=subtitles_stroke_color,
        stroke_width=subtitles_stroke_thickness,
        size=(1080, 1920),
        method="caption",
    )
    clips = []
    tot_dur = 0
    while tot_dur < max_duration:
        for image_path in images:
            clip = ImageClip(image_path)
            clip.duration = req_dur
            clip = clip.set_fps(30)
            if round((clip.w / clip.h), 4) < 0.5625:
                if get_verbose():
                    info(f" => Resizing Image: {image_path} to 1080x1920")
                clip = crop(clip, width=clip.w, height=round(clip.w / 0.5625), x_center=clip.w / 2, y_center=clip.h / 2)
            else:
                if get_verbose():
                    info(f" => Resizing Image: {image_path} to 1920x1080")
                clip = crop(clip, width=round(0.5625 * clip.h), height=clip.h, x_center=clip.w / 2, y_center=clip.h / 2)
            clip = clip.resize((1080, 1920))
            clips.append(clip)
            tot_dur += clip.duration
    final_clip = concatenate_videoclips(clips)
    final_clip = final_clip.set_fps(30)
    random_song = choose_random_song()
    equalize_subtitles(subtitles_path, subtitles_max_chars)
    subtitles = SubtitlesClip(subtitles_path, generator)
    subtitles.set_pos(("center", "center"))
    random_song_clip = AudioFileClip(random_song).set_fps(44300)
    random_song_clip = random_song_clip.fx(afx.volumex, audio_volume)
    comp_audio = CompositeAudioClip([
        tts_clip.set_fps(44300),
        random_song_clip
    ])
    final_clip = final_clip.set_audio(comp_audio)
    final_clip = final_clip.set_duration(tts_clip.duration)
    final_clip = CompositeVideoClip([
        final_clip,
        subtitles
    ])
    final_clip.write_videofile(combined_image_path, threads=threads)
    success(f"Wrote Video to \"{combined_image_path}\"")
    return combined_image_path

def init_browser(firefox_profile_path: str) -> webdriver.Firefox:
    options: Options = Options()
    if get_headless():
        options.add_argument("--headless")
    options.add_argument("-profile")
    options.add_argument(firefox_profile_path)
    service: Service = Service(GeckoDriverManager().install())
    browser: webdriver.Firefox = webdriver.Firefox(service=service, options=options)
    return browser

def get_channel_id(browser) -> str:
    driver = browser
    driver.get("https://studio.youtube.com")
    time.sleep(2)
    channel_id = driver.current_url.split("/")[-1]
    return channel_id

def upload_video(browser, video_path, title, description, is_for_kids) -> str:
    try:
        title = title[:100]
        description = description[:300]
        driver = browser
        verbose = get_verbose()
        driver.get("https://www.youtube.com/upload")
        FILE_PICKER_TAG = "ytcp-uploads-file-picker"
        file_picker = driver.find_element(By.TAG_NAME, FILE_PICKER_TAG)
        INPUT_TAG = "input"
        file_input = file_picker.find_element(By.TAG_NAME, INPUT_TAG)
        file_input.send_keys(video_path)
        time.sleep(5)
        textboxes = driver.find_elements(By.ID, YOUTUBE_TEXTBOX_ID)
        title_el = textboxes[0]
        description_el = textboxes[-1]
        if verbose:
            info("\t=> Setting title...")
        title_el.click()
        time.sleep(1)
        title_el.clear()
        title_el.send_keys(title)
        if verbose:
            info("\t=> Setting description...")
        try:
            time.sleep(5)
            description_el.click()
            time.sleep(0.5)
            description_el.clear()
            description_el.send_keys(description)
        except:
            warning("Description not clickable, skipping...")
        time.sleep(0.5)
        if verbose:
            info("\t=> Setting `made for kids` option...")
        is_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_MADE_FOR_KIDS_NAME)
        is_not_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_NOT_MADE_FOR_KIDS_NAME)
        if not is_for_kids:
            is_not_for_kids_checkbox.click()
        else:
            is_for_kids_checkbox.click()
        time.sleep(0.5)
        if verbose:
            info("\t=> Clicking next...")
        next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
        next_button.click()
        if verbose:
            info("\t=> Clicking next again...")
        next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
        next_button.click()
        time.sleep(2)
        if verbose:
            info("\t=> Clicking next again...")
        next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
        next_button.click()
        if verbose:
            info("\t=> Setting as public...")
        radio_button = driver.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)
        radio_button[2].click()
        if verbose:
            info("\t=> Clicking done button...")
        done_button = driver.find_element(By.ID, YOUTUBE_DONE_BUTTON_ID)
        done_button.click()
        time.sleep(2)
        if verbose:
            info("\t=> Getting video URL...")
        driver.get(f"https://studio.youtube.com/channel/{get_channel_id(browser)}/videos/short")
        time.sleep(2)
        videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
        first_video = videos[0]
        anchor_tag = first_video.find_element(By.TAG_NAME, "a")
        href = anchor_tag.get_attribute("href")
        if verbose:
            info(f"\t=> Extracting video ID from URL: {href}")
        video_id = href.split("/")[-2]

        # Build URL
        url = build_url(video_id)

        if verbose:
            success(f" => Uploaded Video: {url}")

        # Close the browser
        driver.quit()

        return url
    except:
        browser.quit()
        return ""

def main():
    generators_configs = get_generators()
    done = 0
    info(f"Generating {len(generators_configs)} videos...")
    for generator_config in generators_configs:
        try:
            generator = Generator(generator_config)
            data = generator.generate_video()
            generator.upload_video(data["video_path"], data["title"], data["description"])
            done += 1
        except Exception as e:
            error(f"Error occurred while generating video: {str(e)}")
            continue
    info(f"Generated {done} videos. Exiting...")

if __name__ == "__main__":
    # Setup file tree
    assert_folder_structure()

    # Remove temporary files
    rem_temp_files()

    while True:
        try:
            main()
        except Exception as e:
            error(f"Error occurred: {str(e)}")
        sleep(3600*8 + random.randint(0, 3600))
