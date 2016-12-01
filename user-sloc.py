"""
Python Script to count all sloc for a github user

need cloc-git.sh in the same folder and cloc (count lines of code)
see http://stackoverflow.com/questions/26881441/can-you-get-the-number-of-lines-of-code-from-a-github-repository

requires:
- PyGithub library https://github.com/PyGithub/PyGithub

"""
import sys
import subprocess
import getpass                                                  # read pw without echo
import sqlite3
import json
from github import Github
from github import BadCredentialsException

def get_repos(username, password):
    """Returns list of github repo names username/reponame"""
    github_object = Github(username, password)
    return [repo.full_name for repo in github_object.get_user().get_repos()]

def run_cloc_script(url):
    """Call shell script to clone repo and count sloc"""
    subprocess.call(['bash', 'cloc-git-test.sh', url])


def initalize_db():
    """Initalize db to have a single table Languages with no entries"""
    con = sqlite3.connect('db')
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS LANGUAGES")
    cur.executescript("""
                    CREATE TABLE LANGUAGES
                        (language TEXT,
                        sloc_count INTEGER,
                        no_files INTEGER,
                        PRIMARY KEY(language))
                    """)    # can be done with cur.execute without formatting and string contact, but this looks nicer
    return cur, con

def update_db(cur, con):
    """Read json shell script writes to and updates db"""
    # cur.execute("INSERT INTO LANGUAGES VALUES ('Python', 69, 1)")
    # con.commit()    # need this to commit insert
    with open('data.json') as json_data:
        data = json.load(json_data)
        for language in data:
            if language not in ['header','SUM']:
                print('a language: ' + str(language))
                language_match = language
                cur.execute("SELECT language, sloc_count, no_files FROM Languages WHERE language=?", (language_match,))    # , means there are other things after this entry
                result = cur.fetchall()
                # gives back a row's data if something, else empty array
                print(result)
                if result: # row in table, just updated
                    print("Updating db")
                    sloc = result[0][1]
                    no_files = result[0][2]
                    sloc = data[language_match]["code"] + sloc
                    no_files += data[language_match]["nFiles"]
                    cur.execute("UPDATE Languages SET sloc_count=?, no_files=? WHERE language=?", (sloc, no_files, language_match))
                    con.commit()    # need this to see changeS!
                else:   # insert
                # if in sql table, just update
                    print("Inserting into db")
                    sloc = data[language_match]["code"]
                    no_files = data[language_match]["nFiles"]
                    cur.execute("INSERT INTO Languages Values (?,?,?)", (language_match,sloc, no_files))
                    con.commit()
                # else if not in sql table, create row



def count_user_sloc(username, password):
    user_repos = get_repos(username, password)                  # all repos the user owns/contributed to
    base_url = "https://github.com/"
    cur, con = initalize_db()
    for repo_name in user_repos:
        url = base_url + repo_name + ".git"
        run_cloc_script(url)
        update_db(cur, con)
    print("Finished processing repos...")
    print("Final SLOC Count")
    cur.execute("SELECT * FROM Languages")
    print(cur.fetchall())



if __name__ == "__main__":
    username = sys.argv[1]
    password = getpass.getpass()
    try:
        count_user_sloc(username, password)
    except BadCredentialsException:
        print("Invalid Credentials")
        sys.exit(0)
