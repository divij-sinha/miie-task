# %%
from requests import session
import dotenv
import json
import os
from bs4 import BeautifulSoup
import time

dotenv.load_dotenv()


def create_img_folder(school, img_size):
    img_folder = "imgs"
    folder_name = "_".join([school["name"], str(school["year"]), img_size])
    folder_name = "/".join([img_folder, folder_name])
    if not os.path.exists(img_folder):
        os.mkdir(img_folder)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    return folder_name


def save_data_dict(session, school, data_dict, img_size="largeSizeUrl"):
    folder_name = create_img_folder(school, img_size)
    for page in data_dict["yearbookPages"]:
        save_page(session, page["pageNumber"], page[img_size], img_size, folder_name)


def save_page(session, pg, img_url, img_size, folder_name):
    file_name = "_".join(["pg", str(pg), "img", img_size.replace("Url", "")])
    file_name = ".".join([file_name, "jpeg"])
    file_name = "/".join([folder_name, file_name])
    img = session.get(img_url)
    if img.status_code == 200:
        with open(file_name, "wb") as f:
            f.write(img.content)


def login(session, page_url):
    base_page = session.get(page_url)
    print(base_page.url, base_page)
    login_link_tag = [
        linktag
        for linktag in BeautifulSoup(base_page.content, features="lxml").findAll("a")
        if linktag.text == "Sign in"
    ]
    login_url = login_link_tag[0]["href"]
    login_page = session.get(login_url)
    print(login_page.url, login_page)
    login_soup = BeautifulSoup(login_page.content, features="lxml")
    csrf_token = login_soup.find("input", {"name": "_csrf"})["value"]
    form_data = {
        "_csrf": csrf_token,
        "emailOrRegId": os.environ["USER_ID"],
        "password": os.environ["USER_PW"],
        "rememberme": "yes",
        "successUrl": page_url,
        "g-recaptcha-response": "",
    }
    resp = session.post(login_url, data=form_data)
    print(resp.url, resp)
    return session


if __name__ == "__main__":
    page_url = (
        "https://www.classmates.com/yearbooks/Alameda-High-School/4182755124?page=1"
    )
    headers = {}
    headers[
        "User-Agent"
    ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    cur_session = session()
    cur_session.headers = headers
    cur_session = login(cur_session, page_url)

    # API CALL
    cur_session.headers["version"] = "v2"
    school = {"name": "Alameda High School", "year": "2010"}
    page = 0
    limit = 100
    while True:
        api_url = f"https://www.classmates.com/node/api/yearbookPages?limit={limit}&offset={page*limit}&yearbookId=4182755124&_={str(time.time_ns())}"
        api_resp = cur_session.get(api_url)
        if not api_resp.status_code == 200:
            break
        print(f"saving pages {(page*limit)+1} to {(page+1)*limit}")
        save_data_dict(cur_session, school, json.loads(api_resp.text))
        page += 1
# %%
