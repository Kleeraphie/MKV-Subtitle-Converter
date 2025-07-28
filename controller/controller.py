from gui.gui import GUI
from config import Config
from backend.main import SubMain
import backend.helper as subhelper
import time
from controller.jobs import Jobs
from controller.sub_formats import SubtitleFormats
from multiprocessing import Process, Manager

class Controller:
    controller = None

    def __new__(cls, *args, **kwargs):
        if not cls.controller:
            cls.controller = super(Controller, cls).__new__(cls, *args, **kwargs)
            cls.controller._initialize_controller()
        return cls.controller

    def _initialize_controller(self):
        self.file_counter = 0 # number of mkv files
        self.finished_files_counter = 0
        self.files_with_error_counter = 0
        self.job = Jobs.IDLE
        self.config = Config()
        self.exit_code = -1
        self.sc_error_code = 0
        self.sc_error_msg = ""
        self.sc_edit_flag = False
        self.sub_dir = None

    def register_gui(self, gui: GUI):
        self.gui = gui

    def register_subconverter(self, subconverter: SubMain):
        self.subconverter = subconverter

    def start_program(self):
        if self.config.check_for_updates():
            self.gui.check_for_updates()

        while self.exit_code != 1:
            self.run_program()

    def run_program(self):
        exit_code, values = self.gui.run()
        self.gui_send_values(exit_code, values)

        if self.exit_code == 1:
            return

        if self.file_counter > 0:
            self.notify_gui()
            self.start_subconverter()
        else:
            self.gui.show_no_files_selected_dialog()

    def gui_send_values(self, exit_code: int, values: dict):
        self.exit_code = exit_code
        self.sc_values = values
        self.file_counter = len(values['selected_paths'])

    def sc_change_job(self, job: Jobs):
        self.job = job

    def notify_gui(self):
        self.gui.update(self.file_counter, self.finished_files_counter, self.files_with_error_counter, self.job, self.sc_error_code, self.sc_error_msg, self.sc_edit_flag, self.sub_dir)

    def start_subconverter(self):
        if self.exit_code == 0:
            self.gui.show_progress()
            sc_values = {
                'selected_paths': self.sc_values['selected_paths'],
                'edit_subs': self.sc_values['edit_subs'],
                'save_images': self.sc_values['save_images'],
                'keep_old_mkvs': self.sc_values['keep_old_mkvs'],
                'keep_old_subs': self.sc_values['keep_old_subs'],
                'keep_new_subs': self.sc_values['keep_new_subs'],
                'diff_langs': subhelper.diff_langs_from_text(self.sc_values['diff_langs']),
                'sub_format': SubtitleFormats.get_name(self.sc_values['sub_format']),
                'brightness_diff': self.sc_values['brightness_diff'] / 100
            }

            manager = Manager()
            shared_dict = manager.dict({'done': False})

            thread = Process(target=start_subconverter_thread, args=(sc_values, shared_dict))
            thread.start()

            while not shared_dict['done']:  # Wait until the subprocess signals completion
                self.finished_files_counter = shared_dict.get('finished_files_counter', 0)
                self.files_with_error_counter = shared_dict.get('files_with_error_counter', 0)
                self.job = shared_dict.get('current_job', Jobs.IDLE)
                self.sc_error_code = shared_dict.get('error_code', 0)
                self.sc_error_msg = shared_dict.get('error_message', "")
                self.sc_edit_flag = shared_dict.get('edit_flag', False)
                self.sub_dir = shared_dict.get('sub_dir', None)

                self.notify_gui()

                if self.gui.continue_flag is not None:
                    shared_dict['continue_flag'] = self.gui.continue_flag
                if self.gui.edit_flag is not None:
                    shared_dict['edit_flag'] = self.gui.edit_flag
                if self.gui.get_stop_flag():
                    # Handle stop flag if needed
                    thread.terminate()
                    break

                time.sleep(1)

            self.gui.hide_progress()
            self.gui.show_finish_dialog()


def start_subconverter_thread(sc_values, shared_dict):
    sc = SubMain(sc_values['selected_paths'],
                 sc_values['edit_subs'],
                 sc_values['save_images'],
                 sc_values['keep_old_mkvs'],
                 sc_values['keep_old_subs'],
                 sc_values['keep_new_subs'],
                 sc_values['diff_langs'],
                 sc_values['sub_format'],
                 sc_values['brightness_diff'],
                 shared_dict)

    # Start the conversion process
    sc.convert()

    # Update shared_dict with the final state after conversion
    shared_dict['done'] = True  # Indicate completion
