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
    all_sets = [ds for ds in tqdm(pgs.iter_displaysets())]

    # building SRT file from DisplaySets
    sub_text = ""
    sub_start = 0
    sub_index = 0
    for ds in tqdm(all_sets):
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
    print(f"Done. SRT file saved as {srt_file}")

# helper function for threading
def extract(file: str, track_id: int):
    os.system(f"mkvextract \"{file.name}\" tracks {track_id}:{track_id}.sup")

def extract_subtitles(file: str): # TODO add return type
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

def clean(subtitle_ids):
    print("Cleaning up...")
    if os.path.exists("img/"):
        shutil.rmtree("img/")
    for track_id in subtitle_ids:
        os.remove(f"{track_id}.sup")
        os.remove(f"{track_id}.srt")

def main():
    for file in os.scandir():
        if not file.name.endswith(".mkv"):
            continue

        file_name = os.path.splitext(os.path.basename(file.path))[0]
        mkv = pymkv.MKVFile(file.name)
        thread_pool = []

        print(f"Processing {file_name}...")
        subtitle_ids = extract_subtitles(file)

        if len(subtitle_ids) == 0:
            print("No subtitles found.\n")
            continue

        for track_id in subtitle_ids:
            track = mkv.tracks[track_id]

            # get language used in subtitle
            lang_code = track.language
            language = get_lang(lang_code)

            thread = threading.Thread(name=f"Convert subtitle #{track_id}", target=convert_to_srt, args=(language, track_id))
            thread.start()
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.join()

        print(f"Replacing subtitles in {file_name}...")
        for track_id in subtitle_ids:
            track = mkv.tracks[track_id]
            # make new track from new .srt file and settings from old PGS subtitle
            new_sub = pymkv.MKVTrack(f"{track_id}.srt", track_name=track.track_name, language=track.language, default_track=track.default_track, forced_track=track.forced_track)
            mkv.replace_track(track_id, new_sub)

        # create empty .mkv file
        open(f"{file_name} (1).mkv", "w").close()
        
        print("Muxing file...")
        mkv.mux(f"{file_name} (1).mkv", silent=True)
        clean(subtitle_ids)

        print(f"Finished {file_name}\n")

if __name__ == "__main__":
    main()
