from flask import Flask, request, jsonify, render_template
import json
from textblob import Word
from difflib import get_close_matches
import re


app = Flask(__name__)

with open('disease.json') as f:
    diseases_data = json.load(f)

symptoms_list = list(diseases_data.keys())
diseases_list = [diseases_data[key]["disease"] for key in symptoms_list]

def split_and_correct_text(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([a-z])([0-9])", r"\1 \2", text)
    text = re.sub(r"([0-9])([a-z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])(\s+)([A-Za-z])", r"\1 \3", text)
    return text

def correct_spelling(text):
    words = text.split()
    corrected_words = []
    for word in words:
        corrected_word = Word(word).correct()
        corrected_words.append(corrected_word)
    return ' '.join(corrected_words)

def find_close_matches(input_symptoms):
    words = input_symptoms.split()
    matches = []
    for word in words:
        close_match = get_close_matches(word, symptoms_list, n=1, cutoff=0.8)
        if close_match:
            matches.append(close_match[0])
        else:
            matches.append(word)
    return ' '.join(matches)

def search_disease_by_symptoms(symptom):
    found_diseases = []
    for disease_symptoms, disease_info in diseases_data.items():
        if re.search(r'\b' + re.escape(symptom.lower()) + r'\b', disease_symptoms.lower()):
            found_diseases.append(disease_info)
    return found_diseases

def search_disease_by_name(disease_name):
    for disease_symptoms, disease_info in diseases_data.items():
        if disease_info["disease"].lower() == disease_name.lower():
            return disease_info
    return None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/check_symptoms', methods=['POST'])
def check_symptoms():
    input_symptoms = request.form.get('symptoms', '')

    split_corrected_symptoms = split_and_correct_text(input_symptoms)
    corrected_symptoms = correct_spelling(split_corrected_symptoms)
    
    matched_symptoms = find_close_matches(corrected_symptoms)
    
    matching_diseases = search_disease_by_symptoms(matched_symptoms)
    
    if not matching_diseases:
        best_match = {
            "disease": "No disease found",
            "description": "The given symptoms do not match any known disease.",
            "medicine": "N/A"
        }
        similar_diseases_message = [{"disease": "No similar diseases found", "description": "There are no similar diseases for the given symptoms.", "medicine": "N/A"}]
    else:
        best_match = matching_diseases[0]
        similar_diseases_message = [{"disease": disease["disease"], "description": disease["description"], "medicine": disease["medicine"]} for disease in matching_diseases if disease["disease"] != best_match["disease"]]
    
    result = {
        "disease": best_match["disease"],
        "description": best_match["description"],
        "medicine": best_match["medicine"],
        "similar_diseases": similar_diseases_message if similar_diseases_message else [{"disease": "No similar diseases found", "description": "There are no similar diseases for the given symptoms.", "medicine": "N/A"}]
    }
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    return render_template('index.html', result=result)

@app.route('/api/search_disease', methods=['POST'])
def search_disease():
    disease_name = request.form.get('disease_name', '').strip()
    
    if not disease_name:
        return jsonify({"error": "Please provide a disease name."}), 400
    
    disease_info = search_disease_by_name(disease_name)
    
    if not disease_info:
        result = {
            "disease": "No disease found",
            "description": "The provided disease name does not match any known disease.",
            "medicine": "N/A"
        }
    else:
        result = {
            "disease": disease_info["disease"],
            "description": disease_info["description"],
            "medicine": disease_info["medicine"]
        }
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    return render_template('index.html', disease_result=result)

@app.route('/api/symptom_autocomplete', methods=['GET'])
def symptom_autocomplete():
    query = request.args.get('query', '').lower()
    matches = [symptom for symptom in symptoms_list if query in symptom.lower()]
    return jsonify(matches)

if __name__ == '__main__':
    app.run(debug=True)
