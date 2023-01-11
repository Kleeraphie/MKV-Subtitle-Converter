# source: https://github.com/EzraBC/pgsreader

#!/usr/bin/env python3
from os.path import split as pathsplit
from collections import namedtuple

# Segments
PDS = int('0x14', base=16) # Palette Definition Segment, 0x14
ODS = int('0x15', base=16) # Object Definition Segment, 0x15
PCS = int('0x16', base=16) # Presentation Composition Segment, 0x16
WDS = int('0x17', base=16) # Window Definition Segment, 0x17
END = int('0x80', base=16) # End of Display Set Segment, 0x80

# Named tuple access for static PDS palettes 
Palette = namedtuple('Palette', "Y Cr Cb Alpha")

class InvalidSegmentError(Exception):
    '''Raised when a segment does not match PGS specification'''


class PGSReader:

    def __init__(self, filepath):
        self.filedir, self.file = pathsplit(filepath) 
        with open(filepath, 'rb') as f:
            self.bytes = f.read()
            

    def make_segment(self, bytes_):
        #print(bytes_[10]) # TODO could be devided by something because it's much larger than the dict's size
        print(int(str(bytes_[10]), base=16))
        cls = SEGMENT_TYPE[bytes_[10]]
        return cls(bytes_) # can return any segment, but cls is no segment

    def iter_segments(self):
        bytes_ = self.bytes[:]
        while bytes_:
            size = 13 + int(bytes_[11:13].hex(), 16)
            yield self.make_segment(bytes_[:size])
            bytes_ = bytes_[size:]

    def iter_displaysets(self):
        ds = []
        for s in self.iter_segments():
            ds.append(s)
            if s.type == 'END':
                yield DisplaySet(ds)
                ds = []

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            self._segments = list(self.iter_segments())
        return self._segments

    @property
    def displaysets(self):
        if not hasattr(self, '_displaysets'):
            self._displaysets = list(self.iter_displaysets())
        return self._displaysets


class BaseSegment:

    SEGMENT = {
        PDS: 'PDS', 
        ODS: 'ODS', 
        PCS: 'PCS', 
        WDS: 'WDS', 
        END: 'END'
    }
    
    def __init__(self, bytes_):
        self.bytes = bytes_
        if bytes_[:2] != b'PG': # magic number (0x5047)
            raise InvalidSegmentError
        self.pts = int(bytes_[2:6].hex(), base=16)/90 # presentation timestamp (90kHz clock)
        self.dts = int(bytes_[6:10].hex(), base=16)/90 # decoding timestamp (90kHz clock) # can be ignored because it should always be 0.
        self.type = self.SEGMENT[bytes_[10]] # segment type
        self.size = int(bytes_[11:13].hex(), base=16) # segment size
        self.data = bytes_[13:] # segment data

        if self.dts != 0:
            print('Warning: Decoding timestamp (DTS) not 0')

    def __len__(self):
        return self.size

    @property
    def presentation_timestamp(self): return self.pts

    @property
    def decoding_timestamp(self): return self.dts

    @property
    def segment_type(self): return self.type


class PresentationCompositionSegment(BaseSegment):

    class CompositionObject:

        def __init__(self, bytes_):
            self.bytes = bytes_
            self.object_id = int(bytes_[0:2].hex(), base=16) # ID of the ODS segment that defines the image to be shown
            self.window_id = bytes_[2] # ID of the WDS segment that defines the window in which the image is to be shown
            self.cropped = bool(bytes_[3]) # 0x00: not cropped, 0x40: Force display of the cropped image object
            self.x_offset = int(bytes_[4:6].hex(), base=16) # horizontal offset of the image in the window
            self.y_offset = int(bytes_[6:8].hex(), base=16) # vertical offset of the image in the window
            if self.cropped:
                self.crop_x_offset = int(bytes_[8:10].hex(), base=16) # horizontal offset of the cropped image
                self.crop_y_offset = int(bytes_[10:12].hex(), base=16) # vertical offset of the cropped image
                self.crop_width = int(bytes_[12:14].hex(), base=16) # width of the cropped image
                self.crop_height = int(bytes_[14:16].hex(), base=16) # height of the cropped image

    STATE = {
        int('0x00', base=16): 'Normal',
        int('0x40', base=16): 'Acquisition Point',
        int('0x80', base=16): 'Epoch Start'
    }

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.width = int(self.data[0:2].hex(), base=16) # video width
        self.height = int(self.data[2:4].hex(), base=16) # video height
        self.frame_rate = self.data[4] # can be ignored because it should always be 1 (0x10).
        self._num = int(self.data[5:7].hex(), base=16) # number of composition objects (max 32, Number of this specific composition. It is incremented by one every time a graphics update occurs.)
        self._state = self.STATE[self.data[7]] # composition state (0x00: Normal, 0x40: Acquisition Point, 0x80: Epoch Start)
        self.palette_update = bool(self.data[8]) # palette update flag (0x00: No update, 0x80: Update)
        self.palette_id = self.data[9] # palette id (0x00: Palette 0, 0x01: Palette 1)
        self._num_comps = self.data[10] # number of composition objects in this segment (max 16)

        """about composition state:
        Epoch Start: defines a new display; contains all functional segments needed to display a new composition
        Acquisition Point: defines a display refresh; used to compose in the middle of the Epoch. includes functional segments with new objects to be used in a new composition, replacing old objects with same Object ID.
        Normal: defines a display update, and contains only functional segments with elements that are different from the preceding composition. mostly used to stop displaying objects on the screen by defining a composition with no composition objects (0x0 in the Number of Composition Objects flag) but also used to define a new composition with new objects and objects defined since the Epoch Start."""

    @property
    def composition_number(self) -> int:
        return self._num

    @property
    def composition_state(self) -> str:
        return self._state

    @property
    def composition_objects(self) -> list[CompositionObject]:
        if not hasattr(self, '_composition_objects'):
            self._composition_objects = self.get_composition_objects()

            if len(self._composition_objects) != self._num_comps:
                print('Warning: Number of composition objects is not equal to the number of composition objects in this segment.')

        return self._composition_objects

    def get_composition_objects(self) -> list[CompositionObject]:
        bytes_ = self.data[11:]
        compositions = []

        while len(bytes_) > 0:
            length = 8
            if bytes_[3]:
                length += 8

            compositions.append(self.CompositionObject(bytes_[:length]))
            bytes_ = bytes_[length:]
        return compositions


class WindowDefinitionSegment(BaseSegment):

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.num_windows = self.data[0]
        self.window_id = self.data[1]
        self.x_offset = int(self.data[2:4].hex(), base=16)
        self.y_offset = int(self.data[4:6].hex(), base=16)
        self.width = int(self.data[6:8].hex(), base=16)
        self.height = int(self.data[8:10].hex(), base=16)

class PaletteDefinitionSegment(BaseSegment):

    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.palette_id = self.data[0]
        self.version = self.data[1]
        self.palette = [Palette(0, 0, 0, 0)]*256
        # Slice from byte 2 til end of segment. Divide by 5 to determine number of palette entries
        # Iterate entries. Explode the 5 bytes into namedtuple Palette. Must be exploded
        for entry in range(len(self.data[2:])//5):
            i = 2 + entry*5
            self.palette[self.data[i]] = Palette(*self.data[i+1:i+5])


class ObjectDefinitionSegment(BaseSegment):

    SEQUENCE = {
        int('0x40', base=16): 'Last',
        int('0x80', base=16): 'First',
        int('0xc0', base=16): 'First and last'
    }
    
    def __init__(self, bytes_):
        BaseSegment.__init__(self, bytes_)
        self.id = int(self.data[0:2].hex(), base=16)
        self.version = self.data[2]
        self.in_sequence = self.SEQUENCE[self.data[3]]
        self.data_len = int(self.data[4:7].hex(), base=16)
        self.width = int(self.data[7:9].hex(), base=16)
        self.height = int(self.data[9:11].hex(), base=16)
        self.img_data = self.data[11:]
        if len(self.img_data) != self.data_len - 4:
            print('Warning: Image data length asserted does not match the '
                  'length found.')


class EndSegment(BaseSegment):
    pass


class DisplaySet:

    def __init__(self, segments):
        self.segments = segments
        self.segment_types = [s.type for s in segments]
        self.has_image = 'ODS' in self.segment_types


SEGMENT_TYPE = {
    PDS: PaletteDefinitionSegment,
    ODS: ObjectDefinitionSegment,
    PCS: PresentationCompositionSegment,
    WDS: WindowDefinitionSegment,
    END: EndSegment
}
        
def segment_by_type_getter(type_):
    def f(self):
        return [s for s in self.segments if s.type == type_]
    return f

for type_ in BaseSegment.SEGMENT.values():
    setattr(DisplaySet, type_.lower(), property(segment_by_type_getter(type_)))