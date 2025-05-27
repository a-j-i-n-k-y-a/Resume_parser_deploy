import os
import re
import fitz
import docx2txt
import pandas as pd
import unicodedata
import spacy
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

class ResumeParser:
    def __init__(self):
        # Load models
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    def read_file_safely(self, file_content: bytes, file_extension: str) -> str:
        encodings = ['utf-8', 'cp1252', 'ISO-8859-1', 'latin-1']
        text = ""
        
        if file_extension.lower() == 'pdf':
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
        elif file_extension.lower() in ['doc', 'docx']:
            # Save temporarily to process
            temp_path = "temp_file." + file_extension
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            text = docx2txt.process(temp_path)
            os.remove(temp_path)
        else:
            for enc in encodings:
                try:
                    text = file_content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
        
        return unicodedata.normalize("NFKD", text)

    def extract_info_hybrid(self, text: str) -> Dict:
        info = {}
        doc = self.spacy_nlp(text)
        bert_entities = self.ner_pipeline(text)

        # Name extraction
        name = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        if name:
            info['Name'] = name[0]
        else:
            bert_names = [ent['word'] for ent in bert_entities if ent['entity_group'] == 'PER']
            info['Name'] = " ".join(bert_names[:2]) if bert_names else "Not Found"

        # Email extraction
        email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
        info['Email'] = email[0] if email else "Not Found"

        # Education extraction
        edu_keywords = ['University', 'College', 'Institute', 'B.Tech', 'M.Tech', 'B.E.', 'M.E.', 'B.Sc', 'M.Sc']
        edu_ents = [ent['word'] for ent in bert_entities if ent['entity_group'] in ['ORG', 'MISC']]
        edu_found = [e for e in edu_ents if any(kw in e for kw in edu_keywords)]
        info['Education'] = edu_found[0] if edu_found else "Not Found"

        # Experience
        exp_matches = re.findall(r'(\d+\s+(?:months?|years?)\s+of\s+experience)', text, re.I)
        info['Experience'] = ", ".join(exp_matches) if exp_matches else "Not Found"

        return info

    def extract_skills_hybrid(self, jd_text: str, resume_text: str, threshold: float = 0.6) -> List[str]:
        jd_doc = self.spacy_nlp(jd_text)
        resume_doc = self.spacy_nlp(resume_text)

        jd_chunks = [chunk.text.lower() for chunk in jd_doc.noun_chunks]
        resume_chunks = [chunk.text.lower() for chunk in resume_doc.noun_chunks]

        jd_embeddings = self.embed_model.encode(jd_chunks)
        resume_embeddings = self.embed_model.encode(resume_chunks)

        matched_skills = []
        for idx, r_emb in enumerate(resume_embeddings):
            sims = cosine_similarity([r_emb], jd_embeddings)[0]
            if max(sims) > threshold:
                matched_skills.append(resume_chunks[idx])

        return list(set(matched_skills))

    def compute_similarity(self, text1: str, text2: str) -> float:
        emb1 = self.embed_model.encode([text1])[0]
        emb2 = self.embed_model.encode([text2])[0]
        return cosine_similarity([emb1], [emb2])[0][0]

    def parse_resumes(self, resumes: List[bytes], resume_extensions: List[str], job_description: bytes, jd_extension: str) -> pd.DataFrame:
        results = []
        jd_text = self.read_file_safely(job_description, jd_extension)

        for resume, ext in zip(resumes, resume_extensions):
            try:
                resume_text = self.read_file_safely(resume, ext)
                info = self.extract_info_hybrid(resume_text)
                skills = self.extract_skills_hybrid(jd_text, resume_text)
                similarity = self.compute_similarity(jd_text, resume_text)

                info['Skills'] = skills
                info['Similarity'] = similarity
                results.append(info)
            except Exception as e:
                print(f"Error processing resume: {e}")
                continue

        return pd.DataFrame(results)