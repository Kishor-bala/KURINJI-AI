import React, { useState, useRef } from 'react';
import { Mic, Square, Search, X, Loader2 } from 'lucide-react';

/**
 * Encodes Float32 PCM audio samples directly into a 16-bit Mono WAV Blob (16,000 Hz).
 * 100% authentic RIFF WAVE format for acoustic recognition.
 */
function encodeWAV(samples, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: 'audio/wav' });
}

export default function DirectAudioBar({
  onSelectCard,
  selectedLanguage = 'Badaga',
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusNotice, setStatusNotice] = useState('');

  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const streamRef = useRef(null);
  const recordedSamplesRef = useRef([]);
  const timerRef = useRef(null);

  // Direct raw audio microphone recording
  const startRecording = async () => {
    setStatusNotice('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContextClass();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      recordedSamplesRef.current = [];

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        for (let i = 0; i < inputData.length; i++) {
          recordedSamplesRef.current.push(inputData[i]);
        }
      };

      const muteGain = audioCtx.createGain();
      muteGain.gain.value = 0;

      source.connect(processor);
      processor.connect(muteGain);
      muteGain.connect(audioCtx.destination);
      streamRef.current = stream;

      setIsRecording(true);
      setSeconds(0);
      timerRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setStatusNotice('Microphone access unavailable: ' + err.message);
    }
  };

  const stopRecording = async () => {
    if (!isRecording) return;
    clearInterval(timerRef.current);
    setIsRecording(false);

    if (processorRef.current) processorRef.current.disconnect();
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }

    const rawSamples = new Float32Array(recordedSamplesRef.current);
    if (rawSamples.length < 4000) {
      setStatusNotice('Recording too short. Speak a word clearly.');
      return;
    }

    const wavBlob = encodeWAV(rawSamples, 16000);
    submitAudioForRecognition(wavBlob);
  };

  const submitAudioForRecognition = async (wavBlob) => {
    setIsAnalyzing(true);
    setStatusNotice('Matching acoustic model...');

    const formData = new FormData();
    formData.append('file', wavBlob, 'audio.wav');
    formData.append('language', selectedLanguage);

    try {
      const res = await fetch('/api/recognize', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Recognition error');
      const data = await res.json();

      if (data.learning_card) {
        onSelectCard(data.learning_card);
        setStatusNotice('');
      } else if (data.status === 'recognized') {
        setStatusNotice(`Recognized: ${data.english_meaning} (${data.tamil_meaning})`);
        fetchCardByWordId(data.word_id, data);
      } else {
        setStatusNotice(data.message || 'Word not recognized. Please speak clearly.');
      }
    } catch (err) {
      setStatusNotice('Voice recognition failed. Check server.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fetchCardByWordId = async (wordId, recognitionData) => {
    try {
      const res = await fetch('/api/modules');
      const data = await res.json();
      const match = data.cards.find((c) => c.word_id === wordId);
      if (match) {
        onSelectCard(match);
      } else {
        // Fallback card from recognition data
        onSelectCard({
          id: `dyn_${wordId}`,
          category: 'nature',
          word_id: wordId,
          badaga: {
            word: recognitionData.english_meaning,
            tamil_script: recognitionData.tamil_meaning,
            pronunciation: recognitionData.english_meaning,
          },
          marwari: {
            word: recognitionData.english_meaning,
            tamil_script: recognitionData.tamil_meaning,
            pronunciation: recognitionData.english_meaning,
          },
          tamil: {
            word: recognitionData.tamil_meaning,
            phonics: recognitionData.tamil_meaning,
            letters: (recognitionData.tamil_meaning || '').split(''),
            example: '',
          },
          english: {
            word: recognitionData.english_meaning,
            phonics: (recognitionData.english_meaning || '').toUpperCase().split('').join(' - '),
            letters: (recognitionData.english_meaning || '').toUpperCase().split(''),
            example: '',
          },
          image_url: '',
          illustration_name: 'tree',
        });
      }
    } catch {}
  };

  // Direct text search
  const handleTextSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim() || isAnalyzing) return;

    setIsAnalyzing(true);
    setStatusNotice('');

    try {
      const res = await fetch('/api/translate/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: searchQuery.trim(),
          language: selectedLanguage,
        }),
      });

      const data = await res.json();
      if (data.learning_card) {
        onSelectCard(data.learning_card);
        setSearchQuery('');
      } else if (data.status === 'recognized') {
        fetchCardByWordId(data.word_id, data);
        setSearchQuery('');
      } else {
        setStatusNotice(`Word "${searchQuery}" not found.`);
      }
    } catch {
      setStatusNotice('Search failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="direct-audio-bar">
      {/* Microphone Record Action Button */}
      <div className="audio-mic-action-group">
        {!isRecording ? (
          <button
            type="button"
            className="direct-mic-btn"
            onClick={startRecording}
            disabled={isAnalyzing}
            title="Click to speak native Badaga word"
          >
            {isAnalyzing ? (
              <Loader2 size={18} className="spin-animate" />
            ) : (
              <Mic size={18} />
            )}
            <span>{isAnalyzing ? 'Matching Audio...' : `Speak ${selectedLanguage}`}</span>
          </button>
        ) : (
          <button
            type="button"
            className="direct-mic-btn active-recording"
            onClick={stopRecording}
            title="Click to stop and recognize"
          >
            <Square size={16} />
            <span>Listening ({seconds}s)... Click to Finish</span>
          </button>
        )}
      </div>

      {/* Quick Search Form */}
      <form className="quick-search-form" onSubmit={handleTextSearch}>
        <Search size={15} className="search-lead-icon" />
        <input
          type="text"
          className="quick-search-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={`Type ${selectedLanguage} word (e.g. maraa, kannu, pal, mande)...`}
          disabled={isRecording || isAnalyzing}
        />
        {searchQuery && (
          <button
            type="button"
            className="clear-search-btn"
            onClick={() => setSearchQuery('')}
          >
            <X size={14} />
          </button>
        )}
      </form>

      {statusNotice && (
        <span className="audio-status-notice">{statusNotice}</span>
      )}
    </div>
  );
}
