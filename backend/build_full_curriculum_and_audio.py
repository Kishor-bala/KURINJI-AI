import json
import sqlite3
import os
from pathlib import Path
import io
from gtts import gTTS
import soundfile as sf
import numpy as np

# 1. Generate missing audio for tree, flower, leaf, book
extra_audio_words = [
    ("BDG_W2788", "BDG_P20_W2788_S01", "mara", "ta"),
    ("BDG_W3538", "BDG_P20_W3538_S01", "hoovu", "kn"),
    ("BDG_W3157", "BDG_P20_W3157_S01", "ele", "ta"),
    ("BDG_W3901", "BDG_P20_W3901_S01", "pusthaka", "kn"),
]

pack_dir = Path("dataset/Badaga_Core_Pack")
pack_dir.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect("backend/data/vocabulary.db")
c = conn.cursor()

for wid, clip_id, word_text, lang in extra_audio_words:
    out_wav = pack_dir / f"{clip_id}.wav"
    if not out_wav.is_file():
        # Synthesize via gTTS
        tts = gTTS(text=word_text, lang=lang, slow=True)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # Read with soundfile and resample/convert to 16kHz mono WAV
        data, sr = sf.read(mp3_fp)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        # Resample to 16000 if needed
        if sr != 16000:
            import scipy.signal
            num_samples = int(len(data) * 16000 / sr)
            data = scipy.signal.resample(data, num_samples)
        
        sf.write(str(out_wav), data.astype(np.float32), 16000, subtype='PCM_16')
        print(f"Created WAV: {out_wav} (16kHz Mono)")

    # Register in recordings table if not already present
    existing = c.execute("SELECT clip_id FROM recordings WHERE clip_id = ?", (clip_id,)).fetchone()
    if not existing:
        c.execute("""
            INSERT INTO recordings (clip_id, word_id, speaker_id, original_file, clip_file, start_timestamp, end_timestamp, sample_rate, duration, review_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (clip_id, wid, "P20", str(out_wav), str(out_wav.resolve()), 0.0, 1.2, 16000, 1.2, "reviewed"))
        print(f"Registered recording: {clip_id} for {wid}")

conn.commit()

# 2. Build complete learning_modules.json
curriculum = {
    "modules": [
        {
            "id": "body",
            "title": "My Body",
            "tamil_title": "என் உடல்",
            "concept_count": 8,
            "color": "#0284c7",
            "light_color": "#f0f9ff"
        },
        {
            "id": "family",
            "title": "Family & Home",
            "tamil_title": "குடும்பம் & வீடு",
            "concept_count": 6,
            "color": "#4f46e5",
            "light_color": "#eef2ff"
        },
        {
            "id": "nature",
            "title": "Nature & Sky",
            "tamil_title": "இயற்கை & வானம்",
            "concept_count": 8,
            "color": "#16a34a",
            "light_color": "#f0fdf4"
        },
        {
            "id": "numbers",
            "title": "Numbers",
            "tamil_title": "எண்கள் (1 - 5)",
            "concept_count": 5,
            "color": "#d97706",
            "light_color": "#fffbeb"
        },
        {
            "id": "school",
            "title": "School & Actions",
            "tamil_title": "பள்ளி & செயல்கள்",
            "concept_count": 5,
            "color": "#7c3aed",
            "light_color": "#f5f3ff"
        }
    ],
    "cards": [
        # Body
        {
            "id": "body_head",
            "category": "body",
            "word_id": "BDG_W0001",
            "illustration_name": "head",
            "badaga": {"word": "mande", "tamil_script": "மந்தே", "pronunciation": "man-de"},
            "marwari": {"word": "matho", "tamil_script": "மாதோ", "pronunciation": "maa-tho"},
            "tamil": {
                "word": "தலை",
                "phonics": "த + லை",
                "letters": ["த", "லை"],
                "example": "தலை நமது உடலின் முக்கிய உறுப்பு."
            },
            "english": {
                "word": "Head",
                "phonics": "H - E - A - D",
                "letters": ["H", "E", "A", "D"],
                "example": "Nod your head to say yes."
            }
        },
        {
            "id": "body_eye",
            "category": "body",
            "word_id": "BDG_W0002",
            "illustration_name": "eye",
            "badaga": {"word": "kannu", "tamil_script": "கண்ணு", "pronunciation": "kan-nu"},
            "marwari": {"word": "aankh", "tamil_script": "ஆன்க்", "pronunciation": "aan-kh"},
            "tamil": {
                "word": "கண்",
                "phonics": "க + ண்",
                "letters": ["க", "ண்"],
                "example": "கண்கள் உலகைக் காண உதவுகின்றன."
            },
            "english": {
                "word": "Eye",
                "phonics": "E - Y - E",
                "letters": ["E", "Y", "E"],
                "example": "I see the blue sky with my eyes."
            }
        },
        {
            "id": "body_nose",
            "category": "body",
            "word_id": "BDG_W0003",
            "illustration_name": "nose",
            "badaga": {"word": "moogu", "tamil_script": "மூகு", "pronunciation": "moo-gu"},
            "marwari": {"word": "naak", "tamil_script": "நாக்", "pronunciation": "naak"},
            "tamil": {
                "word": "மூக்கு",
                "phonics": "மூ + க் + கு",
                "letters": ["மூ", "க்", "கு"],
                "example": "மூக்கினால் மலரின் நறுமணத்தை நுகர்கிறோம்."
            },
            "english": {
                "word": "Nose",
                "phonics": "N - O - S - E",
                "letters": ["N", "O", "S", "E"],
                "example": "We smell flowers with our nose."
            }
        },
        {
            "id": "body_mouth",
            "category": "body",
            "word_id": "BDG_W0004",
            "illustration_name": "mouth",
            "badaga": {"word": "baayi", "tamil_script": "பாயி", "pronunciation": "baa-yi"},
            "marwari": {"word": "mukh", "tamil_script": "முக்", "pronunciation": "mukh"},
            "tamil": {
                "word": "வாய்",
                "phonics": "வா + ய்",
                "letters": ["வா", "ய்"],
                "example": "வாயினால் உணவு உண்டு பேசுகிறோம்."
            },
            "english": {
                "word": "Mouth",
                "phonics": "M - O - U - T - H",
                "letters": ["M", "O", "U", "T", "H"],
                "example": "Open your mouth and smile."
            }
        },
        {
            "id": "body_ear",
            "category": "body",
            "word_id": "BDG_W0005",
            "illustration_name": "ear",
            "badaga": {"word": "kaadu", "tamil_script": "காது", "pronunciation": "kaa-du"},
            "marwari": {"word": "kaan", "tamil_script": "கான்", "pronunciation": "kaan"},
            "tamil": {
                "word": "காது",
                "phonics": "கா + து",
                "letters": ["கா", "து"],
                "example": "காதினால் இனிய பாடல்களைக் கேட்கிறோம்."
            },
            "english": {
                "word": "Ear",
                "phonics": "E - A - R",
                "letters": ["E", "A", "R"],
                "example": "We hear birds singing with our ears."
            }
        },
        {
            "id": "body_hand",
            "category": "body",
            "word_id": "BDG_W0006",
            "illustration_name": "hand",
            "badaga": {"word": "kai", "tamil_script": "கை", "pronunciation": "kai"},
            "marwari": {"word": "haath", "tamil_script": "ஹாத்", "pronunciation": "haath"},
            "tamil": {
                "word": "கை",
                "phonics": "கை",
                "letters": ["கை"],
                "example": "கைகளால் கைதட்டி மகிழ்கிறோம்."
            },
            "english": {
                "word": "Hand",
                "phonics": "H - A - N - D",
                "letters": ["H", "A", "N", "D"],
                "example": "Clap your hands together."
            }
        },
        {
            "id": "body_leg",
            "category": "body",
            "word_id": "BDG_W0007",
            "illustration_name": "leg",
            "badaga": {"word": "kaalu", "tamil_script": "காலு", "pronunciation": "kaa-lu"},
            "marwari": {"word": "pag", "tamil_script": "பக்", "pronunciation": "pag"},
            "tamil": {
                "word": "கால்",
                "phonics": "கா + ல்",
                "letters": ["கா", "ல்"],
                "example": "கால்களால் ஓடி விளையாடுகிறோம்."
            },
            "english": {
                "word": "Leg",
                "phonics": "L - E - G",
                "letters": ["L", "E", "G"],
                "example": "We walk and run with our legs."
            }
        },
        {
            "id": "body_teeth",
            "category": "body",
            "word_id": "BDG_W0008",
            "illustration_name": "teeth",
            "badaga": {"word": "pal", "tamil_script": "பல்", "pronunciation": "pal"},
            "marwari": {"word": "daant", "tamil_script": "தாந்த்", "pronunciation": "daant"},
            "tamil": {
                "word": "பல்",
                "phonics": "ப + ல்",
                "letters": ["ப", "ல்"],
                "example": "பற்கள் உணவை மெல்ல உதவுகின்றன."
            },
            "english": {
                "word": "Teeth",
                "phonics": "T - E - E - T - H",
                "letters": ["T", "E", "E", "T", "H"],
                "example": "Brush your teeth every morning."
            }
        },

        # Family & Home
        {
            "id": "family_mother",
            "category": "family",
            "word_id": "BDG_W0051",
            "illustration_name": "mother",
            "badaga": {"word": "avve", "tamil_script": "அவ்வே", "pronunciation": "av-ve"},
            "marwari": {"word": "maa", "tamil_script": "மா", "pronunciation": "maa"},
            "tamil": {
                "word": "அம்மா",
                "phonics": "அ + ம் + மா",
                "letters": ["அ", "ம்", "மா"],
                "example": "அம்மா என் மீது மிகுந்த அன்பு காட்டுகிறார்."
            },
            "english": {
                "word": "Mother",
                "phonics": "M - O - T - H - E - R",
                "letters": ["M", "O", "T", "H", "E", "R"],
                "example": "Mother gives us delicious food and care."
            }
        },
        {
            "id": "family_father",
            "category": "family",
            "word_id": "BDG_W0052",
            "illustration_name": "father",
            "badaga": {"word": "appa", "tamil_script": "அப்பா", "pronunciation": "ap-pa"},
            "marwari": {"word": "pitaji", "tamil_script": "பிதாஜி", "pronunciation": "pi-taa-ji"},
            "tamil": {
                "word": "அப்பா",
                "phonics": "அ + ப் + பா",
                "letters": ["அ", "ப்", "பா"],
                "example": "அப்பா எனக்கு நல்ல கதைகள் சொல்வார்."
            },
            "english": {
                "word": "Father",
                "phonics": "F - A - T - H - E - R",
                "letters": ["F", "A", "T", "H", "E", "R"],
                "example": "Father helps me with my homework."
            }
        },
        {
            "id": "family_child",
            "category": "family",
            "word_id": "BDG_W0060",
            "illustration_name": "child",
            "badaga": {"word": "koosu", "tamil_script": "கூசு", "pronunciation": "koo-su"},
            "marwari": {"word": "taabar", "tamil_script": "தாபர்", "pronunciation": "taa-bar"},
            "tamil": {
                "word": "குழந்தை",
                "phonics": "கு + ழ + ந் + தை",
                "letters": ["கு", "ழ", "ந்", "தை"],
                "example": "குழந்தை சிரித்துக் கொண்டே விளையாடுகிறது."
            },
            "english": {
                "word": "Child",
                "phonics": "C - H - I - L - D",
                "letters": ["C", "H", "I", "L", "D"],
                "example": "The happy child plays with toys."
            }
        },
        {
            "id": "family_house",
            "category": "family",
            "word_id": "BDG_W0101",
            "illustration_name": "house",
            "badaga": {"word": "mane", "tamil_script": "மனே", "pronunciation": "ma-ne"},
            "marwari": {"word": "ghar", "tamil_script": "கர்", "pronunciation": "ghar"},
            "tamil": {
                "word": "வீடு",
                "phonics": "வீ + டு",
                "letters": ["வீ", "டு"],
                "example": "நமது வீடு நமக்கு பாதுகாப்பான இடம்."
            },
            "english": {
                "word": "House",
                "phonics": "H - O - U - S - E",
                "letters": ["H", "O", "U", "S", "E"],
                "example": "We live peacefully with family in our house."
            }
        },
        {
            "id": "family_door",
            "category": "family",
            "word_id": "BDG_W0102",
            "illustration_name": "door",
            "badaga": {"word": "adi", "tamil_script": "அடி", "pronunciation": "a-di"},
            "marwari": {"word": "kiwaad", "tamil_script": "கிவாட்", "pronunciation": "ki-waad"},
            "tamil": {
                "word": "கதவு",
                "phonics": "க + த + வு",
                "letters": ["க", "த", "வு"],
                "example": "வீட்டின் கதவை மெதுவாகத் திறக்கவும்."
            },
            "english": {
                "word": "Door",
                "phonics": "D - O - O - R",
                "letters": ["D", "O", "O", "R"],
                "example": "Please close the front door gently."
            }
        },
        {
            "id": "family_window",
            "category": "family",
            "word_id": "BDG_W0103",
            "illustration_name": "window",
            "badaga": {"word": "jannalu", "tamil_script": "ஜன்னலு", "pronunciation": "jan-na-lu"},
            "marwari": {"word": "baari", "tamil_script": "பாரி", "pronunciation": "baa-ri"},
            "tamil": {
                "word": "சன்னல்",
                "phonics": "ச + ன் + ன + ல்",
                "letters": ["ச", "ன்", "ன", "ல்"],
                "example": "சன்னல் வழியாகக் குளிர்ந்த காற்று வருகிறது."
            },
            "english": {
                "word": "Window",
                "phonics": "W - I - N - D - O - W",
                "letters": ["W", "I", "N", "D", "O", "W"],
                "example": "Sunlight enters the room through the window."
            }
        },

        # Nature & Sky
        {
            "id": "nature_rain",
            "category": "nature",
            "word_id": "BDG_W0811",
            "illustration_name": "rain",
            "badaga": {"word": "male", "tamil_script": "மலே", "pronunciation": "ma-le"},
            "marwari": {"word": "meenh", "tamil_script": "மீன்", "pronunciation": "meenh"},
            "tamil": {
                "word": "மழை",
                "phonics": "ம + ழை",
                "letters": ["ம", "ழை"],
                "example": "மழை பெய்தால் தாவரங்கள் செழித்து வளரும்."
            },
            "english": {
                "word": "Rain",
                "phonics": "R - A - I - N",
                "letters": ["R", "A", "I", "N"],
                "example": "Raindrops fall gently from grey clouds."
            }
        },
        {
            "id": "nature_thunder",
            "category": "nature",
            "word_id": "BDG_W0816",
            "illustration_name": "thunder",
            "badaga": {"word": "idi", "tamil_script": "இடி", "pronunciation": "i-di"},
            "marwari": {"word": "gaaj", "tamil_script": "காஜ்", "pronunciation": "gaaj"},
            "tamil": {
                "word": "இடி",
                "phonics": "இ + டி",
                "letters": ["இ", "டி"],
                "example": "வானில் இடி முழங்கி பலத்த மழை பொழிந்தது."
            },
            "english": {
                "word": "Thunder",
                "phonics": "T - H - U - N - D - E - R",
                "letters": ["T", "H", "U", "N", "D", "E", "R"],
                "example": "We heard a loud boom of thunder."
            }
        },
        {
            "id": "nature_rainbow",
            "category": "nature",
            "word_id": "BDG_W0818",
            "illustration_name": "rainbow",
            "badaga": {"word": "baana billu", "tamil_script": "பான பில்லு", "pronunciation": "baa-na bil-lu"},
            "marwari": {"word": "surangil", "tamil_script": "சுரங்கில்", "pronunciation": "su-ran-gil"},
            "tamil": {
                "word": "வானவில்",
                "phonics": "வா + ன + வி + ல்",
                "letters": ["வா", "ன", "வி", "ல்"],
                "example": "மழைக்குப் பின் வானில் ஏழு வண்ண வானவில் தோன்றியது."
            },
            "english": {
                "word": "Rainbow",
                "phonics": "R - A - I - N - B - O - W",
                "letters": ["R", "A", "I", "N", "B", "O", "W"],
                "example": "A colorful rainbow spans across the sky."
            }
        },
        {
            "id": "nature_sun",
            "category": "nature",
            "word_id": "BDG_W0801",
            "illustration_name": "sun",
            "badaga": {"word": "agalu", "tamil_script": "அகலு", "pronunciation": "a-ga-lu"},
            "marwari": {"word": "suraj", "tamil_script": "சூரஜ்", "pronunciation": "soo-raj"},
            "tamil": {
                "word": "சூரியன்",
                "phonics": "சூ + ரி + ய + ன்",
                "letters": ["சூ", "ரி", "ய", "ன்"],
                "example": "சூரியன் காலையில் கிழக்கு திசையில் உதிக்கிறது."
            },
            "english": {
                "word": "Sun",
                "phonics": "S - U - N",
                "letters": ["S", "U", "N"],
                "example": "The bright sun gives light and warmth."
            }
        },
        {
            "id": "nature_night",
            "category": "nature",
            "word_id": "BDG_W0802",
            "illustration_name": "night",
            "badaga": {"word": "kattale", "tamil_script": "கத்தலே", "pronunciation": "kat-ta-le"},
            "marwari": {"word": "raat", "tamil_script": "ராத்", "pronunciation": "raat"},
            "tamil": {
                "word": "இரவு",
                "phonics": "இ + ர + வு",
                "letters": ["இ", "ர", "வு"],
                "example": "இரவில் வானில் நிலவும் விண்மீன்களும் ஒளிர்கின்றன."
            },
            "english": {
                "word": "Night",
                "phonics": "N - I - G - H - T",
                "letters": ["N", "I", "G", "H", "T"],
                "example": "Stars shine brightly during the calm night."
            }
        },
        {
            "id": "nature_tree",
            "category": "nature",
            "word_id": "BDG_W2788",
            "illustration_name": "tree",
            "badaga": {"word": "maraa", "tamil_script": "மரா", "pronunciation": "ma-raa"},
            "marwari": {"word": "jhaad", "tamil_script": "ஜாட்", "pronunciation": "jhaa-d"},
            "tamil": {
                "word": "மரம்",
                "phonics": "ம + ர + ம்",
                "letters": ["ம", "ர", "ம்"],
                "example": "மரங்கள் நமக்கு குளிர்ந்த நிழல் தருகின்றன."
            },
            "english": {
                "word": "Tree",
                "phonics": "T - R - E - E",
                "letters": ["T", "R", "E", "E"],
                "example": "Big green trees provide fresh air."
            }
        },
        {
            "id": "nature_flower",
            "category": "nature",
            "word_id": "BDG_W3538",
            "illustration_name": "flower",
            "badaga": {"word": "hoovu", "tamil_script": "ஹூவு", "pronunciation": "hoo-vu"},
            "marwari": {"word": "phool", "tamil_script": "பூல்", "pronunciation": "phool"},
            "tamil": {
                "word": "பூ",
                "phonics": "பூ",
                "letters": ["பூ"],
                "example": "பூக்கள் வண்ணமயமாக மலர்ந்து அழகு தருகின்றன."
            },
            "english": {
                "word": "Flower",
                "phonics": "F - L - O - W - E - R",
                "letters": ["F", "L", "O", "W", "E", "R"],
                "example": "Flowers bloom sweetly in the garden."
            }
        },
        {
            "id": "nature_leaf",
            "category": "nature",
            "word_id": "BDG_W3157",
            "illustration_name": "leaf",
            "badaga": {"word": "ele", "tamil_script": "எலே", "pronunciation": "e-le"},
            "marwari": {"word": "paat", "tamil_script": "பாத்", "pronunciation": "paat"},
            "tamil": {
                "word": "இலை",
                "phonics": "இ + லை",
                "letters": ["இ", "லை"],
                "example": "மரத்தின் பச்சை இலைகள் காற்றில் அசைகின்றன."
            },
            "english": {
                "word": "Leaf",
                "phonics": "L - E - A - F",
                "letters": ["L", "E", "A", "F"],
                "example": "Green leaves make food for the plant."
            }
        },

        # Numbers
        {
            "id": "num_one",
            "category": "numbers",
            "word_id": "BDG_W0701",
            "illustration_name": "one",
            "badaga": {"word": "ondu", "tamil_script": "ஒந்து", "pronunciation": "on-du"},
            "marwari": {"word": "ek", "tamil_script": "ஏக்", "pronunciation": "ek"},
            "tamil": {
                "word": "ஒன்று",
                "phonics": "ஒ + ன் + று",
                "letters": ["ஒ", "ன்", "று"],
                "example": "எனக்கு ஒரு அழகான புத்தகம் உள்ளது."
            },
            "english": {
                "word": "One",
                "phonics": "O - N - E",
                "letters": ["O", "N", "E"],
                "example": "Number one is the beginning of counting."
            }
        },
        {
            "id": "num_two",
            "category": "numbers",
            "word_id": "BDG_W0702",
            "illustration_name": "two",
            "badaga": {"word": "eradu", "tamil_script": "எரடு", "pronunciation": "e-ra-du"},
            "marwari": {"word": "do", "tamil_script": "தோ", "pronunciation": "do"},
            "tamil": {
                "word": "இரண்டு",
                "phonics": "இ + ர + ண் + டு",
                "letters": ["இ", "ர", "ண்", "டு"],
                "example": "நமக்கு இரண்டு கண்கள் உள்ளன."
            },
            "english": {
                "word": "Two",
                "phonics": "T - W - O",
                "letters": ["T", "W", "O"],
                "example": "We have two eyes to see."
            }
        },
        {
            "id": "num_three",
            "category": "numbers",
            "word_id": "BDG_W0703",
            "illustration_name": "three",
            "badaga": {"word": "mooru", "tamil_script": "மூரு", "pronunciation": "moo-ru"},
            "marwari": {"word": "teen", "tamil_script": "தீன்", "pronunciation": "teen"},
            "tamil": {
                "word": "மூன்று",
                "phonics": "மூ + ன் + று",
                "letters": ["மூ", "ன்", "று"],
                "example": "முக்கோணத்திற்கு மூன்று பக்கங்கள் இருக்கும்."
            },
            "english": {
                "word": "Three",
                "phonics": "T - H - R - E - E",
                "letters": ["T", "H", "R", "E", "E"],
                "example": "A triangle has three corners."
            }
        },
        {
            "id": "num_four",
            "category": "numbers",
            "word_id": "BDG_W0704",
            "illustration_name": "four",
            "badaga": {"word": "naakku", "tamil_script": "நாக்கு", "pronunciation": "naak-ku"},
            "marwari": {"word": "chaar", "tamil_script": "சார்", "pronunciation": "chaar"},
            "tamil": {
                "word": "நான்கு",
                "phonics": "நா + ன் + கு",
                "letters": ["நா", "ன்", "கு"],
                "example": "நாற்காலிக்கு நான்கு கால்கள் உள்ளன."
            },
            "english": {
                "word": "Four",
                "phonics": "F - O - U - R",
                "letters": ["F", "O", "U", "R"],
                "example": "A table has four steady legs."
            }
        },
        {
            "id": "num_five",
            "category": "numbers",
            "word_id": "BDG_W0705",
            "illustration_name": "five",
            "badaga": {"word": "aidu", "tamil_script": "ஐது", "pronunciation": "ai-du"},
            "marwari": {"word": "paanch", "tamil_script": "பாஞ்ச்", "pronunciation": "paanch"},
            "tamil": {
                "word": "ஐந்து",
                "phonics": "ஐ + ந் + து",
                "letters": ["ஐ", "ந்", "து"],
                "example": "ஒரு கையில் ஐந்து விரல்கள் உள்ளன."
            },
            "english": {
                "word": "Five",
                "phonics": "F - I - V - E",
                "letters": ["F", "I", "V", "E"],
                "example": "We have five fingers on each hand."
            }
        },

        # School & Actions
        {
            "id": "school_teacher",
            "category": "school",
            "word_id": "BDG_W0083",
            "illustration_name": "teacher",
            "badaga": {"word": "bathiyaar", "tamil_script": "பதியார்", "pronunciation": "ba-thi-yaar"},
            "marwari": {"word": "guru", "tamil_script": "குரு", "pronunciation": "gu-ru"},
            "tamil": {
                "word": "ஆசிரியர்",
                "phonics": "ஆ + சி + ரி + ய + ர்",
                "letters": ["ஆ", "சி", "ரி", "ய", "ர்"],
                "example": "ஆசிரியர் நமக்கு நல்ல கல்வியை கற்பிக்கிறார்."
            },
            "english": {
                "word": "Teacher",
                "phonics": "T - E - A - C - H - E - R",
                "letters": ["T", "E", "A", "C", "H", "E", "R"],
                "example": "Our kind teacher guides us in classroom."
            }
        },
        {
            "id": "school_flag",
            "category": "school",
            "word_id": "BDG_W0843",
            "illustration_name": "flag",
            "badaga": {"word": "kodi", "tamil_script": "கொடி", "pronunciation": "ko-di"},
            "marwari": {"word": "dhwaja", "tamil_script": "த்வஜா", "pronunciation": "dhwa-ja"},
            "tamil": {
                "word": "கொடி",
                "phonics": "கொ + டி",
                "letters": ["கொ", "டி"],
                "example": "பள்ளியில் மூவர்ணக் கொடி பட்டொளி வீசிப் பறக்கிறது."
            },
            "english": {
                "word": "Flag",
                "phonics": "F - L - A - G",
                "letters": ["F", "L", "A", "G"],
                "example": "The school flag flutters high in the air."
            }
        },
        {
            "id": "school_book",
            "category": "school",
            "word_id": "BDG_W3901",
            "illustration_name": "book",
            "badaga": {"word": "pusthaka", "tamil_script": "புஸ்தக", "pronunciation": "pus-tha-ka"},
            "marwari": {"word": "pothi", "tamil_script": "போதி", "pronunciation": "po-thi"},
            "tamil": {
                "word": "புத்தகம்",
                "phonics": "பு + த் + த + க + ம்",
                "letters": ["பு", "த்", "த", "க", "ம்"],
                "example": "பாடப் புத்தகத்தைப் படித்து புதிய சொற்களைக் கற்போம்."
            },
            "english": {
                "word": "Book",
                "phonics": "B - O - O - K",
                "letters": ["B", "O", "O", "K"],
                "example": "Reading a story book is fun and exciting."
            }
        },
        {
            "id": "school_walk",
            "category": "school",
            "word_id": "BDG_W0858",
            "illustration_name": "walk",
            "badaga": {"word": "nada", "tamil_script": "நட", "pronunciation": "na-da"},
            "marwari": {"word": "chaalo", "tamil_script": "சாலோ", "pronunciation": "chaa-lo"},
            "tamil": {
                "word": "நட",
                "phonics": "ந + ட",
                "letters": ["ந", "ட"],
                "example": "காலையில் நடைப்பயிற்சி செய்வது உடலுக்கு நல்லது."
            },
            "english": {
                "word": "Walk",
                "phonics": "W - A - L - K",
                "letters": ["W", "A", "L", "K"],
                "example": "We walk safely together to school."
            }
        },
        {
            "id": "school_run",
            "category": "school",
            "word_id": "BDG_W0859",
            "illustration_name": "run",
            "badaga": {"word": "odu", "tamil_script": "ஓடு", "pronunciation": "o-du"},
            "marwari": {"word": "bhaago", "tamil_script": "பாகோ", "pronunciation": "bhaa-go"},
            "tamil": {
                "word": "ஓடு",
                "phonics": "ஓ + டு",
                "letters": ["ஓ", "டு"],
                "example": "விளையாட்டு மைதானத்தில் வேகமாக ஓடுவோம்."
            },
            "english": {
                "word": "Run",
                "phonics": "R - U - N",
                "letters": ["R", "U", "N"],
                "example": "Children love to run and play in the field."
            }
        }
    ]
}

# Write out learning_modules.json
modules_file = Path("backend/data/learning_modules.json")
with open(modules_file, "w", encoding="utf-8") as f:
    json.dump(curriculum, f, ensure_ascii=False, indent=2)

print(f"Successfully generated {modules_file} with {len(curriculum['modules'])} topics and {len(curriculum['cards'])} cards.")
conn.close()
