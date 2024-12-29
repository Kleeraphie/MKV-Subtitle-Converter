from enum import Enum
from config import Config

class Jobs(Enum):
    config = Config()
    IDLE     = config.translate('Idle')
    EXTRACT  = config.translate('Extracting')
    CONVERT  = config.translate('Converting')
    REPLACE  = config.translate('Replacing')
    MUXING   = config.translate('Muxing new video')
    FINISHED = config.translate('Finished')
    CANCEL   = config.translate('Cancelled')

    def get_percentage(job) -> int:
        match job:
            case Jobs.IDLE:
                return 20
            case Jobs.EXTRACT:
                return 40
            case Jobs.CONVERT:
                return 60
            case Jobs.MUXING:
                return 80
            case Jobs.FINISHED:
                return 100
            case Jobs.CANCEL:
                return 0