import pymkv
import os
import pytesseract
from pgsreader import PGSReader
from imagemaker import make_image
from tqdm import tqdm
from pysrt import SubRipFile, SubRipItem, SubRipTime
import srtchecker
import shutil

def get_lang(lang_code: str) -> str | None: 
    if lang_code == "None":
        return None
    else:
        return lang_code

def convert_to_srt(lang:str, track_id: int, img_dir:str, save_images:bool=False):
    srt_file = f"{track_id}.srt"
    pgs_file = f"{track_id}.sup" # TODO change so that it can use any PGS file, not just .sup
    pgs = PGSReader(pgs_file)
    srt = SubRipFile()

    print("Using language: " + lang)
    
    if save_images:
        os.makedirs(img_dir, exist_ok=True)

    print("Loading DisplaySets...")
    all_sets = [ds for ds in tqdm(pgs.iter_displaysets())]

    print(f"Buildung SRT file based on {len(all_sets)} DisplaySets...")
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
    print("Checking SRT file...")
    srtchecker.check_srt(srt_file)
    print(f"Done. SRT file saved as {srt_file}")

def extract_subtitles(file: str): # TODO add return type
    # TODO get path from mkv and change so that mkv is given, not file
    mkv = pymkv.MKVFile(file.name)
    subtitle_ids = []

    for track in mkv.tracks:
        if track.track_type == "subtitles":

            track: pymkv.MKVTrack
            track_id = track.track_id

            if track.track_codec != "HDMV PGS":
                continue

            os.system(f"mkvextract \"{file.name}\" tracks {track_id}:{track_id}.sup")

            subtitle_ids.append(track_id)
            
    return subtitle_ids

def clean(file_name: str, ids): # TODO add type hint
    print("Cleaning up...")
    print(file_name)
    for track_id in ids:
        os.remove(f"{track_id}.sup")
        os.remove(f"{track_id}.srt")
        shutil.rmtree(f"img/{track_id}")

def main():
    for file in os.scandir():
        if not file.name.endswith(".mkv"):
            continue

        file_name = os.path.splitext(os.path.basename(file.path))[0]
        mkv = pymkv.MKVFile(file.name)

        print(f"Processing {file_name}...")
        subtitle_ids = extract_subtitles(file)

        for track_id in subtitle_ids:
            track = mkv.tracks[track_id]

            # get language used in subtitle
            lang_code = track.language
            language = get_lang(lang_code)

            convert_to_srt(language, track_id, f"img/{track_id}", True)

        if len(subtitle_ids) == 0:
            print("No subtitles found.\n")
            continue

        print(f"Replacing subtitles in {file_name}...")
        for track_id in subtitle_ids:
            track = mkv.tracks[track_id]
            # make new track from new .srt file and settings from old PGS subtitle
            new_sub = pymkv.MKVTrack(f"{track_id}.srt", track_name=track.track_name, language=track.language, default_track=track.default_track, forced_track=track.forced_track)
            mkv.replace_track(track_id, new_sub)

        print("Copying file...")
        shutil.copy(file.name, f"{file_name} (1).mkv")
        print("Muxing file...")
        mkv.mux(f"{file_name} (1).mkv", silent=True)
        clean(file.name, subtitle_ids)

        print(f"Finished {file_name}\n")

if __name__ == "__main__":
    main()
