import csv
import sys
import json
import re
import ollama
import chromadb
from langdetect import detect
import reporter as jr

CLIENT = chromadb.Client()
COLLECTION = CLIENT.create_collection(name="docs")
JOBS_CSV_PATH = "./inputs/jobs_25-03-03_09-42.csv"
PROFILE_PATH = "./inputs/profile.txt"
EMBEDDINGS_MODEL = "nomic-embed-text"  # Model for generating embeddings
MODEL = "llama3.2"  # Language model to query
N_RESULTS = 25  # Number of search results to include
LANG = "en" # language of jobs to search for
CURATION_PROMPT = (
    """
    You are a job hiring assistant.
    You will receive a candidate profile and a job description
    Your task is to answer the following questions:
    On a scale of 0 to 5, how suitable is the candidate for the job, with 5 being most suitable.
    What are the main tasks of the job?
    What area is this job in?
    How well do the candidate's skills and interests match the description?
    Are there skills that the candidate lacks?
    Is the candidate suitably qualified?
    Is the candidate a good fit for this role?
    "Answer concisely using an objective tone.
    "Output your answer as json with the following format:
    { 
        "Suitability": <int[0-5],
        "Job_summary": "<string>",
        "Match_summary": "<string>"
    }
    The Job_summary and Match_summary fields should be no longer than one paragraph each.
    Output only valid json with double quotation marks around fields and values.
    Be sure that the field names exactly match the description: Suitability, Job_summary, Match_summary.
    Output only valid json. Do not add anything outside the json.
    Do not add a note or explanation.
    """
)


def create_embedding(text):
    """
    Generate an embedding for a given text using the specified model.

    Args:
        text (str): The text to embed.

    Returns:
        list: The embedding vector for the input text.
    """
    text = ' '.join(re.sub(r'[^\x00-\x7F]+', '', text).split())
    response = ollama.embeddings(model=EMBEDDINGS_MODEL, prompt=text)
    return response["embedding"]


def store_embeddings(ids, embeddings, documents):
    """
    Store embeddings in the ChromaDB collection.

    Args:
        ids (list): List of unique IDs for the documents.
        embeddings (list): List of embedding vectors.
        documents (list): List of corresponding documents.
    """
    try: 
        COLLECTION.add(ids=ids, embeddings=embeddings, documents=documents)
        print(f"Embeddings stored with Ids: {ids}")
        return True
    except Exception:
        print("Failed to store embeddings")
        return False


def query_embedding(embedding, n_results=N_RESULTS):
    """
    Query the database for the most relevant documents to a given embedding.

    Args:
        embedding (list): The embedding vector to query.
        n_results (int): The number of top results to retrieve.

    Returns:
        dict: Query results containing relevant document IDs and metadata.
    """
    results = COLLECTION.query(query_embeddings=embedding, n_results=n_results)
    return results


def remove_duplicates(lst, key):
    """
    Removes duplicate dictionaries from a list based on a specified key.

    Args:
        lst (list of dict): The list of dictionaries.
        key (str): The key to check for uniqueness.

    Returns:
        list of dict: A list with duplicates removed.
    """
    seen = set()
    unique_list = []
    
    for d in lst:
        value = d.get(key)
        if value not in seen:
            seen.add(value)
            unique_list.append(d)
    
    return unique_list


def remove_exact_duplicates(lst):
    """
    Removes duplicate dictionaries from a list, considering all fields.

    Args:
        lst (list of dict): The list of dictionaries.

    Returns:
        list of dict: A list with exact duplicates removed.
    """
    unique_list = []
    seen = set()

    for d in lst:
        tuple_repr = tuple(sorted(d.items()))  # Convert dict to a hashable form
        if tuple_repr not in seen:
            seen.add(tuple_repr)
            unique_list.append(d)

    return unique_list


def embed_jobs(jobs):
    """
    Embed a list of jobs and store them in the embeddings database.

    Args:
        job (list): List of dictionaries with "document" and "uri" keys.
    """
    for job in jobs:
        if detect(job['description']) == LANG:
            print(job['title'])
            job_text = job['title'] + job['description'] + job['company']
            embedding = create_embedding(job_text)
            store_embeddings(
                ids = [job['id']],
                embeddings = [embedding],
                documents = [job['description']],
            )


def process_jobs_csv(file_path):
    """
    Reads a CSV file containing job data and creates a list of dicts.
    Each job is assigned a unique ID based on its row position in the CSV.
    """
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        jobs = []
        for job_id, row in enumerate(reader, start=1):
            job = {
                'id': str(job_id),
                'title': row.get('title', ''),
                'url': row.get('url', ''),
                'location': row.get('location', ''),
                'date': row.get('date', ''),
                'applicants': row.get('applicants', ''),
                'description': row.get('description', ''),
                'company': row.get('company', '')
            }
            jobs.append(job)
        return jobs


def get_profile(file_path):
    """
    Open the person profile file and return the string
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


# Create embeddings of the jobs
jobs_list = process_jobs_csv(JOBS_CSV_PATH)
jobs_list = remove_exact_duplicates(jobs_list)

# for job in jobs_list:
#     job['summary'] = "Here is the summary of the job"

# html = jr.generate_job_listings(jobs_list)
# jr.save_report(html, "./")
# sys.exit()

embed_jobs(jobs_list)
# print(jobs_list)

# Create string and embedding of the profile
profile = get_profile(PROFILE_PATH)
profile_embedding = create_embedding(profile)

# Compare profile to jobs to get relevant jobs
relevant_jobs = query_embedding(profile_embedding, n_results=N_RESULTS)

# Loop through the relevant jobs
# get their info from the original jobs list
final_jobs = [] # jobs after AI curation
print(relevant_jobs['ids'][0])
for Id in relevant_jobs['ids'][0]:
    print(f"\nJOB: {Id}\n")
    current_job = next((d for d in jobs_list if d.get("id") == Id), None)
    print(current_job['title'])
    
    # Query the language model
    prompt = f"{CURATION_PROMPT} The profile is:{profile}. The job description is: {current_job['description']}"
    print("\nQuerying Ollama...\n")
    summary = ollama.generate(model=MODEL, prompt=prompt, stream=False)
    print(summary['response'])
    try:
        response = json.loads(re.sub(r"^[^{]*|[^}]*$", "", summary['response']))
        print(response)
        if int(response['Suitability']) > 0:
            current_job['summary'] = response['Job_summary']
            current_job['match'] = response['Match_summary']
            current_job['suitability'] = str(response['Suitability'])
            final_jobs.append(current_job)
    except Exception as e:
        print(e)

# sort the jobs by suitability and create a report
final_jobs = sorted(final_jobs, key=lambda d: d.get("suitability", 2), reverse=True)
html = jr.generate_job_listings(final_jobs)
jr.save_report(html, "./")
