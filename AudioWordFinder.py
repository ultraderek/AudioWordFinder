"""
Profanity Remover

This Python script uses speech recognition and audio manipulation
to censor profanity in an audio file.
It transcribes the audio, searches for profanity keywords, and replaces them with asterisks.
The script then applies silence to the original audio file based on the location of
profanity, effectively "muting" profane sections.
The output is a new audio file with profanity silenced.
"""

import argparse
import csv
import os
import whisper
from stable_whisper import modify_model
from pydub import AudioSegment

def parse_tsv(tsv_string):
    """
    Parses a TSV string into a list of tuples.
    """
    words = []
    reader = csv.reader(tsv_string.split('\n'), delimiter='\t')
    for row in reader:
        if len(row) == 3:
            start_time, end_time, word = row
            words.append((float(start_time), float(end_time), word))
    return words

def convert_to_wav(input_file):
    """
    Converts the input audio file to WAV format.
    """
    audio = AudioSegment.from_file(input_file)
    wav_file = os.path.splitext(input_file)[0] + ".wav"
    audio.export(wav_file, format="wav")
    return wav_file

def transcribe_audio(audio_file):
    """
    Transcribes the audio using the Whisper ASR model.
    """
    model = whisper.load_model("large")
    modify_model(model)
    result = model.transcribe(audio_file, suppress_silence=True)
    return result.to_tsv('', segment_level=False, word_level=True)

def censor_profanity(words):
    """
    Flags profanity in the provided list of words.
    """
    profanity_keywords = ["fuck", "shit", "god damn", "damn", "bitch", "pussy", "cunt"]
    censored_words = []
    for start_time, end_time, word in words:
        is_profanity = any(profanity in word.lower() for profanity in profanity_keywords)
        censored_words.append((start_time, end_time, word, is_profanity))
    return censored_words

def mute_profanity(audio_file, words, padding_ms=16):
    """
    Mutes sections of the audio where profanity is flagged, with additional padding.
    """
    audio = AudioSegment.from_file(audio_file)
    for start_time, end_time, pword, is_profanity in words:
        if is_profanity:
            start_ms = max(0, int(start_time) - padding_ms)
            end_ms = min(len(audio), int(end_time) + padding_ms)
            silence = AudioSegment.silent(duration=end_ms - start_ms)
            audio = audio[:start_ms] + silence + audio[end_ms:]
            #converting ms to the corrisponding units
            start_s=int(start_ms/1000)
            end_s=int(end_ms/1000)
            start_m = int(start_s/60)
            end_m=int(end_s/60)
#getting the hours
            start_h=int(start_m/60)
            end_h=int(end_m/60)
#getting the seconds
            start_s=int(start_s%60)
            end_s=int(end_s%60)
#getting the minutes
            start_m=int(start_m%60)
            end_m=int(end_m%60)
#getting the frames
            start_f=int(((start_ms%1000)*60)/1000)
            end_f=int(((end_ms%1000)*60)/1000)
            print(pword, ":: start- "+str(start_h) +"h:"+ str(start_m)+"m:"+ str(start_s)+"s:"+str(start_f) + "f  ::  end- "+str(end_h) +"h:"+ str(end_m)+"m:"+ str(end_s)+"s:"+str(end_f)+"f")
    return audio

def remove_file(file_path):
    """
    Removes the specified file from the filesystem.
    """
# pylint: disable=broad-exception-caught
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed file: {file_path}")
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")

def main():
    """
    Main function to handle command line arguments and execute the profanity removal process.
    """
    parser = argparse.ArgumentParser(description='Profanity Silencer for Audio Files')
    parser.add_argument('input', help='Input audio file path')
    parser.add_argument('output', help='Output audio file path')
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    wav_file = ''

    if not input_file.lower().endswith(".wav"):
        print("Converting input audio to WAV format...")
        wav_file = convert_to_wav(input_file)
        input_file = wav_file
# pylint: disable=broad-exception-caught
    try:
        tsv_string = transcribe_audio(input_file)
        words = parse_tsv(tsv_string)
        censored_words = censor_profanity(words)
        muted_audio = mute_profanity(input_file, censored_words, padding_ms=50)
        muted_audio.export(output_file, format="mp3")
        print("Profanity silenced successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if wav_file:
            remove_file(wav_file)

if __name__ == "__main__":
    main()
    