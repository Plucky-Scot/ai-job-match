"""
Module: jobs_reporter

This module provides functionality for generating reports of job listings.
It includes a function to generate an HTML page from a list of job postings.
"""

from datetime import datetime

def generate_job_listings(jobs):
    """
    Generates an HTML page containing a list of job postings.
    
    Args:
        jobs (list of dict): A list of job dictionaries, each containing the fields:
            - title (str): The job title
            - location (str): The job location
            - date (str): The posting date
            - applicants (int): Number of applicants
            - summary (str): A brief summary of the job
            - match (str): How the candidate profile matches the job
            - suitability (str): Score out of 5 with 5 most suitable
            - description (str): A detailed job description
            - company (str): The company name
    
    Returns:
        str: A string containing the generated HTML page.
    """
    html_template = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Job Listings</title>
            <style>
                body { font-family: sans-serif; background-color: #f8f8f8; margin: 20px; }
                ul { list-style-type: none; padding: 0; }
                .job { background: white; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
                h2 a { text-decoration: none; color: #0073e6; }
                h2 a:hover { text-decoration: underline; }
                .info-container { font-size: 14px; color: #555; font-weight: bold; display: flex; gap: 15px; }
                .toggle { cursor: pointer; color: #0073e6; display: block; margin-top: 5px; }
                .hidden { display: none; }
            </style>
        </head>
        <body>
            <h1>Job Listings</h1>
            <ul>
        """

    job_items = """
        """.join(
        f'''<li class="job">
            <h2 class="title"><a href="{job['url']}">{job['title']}</a></h2>
            <div class="info-container">
                <span class="info location">Location: {job['location']}</span>
                <span class="info posting-date">Posted: {job['date']}</span>
                <span class="info applicants">Applicants: {job['applicants']}</span>
            </div>
            <p class="summary">Suitability score: {job['suitability']}</p>
            <p class="summary">Job summary: {job['summary']}</p>
            <p class="summary">Match summary: {job['match']}</p>
            
            <span class="toggle" onclick="toggleSection(this)">Show Description</span>
            <p class="hidden description">{job['description']}</p>
            
            <span class="toggle" onclick="toggleSection(this)">Show Company</span>
            <p class="hidden company">{job['company']}</p>
        </li>'''
        for job in jobs
    )

    html_template += job_items
    html_template += """
            </ul>
            <script>
                function toggleSection(element) {
                    let section = element.nextElementSibling;
                    if (section.classList.contains('hidden')) {
                        section.classList.remove('hidden');
                        element.textContent = element.textContent.replace("Show", "Hide");
                    } else {
                        section.classList.add('hidden');
                        element.textContent = element.textContent.replace("Hide", "Show");
                    }
                }
            </script>
        </body>
        </html>
    """
    return html_template

def save_report(html_text, path_base):
    """
    Saves a generated html report to an html file
    The file will be saved with the current date in the title

    Args:
        html_text (str): the html page to write
        path_base (str): the base of the path to write the file to

    Returns: bool 
    """
    current_date = datetime.today().strftime('%Y-%m-%d')
    file_path = f"{path_base}/jobs_report_{current_date}"
    try:
        with open(file_path, 'w', encoding='utf8') as file:
            file.write(html_text)
        return True
    except Exception:
        return False
