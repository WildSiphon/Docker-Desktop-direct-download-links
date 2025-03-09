#!/usr/bin/env python3

import argparse
import re

import bs4
import requests
import yaml

# TODO comment code
# TODO need clear and atomic function
# TODO consider and save also the release date
# TODO generate and update "utils/resources.yaml" only for new GUIDs found
# TODO add "synchronize" or "verify" function to test if the generated URLs point to a resource to download. Save the results in "DockerDesktop.yaml"


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


def update_guids_database():
    print("Fetching available GUIDs from Docker Desktop release notes page...", end=" ")
    guids = get_available_guids()
    print(f"{len(guids)} GUIDs found!")

    with open("utils/guids.yaml", "r") as file:
        updated_guids = yaml.load(file, yaml.FullLoader)

    print("Updating database...", end=" ")
    updated_guids.update(guids)

    with open("utils/guids.yaml", "w") as file:
        yaml.dump(updated_guids, file, default_flow_style=False, sort_keys=False)

    return updated_guids


def generate_urls(guids: dict) -> list:

    with open("utils/urls.yaml", "r") as file:
        urls = yaml.load(file, yaml.FullLoader)

    data = {}
    for version, guid in guids.items():
        data.setdefault(version, dict())
        for type, url in urls.items():
            data[version][type] = "https://docs.docker.com" + url.format(guid=guid)

    with open("utils/resources.yaml", "w") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)

    return data


def main(update: bool = False, generate: bool = False):

    if update:
        guids = update_guids_database()

    # TODO add loading of guids if no update

    if generate:
        data = generate_urls(guids=guids)

    print("All done.")


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(
        description="Track and list all Docker Desktop direct download links since version `4.0.0` (released on `2021-08-31`).",
    )

    arguments.add_argument(
        "--update",
        action="store_true",
        default=False,
        help='Fetch available GUIDs from Docker Desktop release notes page and update "utils/guids.yaml".',
    )

    arguments.add_argument(
        "--generate",
        action="store_true",
        default=False,
        help='Generates all possible combinations of URLs from the GUIDs and the URLs stored in "utils" and save them into "utils/ressources.yaml"',
    )

    args = arguments.parse_args()

    main(update=args.update, generate=args.generate)
