# Language Learning tools

This repository contains some tools that have helped me in my language learning journey.

Most of the code here is vibe coded, and not meant to be used by anyone else. But if you find it useful, feel free to use it or contribute!

# Ideas

 - Take the Language Transfer course audio files, transcribe them, and create Anki decks of all the new vocabulary introduced in each lesson
 - To do this, we will use OpenAI's WhisperX for transcription, and some LLM API to extract the new vocabulary and examples

 - There are anki decks of the top 1000 spanish words (or so), but they are not super high quality. The one I'm using is also only in one direction (Spanish -> English)
 - Ideally, I would like to add the other direction, and german translations (my native language).
 - So I take every word pair in the deck, and use an LLM to annotate it for quality and generate more accurate translations and example sentences. And reverse translation direction.

## transcriptions

Download Language Transfer course from [here](https://downloads.languagetransfer.org/spanish/spanish.zip), and unzip the contents into `./data/lt`

Add huggingface token in `.env.example` and rename to `.env`

`pip3 install torch torchvision torchcodec --index-url https://download.pytorch.org/whl/cu130`

`pip3 install -r requirements.txt`

`python3 src/transcribe_folder.py`