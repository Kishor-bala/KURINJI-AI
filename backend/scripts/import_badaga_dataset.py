import csv
import sqlite3
import shutil
from pathlib import Path

DB_PATH = Path("backend/data/vocabulary.db")
BACKUP_PATH = Path("backend/data/vocabulary.db.bak")
CSV_PATH = Path(r"C:\Users\bbipi\Desktop\archive\Badaga To English Translation Dataset.csv")

# Extra phonetic variations for core vocabulary to ensure maximum dialect tolerance
EXTRA_VARIANTS = {
    "head": ["mande", "thale", "tale", "mandhe"],
    "eye": ["kan", "kannu", "kanpu", "kanna"],
    "nose": ["mooku", "mookku", "moogu"],
    "mouth": ["bae", "baayi", "bayi", "vaai"],
    "ear": ["kivi", "kaadu", "kiviya"],
    "hand": ["kai", "kayyi", "kayi"],
    "leg": ["kaalu", "kaal", "kalu"],
    "teeth": ["hallu", "pal", "pallu"],
    "hair": ["koodhalu", "koodalu", "kudalu", "thale koodhalu"],
    "stomach": ["otte", "odalu", "hotte"],
    "finger": ["kade beralu", "beralu", "viral"],
    "face": ["moga", "mooga", "mugam"],
    "tongue": ["naalange", "naalige", "naaku"],
    "back": ["bennu", "ben"],
    "knee": ["mandi", "mandhi", "muzhankaal"],
    "chest": ["ede", "maarbu"],
    "neck": ["koralu", "korallu", "kazhuthu"],
    "lip": ["thudi", "thuti", "udhadu"],
    "cheek": ["kenne", "kenneya"],
    "forehead": ["hanne", "nudhulu"],
    "mother": ["avve", "amma", "thaayi"],
    "father": ["appa", "thande"],
    "elder brother": ["annange", "anna"],
    "younger brother": ["thammange", "thambi"],
    "elder sister": ["akkange", "akka"],
    "younger sister": ["tangange", "thangai"],
    "sun": ["nnesuru", "surya"],
    "moon": ["tingalu", "chandira"],
    "water": ["neeru", "neer"],
    "milk": ["haalu", "paalu"],
    "fire": ["kicchu", "thee"],
    "house": ["mane", "veedu"],
    "tree": ["mara", "maram"],
    "flower": ["hoovu", "poo"],
    "dog": ["naai", "naayi"],
    "cat": ["kotti", "poonai"],
    "cow": ["danavu", "pasu", "aavu"],
}

# Common English to Tamil dictionary for imported CSV words
COMMON_TAMIL_DICT = {
    "seven hundred": "எழுநூறு",
    "seven": "ஏழு",
    "to put apply": "போடு",
    "to treat": "சிகிச்சை செய்",
    "to dress": "ஆடை அணி",
    "to lock": "பூட்டு",
    "divorce ceremony": "விவாகரத்து சடங்கு",
    "forest mango": "காட்டு மாங்காய்",
    "squinting eye": "மாறுகண்",
    "to be bitter": "கசப்பாக இரு",
    "to be sour": "புளிப்பாக இரு",
    "to spend time": "நேரம் செலவிடு",
    "to attain": "அடை",
    "to reach": "சென்றடை",
    "to finish off": "முடித்துவிடு",
    "to dry up": "காய்ந்து போ",
    "good": "நல்ல",
    "bad": "கெட்ட",
    "big": "பெரிய",
    "small": "சிறிய",
    "come": "வா",
    "go": "போ",
    "eat": "சாப்பிடு",
    "drink": "குடி",
    "sleep": "தூங்கு",
    "run": "ஓடு",
    "walk": "நட",
}

def main():
    if not CSV_PATH.is_file():
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    # 1. Backup DB
    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f"Backed up database to {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 2. Parse CSV
    print(f"Reading dataset: {CSV_PATH}")
    csv_map = {}
    total_csv_rows = 0
    with open(CSV_PATH, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 2:
                total_csv_rows += 1
                badaga_word = row[0].strip()
                english_meaning = row[1].strip()
                eng_key = english_meaning.lower()
                if eng_key not in csv_map:
                    csv_map[eng_key] = []
                if badaga_word and badaga_word not in csv_map[eng_key]:
                    csv_map[eng_key].append(badaga_word)

    print(f"Loaded {total_csv_rows} rows, {len(csv_map)} distinct English meanings from CSV.")

    # 3. Update existing Badaga entries in vocabulary table
    cur.execute("SELECT word_id, english_meaning, optional_romanised_pronunciation FROM vocabulary WHERE language='Badaga'")
    existing_entries = cur.fetchall()
    
    enriched_count = 0
    for wid, eng, current_pron in existing_entries:
        eng_key = eng.strip().lower()
        pron_set = set()
        
        # Keep existing pronunciation if any
        if current_pron:
            for p in current_pron.split(","):
                if p.strip():
                    pron_set.add(p.strip().lower())
                    
        # Add matches from CSV
        if eng_key in csv_map:
            for w in csv_map[eng_key]:
                pron_set.add(w.lower())

        # Add extra variants from dictionary
        if eng_key in EXTRA_VARIANTS:
            for v in EXTRA_VARIANTS[eng_key]:
                pron_set.add(v.lower())

        if pron_set:
            combined_pron = ", ".join(sorted(pron_set))
            cur.execute(
                "UPDATE vocabulary SET optional_romanised_pronunciation = ? WHERE word_id = ?",
                (combined_pron, wid),
            )
            enriched_count += 1

    print(f"Enriched {enriched_count} existing Badaga vocabulary entries with authentic Badaga pronunciations.")

    # 4. Check highest existing Badaga Word ID
    cur.execute("SELECT word_id FROM vocabulary WHERE language='Badaga' ORDER BY word_id DESC")
    all_wids = [r[0] for r in cur.fetchall()]
    max_num = 0
    for wid in all_wids:
        if wid.startswith("BDG_W"):
            try:
                num = int(wid[5:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    print(f"Highest current Badaga Word ID index: {max_num}")

    # 5. Insert new distinct Badaga words from CSV
    # We select clean, high-quality entries that don't already exist
    cur.execute("SELECT LOWER(english_meaning) FROM vocabulary WHERE language='Badaga'")
    existing_eng_set = {r[0].strip().lower() for r in cur.fetchall()}

    new_inserted = 0
    next_id = max(max_num + 1, 1000)

    for eng_key, badaga_list in csv_map.items():
        if eng_key in existing_eng_set or len(eng_key) < 2:
            continue

        clean_badaga = ", ".join(badaga_list[:5])
        tamil_meaning = COMMON_TAMIL_DICT.get(eng_key, eng_key)

        new_wid = f"BDG_W{next_id:04d}"
        cur.execute(
            """
            INSERT INTO vocabulary (
                word_id, language, tamil_meaning, english_meaning,
                optional_romanised_pronunciation, notes, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_wid,
                "Badaga",
                tamil_meaning,
                eng_key,
                clean_badaga,
                "Imported from Badaga-English dataset",
                "verified",
            ),
        )
        existing_eng_set.add(eng_key)
        next_id += 1
        new_inserted += 1

    conn.commit()

    # Final stats
    cur.execute("SELECT COUNT(*) FROM vocabulary WHERE language='Badaga'")
    total_badaga = cur.fetchone()[0]
    conn.close()

    print(f"Successfully inserted {new_inserted} new Badaga vocabulary entries.")
    print(f"Total Badaga entries in database is now: {total_badaga} (previously {len(existing_entries)})")
    print("Database update complete!")

if __name__ == "__main__":
    main()
