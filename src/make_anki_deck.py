import genanki
import json
import os

# --- Configuration ---
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../anki/Refold ES1K/")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../anki/Refold ES1K_deck/")

# --- Define the Model strictly using your provided specs ---
MODEL_ID = 1184655693

Q_FMT = """<div class="flashcard">
    <div class="front">
        <p class="word">{{Word}}</p>
        <p class="word-audio">{{word_audio}}</p>
    </div>
</div>"""

A_FMT = """<div class="flashcard">
    <div class="front">
        <p class="word">{{Word}}</p>
    </div>

    <hr id="answer" />

    <div class="back">
        <div class="definition">{{Definition}}</div>

        {{#Irregular Forms}}
            <p class="irregular-forms">
                <strong>Irregular Forms:</strong>
                {{Irregular Forms}}
            </p>
        {{/Irregular Forms}}
				
        <p class="example-sentence">
            "{{Example Sentence}}"

            <div class="sentence-translation">
                {{hint:Translation}}
            </div>

            <p class="example-sentence-audio">{{sentence_audio}}</p>
        </p>
    </div>
</div>"""

CSS = """.card {
     font-family: sans-serif;
     font-size: 16px;
     text-align: left;
     color: rgb(48, 32, 111);
     background-color: rgb(251, 250, 254);
}

.card.nightMode {
     color: rgba(255, 255, 255, 0.85);
     background-color: rgb(11, 7, 22);
}

.flashcard {
     display: block;
     padding: 0 24px 20px 24px;
     min-height: 200px;
     max-width: 500px;
     margin: 0 auto;
     border-radius: 10px;
     background-color: rgb(255, 255, 255);
     box-shadow: 0 5px 10px -5px rgba(133, 102, 255, 0.4);
}

.nightMode .flashcard {
     background-color: rgb(19, 12, 34);
     box-shadow: 0 5px 10px -5px rgba(0, 0, 0, 0.75);
}

.front {
     display: flex;
     justify-content: space-between;
     align-items: center;
     margin-bottom: -10px;
     font-family: "Montserrat", sans-serif;
}

.back {
     font-family: "Open Sans", sans-serif;
}

.word {
     color: rgb(75, 50, 174);
     font-size: 32px;
     font-weight: 700;
}

.nightMode .word {
     color:rgb(133, 102, 255);
}

.definition {
     font-size: 24px;
     margin-bottom: 0;
}

.irregular-forms {
     color: rgb(75, 50, 174);
     margin-top: 12px;
}

.nightMode .irregular-forms {
     color: rgb(153, 128, 255);
}

.example-sentence {
     margin-top: 34px 
}

.sentence-translation {
		 font-style: italic;
}

hr {
     border: 0;
     border-bottom: 1px solid rgb(216, 208, 249);
     margin-bottom: 32px;
}

.nightMode hr {
     border-color: rgb(48, 32, 111);
}

.replay-button svg circle { 
     fill: rgb(246, 245, 253);
     stroke: rgb(216, 208, 249);
     stroke-width: 1;
}

.replay-button svg path { 
     fill: rgb(75, 50, 174);
     transform: scale(0.6) translate(19px, 20px);
}

.nightMode .replay-button svg circle { 
     fill: rgb(26, 18, 61);
     stroke: rgb(48, 32, 111);
}

.nightMode .replay-button svg path { 
     fill: rgb(255, 255, 255); 
}

.hint {
     color: rgb(101, 68, 233);
}

.nightMode .hint {
     color: rgb(133, 102, 255);
}"""

es1k_model = genanki.Model(
    MODEL_ID,
    'ES1Kv2',
    fields=[
        {'name': 'Index'},
        {'name': 'Word'},
        {'name': 'Definition'},
        {'name': 'Irregular Forms'},
        {'name': 'Example Sentence'},
        {'name': 'Translation'},
        {'name': 'word_audio'},
        {'name': 'sentence_audio'}
    ],
    templates=[{
        'name': 'ES1K Vocab',
        'qfmt': Q_FMT,
        'afmt': A_FMT,
    }],
    css=CSS,
    model_type=0
)

def build_decks():
    # Ensure folders exist
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: Could not find input folder at {INPUT_FOLDER}")
        return
    
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Dictionary to hold the deck for each CEFR level
    decks_by_level = {}
    
    # Base Deck ID from your instructions
    BASE_DECK_ID = 2048342517

    print("Reading JSON files and generating cards...")
    
    for filename in os.listdir(INPUT_FOLDER):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(INPUT_FOLDER, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
                
                # Our schema is an array with exactly two dicts (one for each direction)
                if not isinstance(cards_data, list):
                    continue

                for card in cards_data:
                    level = card.get("mandatory_level")
                    if not level:
                        continue
                    
                    # Initialize the deck for this level if it doesn't exist yet
                    if level not in decks_by_level:
                        # Generate a deterministic unique ID based on the Base ID + level hash
                        unique_deck_id = BASE_DECK_ID + abs(hash(level)) % 1000000 
                        deck_name = f"Refold ES1K modified::{level}" # using :: creates subdecks in Anki cleanly
                        decks_by_level[level] = genanki.Deck(unique_deck_id, deck_name)

                    direction = card.get("direction")
                    
                    # Prepare the data mapped perfectly to your Anki Model
                    index = ""
                    irregular_forms = ""
                    word_audio = ""
                    sentence_audio = ""

                    if direction == "spanish_to_target":
                        word = card.get("cue_spanish", "")
                        
                        # Combine EN and DE definitions
                        target_en = ", ".join(card.get("target_en",[]))
                        target_de = ", ".join(card.get("target_de",[]))
                        definition = f"<strong>EN:</strong> {target_en}<br><strong>DE:</strong> {target_de}"
                        
                        example_sentence = card.get("example_sentence_es", "")
                        
                        # Combine EN and DE sentence translations
                        sentence_en = card.get("example_sentence_en", "")
                        sentence_de = card.get("example_sentence_de", "")
                        translation = f"<strong>EN:</strong> {sentence_en}<br><br><strong>DE:</strong> {sentence_de}"

                    elif direction == "target_to_spanish":
                        # Combine EN and DE as the cue word
                        word = f"{card.get('cue_en', '')} <br><span style='font-size:22px; color:gray;'>({card.get('cue_de', '')})</span>"
                        
                        definition = f"<strong>ES:</strong> {', '.join(card.get('target_es',[]))}"
                        
                        # Put EN and DE sentence on the front as "Example Sentence" placeholder
                        example_sentence = f"<strong>EN:</strong> {card.get('example_sentence_en', '')}<br><br><strong>DE:</strong> {card.get('example_sentence_de', '')}"
                        
                        # The translation is the target Spanish
                        translation = f"<strong>ES:</strong> {card.get('example_sentence_es', '')}"
                    else:
                        continue # Skip unrecognized structure

                    # Create Note
                    note = genanki.Note(
                        model=es1k_model,
                        fields=[
                            index, 
                            word, 
                            definition, 
                            irregular_forms, 
                            example_sentence, 
                            translation, 
                            word_audio, 
                            sentence_audio
                        ]
                    )
                    
                    # Add Note to respective Deck
                    decks_by_level[level].add_note(note)

        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    # Export decks to .apkg files
    for level, deck in decks_by_level.items():
        output_path = os.path.join(OUTPUT_FOLDER, f"Refold_ES1K_{level}.apkg")
        genanki.Package(deck).write_to_file(output_path)
        print(f"Success! Created: Refold_ES1K_{level}.apkg with {len(deck.notes)} cards.")

if __name__ == "__main__":
    build_decks()