import pymkv
import os
import pytesseract
from pgsreader import PGSReader
from imagemaker import make_image
from tqdm import tqdm
from pysrt import SubRipFile, SubRipItem, SubRipTime
import srtchecker
import shutil

def convert_to_srt(lang:str, srt_file:str, pgs:PGSReader, img_dir:str, save_images:bool=False):
    srt = SubRipFile()
    
    if save_images:
        os.makedirs(img_dir, exist_ok=True)

    print("Loading DisplaySets...")
    all_sets = [ds for ds in tqdm(pgs.iter_displaysets())]

    print(f"Running OCR on {len(all_sets)} DisplaySets and building SRT file...")
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

    srt.save(srt_file, encoding='utf-8')
    print(f"Done. SRT file saved as {srt_file}")

def main():
    
    for file in os.scandir():
        if not file.name.endswith(".mkv"):
            continue

        mkv = pymkv.MKVFile(file.name)
        subtitle_ids = []

        print(f"Processing {mkv.mkvmerge_path}...")
    
        for track in mkv.tracks:
            if track.track_type == "subtitles":

                track: pymkv.MKVTrack
                track_id = track.track_id

                if track.track_codec != "HDMV PGS":
                    continue

                #os.system(f"mkvextract \"HOTD S01E01.mkv\" tracks {track_id}:{track_id}.sup")
                subtitle_ids.append(track_id)

                srt_file = f"{track_id}.srt"
                pgs = PGSReader(f"{track_id}.sup")
                convert_to_srt("ger", srt_file, pgs, f"img/{track_id}", True)

                print("Checking SRT file...")
                srtchecker.check_srt(srt_file)

        print(f"Replacing subtitles in {mkv.title}...")
        for track_id in subtitle_ids:
            #mkv.replace_track(track_id, f"{track_id}.srt")
            mkv.remove_track(track_id)
            mkv.add_track(f"{track_id}.srt")
            #print(mkv.tracks[track_id].info)

        
        shutil.copyfile(file, f"{file.name} (1).mkv")
        mkv2 = pymkv.MKVFile(f"{file.name} (1).mkv")
        mkv.mux(f"{file.name} (1).mkv")
        print(f"Finished {mkv.title}\n")

if __name__ == "__main__":
    main()
