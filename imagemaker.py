# source: https://github.com/EzraBC/pgsreader

import numpy as np
from PIL import Image

class ImageMaker:

    def __init__(self, text_color=None):
        self.__text_color = text_color
        self.__sub_colors = {}

    def is_similar_color(self, color1, color2, color_diff:int =25):
        if color1 is None or color2 is None:
            return False
        
        return abs(color1[0] - color2[0]) < color_diff and abs(color1[1] - color2[1]) < color_diff and abs(color1[2] - color2[2]) < color_diff
    
    def get_similiarity(self, color1, color2):
        return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2]) / 3
    
    def reduce_sub_colors(self):
        temp_sub_colors = {}
        for color in self.__sub_colors.copy():

            if color not in self.__sub_colors:
                continue

            most_common_similiar_color = color
            most_common_similiar_color_count = self.__sub_colors[color]
            similar_colors = []
            similar_colors_count = 0

            for color2 in self.__sub_colors.copy():
                if self.is_similar_color(color, color2):
                    similar_colors.append(color2)
                    similar_colors_count += self.__sub_colors[color2]

                    if self.__sub_colors[color2] > most_common_similiar_color_count:
                        most_common_similiar_color = color2
                        most_common_similiar_color_count = self.__sub_colors[color2]

            for color2 in similar_colors:
                    self.__sub_colors.pop(color2)

            temp_sub_colors[most_common_similiar_color] = similar_colors_count

        self.__sub_colors = temp_sub_colors
        #TODO remove temp_sub_colors, only use self.__sub_colors

    def count_sub_colors(self, img: Image):
        self.__sub_colors = {}

        for x in range(img.width):
            for y in range(img.height):
                color = img.getpixel((x, y))
                self.__sub_colors[color] = self.__sub_colors.get(color, 0) + 1

    def find_text_color(self):
        grey = (160, 160, 160)
        similiarity = 256
        for color in self.__sub_colors:
            if self.get_similiarity(color, grey) < similiarity:
                similiarity = self.get_similiarity(color, grey)
                self.__text_color = color


    def read_rle_bytes(self, ods_bytes):

        pixels = []
        line_builder = []

        i = 0
        while i < len(ods_bytes):
            if ods_bytes[i]:
                incr = 1
                color = ods_bytes[i]
                length = 1
            else:
                check = ods_bytes[i+1]
                if check == 0:
                    incr = 2
                    color = 0
                    length = 0
                    pixels.append(line_builder)
                    line_builder = []
                elif check < 64:
                    incr = 2
                    color = 0
                    length = check
                elif check < 128:
                    incr = 3
                    color = 0
                    length = ((check - 64) << 8) + ods_bytes[i + 2]
                elif check < 192:
                    incr = 3
                    color = ods_bytes[i+2]
                    length = check - 128
                else:
                    incr = 4
                    color = ods_bytes[i+3]
                    length = ((check - 192) << 8) + ods_bytes[i + 2]
            line_builder.extend([color]*length)
            i += incr

        if line_builder:
            raise Exception("RLE data ended before end of line was reached")

        return pixels
                            
    def ycbcr2rgb(self, ar):
        xform = np.array([[1, 0, 1.402], [1, -0.34414, -.71414], [1, 1.772, 0]]).T
        rgb = ar.astype(np.single)
        # Subtracting 128 from R & G channels
        rgb[:,[1,2]] -= 128
        rgb = rgb.dot(xform)
        np.clip(rgb, 0, 255, out=rgb)
        return np.uint8(rgb)

    def px_rgb_a(self, ods, pds, swap):
        px = self.read_rle_bytes(ods.img_data)
        px = np.array([[255]*(ods.width - len(l)) + l for l in px], dtype=np.uint8)
        
        # Extract the YCbCrA palette data, swapping channels if requested.
        if swap:
            ycbcr = np.array([(entry.Y, entry.Cb, entry.Cr) for entry in pds.palette])
        else:
            ycbcr = np.array([(entry.Y, entry.Cr, entry.Cb) for entry in pds.palette])
        
        rgb = self.ycbcr2rgb(ycbcr)
        
        # Separate the Alpha channel from the YCbCr palette data
        a = [entry.Alpha for entry in pds.palette]
        a = np.array([[a[x] for x in l] for l in px], dtype=np.uint8)

        return px, rgb, a

    def make_image(self, ods, pds, swap=False):
        px, rgb, a = self.px_rgb_a(ods, pds, swap)
        alpha = Image.fromarray(a, mode='L')
        img = Image.fromarray(px, mode='P')
        img.putpalette(rgb)
        img.putalpha(alpha)
        img = img.convert("RGB")

        img.save("current.png")

        if self.__text_color is None:
            self.count_sub_colors(img)
            self.reduce_sub_colors()
            self.find_text_color()

        pixels = img.getdata()
        new_data = []
        for pixel in pixels:
            if self.is_similar_color(pixel, self.__text_color):
                new_data.append((0, 0, 0))
            else:
                new_data.append((255, 255, 255))

        img.putdata(new_data)

        scale = 1
        padding = 25
        
        img = img.resize((img.width*scale, img.height*scale), Image.NEAREST)

        # add padding to image so text is not at the edge to improve OCR
        width, height = img.size
        new_width = width + 2*padding
        new_height = height + 2*padding

        new_img = Image.new(img.mode, (new_width, new_height), (255, 255, 255))
        new_img.paste(img, (padding, padding))
        img = new_img

        return img
