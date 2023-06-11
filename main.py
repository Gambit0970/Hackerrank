#!/usr/bin/python3
import time
import base64
import json
import pickle
import argparse
import requests
import os
from bs4 import BeautifulSoup

#added a load of the Processed challenges
def getProcd():
    # this will create an empty file first time through.
    if not os.path.exists("procd.txt"):
        file(filename, 'w').close()
    f = open("procd.txt", "r")
    d = f.read().splitlines()
    f.close()
    a = []
    a = sorted([int(j) for i in d for j in i.split(",") if j.strip() and int(j) not in a])
    return a

#added a save of the Processed challenges
def saveProcd(a):
    f = open("procd.txt","w")
    a.sort()
    f.writelines(",".join([str(_) for _ in a]))
    f.close()


procd = getProcd()

parser = argparse.ArgumentParser(
    description="Download all of the correct submission by a user on HackerRank. By @0xecho. Updated by @Gambit0970"
)
parser.add_argument(
    "uname", metavar="uname", help="Username of the HackerRank account"
)
parser.add_argument(
    "password", metavar="password", help="Password of the HackerRank account"
)

args = parser.parse_args()
UNAME = args.uname
PASSWORD = args.password

main_session = requests.Session()
main_session.headers[
    "User-Agent"
] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0"

response = main_session.get("http://www.hackerrank.com/auth/login")

text = BeautifulSoup(response.text, features="lxml")

csrf_tag = text.find("meta", {"id": "csrf-token"})

csrf_token = csrf_tag["content"]

main_session.headers["X-CSRF-Token"] = csrf_token

# changed username to uname to shorten the code for pulling the submissions
login_data = {
    "login": UNAME,
    "password": PASSWORD,
    "remember_me": False,
    "fallback": True,
}

response = main_session.post("https://www.hackerrank.com/auth/login", data=login_data)

response_data = json.loads(response.text)

assert response_data["status"], "[-] Login Failed \n Incorrect Username or Password"

print("[*] Login Successful")
print("[*] Getting Questions")

main_session.headers["X-CSRF-Token"] = response_data["csrf_token"]

question_models = []
cursor = ""
while True:
    resp = main_session.get(
        f"http://www.hackerrank.com/rest/hackers/{UNAME}/recent_challenges?limit=100&cursor={cursor}&response_version=v2"
    )
    resp_data = json.loads(resp.text)
    cursor = resp_data["cursor"]
    question_models.append(resp_data["models"])
    if resp_data["last_page"]:
        break

questions = []

for i in question_models:
    for j in i:
        questions.append(j)

submissions = []

print("[*] Getting Submissions")

for i in questions:
    resp = main_session.get(
        "https://www.hackerrank.com/rest/contests/master/challenges/{}/submissions/?offset=0&limit=1000".format(
            i["ch_slug"]
        )
    )
    resp_data = json.loads(resp.text)
    submissions.append(resp_data)

accepted_solutions = []

print("[*] Filtering Submissions")

for i in submissions:
    for j in i["models"]:
        # added a line to skip any that have been processed to speed things up
        if j["id"] not in procd:
            slug = j["challenge"]["slug"]
            if j["status"] == "Accepted":
                accepted_solutions.append((slug, j["id"]))
                break

temp_map = {}

EXTENSIONS = {
    "cpp": "cpp",
    "python3": "py",
    "python": "py",
    "pypy": "py",
    "bash": "sh",
}

print("[*] Saving Files")

for i in accepted_solutions:
    slug, ch_id = i
    rerun=True
    while rerun:
        resp = main_session.get(
            f"https://www.hackerrank.com/rest/contests/master/challenges/{slug}/submissions/{ch_id}"
        )
        resp_data = json.loads(resp.text)
        # kept crashing here as there were some returned without Language data - think they timed out
        # so looped any that error and save procd file to enable restart
        try:
            file_lang = resp_data["model"]["language"]
        except:
            print(f"Error getting data: {slug} {ch_id} {resp_data}")
            print("Sleeping for a 60 seconds!")
            saveProcd(procd)
            time.sleep(60)
        else:
            rerun=False
    file_lang = resp_data["model"]["language"]
    file_ext = EXTENSIONS.get(file_lang, file_lang)
    count = temp_map.get(slug, 0)
    
    #created a submissions folder with the ext from the pulled file
    path = "Submissions\\"+ file_ext + "\\"
    if not os.path.exists(path):
        print(f"Making path: {path}")
        os.mkdir(path)
    file_name = slug
    if count:
        file_name += "_" + str(count)
    file_name += "." + file_ext
    file_name = os.path.join(path,file_name)
    with open(file_name, "w") as f:
        f.write(resp_data["model"]["code"])
        
    #print(f"{file_name} created")  # uncomment this to print out a message when files are created.
    procd.append(ch_id)             # apped challenge id to procd list  

print("[+] Finished....")
print("[+] Enjoy")

# commit procd list
saveProcd(procd)
