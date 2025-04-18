import os
import shutil
from config import Config
from controller.jobs import Jobs
from controller.sub_formats import SubtitleFormats, SubtitleFileEndings
import time
import subprocess
from backend.subextractor import SubExtractor
from backend.subconverter import SubtitleConverter

class SubMain:

    def __init__(self, files: list = [], edit_flag: bool = False, keep_imgs: bool = False, keep_old_mkvs: bool = False, keep_old_subs: bool = False, keep_new_subs: bool = False, diff_langs: dict = {}, sub_format: SubtitleFormats = SubtitleFormats.SRT, text_brightness_diff: float = 0.1):
        
        self.file_paths = files
        self.edit_flag = edit_flag
        self.keep_imgs = keep_imgs
        self.keep_old_mkvs = keep_old_mkvs
        self.keep_old_subs = keep_old_subs
        self.keep_new_subs = keep_new_subs
        self.diff_langs = diff_langs
        self.format = SubtitleFileEndings.get_format(sub_format.name).value
        self.text_brightness_diff = text_brightness_diff

        self.config = Config()
        self.translate = self.config.translate

        self.file_counter = 0 # number of mkv files
        self.finished_files_counter = 0
        self.files_with_error_counter = 0
        self.current_job = Jobs.IDLE

        self.error_code = 0
        self.error_message = ""
        self.continue_flag = None

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
        if self.continue_flag is False:
            return

        print(self.translate("Muxing file..."))
        self.config.logger.info(f'Muxing file {self.file_name}.')
        new_file_dir = os.path.dirname(self.file_path)
        new_file_path = f"{new_file_dir}\{self.file_name} (1).mkv"

        self.current_job = Jobs.MUXING

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

        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in iter(process.stderr.readline, ''):
            if "Timestamps are unset in a packet" in line:
                self.config.logger.warning(line + ". This may lead to a decreased playback performance.")

        process.wait()

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
        self.continue_flag = None
        
        for self.file_path in self.file_paths:
            self.file_name = os.path.splitext(os.path.basename(self.file_path))[0]
            
            try:
                print(self.translate("Processing {file_name}...").format(file_name=self.file_name))
                self.config.logger.info(f'Processing {self.file_name}.')

                main_dir_path = self.config.get_datadir() / 'subtitles' / self.file_name
                self.img_dir = main_dir_path / 'images'
                self.sub_dir = main_dir_path / 'subtitles'

                self.current_job = Jobs.EXTRACT
                self.config.logger.debug(f'Starting to extract subtitles.')

                extractor = SubExtractor(self.file_path, self.sub_dir)
                extractor.start()

                self.subtitle_counter = extractor.subtitle_counter
                self.subtitle_languages = extractor.subtitle_languages

                self.config.logger.debug(f'Finished extracting subtitles.')

                # skip title if no PGS subtitles were found
                if self.subtitle_counter == 0:
                    print(self.translate("No subtitles found.") + "\n")
                    self.config.logger.info("No subtitles found.")
                    continue

                self.config.logger.debug(f'Starting to convert subtitles.')
                self.current_job = Jobs.CONVERT

                converter = SubtitleConverter(self.subtitle_counter, self.subtitle_languages, self.diff_langs, self.sub_dir, self.img_dir, self.format, self.keep_imgs, self.text_brightness_diff)
                converter.convert_subtitles()
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
                self.finished_files_counter += 1
            except Exception as e:
                self.files_with_error_counter += 1
                self.error_code = 2
                self.error_message = self.translate('Error while processing {file_name}: {error}').format(file_name=self.file_name, error=e)
                self.config.logger.error(f'Error while processing {self.file_name}: {e}')

                # wait for user input to continue
                while self.continue_flag is None:
                    time.sleep(1)

                if self.continue_flag:
                    self.config.logger.debug("Continuing with the next file after error.")
                    self.clean()
                    print()
                else:
                    self.config.logger.debug("Exiting program after error.")
                    self.clean()
                    break

        self.current_job = Jobs.FINISHED
    
# ----------------FOR THE CONTROLLER----------------
    def get_file_counter(self) -> int:
        return self.file_counter
    
    def get_finished_files_counter(self) -> int:
        return self.finished_files_counter
    
    def get_files_with_error_counter(self) -> int:
        return self.files_with_error_counter
    
    def get_current_job(self) -> str:
        return self.current_job
    
    def get_error_code(self) -> int:
        return self.error_code
    
    def get_error_message(self) -> str:
        return self.error_message
    
    def set_continue_flag(self, flag: bool):
        self.continue_flag = flag
        self.reset_error_code()

    def get_continue_flag(self) -> bool:
        return self.continue_flag
    
    def reset_error_code(self):
        self.error_code = 0
        self.error_message = ""