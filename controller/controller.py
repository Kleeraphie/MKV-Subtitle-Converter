from gui.gui import GUI
from config import Config
from subconverter import SubtitleConverter
import time
from controller.jobs import Jobs
from threading import Thread


class Controller:
    controller = None

    def __new__(cls, *args, **kwargs):
        if not cls.controller:
            cls.controller = super(Controller, cls).__new__(cls, *args, **kwargs)
            cls.controller._initialize_controller()
            cls.controller.start_program()
        return cls.controller

    def _initialize_controller(self):
        self.file_counter = 0 # number of mkv files
        self.finished_files_counter = 0
        self.files_with_error_counter = 0
        self.job = Jobs.IDLE
        self.config = Config()
        self.exit_code = -1

    def register_gui(self, gui: GUI):
        self.gui = gui

    def register_subconverter(self, subconverter: SubtitleConverter):
        self.subconverter = subconverter

    def start_program(self):
        # start the program
        gui = GUI()
        self.register_gui(gui)
        if self.config.check_for_updates():
            gui.check_for_updates()

        while self.exit_code != 1:
            self.run_program()

    def run_program(self):
        exit_code, values = self.gui.run()
        self.exit_code = exit_code
        self.sc_values = values
        self.file_counter = len(values['selected_paths'])
        self.notify_gui()
        self.start_subconverter()

    def gui_send_values(self, exit_code, values):
        self.exit_code = exit_code
        self.sc_values = values
        self.file_counter = len(values['selected_paths'])

    def sc_change_job(self, job: Jobs):
        self.job = job

    def notify_gui(self):
        self.gui.update(self.file_counter, self.finished_files_counter, self.files_with_error_counter, self.job)

    def start_subconverter(self):
        if self.exit_code == 0:
            self.gui.show_progress()
            sc = SubtitleConverter()
            sc = SubtitleConverter(self.sc_values['selected_paths'],
                                   self.sc_values['edit_subs'],
                                   self.sc_values['save_images'],
                                   self.sc_values['keep_old_mkvs'],
                                   self.sc_values['keep_old_subs'],
                                   self.sc_values['keep_new_subs'],
                                   sc.diff_langs_from_text(self.sc_values['diff_langs']),
                                   sc.sub_format_extension(self.sc_values['sub_format']),
                                   self.sc_values['brightness_diff'] / 100)
            
            self.register_subconverter(sc)
            
            thread = Thread(target=sc.convert)
            thread.start()

            while thread.is_alive():
                self.finished_files_counter = sc.get_finished_files_counter()
                self.files_with_error_counter = sc.get_files_with_error_counter()
                self.job = sc.get_current_job()

                self.notify_gui()
                time.sleep(1)

            self.job = sc.get_current_job()
            self.notify_gui()
