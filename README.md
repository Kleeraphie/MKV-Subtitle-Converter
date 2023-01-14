# MKV-Subtitle-Changer

By running the run.bat file in a directory with .mkv files in it, the program will extract all PGS subtitles (i.e .sup files), convert them to text based subtitles (in this case .srt files) using OCR and replace the old PGS subtitles with the newly created .srt-files in the given .mkv file.

## Requirements
The program was tested on Python 3.10 and needs the following python modules to work properly:
- [pymkv](https://github.com/sheldonkwoodward/pymkv)
- [pytesseract](https://github.com/madmaze/pytesseract)
- [tqdm](https://github.com/tqdm/tqdm)
- [pysrt](https://github.com/byroot/pysrt)
- [NumPy](https://numpy.org/)
- [Pillow](https://github.com/python-pillow/Pillow)

## Usage
Place the files from this repository in the folder with the .mkv files you want to change the subtitles from. Then simply run the run.bat file. Firstly, you will be asked if you want to edit the converted subtitles before the program replaces the subtitles. The program then extracts the subtitles of one file after another, converts them, and replaces them.

## Tips
For better OCR results you should download the language models for the languages of the subtitles. But if an english subtitles uses letters like ä, ö or ü, using the german language model instead of the english model because the german model contains all letters that the english one has, plus these special letters.
