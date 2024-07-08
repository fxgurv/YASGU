from typing import List
from uuid import uuid4

import assemblyai as aai
from moviepy.config import change_settings
from moviepy.editor import *
from moviepy.video.fx.all import crop
from moviepy.video.tools.subtitles import SubtitlesClip
from termcolor import colored

from src.utils.config import get_fonts_dir, get_assemblyai_api_key, ROOT_DIR, get_imagemagick_path, get_threads, get_verbose
from src.utils.utils import choose_random_song, equalize_subtitles, info, success


change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})


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
                clip = crop(clip, width=clip.w, height=round(clip.w / 0.5625), \
                            x_center=clip.w / 2, \
                            y_center=clip.h / 2)
            else:
                if get_verbose():
                    info(f" => Resizing Image: {image_path} to 1920x1080")
                clip = crop(clip, width=round(0.5625 * clip.h), height=clip.h, \
                            x_center=clip.w / 2, \
                            y_center=clip.h / 2)
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
