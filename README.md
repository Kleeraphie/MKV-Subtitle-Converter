# MKV-Subtitle-Changer

This program extracts all PGS subtitles (i.e .sup files) in a MKV file, converts them to text based subtitles (in this case .srt files) using OCR and replace the old PGS subtitles with the newly created .srt-files.

## Requirements
- The program needs [Tesseract](https://github.com/tesseract-ocr/tesseract) to be installed to use OCR. If you use Windows, you also need to put the `tessdata` folder in your PATH.
- To extract and replace the subtitles the program also needs [MKVToolNix](https://mkvtoolnix.download/). 

## Usage
Download the files from this repository and place them in a folder. Then simply run the run.bat file. Via the "Browse" button in the top you can go to a directory. Simply select the MKV files you want to use.

## Tips
- For better OCR results you should download the language models for the languages of the subtitles. You can download them [here](https://tesseract-ocr.github.io/tessdoc/Data-Files.html). Simply put them in the `tessdata` folder.
- If a subtitle uses letters of a different language, e.g., an english subtitles uses letters like ä, ö or ü, using the german language model instead of the english model because the german model contains all letters that the english one has, plus these special letters. This can be done by entering the language codes like this after ticking the third checkbox: `old -> new`. In this example it would be `eng -> ger`
- You can select MKV files from different directories, just select the MKV files you want to use and browse to another directory to select the next files.
