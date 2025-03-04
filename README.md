# ai-job-match
Match jobs from a csv to a profile using local AI

Uses a RAG workflow. Job descriptions are embedded. 
The top N matching jobs from the embeddings db are sent to Ollama. 
The LLM gives a suitability score based on how well the profile matches the description.
The LLM summarises the job and its match to the profile.
An html report is generated with the top N matching jobs.

The .csv file of jobs should have the following fields: 
- id, title, url, location, date, applicants, description, company

This is the format output by the linkedin-scraper script.

The profile should be a .txt file containing unstructured CV info.

