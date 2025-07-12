import fs from 'fs/promises';
import path from 'path';
import pofile from 'pofile';

const sourceDir = path.resolve(process.cwd(), '../../languages');
const outputDir = path.resolve(process.cwd(), 'public/locales');

async function convertPoToJson() {
  try {
    await fs.mkdir(outputDir, { recursive: true });
    const files = await fs.readdir(sourceDir);

    for (const file of files) {
      if (path.extname(file) === '.po') {
        const lang = path.basename(file, '.po');
        const poFilePath = path.join(sourceDir, file);
        const jsonFilePath = path.join(outputDir, `${lang}.json`);

        const content = await fs.readFile(poFilePath, 'utf8');
        const po = pofile.parse(content);

        if (po.items) {
          const translations = po.items.reduce((acc, item) => {
            if (item.msgid && item.msgstr[0]) {
              acc[item.msgid] = item.msgstr[0];
            }
            return acc;
          }, {});

          await fs.writeFile(jsonFilePath, JSON.stringify(translations, null, 2));
          console.log(`Successfully converted ${file} to ${lang}.json`);
        }
      }
    }
  } catch (error) {
    console.error('Error converting .po files to JSON:', error);
  }
}

convertPoToJson();