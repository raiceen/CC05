import requests
import os
import sys


def reload_app():
    username = os.getenv('PYTHONANYWHERE_USERNAME')
    token = os.getenv('PYTHONANYWHERE_TOKEN')

    if not username or not token:
        print("Error: Missing PythonAnywhere credentials")
        sys.exit(1)

    domain = f"{username}.pythonanywhere.com"
    url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/"

    try:
        response = requests.post(url, headers={'Authorization': f'Token {token}'})
        response.raise_for_status()
        print(f"Success: App reloaded (Status {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to reload app - {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    reload_app()