import re

import bs4
import requests
import yaml


def get_available_guids() -> dict:
    GUID_REGEX = r"(?:https:\/\/desktop\.docker\.com\/(?:\w*?\/){3})(\d+)"

    url = "https://docs.docker.com/desktop/release-notes"
    response = requests.get(url=url)
    content = bs4.BeautifulSoup(markup=response.text, features="lxml")

    guids = {}

    # Iteration on the different release notes
    titles = content.find_all("h2")
    for title in titles:
        # Each title of a release note is the version number
        version = title.text
        release_date = title.find_next_sibling().text

        # The blockquote contains the download links
        blockquote = title.find_next_sibling().find_next_sibling()
        if blockquote.name != "blockquote":
            continue

        # Finding the GUID
        guid = None
        for a in blockquote.find_all("a"):
            link = a.get("href")

            match = re.search(GUID_REGEX, link)
            if match:
                guid = int(match.groups()[0])
                break

        guids[version] = guid
    return guids


def update_guids_database(guids: dict):
    with open("guids.yaml", "r") as file:
        file_guids = yaml.load(file)

    file_guids.update(guids)

    with open("guids.yaml", "w") as file:
        yaml.dump(file_guids, file, default_flow_style=False, sort_keys=False)


def main():

    guids = get_available_guids()
    update_guids_database(guids=guids)


if __name__ == "__main__":
    main()
