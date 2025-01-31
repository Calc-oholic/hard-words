from flask import Flask, render_template, request, redirect, url_for, send_file
import random
from gtts import gTTS
import os
import tempfile
import io
import time

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Load word list
def load_word_list(filename):
    directory_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(directory_path, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"File '{filename}' not found in '{directory_path}'.")
        return []
    except IOError as e:
        print(f"Error reading file '{filename}': {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

current_word_idx = 0
main_contest_word_IDS = []
main_contest_words = []
wrong_words = []


# Select words for the contest
def select_words(word_list, word_list_IDS):
    selected_words = []
    for id in word_list_IDS:
        selected_words.append(word_list[id-1])
    return selected_words

def rng_word_ids(start_index, end_index, num_words):
    if 1 <= start_index <= end_index <= 1500:
        selected_words = [*range(start_index, end_index+1)]
        random.shuffle(selected_words)
        return selected_words[:num_words]
    else:
        return []

# Generate and play word pronunciation
# def generate_and_play_word(word):
#     tts = gTTS(text=word, lang='en')
#     current_time = int(time.time())
#     temp_file = tempfile.NamedTemporaryFile(suffix=f"_{word}_{current_time}.mp3", delete=False)
#     temp_file.close()
#     tts.save(temp_file.name)
#     audio_data = open(temp_file.name, 'rb').read()
#     try:
#         os.remove(temp_file.name)
#     except PermissionError:
#         pass
#     return audio_data

# Generate and play word pronunciation
def generate_and_play_word_alternate(word):
    # tts = gTTS(text=word, lang='en', tld='com.ng')
    tts = gTTS(text=word, lang='en')
    current_time = int(time.time())
    temp_file = tempfile.NamedTemporaryFile(suffix=f"_{word}_{current_time}.mp3", delete=False)
    temp_file.close()
    tts.save(temp_file.name)

    audio_data = open(temp_file.name, 'rb').read()

    try:
        os.remove(temp_file.name)
    except PermissionError:
        pass

    return audio_data


# Check user input against the correct word
def check_word(user_input):
    global current_word_idx, main_contest_words, main_contest_word_IDS

    if current_word_idx < len(main_contest_words):
      
        # check = main_contest_words[current_word_idx]
        # startPare = check.find('(')
        # checkFix = check
        # if startPare > 0:
        #     checkFix = check[0:startPare-1]
        # else:
        #     checkFix = check
        checkFix = main_contest_words[current_word_idx].split("(")[0].strip()
        
        correct_words = [word.strip() for word in checkFix.split(",")]
        
        user_inputs = [input.strip() for input in user_input.split(",")]

        if all(input in correct_words for input in user_inputs) and all(answer in user_inputs for answer in correct_words):
            return True
        else:
            feedback = f"{current_word_idx}/{len(main_contest_words)}: {main_contest_word_IDS[current_word_idx]} : Incorrect. Correct answer: '{', '.join(correct_words)}'"
            return feedback
    return False

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def index():
    global current_word_idx, main_contest_words, main_contest_word_IDS, wrong_words

    file_names = ["2024.txt", "2023.txt", "2022.txt", "2021.txt", "2020.txt", "2019.txt"]

    if request.method == "POST":
        filename = request.form["filename"]
        start_index = int(request.form["start_index"])
        end_index = int(request.form["end_index"])
        num_words = int(request.form["num_words"])
        word_list = load_word_list(filename)

        if not word_list:
            return render_template("index.html", file_names=file_names, error_message=f"Failed to load word list from '{filename}'.")

        main_contest_word_IDS = rng_word_ids(start_index, end_index, num_words)
        # main_contest_word_IDS = (296, 326, 257, 280, 344, 344, 327, 370, 320, 388, 359, 290, 226, 226, 323, 314, 223, 235, 334, 284, 373, 311, 397, 203, 204, 300, 220, 305, 202, 276, 242, 384, 378, 231, 338, 234, 328, 297, 240, 299, 229, 229, 355, 274,479, 474, 492, 482, 459, 407, 411, 475, 436, 488, 450, 449, 476, 421, 444, 434, 422, 581, 506, 533, 558, 576, 550, 573, 563, 593, 584, 517, 630, 644, 602, 652, 691, 686, 619, 677, 675, 642, 621, 651, 671, 661, 654, 700, 640, 650, 618, 672)
        main_contest_words = select_words(word_list, main_contest_word_IDS)
        
        if not main_contest_words or not main_contest_word_IDS:
            return render_template("index.html", file_names=file_names, error_message=f"Failed to select words from '{filename}'. Please check your indices.")

        current_word_idx = 0
        wrong_words = []

        audio_data = get_and_play_word(main_contest_word_IDS[current_word_idx])
        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None, audio_data=audio_data, file_names=file_names)

    return render_template("index.html", file_names=file_names)

# Inside the /contest route
@app.route("/contest", methods=["GET", "POST"])
def contest():
    global current_word_idx, main_contest_words, wrong_words, main_contest_word_IDS

    if request.method == "POST": # post (user has inputted a guess)
        user_input = request.form["user_input"]
        feedback = check_word(user_input)

        if feedback == True:
            current_word_idx += 1

            if current_word_idx < len(main_contest_words):
                audio_data = get_and_play_word(main_contest_word_IDS[current_word_idx])
                timestamp = int(time.time())
                audio_url = f"/pronounce?timestamp={timestamp}"

                return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data, audio_url=audio_url, wrong_words=wrong_words)

        else:
            wrong_words.append((main_contest_word_IDS[current_word_idx], main_contest_words[current_word_idx], user_input)) # erm what the sigma, why is this giving an error???
        if current_word_idx < len(main_contest_words):
                
            audio_data = get_and_play_word(main_contest_word_IDS[current_word_idx])
            timestamp = int(time.time())
            audio_url = f"/pronounce?timestamp={timestamp}"

            return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data, audio_url=audio_url, wrong_words=wrong_words)
        else:
            return redirect(url_for("index"))

    if current_word_idx < len(main_contest_words): # get (first time seeing a word)
        audio_data = get_and_play_word(main_contest_word_IDS[current_word_idx])
        timestamp = int(time.time())
        audio_url = f"/pronounce?timestamp={timestamp}"

        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None, audio_data=audio_data, audio_url=audio_url, wrong_words=wrong_words)
    else:
        return redirect(url_for("index"))

# Get stored wav file
def get_and_play_word(wordNum):

    directory_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(directory_path, "audiofiles")
    if 0 < wordNum < 501:
        subfolder_path = os.path.join(folder_path, "500")
    elif 500 < wordNum < 1001:
        subfolder_path = os.path.join(folder_path, "1000")
    elif 1000 < wordNum < 1501:
        subfolder_path = os.path.join(folder_path, "1500")
    file_path = os.path.join(subfolder_path, str(wordNum) + ".mp3")
    
    error_file_path = os.path.join(folder_path, "noxious.mp3")
    
    try:
        audio_data = open(file_path, 'rb').read()
    except Exception:
        audio_data = open(error_file_path, 'rb').read()

    # if random.random() < .003:
    #     audio_data = open(error_file_path, 'rb').read()
        # We're pranking Aarush
    

    return audio_data



@app.route("/pronounce")
def pronounce_word():
    global current_word_idx, main_contest_words, main_contest_word_IDS

    if current_word_idx < len(main_contest_words):
        # word = main_contest_words[current_word_idx]


        # audio_data = get_and_play_word(word)
        
        audio_data = get_and_play_word(main_contest_word_IDS[current_word_idx])


        # unique_id = int(time.time())
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg', as_attachment=True, download_name=f'pronunciation_{current_word_idx}.mp3')
    else:
        return send_file(io.BytesIO(b""), mimetype='audio/mpeg', as_attachment=True, download_name='pronunciation_placeholder.mp3')

@app.route("/altpronounce")
def alt_pronounce_word():
    global current_word_idx, main_contest_words

    if current_word_idx < len(main_contest_words):
        word = main_contest_words[current_word_idx]
        audio_data = generate_and_play_word_alternate(word)
        unique_id = int(time.time())
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg', as_attachment=True, download_name=f'pronunciation_{unique_id}.mp3')
    else:
        return send_file(io.BytesIO(b""), mimetype='audio/mpeg', as_attachment=True, download_name='pronunciation_placeholder.mp3')

if __name__ == "__main__":
    app.run(debug=True)


# (599, 'incumbency', 'encumbency')
# (538, 'heavy-handed', 'heavy-hande')
# (561, 'homocentric', 'homicentric')
# (584, 'immunocompromised', 'immunocomprimised')
# (517, 'gramineous', 'graminious')
# (576, 'idolatry', 'idolotry')
