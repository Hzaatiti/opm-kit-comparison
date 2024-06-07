import configparser
import requests
from fpdf import FPDF


# Function to read the GitHub configuration from the config.ini file
def get_github_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    if 'github' not in config:
        raise KeyError("Missing 'github' section in config file")
    required_keys = ['token', 'owner', 'repo']
    for key in required_keys:
        if key not in config['github']:
            raise KeyError(f"Missing '{key}' key in 'github' section of config file")
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
try:
    github_config = get_github_config()
    GITHUB_TOKEN = github_config['token']
    OWNER = github_config['owner']
    REPO = github_config['repo']
except KeyError as e:
    print(e)
    exit(1)


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

    # Define column widths
    col_widths = {
        'title': 60,
        'field': 40,
        'value': 60
    }

    # Add table header
    pdf.cell(col_widths['title'], 10, 'Title', 1, 0, 'C')
    pdf.cell(col_widths['field'], 10, 'Field', 1, 0, 'C')
    pdf.cell(col_widths['value'], 10, 'Value', 1, 1, 'C')

    for project in project_data['data']['repository']['projectsV2']['nodes']:
        # Add the project title
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Project: {project['title']}", 0, 1, 'C')
        pdf.ln(10)  # Add some space after the title

        # Set back to regular font for the rest of the document
        pdf.set_font("Arial", size=12)

        for item in project['items']['nodes']:
            content = item['content']
            title = content.get('title', 'N/A')
            pdf.multi_cell(col_widths['title'], 10, title, 1)
            y_start = pdf.get_y()
            x_start = pdf.get_x()

            # Iterate through content fields dynamically
            for key, value in content.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            field_name = f"{key.capitalize()} {sub_key.capitalize()}"
                            field_value = sub_value
                            pdf.set_xy(x_start + col_widths['title'], y_start)
                            pdf.multi_cell(col_widths['field'], 10, field_name, 1)
                            pdf.set_xy(x_start + col_widths['title'] + col_widths['field'], y_start)
                            pdf.multi_cell(col_widths['value'], 10, str(field_value), 1)
                            y_start = pdf.get_y()
                elif value:
                    field_name = key.capitalize()
                    field_value = value
                    pdf.set_xy(x_start + col_widths['title'], y_start)
                    pdf.multi_cell(col_widths['field'], 10, field_name, 1)
                    pdf.set_xy(x_start + col_widths['title'] + col_widths['field'], y_start)
                    pdf.multi_cell(col_widths['value'], 10, str(field_value), 1)
                    y_start = pdf.get_y()

            # Iterate through custom fields
            for field in item.get('fieldValues', {}).get('nodes', []):
                if '__typename' in field:
                    field_type = field['__typename']
                    field_name = field.get('field', {}).get('name', field_type)
                    field_value = field.get('text') or field.get('number') or field.get('name')
                    if field_value:
                        pdf.set_xy(x_start + col_widths['title'], y_start)
                        pdf.multi_cell(col_widths['field'], 10, field_name, 1)
                        pdf.set_xy(x_start + col_widths['title'] + col_widths['field'], y_start)
                        pdf.multi_cell(col_widths['value'], 10, str(field_value), 1)
                        y_start = pdf.get_y()

    pdf.output(output_file)


# Example usage
if __name__ == "__main__":
    project_data = fetch_project_data(OWNER, REPO)
    if project_data:
        create_pdf(project_data, "project_tasks.pdf")
    else:
        print("Failed to fetch project data.")
