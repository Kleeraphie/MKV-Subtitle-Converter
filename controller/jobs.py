from enum import Enum

class Jobs(Enum):
    IDLE = 'idle'
    EXTRACT = 'extract'
    CONVERT = 'convert'
    REPLACE = 'replace'
    MUXING = 'muxing'
    FINISHED = 'finished'
    CANCEL = 'cancel'