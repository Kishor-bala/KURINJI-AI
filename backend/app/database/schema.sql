-- Table A: Vocabulary
CREATE TABLE IF NOT EXISTS vocabulary (
    word_id TEXT PRIMARY KEY,
    language TEXT NOT NULL CHECK(language IN ('Badaga', 'Marwari')),
    tamil_meaning TEXT NOT NULL,
    english_meaning TEXT NOT NULL,
    optional_romanised_pronunciation TEXT,
    notes TEXT,
    verification_status TEXT DEFAULT 'verified' CHECK(verification_status IN ('verified', 'pending', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vocabulary_lang ON vocabulary(language);

-- Table B: Recordings
CREATE TABLE IF NOT EXISTS recordings (
    clip_id TEXT PRIMARY KEY,
    word_id TEXT NOT NULL,
    speaker_id TEXT NOT NULL,
    original_file TEXT,
    clip_file TEXT NOT NULL,
    start_timestamp REAL DEFAULT 0.0,
    end_timestamp REAL,
    sample_rate INTEGER DEFAULT 16000,
    duration REAL,
    review_status TEXT DEFAULT 'reviewed' CHECK(review_status IN ('reviewed', 'pending_review', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES vocabulary(word_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recordings_word ON recordings(word_id);
CREATE INDEX IF NOT EXISTS idx_recordings_speaker ON recordings(speaker_id);

-- Table C: Embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id TEXT PRIMARY KEY,
    clip_id TEXT NOT NULL,
    word_id TEXT NOT NULL,
    encoder_name TEXT NOT NULL,
    encoder_version TEXT NOT NULL,
    layer_name TEXT NOT NULL,
    pooling_method TEXT NOT NULL,
    embedding_file TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clip_id) REFERENCES recordings(clip_id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES vocabulary(word_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embeddings_word ON embeddings(word_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_clip ON embeddings(clip_id);
