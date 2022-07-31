from programy.clients.embed.datafile import EmbeddedDataFileBot

files = {'aiml': ['robud_chatbot/bot/storage/categories'],
         'learnf': ['robud_chatbot/bot/storage/learnf'],
         'properties': 'robud_chatbot/bot/storage/properties/properties.txt',
         'defaults': 'robud_chatbot/bot/storage/properties/defaults.txt',
         'sets': ['robud_chatbot/bot/storage/sets'],
         'maps': ['robud_chatbot/bot/storage/maps'],
         'rdfs': ['robud_chatbot/bot/storage/rdfs'],
         'denormals': 'robud_chatbot/bot/storage/lookups/denormal.txt',
         'normals': 'robud_chatbot/bot/storage/lookups/normal.txt',
         'genders': 'robud_chatbot/bot/storage/lookups/gender.txt',
         'persons': 'robud_chatbot/bot/storage/lookups/person.txt',
         'person2s': 'robud_chatbot/bot/storage/lookups/person2.txt',
         'regexes': 'robud_chatbot/bot/storage/regex/regex-templates.txt',
         'spellings': 'robud_chatbot/bot/storage/spelling/corpus.txt',
         'preprocessors': 'robud_chatbot/bot/storage/processing/preprocessors.conf',
         'postprocessors': 'robud_chatbot/bot/storage/processing/postprocessors.conf',
         'postquestionprocessors': 'robud_chatbot/bot/storage/processing/postquestionprocessors.conf'
         }

my_bot = EmbeddedDataFileBot(files)

print("Response = %s" % my_bot.ask_question("Hello"))