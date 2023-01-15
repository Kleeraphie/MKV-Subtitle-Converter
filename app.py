import pymkv
import os
import pytesseract
from pgsreader import PGSReader
from imagemaker import make_image
from tqdm import tqdm
from pysrt import SubRipFile, SubRipItem, SubRipTime
import srtchecker
import shutil
import threading
import sys
import time

# helper function for threading
def extract(file: str, track_id: int):
    os.system(f"mkvextract \"{file.name}\" tracks {track_id}:{track_id}.sup")

def extract_subtitles(file: str) -> list[int]: 
    # TODO get path from mkv and change so that mkv is given, not file
    mkv = pymkv.MKVFile(file.name)
    subtitle_ids = []
    thread_pool = []

    for track in mkv.tracks:
        if track.track_type == "subtitles":

            track: pymkv.MKVTrack
            track_id = track.track_id

            if track.track_codec != "HDMV PGS":
                continue

            thread = threading.Thread(name=f"Extract subtitle #{track_id}", target=extract, args=(file, track_id))
            thread.start()
            thread_pool.append(thread)

            subtitle_ids.append(track_id)

    for thread in thread_pool:
        thread.join()
            
    return subtitle_ids

def get_lang(lang_code: str) -> str | None:
    if lang_code == "None":
        return None
    else:
        return lang_code

def convert_to_srt(lang:str, track_id: int, img_dir:str='', save_images:bool=False):
    srt_file = f"{track_id}.srt"
    pgs_file = f"{track_id}.sup"
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
            pds = ds.pds[0] # get Palette Display Segment
            ods = ds.ods[0] # get Object Display Segment
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

def replace_subtitles(mkv: pymkv.MKVFile, subtitle_ids: list[int], file_name: str):
    deleted_tracks = 0

    print(f"Replacing subtitles in {file_name}...")
    for track_id in subtitle_ids:
        # if a subtitle was deleted during editing
        if not os.path.exists(f"{track_id}.srt"):
            mkv.remove_track(track_id - deleted_tracks)
            deleted_tracks += 1
            continue

        track = mkv.tracks[track_id - deleted_tracks]
        # make new track from new .srt file and settings from old PGS subtitle
        new_sub = pymkv.MKVTrack(f"{track_id}.srt", track_name=track.track_name, language=track.language, default_track=track.default_track, forced_track=track.forced_track)
        mkv.replace_track(track_id - deleted_tracks, new_sub)

# estimate new file size based on size of new subtitles
def calc_size(old_size: int, subtitle_ids: list[int]) -> int:
    new_size = old_size
    for track_id in subtitle_ids:
        new_size -= os.path.getsize(f"{track_id}.sup")
        if os.path.exists(f"{track_id}.srt"):
            new_size += os.path.getsize(f"{track_id}.srt")
    return new_size

def mux_file(mkv: pymkv.MKVFile, subtitle_ids: list[int], file: str):
    print("Muxing file...")
    file_size = os.path.getsize(file.path)
    file_name = os.path.splitext(os.path.basename(file.path))[0]
    old_file_size = 0

    pbar = tqdm(total=calc_size(file_size, subtitle_ids), unit='B', unit_scale=True, unit_divisor=1024)

    thread = threading.Thread(name="Muxing", target=mkv.mux, args=(f"{file_name} (1).mkv", True))
    thread.start()

    while thread.is_alive():
        new_file_size = os.path.getsize(f"{file_name} (1).mkv")
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

def clean(subtitle_ids):
    print("Cleaning up...")
    if save_images:
        shutil.rmtree("img/")
    for track_id in subtitle_ids:
        silent_remove(f"{track_id}.sup")
        silent_remove(f"{track_id}.srt")

def main():
    for file in os.scandir():
        if not file.name.endswith(".mkv"):
            continue

        file_name = os.path.splitext(os.path.basename(file.path))[0]
        mkv = pymkv.MKVFile(file.name)
        thread_pool = []

        print(f"Processing {file_name}...")
        subtitle_ids = extract_subtitles(file)

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

            thread = threading.Thread(name=f"Convert subtitle #{id}", target=convert_to_srt, args=(language, id, f"img/{file_name}/{id}/", save_images))
            thread.start()
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.join()

        if edit:
            print("You can now edit the SRT files. Press Enter when you are done.")
            input()

        replace_subtitles(mkv, subtitle_ids, file_name)

        # create empty .mkv file
        open(f"{file_name} (1).mkv", "w").close()
        
        mux_file(mkv, subtitle_ids, file)  
        clean(subtitle_ids)

        print(f"Finished {file_name}\n")

if __name__ == "__main__":
    edit = None
    save_images = None

    try:
        edit = bool(sys.argv[1] == '1')
        save_images = bool(sys.argv[2] == '1')
    except IndexError:
        edit = False if edit is None else edit
        save_images = False if save_images is None else save_images
    main()
