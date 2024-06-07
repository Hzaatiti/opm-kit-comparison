import configparser
import requests
from fpdf import FPDF


# Function to read the GitHub configuration from the config.ini file
def get_github_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    github_config = {
        'token': config['github']['token'],
        'owner': config['github']['owner'],
        'repo': config['github']['repo']
    }
    return github_config


# Read the GraphQL query from an external file
with open('fetch_projects.graphql', 'r') as file:
    query = file.read()

# GitHub GraphQL API URL
GITHUB_GRAPHQL_API_URL = "https://api.github.com/graphql"

# Fetch the GitHub configuration from config.ini
github_config = get_github_config()
GITHUB_TOKEN = github_config['token']
OWNER = github_config['owner']
REPO = github_config['repo']


# Function to fetch project data from GitHub
def fetch_project_data(owner, repo):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    variables = {"owner": owner, "repo": repo}
    response = requests.post(GITHUB_GRAPHQL_API_URL, json={'query': query, 'variables': variables}, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        if 'data' in response_json:
            return response_json
        else:
            print("Error: 'data' key not found in the response")
            print("Response JSON:", response_json)
            return None
    else:
        print(f"Error: Request failed with status code {response.status_code}")
        print("Response:", response.text)
        return None


# Function to create a PDF from the project data
def create_pdf(project_data, output_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for project in project_data['data']['repository']['projectsV2']['nodes']:
        pdf.cell(200, 10, txt=f"Project: {project['title']}", ln=True, align='C')
        for item in project['items']['nodes']:
            content = item['content']
            if 'title' in content:
                pdf.cell(200, 10, txt=f"Title: {content['title']}", ln=True)
            if 'body' in content:
                pdf.multi_cell(0, 10, txt=f"Body: {content['body']}")
            pdf.cell(200, 10, txt=f"Created At: {content['createdAt']}", ln=True)
            pdf.cell(200, 10, txt=f"Updated At: {content['updatedAt']}", ln=True)
            pdf.cell(200, 10, txt=f"State: {content.get('state', 'N/A')}", ln=True)
            pdf.cell(200, 10, txt=f"Author: {content.get('author', {}).get('login', 'N/A')}", ln=True)
            assignees = ", ".join([assignee['login'] for assignee in content.get('assignees', {}).get('nodes', [])])
            pdf.cell(200, 10, txt=f"Assignees: {assignees}", ln=True)
            labels = ", ".join([label['name'] for label in content.get('labels', {}).get('nodes', [])])
            pdf.cell(200, 10, txt=f"Labels: {labels}", ln=True)

            # Add custom fields (status, budget, priority)
            for field in item.get('fieldValues', {}).get('nodes', []):
                field_name = 'Unknown Field'
                field_value = 'N/A'
                if '__typename' in field:
                    if field['__typename'] == 'ProjectV2ItemFieldTextValue':
                        field_name = 'Text'
                        field_value = field.get('text', 'N/A')
                    elif field['__typename'] == 'ProjectV2ItemFieldNumberValue':
                        field_name = 'Number'
                        field_value = field.get('number', 'N/A')
                    elif field['__typename'] == 'ProjectV2ItemFieldSingleSelectValue':
                        field_name = 'Single Select'
                        field_value = field.get('name', 'N/A')
                pdf.cell(200, 10, txt=f"{field_name}: {field_value}", ln=True)

            pdf.cell(200, 10, txt=" ", ln=True)  # Add a blank line for separation

    pdf.output(output_file)


# Example usage
if __name__ == "__main__":
    project_data = fetch_project_data(OWNER, REPO)
    if project_data:
        create_pdf(project_data, "project_tasks.pdf")
    else:
        print("Failed to fetch project data.")
