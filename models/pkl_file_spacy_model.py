import spacy
import pickle

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Save the model to a pickle file
with open('models/spacy_model.pkl', 'wb') as f:
    pickle.dump(nlp, f)

print("SpaCy model saved successfully!")