import pymkv
import os
import pytesseract
import pgsreader
from imagemaker import ImageMaker
from tqdm import tqdm
from pysrt import SubRipFile, SubRipItem, SubRipTime
import srtchecker
import threading
import time
import shutil
import pysubs2
from config import Config

class SubtitleConverter:

    def __init__(self, files: list = [], edit_flag: bool = False, keep_imgs: bool = False, keep_old_mkvs: bool = False, keep_old_subs: bool = False, keep_new_subs: bool = False, diff_langs: bool = False, sub_format: str = "SubRip Text (.srt)", text_brightness_diff: float = 0.1):
        
        self.file_paths = files
        self.edit_flag = edit_flag
        self.keep_imgs = keep_imgs
        self.keep_old_mkvs = keep_old_mkvs
        self.keep_old_subs = keep_old_subs
        self.keep_new_subs = keep_new_subs
        self.diff_langs = diff_langs
        self.format = sub_format
        self.text_brightness_diff = text_brightness_diff

        self.config = Config()
        self.translate = self.config.translate

    def sub_formats(self) -> list[str]:
        subs = [
            "SubRip Text (.srt)",
            "Advanced SubStation Alpha (.ass)",
            "SubStation Alpha (.ssa)",
            "MicroDVD (.sub)",
            "JSON (.json)",
            "MPL2 (.mpl)",
            "TMP (.tmp)",
            "VTT (.vtt)"
        ]
        
        return subs
    
    def sub_format_extension(self, format: str) -> str:

        # check if format is valid
        if format not in self.sub_formats():
            return "srt"

        return format[format.find('.') + 1:format.find(')')]
    
    def convert_language(self, lang: str) -> str:
        '''
        Convert the language code from ISO 639-2/B to ISO 639-2/T
        which is used for OCR
        '''
        alt_lang_codes = {'alb': 'sqi',
                          'arm': 'hye',
                          'baq': 'eus',
                          'bur': 'mya',
                          'chi': 'zho',
                          'cze': 'ces',
                          'dut': 'nld',
                          'fre': 'fra',
                          'geo': 'kat',
                          'ger': 'deu',
                          'gre': 'ell',
                          'ice': 'isl',
                          'mac': 'mkd',
                          'may': 'msa',
                          'mao': 'mri',
                          'per': 'fas',
                          'rum': 'ron',
                          'slo': 'slk',
                          'tib': 'bod',
                          'wel': 'cym'}

        return alt_lang_codes.get(lang, lang)

    def diff_langs_from_text(self, text) -> dict[str, str]:
        if text == "":
            return {}
        
        lines = text.splitlines()
        diff_langs = {}
        for line in lines:
            if line.strip() == "":
                continue

            if "->" not in line:
                print(self.translate("Invalid input: {line}").format(line))

            old_lang, new_lang = line.split("->")
            old_lang = old_lang.strip()
            new_lang = new_lang.strip()
            
            if old_lang != self.convert_language(old_lang):
                print(self.translate('Changed "{old_lang}" to "{new_lang}"').format(old_lang=old_lang, new_lang=self.convert_language(old_lang)))
                old_lang = self.convert_language(old_lang)

            if new_lang != self.convert_language(new_lang):
                print(self.translate('Changed "{old_lang}" to "{new_lang}"').format(old_lang=new_lang, new_lang=self.convert_language(new_lang)))
                new_lang = self.convert_language(new_lang)

            diff_langs[old_lang] = new_lang

        return diff_langs

    # helper function for threading
    def extract(self, track_id: int):        
        os.system(f"mkvextract \"{self.file_path}\" tracks {track_id}:\"{os.path.join(self.sub_dir, f'{track_id}.sup')}\"")

    def extract_subtitles(self) -> list[int]:
        self.subtitle_ids = []
        thread_pool = []

        for track in self.mkv.tracks:
            if track.track_type == "subtitles":

                track: pymkv.MKVTrack
                track_id = track.track_id

                if track.track_codec != "HDMV PGS":
                    continue

                if not os.path.exists(self.sub_dir):
                    os.makedirs(self.sub_dir)

                if os.path.exists(os.path.join(self.sub_dir, f'{track_id}.sup')):
                    self.subtitle_ids.append(track_id)
                    continue

                thread = threading.Thread(name=f"Extract subtitle #{track_id}", target=self.extract, args=([track_id]))
                thread.start()
                thread_pool.append(thread)

                self.subtitle_ids.append(track_id)

        for thread in thread_pool:
            thread.join()

    def convert_subtitles(self): # convert PGS subtitles to SRT subtitles
        thread_pool = []

        for id in self.subtitle_ids:
            track: pymkv.MKVTrack
            track = self.mkv.tracks[id]

            # get language to use in subtitle
            lang_code = track.language
            language = self.get_lang(lang_code)

            thread = threading.Thread(name=f"Convert subtitle #{id}", target=self.convert_to_srt, args=(language, id))
            thread.start()
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.join()

        if pgsreader.exit_code != 0:
            raise Exception(self.translate("Error while converting subtitle #{id}. See console for more info.").format(id))
            # TODO Print error message by exit code, therefore check which warnings trigger exceptions

        # no multithreading here because it's already fast enough
        if self.format != "srt":
            for id in self.subtitle_ids:
                subs = pysubs2.load(os.path.join(self.sub_dir, f'{id}.srt'))
                open(os.path.join(self.sub_dir, f'{id}.{self.format}'), 'w').close()
                subs.save(os.path.join(self.sub_dir, f'{id}.{self.format}'))

    def get_lang(self, lang_code: str) -> str | None:

        lang_code = self.convert_language(lang_code)
        new_lang = self.diff_langs.get(lang_code) # check if user wants to use a different language

        if new_lang is  not None:
            if new_lang in pytesseract.get_languages():
                return new_lang
            else:
                print(self.translate('Language "{new_lang}" is not installed, using "{lang_code}" instead').format(new_lang, lang_code))

        if lang_code in pytesseract.get_languages(): # when user doesn't want to change language or changed language is not installed
            return lang_code
        else:
            print(self.translate('Language "{lang_code}" is not installed, using English instead').format(lang_code))
            return None

    def convert_to_srt(self, lang:str, track_id: int):
        srt_file = os.path.join(self.sub_dir, f'{track_id}.srt')
        pgs_file = os.path.join(self.sub_dir, f'{track_id}.sup')

        open(srt_file, "w").close() # create empty SRT file

        pgs = pgsreader.PGSReader(pgs_file)
        srt = SubRipFile()
        
        if self.keep_imgs:
            track_img_dir = os.path.join(self.img_dir, str(track_id))
            os.makedirs(track_img_dir, exist_ok=True)

        # loading DisplaySets
        all_sets = [ds for ds in tqdm(pgs.iter_displaysets(), unit=" ds")]

        if pgsreader.exit_code != 0:
            return

        # building SRT file from DisplaySets
        sub_text = ""
        sub_start = 0
        sub_index = 0
        im = ImageMaker(self.text_brightness_diff)
        for ds in tqdm(all_sets, unit=" ds"):
            if ds.has_image:
                pds = ds.pds[0] # get Palette Definition Segment
                ods = ds.ods[0] # get Object Definition Segment
                img = im.make_image(ods, pds)

                # TODO add exit code check for ImageMaker
                
                if self.keep_imgs:
                    img.save(os.path.join(track_img_dir, f"{sub_index}.jpg"))
                
                sub_text = pytesseract.image_to_string(img, lang)
                sub_start = ods.presentation_timestamp
            else:
                start_time = SubRipTime(milliseconds=int(sub_start))
                end_time = SubRipTime(milliseconds=int(ds.end[0].presentation_timestamp))
                srt.append(SubRipItem(sub_index, start_time, end_time, sub_text))
                sub_index += 1

        srt.save(srt_file) # save as SRT file
        srtchecker.check_srt(srt_file, True) # check SRT file for common OCR mistakes

    def replace_subtitles(self):
        deleted_tracks = 0

        print(self.translate("Replacing subtitles in {file_name}...").format(self.file_name))
        for track_id in self.subtitle_ids:
            sub_path = os.path.join(self.sub_dir, f'{track_id}.{self.format}')

            # if a subtitle was deleted during editing
            if not os.path.exists(sub_path):
                self.mkv.remove_track(track_id - deleted_tracks)
                deleted_tracks += 1
                continue

            track: pymkv.MKVTrack
            track = self.mkv.tracks[track_id - deleted_tracks]

            # make new track from new .srt file and settings from old PGS subtitle
            new_sub = pymkv.MKVTrack(sub_path, track_name=track.track_name, language=track.language, default_track=track.default_track, forced_track=track.forced_track)
            self.mkv.replace_track(track_id - deleted_tracks, new_sub)

    # estimate new file size based on size of new subtitles
    def calc_size(self) -> int:
        file_size = os.path.getsize(self.file_path)
        new_size = file_size
        for track_id in self.subtitle_ids:
            path = os.path.join(self.sub_dir, str(track_id)) # path to subtitle file without extension

            new_size -= os.path.getsize(f"{path}.sup")

            if os.path.exists(f"{path}.{self.format}"):
                new_size += os.path.getsize(f"{path}.{self.format}")

        return new_size

    def mux_file(self):
        print(self.translate("Muxing file..."))
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = os.path.join(new_file_dir, f"{self.file_name} (1).mkv")
        old_file_size = 0

        pbar = tqdm(total=self.calc_size(), unit='B', unit_scale=True, unit_divisor=1024)

        thread = threading.Thread(name="Muxing", target=self.mkv.mux, args=(new_file_path, True))
        thread.start()

        while thread.is_alive():
            new_file_size = os.path.getsize(new_file_path)
            pbar.update(new_file_size - old_file_size)
            old_file_size = new_file_size
            time.sleep(0.1)

        pbar.close()

    # remove file that may not exist anymore without throwing an error
    def silent_remove(self, file: str):
        try:
            os.remove(file)
        except OSError:
            pass

    def clean(self):
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = os.path.join(new_file_dir, f"{self.file_name} (1).mkv")

        print(self.translate("Cleaning up...") + "\n")

        if not (self.keep_old_subs or self.keep_new_subs):
            if not self.keep_imgs:
                shutil.rmtree(os.path.pardir(self.img_dir))
            else:
                shutil.rmtree(self.sub_dir)
        elif not self.keep_old_subs:
            for track_id in self.subtitle_ids:
                self.silent_remove(os.path.join(self.sub_dir, f'{track_id}.sup'))
        elif not self.keep_new_subs:
            for track_id in self.subtitle_ids:
                self.silent_remove(os.path.join(self.sub_dir, f'{track_id}.srt'))
                self.silent_remove(os.path.join(self.sub_dir, f'{track_id}.{self.format}'))

        if not self.keep_old_mkvs:
            os.remove(self.file_path)
            os.rename(new_file_path, self.file_path)

    def convert(self):
        for self.file_path in self.file_paths:
            self.file_name = os.path.splitext(os.path.basename(self.file_path))[0]
            
            try:
                print(self.translate("Processing {file_name}...").format(self.file_name))

                self.mkv = pymkv.MKVFile(self.file_path)
                main_dir_path = os.path.join('subtitles', self.file_name)
                self.img_dir = os.path.join(main_dir_path, 'images')
                self.sub_dir = os.path.join(main_dir_path, 'subtitles')

                self.extract_subtitles()

                # skip title if no PGS subtitles were found
                if len(self.subtitle_ids) == 0:
                    print(self.translate("No subtitles found.") + "\n")
                    continue

                self.convert_subtitles()

                if self.edit_flag:
                    print(self.translate("You can now edit the new subtitle files. Press Enter when you are done."))
                    print(self.translate("They can be found at: {directory}").format(os.path.join(os.getcwd(), self.sub_dir)))
                    if os.name == "nt":
                        os.system(f"explorer.exe \"{os.path.join(os.getcwd(), self.sub_dir)}\"")
                    input()

                self.replace_subtitles()

                # create empty .mkv file
                new_file_dir = os.path.dirname(self.file_path)
                new_file_name = os.path.join(new_file_dir, f"{self.file_name} (1).mkv")

                open(new_file_name, "w").close()
                
                self.mux_file()
                self.clean()

                print(self.translate("Finished {file}").format(self.file_name)) 
            except Exception as e:
                print(self.translate("Error while processing {file}: {exception}").format(self.file_name, e))
                input(self.translate("Press Enter to continue with the next file..."))
                self.clean()
                print()
