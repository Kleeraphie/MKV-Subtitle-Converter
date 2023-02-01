import pymkv
import os
import pytesseract
from pgsreader import PGSReader
from imagemaker import make_image
from tqdm import tqdm
from pysrt import SubRipFile, SubRipItem, SubRipTime
import srtchecker
import threading
import time
import pgsreader

edit_flag = None # if the user wants to edit the subtitles before muxing
diff_langs = {} # if the user wants to use a different language for some subtitles
mkv = None

def diff_langs_from_text(text) -> dict[str, str]:
    if text == "":
        return {}
    
    lines = text.splitlines()
    diff_langs = {}
    for line in lines:
        if line.strip() == "":
            continue

        if "->" not in line:
            print(f"Invalid input: {line}")

        old_lang, new_lang = line.split("->")
        old_lang = old_lang.strip()
        new_lang = new_lang.strip()

        diff_langs[old_lang] = new_lang

    return diff_langs

# helper function for threading
def extract(file_path: str, track_id: int):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    
    os.system(f"mkvextract \"{file_path}\" tracks {track_id}:\"subtitles/{file_name}/subtitles/{track_id}.sup\"")

def extract_subtitles(file_path: str) -> list[int]:
    subtitle_ids = []
    thread_pool = []

    for track in mkv.tracks:
        if track.track_type == "subtitles":

            track: pymkv.MKVTrack
            track_id = track.track_id

            if track.track_codec != "HDMV PGS":
                continue

            thread = threading.Thread(name=f"Extract subtitle #{track_id}", target=extract, args=(file_path, track_id))
            thread.start()
            thread_pool.append(thread)

            subtitle_ids.append(track_id)

    for thread in thread_pool:
        thread.join()
            
    return subtitle_ids

def get_lang(lang_code: str) -> str | None:

    new_lang = diff_langs.get(lang_code) # check if user wants to use a different language

    if new_lang is  not None:
        if new_lang in pytesseract.get_languages():
            return new_lang
        else:
            print(f"Language {new_lang} is not installed, using {lang_code} instead")

    if lang_code in pytesseract.get_languages(): # when user doesn't want to change language or changed language is not installed
        return lang_code
    else:
        print(f"Language \"{lang_code}\" is not installed, using English instead")
        return None

def convert_to_srt(file_name: str, lang:str, track_id: int, img_dir:str='', save_images:bool=False):
    srt_file = f"subtitles/{file_name}/subtitles/{track_id}.srt"
    pgs_file = f"subtitles/{file_name}/subtitles/{track_id}.sup"
    pgs = PGSReader(pgs_file)
    srt = SubRipFile()
    
    if save_images:
        os.makedirs(img_dir, exist_ok=True)

    # loading DisplaySets
    all_sets = [ds for ds in tqdm(pgs.iter_displaysets(), unit="ds")]

    # building SRT file from DisplaySets
    sub_text = ""
    sub_start = 0
    sub_index = 0
    for ds in tqdm(all_sets, unit="ds"):
        if ds.has_image:
            pds = ds.pds[0] # get Palette Definition Segment
            ods = ds.ods[0] # get Object Definition Segment
            img = make_image(ods, pds)
            
            if save_images:
                img.save(f"{img_dir}/{sub_index}.jpg")
            
            sub_text = pytesseract.image_to_string(img, lang)
            sub_start = ods.presentation_timestamp
        else:
            start_time = SubRipTime(milliseconds=int(sub_start))
            end_time = SubRipTime(milliseconds=int(ds.end[0].presentation_timestamp))
            srt.append(SubRipItem(sub_index, start_time, end_time, sub_text))
            sub_index += 1

    # check and save SRT file
    srt.save(srt_file)
    srtchecker.check_srt(srt_file, True)

def replace_subtitles(subtitle_ids: list[int], file_name: str):
    deleted_tracks = 0

    print(f"Replacing subtitles in {file_name}...")
    for track_id in subtitle_ids:
        # if a subtitle was deleted during editing
        if not os.path.exists(f"subtitles/{file_name}/subtitles/{track_id}.srt"):
            mkv.remove_track(track_id - deleted_tracks)
            deleted_tracks += 1
            continue

        track = mkv.tracks[track_id - deleted_tracks]
        # make new track from new .srt file and settings from old PGS subtitle
        new_sub = pymkv.MKVTrack(f"subtitles/{file_name}/subtitles/{track_id}.srt", track_name=track.track_name, language=track.language, default_track=track.default_track, forced_track=track.forced_track)
        mkv.replace_track(track_id - deleted_tracks, new_sub)

# estimate new file size based on size of new subtitles
def calc_size(file_name: str, old_size: int, subtitle_ids: list[int]) -> int:
    new_size = old_size
    for track_id in subtitle_ids:
        new_size -= os.path.getsize(f"subtitles/{file_name}/subtitles/{track_id}.sup")
        if os.path.exists(f"subtitles/{file_name}/subtitles/{track_id}.srt"):
            new_size += os.path.getsize(f"subtitles/{file_name}/subtitles/{track_id}.srt")
    return new_size

def mux_file(subtitle_ids: list[int], file_path: str):
    print("Muxing file...")
    file_size = os.path.getsize(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    new_file_dir = os.path.dirname(file_path)
    new_file_path = f"{new_file_dir}/{file_name} (1).mkv"
    old_file_size = 0

    pbar = tqdm(total=calc_size(file_name, file_size, subtitle_ids), unit='B', unit_scale=True, unit_divisor=1024)

    thread = threading.Thread(name="Muxing", target=mkv.mux, args=(new_file_path, True))
    thread.start()

    while thread.is_alive():
        new_file_size = os.path.getsize(new_file_path)
        pbar.update(new_file_size - old_file_size)
        old_file_size = new_file_size
        time.sleep(0.1)

    pbar.close()

# remove file that may not exist anymore without throwing an error
def silent_remove(file: str):
    try:
        os.remove(file)
    except OSError:
        pass

def clean(file_path: str, subtitle_ids: list[int], keep_old_mkv: bool, keep_srt: bool):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    new_file_dir = os.path.dirname(file_path)
    new_file_path = f"{new_file_dir}/{file_name} (1).mkv"

    print("Cleaning up...\n")
    for track_id in subtitle_ids:
        silent_remove(f"subtitles/{file_name}/subtitles/{track_id}.sup")
        if not keep_srt:
            silent_remove(f"subtitles/{file_name}/subtitles/{track_id}.srt")

    if not keep_old_mkv:
        os.remove(file_path)
        os.rename(new_file_path, file_path)

def main(file_paths: list[str], edit_subs: bool, keep_imgs: bool, keep_old_mkvs: bool, keep_srt: bool, different_languages: dir):
    global edit_flag, diff_langs, mkv

    edit_flag = edit_subs
    diff_langs = different_languages

    for file_path in file_paths:
        try:

            file_name = os.path.splitext(os.path.basename(file_path))[0]
            mkv = pymkv.MKVFile(file_path)
            thread_pool = []

            print(f"Processing {file_name}...")
            subtitle_ids = extract_subtitles(file_path)

            # skip title if no PGS subtitles were found
            if len(subtitle_ids) == 0:
                print("No subtitles found.\n")
                continue

            # convert PGS subtitles to SRT subtitles
            for id in subtitle_ids:
                track = mkv.tracks[id]

                # get language used in subtitle
                lang_code = track.language
                language = get_lang(lang_code)

                thread = threading.Thread(name=f"Convert subtitle #{id}", target=convert_to_srt, args=(file_name, language, id, f"subtitles/{file_name}/img/{id}/", keep_imgs))
                thread.start()
                thread_pool.append(thread)

            for thread in thread_pool:
                thread.join()

            if edit_flag:
                print("You can now edit the SRT files. Press Enter when you are done.")
                print(f"They can be found at: {os.getcwd()}/subtitles/{file_name}/subtitles")
                os.system("explorer.exe " + os.getcwd())
                input()

            replace_subtitles(subtitle_ids, file_name)

            # create empty .mkv file
            new_file_dir = os.path.dirname(file_path)
            new_file_name = f"{new_file_dir}/{file_name} (1).mkv"

            open(new_file_name, "w").close()
            
            mux_file(subtitle_ids, file_path)

            print(f"Finished {file_name}")
        except Exception as e:
            print(f"Error while processing {file_name}: {e}\n")
            input("Press Enter to continue with the next file...")
            print()

        clean(file_path, subtitle_ids, keep_old_mkvs, keep_srt)
