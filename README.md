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
- For better OCR results you should download the language models for the languages of the subtitles. You can download them [here](https://tesseract-ocr.github.io/tessdoc/Data-Files.html).
- If a subtitle uses letters of a different language, e.g., an english subtitles uses letters like ä, ö or ü, using the german language model instead of the english model because the german model contains all letters that the english one has, plus these special letters. This can be done by entering the language codes at the third question like this: `old->new`, so that your console looks like this:
 ```
 [...]
 Do you want to use a different language for some subtitles?
 1) Yes
 2) No (Default)
 Your Input: 1
 Enter your changes like this: ger->eng :
 Your Input: eng->ger
 Added language change.
 Enter your changes like this: ger->eng :
 Your Input:
 Starting conversion...
 [...]
 ```
