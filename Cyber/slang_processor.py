import re
from .models import SlangInterpretation as slang

# A dictionary of common emojis and their meanings
# You can expand this as needed.
EMOJI_DICT = {
    # '😂': 'laughing', '😭': 'crying', '❤️': 'love', '😍': 'heart eyes',
    # '😊': 'smiling', '🙏': 'praying', '👍': 'thumbs up', '🔥': 'fire',
    # '😔': 'sad', '😡': 'angry', '😈': 'devil', '🖕': 'middle finger',
    # '😩': 'tired', '💔': 'broken heart', '😢': 'sad',

    # Happy and Positive Faces
    '😀': 'grinning face',
    '😃': 'grinning face with big eyes',
    '😄': 'grinning face with smiling eyes',
    '😁': 'beaming face with smiling eyes',
    '😆': 'grinning squinting face',
    '😅': 'grinning face with sweat',
    '🤣': 'rolling on the floor laughing',
    '😂': 'face with tears of joy',
    '🙂': 'slightly smiling face',
    '🙃': 'upside-down face',
    '😉': 'winking face',
    '😊': 'smiling face with smiling eyes',
    '😇': 'smiling face with halo',
    '🥰': 'smiling face with hearts',
    '😘': 'face blowing a kiss',
    '😋': 'face savoring food',
    '😜': 'winking face with tongue',
    '🤪': 'zany face',
    '😎': 'smiling face with sunglasses',
    '🤩': 'star-struck',
    '🥳': 'partying face',
    '🤗': 'hugging face',

    # Sad and Negative Faces
    '😟': 'worried face',
    '😕': 'confused face',
    '🙁': 'slightly frowning face',
    '☹️': 'frowning face',
    '😔': 'pensive face',
    '😖': 'confounded face',
    '😩': 'weary face',
    '😫': 'tired',
    '🥺': 'pleading face',
    '😢': 'crying face',
    '😭': 'loudly crying face',
    '🤧': 'sneezing face',
    '😨': 'fearful face',
    '😱': 'face screaming in fear',
    '😰': 'anxious face with sweat',
    '😥': 'sad but relieved face',
    '😡': 'pouting face',
    '🤬': 'face with symbols on mouth',
    '😠': 'angry face',
    '😤': 'face with steam from nose',

    # Neutral and Unsure Faces
    '😶': 'face without mouth',
    '😐': 'neutral face',
    '😑': 'expressionless face',
    '🤔': 'thinking face',
    '🤫': 'shushing face',
    '🤐': 'zipper-mouth face',
    '🤨': 'face with raised eyebrow',
    '😏': 'smirking face',
    '🙄': 'face with rolling eyes',
    '😬': 'grimacing face',
    '🤥': 'lying face',

    # Hand Gestures
    '👍': 'thumbs up',
    '👎': 'thumbs down',
    '👏': 'clapping hands',
    '🙏': 'folded hands',
    '✌️': 'victory hand',
    '🤞': 'crossed fingers',
    '💪': 'flexed biceps',
    '🤝': 'handshake',
    '🖕': 'middle finger',

    # Hearts and Symbols
    '❤️': 'red heart',
    '🧡': 'orange heart',
    '💛': 'yellow heart',
    '💚': 'green heart',
    '💙': 'blue heart',
    '💜': 'purple heart',
    '💔': 'broken heart',
    '💯': 'hundred points symbol',
    '🔥': 'fire',
    '💩': 'pile of poo',
    '💀': 'skull',
    '👻': 'ghost',
    '😈': 'smiling face with horns',

    # Miscellaneous
    '🤡': 'clown face',
    '👹': 'ogre',
    '👺': 'goblin',
    '👽': 'alien',
    '🤖': 'robot face',
}

def replace_emojis(text):
    """Replaces emojis with their textual descriptions."""
    for emoji, meaning in EMOJI_DICT.items():
        text = text.replace(emoji, f' {meaning} ')
    return text

def load_slang_from_db():
    """Loads all slang terms from the database into a dictionary."""
    slang_dict = {}
    try:
        # Fetch all slang records from the database
        slang_records = slang.objects.all()
        for record in slang_records:
            # Use regex to match whole words only
            pattern = r'\b' + re.escape(record.slangText) + r'\b'
            slang_dict[pattern] = record.meaning
    except Exception as e:
        print(f"Error loading slang from database: {e}")
        return None
    return slang_dict

def replace_slang(text, slang_dict):
    """Replaces slang words with their meanings using a dictionary."""
    if not slang_dict:
        return text
    
    # Sort by key length descending to avoid issues with substrings (e.g., "gonna" before "gon")
    sorted_slang = sorted(slang_dict.items(), key=lambda item: len(item[0]), reverse=True)
    
    for pattern, meaning in sorted_slang:
        # Use re.sub to replace all occurrences based on the pattern
        text = re.sub(pattern, f' {meaning} ', text, flags=re.IGNORECASE)
        
    return text.strip()