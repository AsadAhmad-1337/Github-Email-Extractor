import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import sys
import requests
import re
from colorama import init, Fore, Style
from multiprocessing import Pool

init()

try:
    input = raw_input  
except NameError:
    pass  

def get_user_input(prompt, color):
    return input(color + prompt + Style.RESET_ALL)

def fetch_all_repos(username):
    repos = []
    page = 1
    while True:
        url = "https://api.github.com/users/{}/repos?page={}&per_page=100".format(username, page)
        response = requests.get(url)
        if response.status_code != 200:
            print(Fore.RED + "Error: Unable to fetch data. Status code: {}".format(response.status_code) + Style.RESET_ALL)
            sys.exit(1)
        data = response.json()
        if not data:
            break
        repos.extend([repo['name'] for repo in data])
        page += 1
    return repos

def fetch_commit_data(repo):
    username, repo_name = repo
    url = "https://api.github.com/repos/{}/{}/commits".format(username, repo_name)
    response = requests.get(url)
    if response.status_code != 200:
        print(Fore.YELLOW + "Warning: Unable to fetch data for {}. Status code: {}".format(repo_name, response.status_code) + Style.RESET_ALL)
        return None
    return response.text

def extract_emails(text):
    email_regex = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    return re.findall(email_regex, text)

def filter_emails(emails):
    filtered_emails = set()
    for email in emails:
        if not email.endswith(('@github.com', '@users.noreply.github.com', '@nowhere.local', '@nowhere.com')):
            filtered_emails.add(email)
    return list(filtered_emails)

def print_rainbow(text):
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    rainbow_text = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        rainbow_text += color + char
    print(rainbow_text + Style.RESET_ALL)

def print_bordered_box(text, border_color=Fore.YELLOW):
    lines = text.splitlines()
    max_length = max(len(line) for line in lines)
    border = border_color + '*' + '*' * (max_length + 0) + '*' + Style.RESET_ALL
    print(border)
    for line in lines:
        print(border_color + ' ' + line.ljust(max_length) + ' ' + Style.RESET_ALL)
    print(border)

def save_results_to_file(username, emails, filename):
    with open(filename, 'w') as file:
        file.write("GitHub Profile: {}\n".format(username))
        file.write("Extracted Emails:\n")
        for email in emails:
            file.write("{}\n".format(email))
    print(Fore.GREEN + "Results saved to {}".format(filename) + Style.RESET_ALL)

def main():
    while True:
        welcome_message = Fore.YELLOW + """
   ____ _ _   _   _       _       _____                 _ _   _____      _                  _             
  / ___(_) |_| | | |_   _| |__   | ____|_ __ ___   __ _(_) | | ____|_  _| |_ _ __ __ _  ___| |_ ___  _ __ 
 | |  _| | __| |_| | | | | '_ \  |  _| | '_ ` _ \ / _` | | | |  _| \ \/ / __| '__/ _` |/ __| __/ _ \| '__|
 | |_| | | |_|  _  | |_| | |_) | | |___| | | | | | (_| | | | | |___ >  <| |_| | | (_| | (__| || (_) | |   
  \____|_|\__|_| |_|\__,_|_.__/  |_____|_| |_| |_|\__,_|_|_| |_____/_/\_\\__ |_|  \__,_|\___|\__\___/|_| 
                                                                                             Asad Ahmad
        """ + Style.RESET_ALL
        print(welcome_message)

        username = get_user_input("Enter GitHub profile name: ", Fore.CYAN)
        repos = fetch_all_repos(username)
        if not repos:
            print(Fore.RED + "Nothing found for user {}.".format(username) + Style.RESET_ALL)
            continue

        all_emails = set()
        total_repos = len(repos)
        pool = Pool(processes=10)
        try:
            repo_args = [(username, repo) for repo in repos]
            for i, commit_data in enumerate(pool.imap(fetch_commit_data, repo_args), 1):
                print(Fore.MAGENTA + "Searching" + Style.RESET_ALL)
                if commit_data:
                    emails = extract_emails(commit_data)
                    unique_emails = filter_emails(emails)
                    all_emails.update(unique_emails)
        finally:
            pool.close()
            pool.join()

        print_rainbow("\nEMAILS:")
        email_text = "\n".join(Fore.GREEN + email + Style.RESET_ALL for email in all_emails)
        print_bordered_box(email_text, border_color=Fore.YELLOW)

        save_option = get_user_input("Do you want to save the results to a file? (y/n): ", Fore.CYAN).strip().lower()
        if save_option == 'y':
            filename = get_user_input("Enter the filename to save results (e.g., results.txt): ", Fore.CYAN).strip()
            save_results_to_file(username, all_emails, filename)

        search_again = get_user_input("Do you want to search another profile? (y/n): ", Fore.CYAN).strip().lower()
        if search_again != 'y':
            print(Fore.YELLOW + "Thank you for using the GitHub Email Extractor. Goodbye!" + Style.RESET_ALL)
            break

if __name__ == "__main__":
    main()
