import logging

def check_srt(srt_file: str, silent: bool = False):
    with open(srt_file, 'r', encoding="utf8") as f:
        lines = f.readlines()

    replaced_i = 0

    for index in range(len(lines) - 1):
        if lines[index] == "\n" and lines[index + 1] == "\n":
            if not silent:
                logging.warning(f"Two empty lines at line {index + 1} in {srt_file} probably because OCR failed to recognize the text.")
        elif lines[index] == "\n" and lines[index + 2][:-1].isnumeric():
            if not silent:
                logging.warning(f"No text for subtitle #{int(lines[index + 1]) - 1} at line {index + 1} in {srt_file}.")
        elif '|' in lines[index]:
            # print(f"Replaced '|' with 'I' {lines[index].count('|')} times in line {index + 1}")
            replaced_i += lines[index].count('|')
            lines[index] = lines[index].replace('|', 'I')
            
    with open(srt_file, 'w', encoding="utf8") as f:
        f.writelines(lines)

    if not silent:
        logging.info(f"Replaced '|' with 'I' {replaced_i} times in {srt_file}.")