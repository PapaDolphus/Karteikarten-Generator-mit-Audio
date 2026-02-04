import os
import json
import argparse
import shutil
import re
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI
from mutagen.mp3 import MP3
from audio_generator import AudioGenerator

class VideoPipeline:
    def __init__(self):
        self.client = OpenAI()
        self.audio_gen = AudioGenerator()
        
    def transcribe(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribes audio using Whisper API to get word-level timestamps.
        """
        print(f"  📝 Transcribing {audio_path}...")
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    response_format="verbose_json", 
                    timestamp_granularities=["word"]
                )
            return transcript.words
        except Exception as e:
            print(f"  ❌ Transcription failed: {e}")
            return []

    def parse_flashcard(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Parses flashcard content into structured data for the video.
        """
        # Simple heuristic: Split by <br> or newlines to find list items
        # If line starts with "1.", "-", etc., treat as list item.
        
        # Clean HTML breaks
        clean_answer = answer.replace("<br>", "\n").replace("<br/>", "\n")
        lines = [l.strip() for l in clean_answer.split("\n") if l.strip()]
        
        items = []
        intro_text = ""
        
        for line in lines:
            # Check for list markers
            if line[0].isdigit() and line[1] in ['.', ')']:
                items.append(line)
            elif line.startswith(('-', '•')):
                items.append(line)
            elif not items:
                # If no items found yet, treat as intro
                intro_text += line + "\n"
            else:
                # If items found, append to last item or new item? 
                # For simplicity, append to list if we are in list mode, else ignore
                items.append(line)
                
        return {
            "question": question,
            "intro": intro_text.strip(),
            "items": items,
            "full_text": clean_answer
        }

    def align_content(self, items: List[str], transcript_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aligns visual items to transcript timestamps using keyword matching.
        """
        aligned_items = []
        search_start_index = 0
        
        last_found_time = 0.0
        
        print("  ⏱️ Aligning visuals...")
        
        for item in items:
            # 1. Extract keyword (simple heuristic: first long word)
            # Remove numbering "1. ", "a) "
            clean_item = item
            if item[0].isdigit():
                parts = item.split(" ", 1)
                if len(parts) > 1:
                    clean_item = parts[1]
            
            # Simple keyword extraction: take first word > 3 chars, or just first word
            words = clean_item.split()
            keyword = next((w for w in words if len(w) > 3), words[0] if words else "").lower()
            
            # Clean keyword
            keyword = "".join(c for c in keyword if c.isalnum())
            
            # 2. Search in transcript
            found_time = None
            found_index = search_start_index
            
            # Search buffer: Don't search TOO far ahead immediately? 
            # Actually we want the first occurrence after previous.
            
            for i in range(search_start_index, len(transcript_words)):
                tw = transcript_words[i]
                t_word = "".join(c for c in tw['word'] if c.isalnum()).lower()
                
                # Fuzzy match? Or 'in'?
                if keyword in t_word or t_word in keyword:
                    found_time = tw['start']
                    found_index = i
                    print(f"    found '{keyword}' at {found_time}s (match: {tw['word']})")
                    break
            
            # 3. Fallback logic
            if found_time is not None:
                last_found_time = found_time
                search_start_index = found_index + 1 # Advance search
                aligned_items.append({
                    "text": item,
                    "startFrame": int(found_time * 30),
                    "found": True
                })
            else:
                print(f"    ⚠️ keyword '{keyword}' not found, interpolating...")
                # If not found, append with a flag, we will fix timestamps later or just use last + padding
                aligned_items.append({
                    "text": item,
                    "startFrame": int((last_found_time + 2.0) * 30), # Default 2s delay
                    "found": False
                })
                # Increment last_found slightly for next fallback
                last_found_time += 2.0

        return aligned_items

    def generate_video_data(self, question: str, answer: str, output_dir: str):
        """
        Full pipeline: Audio -> Transcript -> JSON Data for Remotion
        """
        Path(output_dir).mkdir(exist_ok=True, parents=True)
        
        # 1. Generate Audio
        safe_name = self.audio_gen._sanitize_filename(question[:30])
        audio_filename = f"{safe_name}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        print(f"🎬 Processing: {question}")
        if not os.path.exists(audio_path):
            success = self.audio_gen.process_flashcard(question, answer, audio_path)
            if not success:
                raise Exception("Audio generation failed")
                
        # Get duration for frames (30fps)
        from mutagen.mp3 import MP3
        audio = MP3(audio_path)
        duration_sec = audio.info.length
        duration_frames = int(duration_sec * 30) + 90 # Add 3 sec buffer
        
        # 2. Transcribe
        words_obj = self.transcribe(audio_path)
        words = [{"word": w.word, "start": w.start, "end": w.end} for w in words_obj]
        
        # 3. Parse Content
        raw_content = self.parse_flashcard(question, answer)
        
        # 4. Align Content
        aligned_items = self.align_content(raw_content["items"], words)
        
        final_content = {
            "question": raw_content["question"],
            "intro": raw_content["intro"],
            "items": aligned_items, # Now list of objects
        }
        
        # 5. Save Data for Remotion
        data = {
            "audioUrl": audio_filename, 
            "subtitles": words, 
            "content": final_content,
            "durationInFrames": duration_frames
        }
        
        json_path = os.path.join(output_dir, f"{safe_name}.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"  ✅ Data saved to {json_path}")
        return json_path, audio_path

    def produce_compilation_data(self, tsv_path: str, audio_dir: str, output_path: str):
        """
        Generates a single JSON file containing data for ALL cards in the TSV.
        Matches TSV rows to 'karte_XXX' audio files.
        """
        import csv
        
        compilation_cards = []
        
        # 1. Read TSV
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)
            
        print(f"📦 Processing {len(rows)} cards for compilation...")
        
        # 2. Get Audio Files
        audio_files = sorted([f for f in os.listdir(audio_dir) if f.startswith("karte_") and f.endswith(".mp3")])
        
        # Map karte_XXX to filename
        audio_map = {}
        for af in audio_files:
            try:
                # Extract number "karte_001_..." -> 1
                num_part = af.split("_")[1]
                idx = int(num_part)
                audio_map[idx] = af
            except:
                continue
                
        # 3. Iterate
        for i, row in enumerate(rows):
            idx = i + 1 # 1-based index
            if len(row) < 2:
                continue
                
            question = row[0]
            answer = row[1]
            
            # Find audio
            if idx in audio_map:
                audio_filename = audio_map[idx]
            else:
                # Construct expected filename if missing
                print(f"⚠️ Warning: No audio found for Card {idx}, generating...")
                safe_name = self.audio_gen._sanitize_filename(question[:50])
                audio_filename = f"karte_{idx:03d}_{safe_name}.mp3"
                
            audio_path = os.path.join(audio_dir, audio_filename)
            
            # Ensure audio exists
            if not os.path.exists(audio_path):
                print(f"  🎙️ Generating missing audio: {audio_filename}")
                success = self.audio_gen.process_flashcard(question, answer, audio_path)
                if not success:
                    print(f"❌ Failed to generate audio for card {idx}, skipping.")
                    continue

            # Auto-copy to video-generator/public
            public_msg = ""
            public_dir = os.path.join("video-generator", "public")
            Path(public_dir).mkdir(parents=True, exist_ok=True)
            public_path = os.path.join(public_dir, audio_filename)
            
            if not os.path.exists(public_path):
                shutil.copy2(audio_path, public_path)
                public_msg = "and copied to public/"

            print(f"  [{idx}/{len(rows)}] Processing: {question[:30]}... {public_msg}")
            
            try:
                # Transcribe & Align
                from mutagen.mp3 import MP3
                audio = MP3(audio_path)
                duration_sec = audio.info.length
                duration_frames = int(duration_sec * 30) + 60
                
                words_obj = self.transcribe(audio_path)
                words = [{"word": w.word, "start": w.start, "end": w.end} for w in words_obj]
                
                raw_content = self.parse_flashcard(question, answer)
                aligned_items = self.align_content(raw_content["items"], words)
                
                final_content = {
                    "question": raw_content["question"],
                    "intro": raw_content["intro"],
                    "items": aligned_items,
                }
                
                # Add to list
                compilation_cards.append({
                    "id": idx,
                    "audioUrl": audio_filename, # Remotion will look in public/
                    "subtitles": words,
                    "content": final_content,
                    "durationInFrames": duration_frames
                })
                
            except Exception as e:
                print(f"❌ Error processing card {idx}: {e}")
                
        # 4. Save
        data = {
            "type": "compilation",
            "cards": compilation_cards
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Compilation data saved to {output_path} with {len(compilation_cards)} cards.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", help="Flashcard question")
    parser.add_argument("--answer", help="Flashcard answer")
    parser.add_argument("--tsv", help="Path to TSV file")
    parser.add_argument("--out", default="./video-assets", help="Output directory")
    parser.add_argument("--compilation", action="store_true", help="Generate compilation from TSV")
    
    args = parser.parse_args()
    
    pipeline = VideoPipeline()
    
    if args.compilation and args.tsv:
        # Assume audio is in video-generator/public for compilation, OR we use the audio_output dir 
        # But we need to use the files mapped from audio_output. 
        # Actually pipeline.transcribe needs absolute path or relative to CWD.
        # We copied them to video-generator/public/ but for transcription we can read from audio_output/
        pipeline.produce_compilation_data(args.tsv, "audio_output", "video-generator/src/compilation.json")
        
    elif args.tsv:
        # Read first valid line from TSV
        with open(args.tsv, "r") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    pipeline.generate_video_data(parts[0], parts[1], args.out)
                    break
    elif args.question and args.answer:
        pipeline.generate_video_data(args.question, args.answer, args.out)
