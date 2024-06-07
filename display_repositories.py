import requests
import configparser
# GitHub personal access token
# Read GitHub token from configuration file
config = configparser.ConfigParser()
config.read('config.ini')
GITHUB_TOKEN = config['github']['token']


def fetch_user_repositories():
    url = 'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}'
    }
    params = {
        'visibility': 'all',
        'affiliation': 'owner,collaborator',
        'per_page': 100  # Fetch 100 repositories per page
    }

    repositories = []
    page = 1

    while True:
        response = requests.get(url, headers=headers, params={**params, 'page': page})
        if response.status_code != 200:
            print(f"Failed to fetch repositories, status code: {response.status_code}, response: {response.text}")
            break

        page_repositories = response.json()
        if not page_repositories:
            break

        repositories.extend(page_repositories)
        page += 1

    return repositories


def main():
    repositories = fetch_user_repositories()

    if not repositories:
        print("No repositories found or failed to fetch repositories.")
        return

    print("Repositories fetched:")
    for repo in repositories:
        print(repo['name'])


if __name__ == "__main__":
    main()
