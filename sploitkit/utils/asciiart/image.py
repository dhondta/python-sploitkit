# -*- coding: UTF-8 -*-
from collections import Counter
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from terminaltables.terminal_io import terminal_size as termsize


__all__ = ["AsciiImage"]

TERM_WIDTH = termsize()[0]


class AsciiImage(object):
    """ Image as an ASCII art.
    
    This converts an image (JPG, PNG, ... ; anything that can be opened with
     PIL) to an ASCII art using an input character set and the character density
     to match input image's brightness and contrast.
     
    This class is inspired from:
      https://github.com/ajalt/pyasciigen/blob/master/asciigen.py
    
    :param path:       path to the image
    :param width:      desired width in characters
    :param font:       name of a custom font
    :param brightness: image's brightness
    :param contrast:   image's contrast
    :param charset:    character set for the ASCII art
    """
    def __init__(self, path, width=TERM_WIDTH, font=None, brightness=None,
                 contrast=None, charset=".,*@%#/( "):
        # set the font and image first to reset every other parameter
        self.font = font
        self.image = str(path)
        # now set the parameters
        self.width = width
        self.contrast = contrast
        self.brightness = brightness
        self.charset = charset
    
    def __str__(self):
        """ Generate the ASCII image as a string """
        # as characters are not squares, take the character ratio into account
        w = int(self.__size[0] * self.__charsize[0])
        h = int(self.__size[1] * self.__charsize[0])
        # then resize the original image
        pixels = self.__img.resize((w, h), Image.ANTIALIAS).convert("L").load()
        # now build the output string
        s, l = "", len(self.__charset)
        for y in range(h):
            for x in range(w):
                s += self.__charset[int(pixels[x, y] / 255. * (l - 1) + 0.5)]
            s += "\n"
        # now remove every heading and trailing blank line
        lines = s.split("\n")
        while lines[0].strip() == "":
            lines.pop(0)
        while lines[-1].strip() == "":
            lines.pop()            
        return "\n".join(lines)
    
    @property
    def brightness(self):
        return self.__brightness
    
    @brightness.setter
    def brightness(self, brightness):
        # successive brightness changes are multiplicative
        self.__brightness *= brightness or 1
        if brightness is not None:
            self.__img = ImageEnhance.Brightness(self.__img).enhance(brightness)
    
    @property
    def charset(self):
        return self.__charset
    
    @charset.setter
    def charset(self, value):
        def __char_density(c):
            """ Get the number of pixels from a rendered character """
            i = Image.new("1", self.__font.getsize(c), color=255)
            ImageDraw.Draw(i).text((0, 0), c, font=self.__font)
            return Counter(i.getdata())[0]
        # sort the charset, taking character densities into account
        self.__charset = list(sorted(set(value), key=__char_density,
                                     reverse=True))
    
    @property
    def contrast(self):
        return self.__contrast
    
    @contrast.setter
    def contrast(self, contrast):
        # successive contrast changes are multiplicative
        self.__contrast *= contrast or 1
        if contrast is not None:
            self.__img = ImageEnhance.Contrast(self.__img).enhance(contrast)
    
    @property
    def font(self):
        return self.__font
    
    @font.setter
    def font(self, font):
        self.__font = ImageFont.load_default() if font is None else \
                      ImageFont.load(font)
        # get the size of a sample character
        self.__charsize = self.__font.getsize("X")
    
    @property
    def image(self):
        return self.__img
    
    @image.setter
    def image(self, path):
        # reset the image object and its related parameters
        self.__img = Image.open(str(path))
        self.__brightness = 1
        self.__contrast = 1
        self.__size = [self.__img.size[0] / self.__charsize[0],
                       self.__img.size[1] / self.__charsize[1]]
        self.__aspectratio = self.__size[0] / float(self.__size[1])
    
    @property
    def height(self):
        return self.__size[1]
    
    @height.setter
    def height(self, value):
        self.__size[1] = int(value or self.__size[1])
        # adapt the width with the original aspect ratio
        self.__size[0] = int(self.__size[1] * self.__aspectratio)
    
    @property
    def size(self):
        return self.__size
    
    @size.setter
    def size(self, size):
        self.__size = list(size)
    
    @property
    def text(self):
        return str(self)
    
    @property
    def width(self):
        return self.__size[0]
    
    @width.setter
    def width(self, value):
        self.__size[0] = int(value or self.__size[0])
        # adapt the height with the original aspect ratio
        self.__size[1] = int(self.__size[0] / self.__aspectratio)
