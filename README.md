# Flashcard Content Engine 🎓🎬

Turn your study flashcards (TSV files) into engaging multimedia content automatically using AI. 

## What does this project do?
This tool is a complete pipeline processing learning materials into two formats:
1.  **Audio Explanations** 🎧: Natural, podcast-style audio explanations of your flashcards (using OpenAI TTS).
2.  **Viral Video Shorts** 📱: Dynamic YouTube Shorts/TikToks with synchronized text, animations, and "karaoke" subtitles (using Remotion).

## Features
- **Smart Transformation**: Turns rigid Q&A into conversational explanations suitable for listening.
- **Viral Aesthetic**: Dynamic backgrounds, spring animations, and engaging typography for video.
- **Semantic Sync**: Visuals align perfectly with spoken keywords in the video.
- **Batch Processing**: Process hundreds of cards at once.

## Prerequisites
- **Python 3.8+**
- **Node.js 16+** & **npm**
- **FFmpeg** (required by Remotion)
- **OpenAI API Key** (for Text-to-Speech and Whisper)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Python Setup**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Node.js (for Video) Setup**:
   ```bash
   cd video-generator
   npm install
   cd ..
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=sk-your-api-key-here
   ```

## Usage

You can use the tool for just audio, or for full video generation.

### 🎧 Mode 1: Audio Only
Great for learning on the go (Podcast style).

```bash
# Generate audio files for all cards in a TSV
python3 audio_generator.py "your_cards.tsv" --output "./my_audio_files" --voice nova
```
*Options:* `--voice` (alloy, echo, fable, onyx, nova, shimmer)

---

### 🎬 Mode 2: Video Generation
Generates vertical videos for Social Media (YouTube Shorts, TikTok, Reels).

**Step 1. Generate Assets (Audio + Data)**
This command creates the audio, transcribes it, and aligns the visuals.
```bash
python3 video_pipeline.py --tsv "your_cards.tsv" --compilation
```
*Tip: You can use `--audio-dir "my_audio_files"` if you already generated audio in Mode 1.*

**Step 2. Render Video**
Render the full compilation video using Remotion.
```bash
cd video-generator
npx remotion render src/index.ts CompilationVideo out/final_video.mp4 --concurrency=4
```

## Project Structure
- `audio_generator.py`: **Core Audio Logic**. Handles prompt engineering for natural explanations and TTS.
- `video_pipeline.py`: **Video Orchestration**. Handles transcription (Whisper), semantic alignment, and data prep for Remotion.
- `video-generator/`: **Frontend**. React/Remotion project that defines the visual style, animations, and rendering logic.

## License
MIT
