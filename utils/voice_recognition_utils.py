import os
import librosa
import numpy as np
import pickle
import sounddevice as sd
import soundfile as sf

def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=None)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfccs.T, axis=0)

def encode_voices(dataset_path='dataset/voices', model_save_path='models/voice_encodings.pkl'):
    known_encodings = []
    known_names = []

    for filename in os.listdir(dataset_path):
        if filename.endswith('.wav'):
            features = extract_features(os.path.join(dataset_path, filename))
            known_encodings.append(features)
            known_names.append(filename.split('.')[0])

    with open(model_save_path, 'wb') as f:
        pickle.dump((known_encodings, known_names), f)
    print("[INFO] Voice Encodings Saved!")

def record_voice(output_file='temp_voice.wav', duration=3):
    print("[INFO] Recording voice...")
    fs = 44100  # Sample rate
    voice = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    sf.write(output_file, voice, fs)
    print("[INFO] Recording saved!")

def recognize_voice():
    with open('models/voice_encodings.pkl', 'rb') as f:
        known_encodings, known_names = pickle.load(f)

    record_voice()

    features = extract_features('temp_voice.wav')

    distances = [np.linalg.norm(features - enc) for enc in known_encodings]
    min_dist = min(distances)
    min_idx = distances.index(min_dist)

    if min_dist < 20:  # Threshold (tune this value)
        print(f"Recognized as: {known_names[min_idx]}")
        return known_names[min_idx]
    else:
        print("Unknown voice")
        return "Unknown"
