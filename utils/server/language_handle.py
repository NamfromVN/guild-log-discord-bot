import os, json
import logging

logger = logging.getLogger(__name__)
class LocalizationManager():
    def __init__(self, locale_dir='language'):
        self.locale_dir = locale_dir
        self.localizations = {}
        

    def load_localizations(self, silent: bool = False):
        """Tải các dữ liệu bản dịch vào RAM"""
        for root, dirs, files in os.walk(self.locale_dir):
           
            if root == self.locale_dir:
                continue

            language_code = os.path.basename(root)
            self.localizations[language_code] = {}

            for filename in files:
                if filename.endswith('.json'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'r', encoding='utf-8') as file:
                        category = filename[:-5]
                        self.localizations[language_code][category] = json.load(file)
                        if not silent:
                            logger.info(f"Loaded file {filename} for {language_code} language")
                           

    def get(self, locale: str, categoryKey: str, key: str) -> str:
        """Lấy dữ liệu dịch

        USAGE: get(language, categoryKey, 'some_key')
        """
        return self.localizations.get(locale, {}).get(categoryKey, {}).get(key, key)