# MKV-Subtitle-Changer

This program extracts all PGS subtitles (i.e .sup files) in a MKV file, converts them to text based subtitles (in this case .srt files) using OCR and replace the old PGS subtitles with the newly created .srt-files.

## Requirements
- [pymkv](https://github.com/sheldonkwoodward/pymkv)
- [pytesseract](https://github.com/madmaze/pytesseract)
- [tqdm](https://github.com/tqdm/tqdm)
- [pysrt](https://github.com/byroot/pysrt)
- [NumPy](https://numpy.org/)
- [Pillow](https://github.com/python-pillow/Pillow)
- [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI#jump-start-get-the-demo-programs--demo-browser-)
- [MKVToolNix](https://mkvtoolnix.download/).


## Usage
Download the files from this repository and place them in a folder. Then simply run the gui.py file. Via the "Browse" button in the top you can go to a directory. Simply select the MKV files you want to use.

## Tips
- For better OCR results you should download the language models for the languages of the subtitles. You can download them [here](https://tesseract-ocr.github.io/tessdoc/Data-Files.html). Simply put them in the `tessdata` folder.
- If a subtitle uses letters of a different language, e.g., an english subtitles uses letters like ä, ö or ü, using the german language model instead of the english model because the german model contains all letters that the english one has, plus these special letters. This can be done by entering the language codes like this after ticking the third checkbox: `old -> new`. In this example it would be `eng -> ger`
- You can select MKV files from different directories, just select the MKV files you want to use and browse to another directory to select the next files.
