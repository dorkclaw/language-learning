import genanki
import random
import os
import json

# Define Paths
INPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../anki/Refold ES1K/")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../anki/Refold ES1K_deck/")

# Ensure the output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 1. Custom CSS adapted from Refold ES1K with additions for dual languages
CSS = """
.card {
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
     padding: 24px;
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
.word {
     color: rgb(75, 50, 174);
     font-size: 28px;
     font-weight: 700;
     margin-bottom: 16px;
     line-height: 1.3;
}
.nightMode .word {
     color: rgb(133, 102, 255);
}
.definition {
     font-size: 22px;
     margin-bottom: 16px;
     line-height: 1.3;
}
.example-sentence {
     margin-top: 16px;
     font-style: italic;
     line-height: 1.4;
}
.sentence-translation {
     margin-top: 12px;
     font-size: 16px;
     line-height: 1.4;
}
hr {
     border: 0;
     border-bottom: 1px solid rgb(216, 208, 249);
     margin: 24px 0;
}
.nightMode hr {
     border-color: rgb(48, 32, 111);
}
.lang-label {
     color: rgb(101, 68, 233);
     font-size: 0.75em;
     font-weight: bold;
     text-transform: uppercase;
     margin-right: 4px;
}
.nightMode .lang-label {
     color: rgb(153, 128, 255);
}
"""

# 2. Define the Universal Model for our dual-direction setup
MODEL_ID = random.Random("Symmetrical_ES_EN_DE_Vocab").randrange(1<<30, 1<<31) # Reusing a stable base ID
unified_model = genanki.Model(
    MODEL_ID,
    'Symmetrical_ES_EN_DE_Vocab',
    fields=[
        {'name': 'Front_Word'},
        {'name': 'Front_Sentence'},
        {'name': 'Back_Word'},
        {'name': 'Back_Sentence'},
    ],
    templates=[{
        'name': 'Vocabulary Card',
        'qfmt': """
        <div class="flashcard">
            <div class="word">{{Front_Word}}</div>
            <div class="example-sentence">{{Front_Sentence}}</div>
        </div>
        """,
        'afmt': """
        <div class="flashcard">
            <div class="word">{{Front_Word}}</div>
            <div class="example-sentence">{{Front_Sentence}}</div>
            
            <hr id="answer" />
            
            <div class="definition">{{Back_Word}}</div>
            <div class="sentence-translation">{{Back_Sentence}}</div>
        </div>
        """,
    }],
    css=CSS
)

# Dictionary to hold the dynamic decks
decks_by_level = {}

def get_deck_for_level(level):
    """Creates or fetches a deck for a specific language level."""
    if level not in decks_by_level:
        # Seed the random generator with the level name to ensure stable deck IDs across runs
        deck_id = random.Random(f"Deck_Seed_{level}").randrange(1<<30, 1<<31)
        deck_name = f"Spanish Symmetrical - Level {level}"
        decks_by_level[level] = genanki.Deck(deck_id, deck_name)
    return decks_by_level[level]

def format_list(item_list):
    """Helper to join lists of words cleanly."""
    return ", ".join(item_list) if isinstance(item_list, list) else str(item_list)

def process_json_files():
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: Input folder {INPUT_FOLDER} not found.")
        return

    for filename in os.listdir(INPUT_FOLDER):
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(INPUT_FOLDER, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Iterate through the two objects in the array
            for index, card in enumerate(data):
                direction = card.get("direction")
                level = card.get("mandatory_level", "Uncategorized")
                
                # Assign to corresponding deck
                deck = get_deck_for_level(level)
                
                # Determine fields based on direction
                if direction == "spanish_to_target":
                    front_word = card.get("cue_spanish", "")
                    front_sentence = f"\"{card.get('example_sentence_es', '')}\""
                    
                    back_word = (f"<span class='lang-label'>EN:</span> {format_list(card.get('target_en',[]))}<br>"
                                 f"<span class='lang-label'>DE:</span> {format_list(card.get('target_de',[]))}")
                    back_sentence = (f"<span class='lang-label'>EN:</span> {card.get('example_sentence_en', '')}<br>"
                                     f"<span class='lang-label'>DE:</span> {card.get('example_sentence_de', '')}")
                
                elif direction == "target_to_spanish":
                    front_word = (f"<span class='lang-label'>EN:</span> {card.get('cue_en', '')}<br>"
                                  f"<span class='lang-label'>DE:</span> {card.get('cue_de', '')}")
                    front_sentence = (f"<span class='lang-label'>EN:</span> \"{card.get('example_sentence_en', '')}\"<br>"
                                      f"<span class='lang-label'>DE:</span> \"{card.get('example_sentence_de', '')}\"")
                    
                    back_word = f"<span class='lang-label'>ES:</span> {format_list(card.get('target_es',[]))}"
                    back_sentence = f"<span class='lang-label'>ES:</span> {card.get('example_sentence_es', '')}"
                else:
                    continue # Skip if unrecognized format
                
                # Generate a stable GUID from the filename and the card index
                note_guid = genanki.guid_for(filename, str(index))
                
                note = genanki.Note(
                    model=unified_model,
                    fields=[front_word, front_sentence, back_word, back_sentence],
                    guid=note_guid
                )
                
                deck.add_note(note)
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # 4. Export the decks
    print("\n--- Generating Anki Packages ---")
    for level, deck in decks_by_level.items():
        output_file = os.path.join(OUTPUT_FOLDER, f"Spanish_Symmetrical_{level}.apkg")
        genanki.Package(deck).write_to_file(output_file)
        print(f"Successfully created: {output_file} (Notes: {len(deck.notes)})")

if __name__ == "__main__":
    process_json_files()