#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

import bs4
import requests
import yaml
from tqdm import tqdm


def get_available_guids() -> dict:
    """
    Scrape the Docker Desktop release notes page.
    Extract version GUIDs and release dates.
    """
    GUID_REGEX = r"(?:https:\/\/desktop\.docker\.com\/(?:\w*?\/){3})(\d+)"
    url = "https://docs.docker.com/desktop/release-notes"
    response = requests.get(url=url)
    content = bs4.BeautifulSoup(markup=response.text, features="lxml")

    guids = []
    for title in tqdm(content.find_all("h2"), desc="Extracting GUIDs", unit="version"):
        version = title.text.strip()
        release_date = title.find_next_sibling().text.strip()

        blockquote = title.find_next_sibling().find_next_sibling()
        if blockquote.name != "blockquote":
            continue

        guid = None
        for a in blockquote.find_all("a"):
            link = a.get("href")
            match = re.search(GUID_REGEX, link)
            if match:
                guid = int(match.group(1))
                break

        if guid:
            guids.append((version, {"guid": guid, "release_date": release_date}))

    return dict(reversed(guids))


def load_yaml(filepath: str) -> dict:
    """
    Load a YAML file safely.
    Return an empty dictionary if the file does not exist.
    """
    path = Path(filepath)
    if path.exists():
        with path.open("r") as file:
            return yaml.safe_load(file) or {}
    return {}


def save_yaml(filepath: str, data: dict):
    """
    Save a dictionary as a YAML file.
    """
    with Path(filepath).open("w") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)


def update_guids_database() -> dict:
    """
    Fetch and update the GUIDs database.
    Only new GUIDs are added to the existing data in chronological order.
    """
    guids = get_available_guids()
    existing_guids = load_yaml("utils/guids.yaml")

    new_guids = {k: v for k, v in guids.items() if k not in existing_guids}
    if new_guids:
        updated_guids = {**existing_guids, **new_guids}  # Preserve order
        save_yaml("utils/guids.yaml", updated_guids)
        return updated_guids

    return existing_guids


def generate_urls(guids: dict) -> dict:
    """
    Generate URLs using GUIDs.
    Update 'utils/resources.yaml' only for new GUIDs.
    """
    url_templates = load_yaml("utils/urls.yaml")
    existing_resources = load_yaml("utils/resources.yaml")

    new_resources = {}
    for version, data in tqdm(guids.items(), desc="Generating URLs", unit="version"):
        if version in existing_resources:
            continue
        new_resources[version] = {
            type_: f"https://desktop.docker.com{url.format(guid=data['guid'])}" for type_, url in url_templates.items()
        }
        new_resources[version]["release_date"] = data["release_date"]

    if new_resources:
        updated_resources = {**existing_resources, **new_resources}
        save_yaml("utils/resources.yaml", updated_resources)
        return updated_resources

    return existing_resources


def verify_urls(resources: dict):
    """
    Verify if generated URLs are valid.
    Save filtered results in 'DockerDesktop.yaml'.
    """
    verified_resources = {}
    for version, data in tqdm(resources.items(), desc="Verifying URLs", unit="version"):
        valid_urls = {
            type_: url
            for type_, url in data.items()
            if type_ != "release_date" and requests.head(url, allow_redirects=True).status_code == 200
        }
        if valid_urls:
            valid_urls["release_date"] = data["release_date"]
            verified_resources[version] = valid_urls

    save_yaml("DockerDesktop.yaml", verified_resources)


def main(update: bool = False, generate: bool = False, verify: bool = False):
    """
    Main function to handle updates.
    Generates URLs and verifies their accessibility.
    """
    guids = load_yaml("utils/guids.yaml")

    if update:
        guids = update_guids_database()
    elif not guids:
        return

    resources = {}
    if generate:
        resources = generate_urls(guids)

    if verify:
        if not resources:
            resources = load_yaml("utils/resources.yaml")
        verify_urls(resources)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Track and list all Docker Desktop direct download links since version 4.0.0 (released on 2021-08-31)."
    )
    parser.add_argument("--update", action="store_true", help="Fetch available GUIDs and update 'utils/guids.yaml'.")
    parser.add_argument("--generate", action="store_true", help="Generate URLs and save to 'utils/resources.yaml'.")
    parser.add_argument(
        "--verify", action="store_true", help="Verify URLs and save filtered results in 'DockerDesktop.yaml'."
    )
    args = parser.parse_args()

    main(update=args.update, generate=args.generate, verify=args.verify)
