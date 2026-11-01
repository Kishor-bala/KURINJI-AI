import sqlite3
import json
from pathlib import Path

conn = sqlite3.connect('backend/data/vocabulary.db')
c = conn.cursor()

words_needed = [
    # Body
    ('body_head', 'body', 'head', 'BDG_W0001', 'mande', 'மந்தே', 'தலை', ['த', 'லை'], 'Head', ['H', 'E', 'A', 'D'], 'head'),
    ('body_eye', 'body', 'eye', 'BDG_W0002', 'kannu', 'கண்ணு', 'கண்', ['க', 'ண்'], 'Eye', ['E', 'Y', 'E'], 'eye'),
    ('body_nose', 'body', 'nose', 'BDG_W0003', 'moogu', 'மூகு', 'மூக்கு', ['மூ', 'க்', 'கு'], 'Nose', ['N', 'O', 'S', 'E'], 'nose'),
    ('body_mouth', 'body', 'mouth', 'BDG_W0004', 'baayi', 'பாயி', 'வாய்', ['வா', 'ய்'], 'Mouth', ['M', 'O', 'U', 'T', 'H'], 'mouth'),
    ('body_ear', 'body', 'ear', 'BDG_W0005', 'kaadu', 'காது', 'காது', ['கா', 'து'], 'Ear', ['E', 'A', 'R'], 'ear'),
    ('body_hand', 'body', 'hand', 'BDG_W0006', 'kai', 'கை', 'கை', ['கை'], 'Hand', ['H', 'A', 'N', 'D'], 'hand'),
    ('body_leg', 'body', 'leg', 'BDG_W0007', 'kaalu', 'காலு', 'கால்', ['கா', 'ல்'], 'Leg', ['L', 'E', 'G'], 'leg'),
    ('body_teeth', 'body', 'teeth', 'BDG_W0008', 'pal', 'பல்', 'பல்', ['ப', 'ல்'], 'Teeth', ['T', 'E', 'E', 'T', 'H'], 'teeth'),

    # Family & Home
    ('family_mother', 'family', 'mother', 'BDG_W0051', 'avve', 'அவ்வே', 'அம்மா', ['அ', 'ம்', 'மா'], 'Mother', ['M', 'O', 'T', 'H', 'E', 'R'], 'mother'),
    ('family_father', 'family', 'father', 'BDG_W0052', 'appa', 'அப்பா', 'அப்பா', ['அ', 'ப்', 'பா'], 'Father', ['F', 'A', 'T', 'H', 'E', 'R'], 'father'),
    ('family_child', 'family', 'child', 'BDG_W0060', 'koosu', 'கூசு', 'குழந்தை', ['கு', 'ழ', 'ந்', 'தை'], 'Child', ['C', 'H', 'I', 'L', 'D'], 'child'),
    ('family_house', 'family', 'house', 'BDG_W0101', 'mane', 'மனே', 'வீடு', ['வீ', 'டு'], 'House', ['H', 'O', 'U', 'S', 'E'], 'house'),
    ('family_door', 'family', 'door', 'BDG_W0102', 'adi', 'அடி', 'கதவு', ['க', 'த', 'வு'], 'Door', ['D', 'O', 'O', 'R'], 'door'),
    ('family_window', 'family', 'window', 'BDG_W0103', 'jannalu', 'ஜன்னலு', 'சன்னல்', ['ச', 'ன்', 'ன', 'ல்'], 'Window', ['W', 'I', 'N', 'D', 'O', 'W'], 'window'),

    # Nature & Sky
    ('nature_rain', 'nature', 'rain', 'BDG_W0811', 'male', 'மலே', 'மழை', ['ம', 'ழை'], 'Rain', ['R', 'A', 'I', 'N'], 'rain'),
    ('nature_thunder', 'nature', 'thunder', 'BDG_W0816', 'idi', 'இடி', 'இடி', ['இ', 'டி'], 'Thunder', ['T', 'H', 'U', 'N', 'D', 'E', 'R'], 'thunder'),
    ('nature_rainbow', 'nature', 'rainbow', 'BDG_W0818', 'baana billu', 'பான பில்லு', 'வானவில்', ['வா', 'ன', 'வி', 'ல்'], 'Rainbow', ['R', 'A', 'I', 'N', 'B', 'O', 'W'], 'rainbow'),
    ('nature_sun', 'nature', 'sun', 'BDG_W0801', 'agalu', 'அகலு', 'சூரியன்', ['சூ', 'ரி', 'ய', 'ன்'], 'Sun', ['S', 'U', 'N'], 'sun'),
    ('nature_night', 'nature', 'night', 'BDG_W0802', 'kattale', 'கத்தலே', 'இரவு', ['இ', 'ர', 'வு'], 'Night', ['N', 'I', 'G', 'H', 'T'], 'night'),
    ('nature_tree', 'nature', 'tree', 'BDG_W2788', 'maraa', 'மரா', 'மரம்', ['ம', 'ர', 'ம்'], 'Tree', ['T', 'R', 'E', 'E'], 'tree'),
    ('nature_flower', 'nature', 'flower', 'BDG_W3538', 'hoovu', 'ஹூவு', 'பூ', ['பூ'], 'Flower', ['F', 'L', 'O', 'W', 'E', 'R'], 'flower'),
    ('nature_leaf', 'nature', 'leaf', 'BDG_W3157', 'ele', 'எலே', 'இலை', ['இ', 'லை'], 'Leaf', ['L', 'E', 'A', 'F'], 'leaf'),

    # Numbers
    ('num_one', 'numbers', 'one', 'BDG_W0701', 'ondu', 'ஒந்து', 'ஒன்று', ['ஒ', 'ன்', 'று'], 'One', ['O', 'N', 'E'], 'one'),
    ('num_two', 'numbers', 'two', 'BDG_W0702', 'eradu', 'எரடு', 'இரண்டு', ['இ', 'ர', 'ண்', 'டு'], 'Two', ['T', 'W', 'O'], 'two'),
    ('num_three', 'numbers', 'three', 'BDG_W0703', 'mooru', 'மூரு', 'மூன்று', ['மூ', 'ன்', 'று'], 'Three', ['T', 'H', 'R', 'E', 'E'], 'three'),
    ('num_four', 'numbers', 'four', 'BDG_W0704', 'naakku', 'நாக்கு', 'நான்கு', ['நா', 'ன்', 'கு'], 'Four', ['F', 'O', 'U', 'R'], 'four'),
    ('num_five', 'numbers', 'five', 'BDG_W0705', 'aidu', 'ஐது', 'ஐந்து', ['ஐ', 'ந்', 'து'], 'Five', ['F', 'I', 'V', 'E'], 'five'),

    # School & Actions
    ('school_teacher', 'school', 'teacher', 'BDG_W0083', 'bathiyaar', 'பதியார்', 'ஆசிரியர்', ['ஆ', 'சி', 'ரி', 'ய', 'ர்'], 'Teacher', ['T', 'E', 'A', 'C', 'H', 'E', 'R'], 'teacher'),
    ('school_flag', 'school', 'flag', 'BDG_W0843', 'kodi', 'கொடி', 'கொடி', ['கொ', 'டி'], 'Flag', ['F', 'L', 'A', 'G'], 'flag'),
    ('school_walk', 'school', 'walk', 'BDG_W0858', 'nada', 'நட', 'நட', ['ந', 'ட'], 'Walk', ['W', 'A', 'L', 'K'], 'walk'),
    ('school_run', 'school', 'run', 'BDG_W0859', 'odu', 'ஓடு', 'ஓடு', ['ஓ', 'டு'], 'Run', ['R', 'U', 'N'], 'run'),
    ('school_book', 'school', 'book', 'BDG_W3901', 'pusthaka', 'புஸ்தக', 'புத்தகம்', ['பு', 'த்', 'த', 'க', 'ம்'], 'Book', ['B', 'O', 'O', 'K'], 'book'),
]

print(f"Total curriculum words: {len(words_needed)}")
missing_audio = []
for item in words_needed:
    cid, cat, en_key, wid, bdg, bdg_scr, tam, tam_lets, eng, eng_lets, ill = item
    recs = c.execute("SELECT clip_id, clip_file FROM recordings WHERE word_id = ?", (wid,)).fetchall()
    if recs:
        print(f"OK: {wid:<10} | {eng:<8} -> {len(recs)} clips: {recs[0][0]}")
    else:
        print(f"NO CLIP: {wid:<10} | {eng:<8}")
        missing_audio.append((wid, bdg, eng))

conn.close()
print(f"\nMissing audio count: {len(missing_audio)}")
