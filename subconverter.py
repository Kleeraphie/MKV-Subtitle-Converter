import os
import pytesseract
import pgsreader
from imagemaker import ImageMaker
from tqdm import tqdm
from pysrt import SubRipFile, SubRipItem, SubRipTime
import srtchecker
import threading
import pymkv
import shutil
import pysubs2
from config import Config
import sys
from pathlib import Path
import subprocess
import bitmath
import json

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
                self.config.logger.error(f"Invalid input: {line}.")

            old_lang, new_lang = line.split("->")
            old_lang = old_lang.strip()
            new_lang = new_lang.strip()
            
            if old_lang != self.convert_language(old_lang):
                print(self.translate('Changed "{old_lang}" to "{new_lang}"').format(old_lang=old_lang, new_lang=self.convert_language(old_lang)))
                self.config.logger.info(f'Changed "{old_lang}" to "{self.convert_language(old_lang)}".')
                old_lang = self.convert_language(old_lang)

            if new_lang != self.convert_language(new_lang):
                print(self.translate('Changed "{old_lang}" to "{new_lang}"').format(old_lang=new_lang, new_lang=self.convert_language(new_lang)))
                self.config.logger.info(f'Changed "{new_lang}" to "{self.convert_language(new_lang)}".')
                new_lang = self.convert_language(new_lang)

            diff_langs[old_lang] = new_lang

        return diff_langs
    
    def extract_metadata(self, file_path: str):
        self.probe = os.popen(f"ffprobe \"{self.file_path}\" -of json -show_entries format:stream").read()
        self.probe = json.loads(self.probe)

        self.subtitle_languages = []
        metadata_file = str(Path(self.get_datadir(), "metadata.txt"))

        # TODO: can be stopped earlier (probably when time starts to change)
        os.system(f"ffmpeg -i \"{self.file_path}\" -map 0:s -c copy -f ffmetadata \"{metadata_file}\"")
        with open(metadata_file, "r") as file:
            metadata = file.read()
            metadata = metadata.splitlines()
            languages = [line for line in metadata if "language" in line]
            self.subtitle_languages= [line.split("=")[1] for line in languages]
        os.remove(metadata_file)

    # helper function for threading
    def extract(self, track_id: int, sizes: list[int], finished: list[bool]):
        sub_file_path = Path(self.sub_dir, f"{track_id}.sup")
        command = "ffmpeg -y -i \"{0}\" -map 0:s:{1} -c copy \"{2}\"".format(self.file_path, track_id, str(sub_file_path))
        print(f'Start {track_id}')
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in iter(process.stderr.readline, ''):
            latest_output = line.strip()
            if "size=" in latest_output:
                latest_output = latest_output.split("size=")[1]
                latest_output = latest_output.split("time=")[0]
                latest_output = latest_output.strip()
                subtitle_size = bitmath.parse_string(latest_output)
                subtitle_size.to_Byte()
                sizes[track_id] = subtitle_size

        process.wait()
        finished[track_id] = True
        print(f'Finished {track_id}')


    def extract_subtitles(self) -> list[int]:
        self.subtitle_counter = 0
        thread_pool = []
        subtitle_streams = [stream for stream in self.probe['streams'] if stream['codec_name'] == 'hdmv_pgs_subtitle']
        current_size, total_size_B = 0, 0
        current_sizes = []
        finished = []

        if not os.path.exists(self.sub_dir):
            self.sub_dir.mkdir(parents=True, exist_ok=True)
            
        for i, subtitle in enumerate(subtitle_streams):

            # calculate total size of subtitles
            subtitle_size = int(subtitle['tags']['NUMBER_OF_BYTES-eng'])
            total_size_B += subtitle_size

            self.subtitle_counter += 1

            # skip if subtitle already exists
            if os.path.exists(str(self.sub_dir / f'{self.subtitle_counter - 1}.sup')):
                continue
            
            current_sizes.append(0)
            thread = threading.Thread(name=f"Extract subtitle #{i}", target=self.extract, args=(i, current_sizes, finished))
            finished.append(False)
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.start()

        while not all(finished):
            current_size = sum(current_sizes)
            print("Progress: " + str(int(current_size / total_size_B * 1024 * 100)) + "%", end="\r")
            
        print("Progress: " + str(int(current_size / total_size_B * 1024 * 100)) + "%")
        # print("Progress: 100%")
        # TODO: add i18n

        for thread in thread_pool:
            thread.join()

    def convert_subtitles(self): # convert PGS subtitles to SRT subtitles
        thread_pool = []

        for id in range(self.subtitle_counter):

            # get language to use in subtitle
            lang_code = self.subtitle_languages[id]
            language = self.get_lang(lang_code)

            thread = threading.Thread(name=f"Convert subtitle #{id}", target=self.convert_to_srt, args=(language, id))
            thread.start()
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.join()

        if pgsreader.exit_code != 0:
            self.config.logger.error('Error while converting subtitle #{id}. See messages before for more information.')
            raise Exception(self.translate("Error while converting subtitle #{id}. See console for more info.").format(id))
            # TODO Print error message by exit code, therefore check which warnings trigger exceptions

        # no multithreading here because it's already fast enough
        if self.format != "srt":
            for id in range(self.subtitle_counter):
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
                self.config.logger.warning(f'Language "{new_lang}" is not installed, using "{lang_code}" instead.')

        if lang_code in pytesseract.get_languages(): # when user doesn't want to change language or changed language is not installed
            return lang_code
        else:
            print(self.translate('Language "{lang_code}" is not installed, using English instead').format(lang_code))
            self.config.logger.warning(f'Language "{lang_code}" is not installed, using English instead.')
            return None

    def convert_to_srt(self, lang:str, track_id: int):
        srt_file = os.path.join(self.sub_dir, f'{track_id}.srt')
        pgs_file = os.path.join(self.sub_dir, f'{track_id}.sup')

        open(srt_file, "w").close() # create empty SRT file

        pgs = pgsreader.PGSReader(pgs_file)
        srt = SubRipFile()
        
        if self.keep_imgs:
            track_img_dir = self.img_dir / str(track_id)
            track_img_dir.mkdir(parents=True, exist_ok=True)

        # loading DisplaySets
        all_sets = [ds for ds in tqdm(pgs.iter_displaysets(), unit=" ds")]

        if pgsreader.exit_code != 0:
            return

        # building SRT file from DisplaySets
        sub_text = ""
        sub_start = 0
        sub_index = 0
        im = ImageMaker(self.text_brightness_diff)
        progress_bar = tqdm(all_sets, unit=" ds")
        for ds in progress_bar:
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

        self.config.logger.debug(f'Finished converting subtitle #{track_id} in {int(progress_bar.format_dict["elapsed"])}s.')
        srt.save(srt_file) # save as SRT file

        # remove \f and new double empty lines from file
        # with open(srt_file, "r") as file:
        #     content = file.read()

        # content = content.replace("\f", "\n")
        # content = re.sub(r'\n\s*\n', '\n\n', content)

        # with open(srt_file, "w") as file:
        #     file.write(content)

        srtchecker.check_srt(srt_file, True) # check SRT file for common OCR mistakes

    # estimate new file size based on size of new subtitles
    def calc_size(self) -> int:
        file_size = os.path.getsize(self.file_path)
        new_size = file_size
        for track_id in range(self.subtitle_counter):
            path = os.path.join(self.sub_dir, str(track_id)) # path to subtitle file without extension

            new_size -= os.path.getsize(f"{path}.sup")

            if os.path.exists(f"{path}.{self.format}"):
                new_size += os.path.getsize(f"{path}.{self.format}")

        return new_size

    def mux_file(self):
        print(self.translate("Muxing file..."))
        self.config.logger.info(f'Muxing file {self.file_name}.')
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = f"{new_file_dir}\{self.file_name} (1).mkv"

        ffmpeg_cmd = f'ffmpeg -i \"{self.file_path}\" -y'

        # add new subtitles as inputs
        for track_id in range(self.subtitle_counter):
            sub_path = os.path.join(self.sub_dir, f'{track_id}.{self.format}')
            ffmpeg_cmd += f' -i \"{sub_path}\"'

        # add video and audio streams to new file
        ffmpeg_cmd += ' -map 0:v -map 0:a'

        # add new subtitles to the new file
        for i in range(self.subtitle_counter):
            ffmpeg_cmd += f" -map {i + 1}:0"

        # add metadata for new subtitles
        for i in range(self.subtitle_counter):
            lang = self.subtitle_languages[i]
            ffmpeg_cmd += f' -metadata:s:s:{i} language={lang}'

        # copy the codecs of video, audio and subtitle streams
        ffmpeg_cmd += f' -c copy'
        ffmpeg_cmd += f' \"{new_file_path}\"'

        print(ffmpeg_cmd)
        os.system(ffmpeg_cmd)

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
        self.config.logger.info("Cleaning up.")

        if not (self.keep_old_subs or self.keep_new_subs):
            if not self.keep_imgs:
                shutil.rmtree(os.path.pardir(self.img_dir))
            else:
                shutil.rmtree(self.sub_dir)
        elif not self.keep_old_subs:
            for track_id in range(self.subtitle_counter):
                self.silent_remove(os.path.join(self.sub_dir, f'{track_id}.sup'))
        elif not self.keep_new_subs:
            for track_id in self.subtitle_counter:
                self.silent_remove(os.path.join(self.sub_dir, f'{track_id}.srt'))
                self.silent_remove(os.path.join(self.sub_dir, f'{track_id}.{self.format}'))

        if not self.keep_old_mkvs:
            os.remove(self.file_path)
            os.rename(new_file_path, self.file_path)

    def convert(self):
        for self.file_path in self.file_paths:
            self.file_name = os.path.splitext(os.path.basename(self.file_path))[0]
            
            try:
                print(self.translate("Processing {file_name}...").format(file_name=self.file_name))
                self.config.logger.info(f'Processing {self.file_name}.')

                self.mkv = pymkv.MKVFile(self.file_path)
                main_dir_path = self.get_datadir() / 'subtitles' / self.file_name
                self.img_dir = main_dir_path / 'images'
                self.sub_dir = main_dir_path / 'subtitles'

                self.extract_metadata(self.file_path)

                self.config.logger.debug(f'Starting to extract subtitles.')
                self.extract_subtitles()
                self.config.logger.debug(f'Finished extracting subtitles.')

                # skip title if no PGS subtitles were found
                if self.subtitle_counter == 0:
                    print(self.translate("No subtitles found.") + "\n")
                    self.config.logger.info("No subtitles found.")
                    continue

                self.config.logger.debug(f'Starting to convert subtitles.')
                self.convert_subtitles()
                self.config.logger.debug(f'Finished converting subtitles.')

                if self.edit_flag:
                    print(self.translate("You can now edit the new subtitle files. Press Enter when you are done."))
                    print(self.translate("They can be found at: {directory}").format(directory=str(self.sub_dir)))
                    self.config.logger.debug(f'Pause for editing subtitles in {self.sub_dir}.')
                    if os.name == "nt":
                        os.system(f"explorer.exe \"{os.path.join(os.getcwd(), self.sub_dir)}\"")
                    input()
                    self.config.logger.debug(f'Continue after pausing for subtitle editing.')
                
                self.mux_file()
                self.clean()

                print(self.translate("Finished {file}").format(file=self.file_name)) 
                self.config.logger.info(f'Finished {self.file_name}.')
            except Exception as e:
                print(self.translate("Error while processing {file}: {exception}").format(file=self.file_name, exception=e))
                self.config.logger.error(f'Error while processing {self.file_name}: {e}')
                input(self.translate("Press Enter to continue with the next file..."))
                self.config.logger.debug("Continuing with the next file.")
                self.clean()
                print()

    def get_datadir(self) -> Path:
        """
        Returns a parent directory path
        where persistent application data can be stored.

        # Linux: ~/.local/share/MKV Subtitle Converter
        # macOS: ~/Library/Application Support/MKV Subtitle Converter
        # Windows: C:/Users/<USER>/AppData/Roaming/MKV Subtitle Converter
        """

        if sys.platform.startswith("win"):
            # path = Path(os.getenv("LOCALAPPDATA"))
            path = Path('.')
        elif sys.platform.startswith("darwin"):
            path = Path("~/Library/Application Support")
        else:
            # linux
            path = Path(os.getenv("XDG_DATA_HOME", "~/.local/share"))

        path = path / "MKV Subtitle Converter"
        path.mkdir(parents=True, exist_ok=True)

        return path
