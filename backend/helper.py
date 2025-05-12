from config import Config

def convert_language(lang: str) -> str:
    '''
    Convert the language code from ISO 639-2/B to ISO 639-2/T
    which is used for OCR
    '''
    alt_lang_codes = {'alb': 'sqi',
                        'arm': 'hye',
                        'baq': 'eus',
                        'bur': 'mya',
                        'chi': 'zho',
                        'cze': 'ces',
                        'dut': 'nld',
                        'fre': 'fra',
                        'geo': 'kat',
                        'ger': 'deu',
                        'gre': 'ell',
                        'ice': 'isl',
                        'mac': 'mkd',
                        'may': 'msa',
                        'mao': 'mri',
                        'per': 'fas',
                        'rum': 'ron',
                        'slo': 'slk',
                        'tib': 'bod',
                        'wel': 'cym'}

    return alt_lang_codes.get(lang, lang)

def diff_langs_from_text(text: str) -> dict[str, str]:
    config = Config()
    if text == "":
        return {}
    
    lines = text.splitlines()
    diff_langs = {}
    for line in lines:
        if line.strip() == "":
            continue

        if "->" not in line or line.count("->") > 1:
            config.logger.error(f"Invalid input: {line}.")
            continue

        old_lang, new_lang = line.split("->")
        old_lang = old_lang.strip()
        new_lang = new_lang.strip()
        
        if old_lang != convert_language(old_lang):
            config.logger.info(f'Changed "{old_lang}" to "{convert_language(old_lang)}".')
            old_lang = convert_language(old_lang)

        if new_lang != convert_language(new_lang):
            config.logger.info(f'Changed "{new_lang}" to "{convert_language(new_lang)}".')
            new_lang = convert_language(new_lang)

        diff_langs[old_lang] = new_lang

    return diff_langs
