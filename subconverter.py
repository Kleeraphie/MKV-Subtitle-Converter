import ffmpeg
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
from pprint import pprint

class SubtitleConverter:

    def __init__(self, files: list = None, edit_flag: bool = False, keep_imgs: bool = False, keep_old_mkvs: bool = False, keep_old_subs: bool = False, keep_new_subs: bool = False, diff_langs: bool = False, sub_format: str = "SubRip Text (.srt)", text_brightness_diff: float = 0.1):
        if files is None:
            files = []
        
        self.file_paths = files
        self.edit_flag = edit_flag
        self.keep_imgs = keep_imgs
        self.keep_old_mkvs = keep_old_mkvs
        self.keep_old_subs = keep_old_subs
        self.keep_new_subs = keep_new_subs
        self.diff_langs = diff_langs
        self.format = sub_format
        self.text_brightness_diff = text_brightness_diff

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

    def diff_langs_from_text(self, text) -> dict[str, str]:
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
    def extract(self, track_id: int):        
        os.system(f"mkvextract \"{self.file_path}\" tracks {track_id}:\"{self.sub_dir}\{track_id}.sup\"")

    def extract_subtitles(self) -> list[int]:
        self.subtitle_ids = []
        thread_pool = []
        probe = ffmpeg.probe(self.file_path)
        subtitle_streams = [stream for stream in probe['streams'] if stream['codec_name'] == 'hdmv_pgs_subtitle']

        for subtitle in subtitle_streams:
            track_id = subtitle['index']

            if os.path.exists(f"{self.sub_dir}\{track_id}.sup"):
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
        probe = ffmpeg.probe(self.file_path)
        subtitle_streams = probe['streams']

        for id in self.subtitle_ids:
            subtitle = subtitle_streams[id]

            # get language to use in subtitle
            lang_code = subtitle['tags']['language']
            language = self.get_lang(lang_code)

            thread = threading.Thread(name=f"Convert subtitle #{id}", target=self.convert_to_srt, args=(language, id))
            thread.start()
            thread_pool.append(thread)

        for thread in thread_pool:
            thread.join()

        if pgsreader.exit_code != 0:
            raise Exception(f"Error while converting subtitle #{id}. See console for more info.")
            # TODO Print error message by exit code, therefore check which warnings trigger exceptions

        # no multithreading here because it's already fast enough
        if self.format != "srt":
            for id in self.subtitle_ids:
                subs = pysubs2.load(f"{self.sub_dir}\{id}.srt")
                open(f"{self.sub_dir}\{id}.{self.format}", 'w').close()
                subs.save(f"{self.sub_dir}\{id}.{self.format}")

    def get_lang(self, lang_code: str) -> str | None:

        new_lang = self.diff_langs.get(lang_code) # check if user wants to use a different language

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

    def convert_to_srt(self, lang:str, track_id: int):
        srt_file = f"{self.sub_dir}\{track_id}.srt"
        pgs_file = f"{self.sub_dir}\{track_id}.sup"

        open(srt_file, "w").close() # create empty SRT file

        pgs = pgsreader.PGSReader(pgs_file)
        srt = SubRipFile()
        
        if self.keep_imgs:
            os.makedirs(f"{self.img_dir}\{track_id}", exist_ok=True)

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
                    img.save(f"{self.img_dir}\{track_id}\{sub_index}.jpg")
                
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
        # TODO: after muxing, the player needs longer to load the video
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = f"{new_file_dir}\{self.file_name} (1).mkv"

        print(f"Replacing subtitles in {self.file_name}...")
        # input_ffmpeg = ffmpeg.input(self.file_path)
        # input_video = input_ffmpeg['v']
        # input_audio = input_ffmpeg['a']

        # # list of input streams
        # streams = [input_video, input_audio]

        # # Add subtitle streams to input streams list
        # for track_id in self.subtitle_ids:
        #     sub_path = os.path.join(self.sub_dir, f"{track_id}.{self.format}")
        #     input_sub = ffmpeg.input(sub_path)
        #     streams.append(input_sub['s'])

        # # Output video with copied video and audio streams and new subtitle streams
        # output_ffmpeg = ffmpeg.output(
        #     *streams,
        #     new_file_path,
        #     vcodec='copy',
        #     acodec='copy',
        #     scodec='copy'
        # )

        probe = ffmpeg.probe(self.file_path)
        # video_stream = [stream['index'] for stream in probe['streams'] if stream['codec_type'] == 'video']
        # audio_stream = [stream['index'] for stream in probe['streams'] if stream['codec_type'] == 'audio']
        # subtitle_streams = [stream['index'] for stream in probe['streams'] if stream['codec_type'] == 'subtitle']
        # pprint(video_stream)
        # pprint(audio_stream)
        # pprint(subtitle_streams)

        ffmpeg_cmd = f'ffmpeg -i \"{self.file_path}\"'

        for track_id in self.subtitle_ids:
            sub_path = os.path.join(self.sub_dir, f"{track_id}.{self.format}")
            ffmpeg_cmd += f' -i \"{sub_path}\"'

        video_audio_streams = [stream['index'] for stream in probe['streams'] if stream['codec_type'] in ['video', 'audio']]
        maps = [f"-map 0:{stream}" for stream in video_audio_streams]

        # ffmpeg_cmd += ' ' + ' '.join(maps)

        for i, track_id in enumerate(self.subtitle_ids):
            maps.append(f" -map {i + 1}:0")

        ffmpeg_cmd += ' ' + ' '.join(maps)

        ffmpeg_cmd += f' -c:v copy -c:a copy -c:s copy'
        ffmpeg_cmd += f' \"{new_file_path}\"'

        # for track_id in self.subtitle_ids:
        #     sub_path = os.path.join(self.sub_dir, f"{track_id}.{self.format}")
        #     output_ffmpeg = ffmpeg.input(new_file_path)
        #     output_ffmpeg = ffmpeg.input(sub_path)
        #     output_ffmpeg = ffmpeg.output(output_ffmpeg, new_file_path, vcodec='copy', acodec='copy', scodec='copy')
        #     print(' '.join(ffmpeg.compile(output_ffmpeg)))
        #     ffmpeg.run(output_ffmpeg)

        print(ffmpeg_cmd)
        os.system(ffmpeg_cmd)        

        # print(' '.join(ffmpeg.compile(output_ffmpeg)))
        # ffmpeg.run(output_ffmpeg)
        exit(0)

    # estimate new file size based on size of new subtitles
    def calc_size(self) -> int:
        file_size = os.path.getsize(self.file_path)
        new_size = file_size
        for track_id in self.subtitle_ids:
            path = f"{self.sub_dir}\{track_id}" # path to subtitle file without extension

            new_size -= os.path.getsize(f"{path}.sup")

            if os.path.exists(f"{path}.{self.format}"):
                new_size += os.path.getsize(f"{path}.{self.format}")

        return new_size

    def mux_file(self):
        print("Muxing file...")
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = f"{new_file_dir}\{self.file_name} (1).mkv"
        self.video.output(new_file_path, vcodec='libx265', acodec='copy').run()
        # old_file_size = 0

        # pbar = tqdm(total=self.calc_size(), unit='B', unit_scale=True, unit_divisor=1024)

        # thread = threading.Thread(name="Muxing", target=self.video.output(new_file_path).run)
        # thread.start()

        # while thread.is_alive():
        #     new_file_size = os.path.getsize(new_file_path)
        #     pbar.update(new_file_size - old_file_size)
        #     old_file_size = new_file_size
        #     time.sleep(0.1)

        # pbar.close()

    # remove file that may not exist anymore without throwing an error
    def silent_remove(self, file: str):
        try:
            os.remove(file)
        except OSError:
            pass

    def clean(self):
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = f"{new_file_dir}\{self.file_name} (1).mkv"

        print("Cleaning up...\n")

        if not (self.keep_old_subs or self.keep_new_subs):
            if not self.keep_imgs:
                shutil.rmtree(f"subtitles\{self.file_name}")
            else:
                shutil.rmtree(self.sub_dir)
        elif not self.keep_old_subs:
            for track_id in self.subtitle_ids:
                self.silent_remove(f"{self.sub_dir}\{track_id}.sup")
        elif not self.keep_new_subs:
            for track_id in self.subtitle_ids:
                self.silent_remove(f"{self.sub_dir}\{track_id}.srt")

        if not self.keep_old_mkvs:
            os.remove(self.file_path)
            os.rename(new_file_path, self.file_path)

    def convert(self):
        for self.file_path in self.file_paths:
            self.file_name = os.path.splitext(os.path.basename(self.file_path))[0]
            
            try:
                print(f"Processing {self.file_name}...")

                self.img_dir = f"subtitles\{self.file_name}\img"
                self.sub_dir = f"subtitles\{self.file_name}\subtitles"

                self.extract_subtitles()

                # skip title if no PGS subtitles were found
                if len(self.subtitle_ids) == 0:
                    print("No subtitles found.\n")
                    continue

                self.convert_subtitles()

                if self.edit_flag:
                    print("You can now edit the new subtitle files. Press Enter when you are done.")
                    print(f"They can be found at: {os.getcwd()}\{self.sub_dir}")
                    if os.name == "nt":
                        os.system(f"explorer.exe \"{os.getcwd()}\{self.sub_dir}\"")
                    input()

                self.replace_subtitles()

                # create empty .mkv file
                new_file_dir = os.path.dirname(self.file_path)
                new_file_name = f"{new_file_dir}\{self.file_name} (1).mkv"

                open(new_file_name, "w").close()
                
                self.mux_file()
                self.clean()

                print(f"Finished {self.file_name}")
            except Exception as e:
                print(f"Error while processing {self.file_name}: {e}")
                input("Press Enter to continue with the next file...")
                self.clean()
                print()
