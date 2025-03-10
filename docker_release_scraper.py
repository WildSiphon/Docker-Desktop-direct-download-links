#!/usr/bin/env python3

import re
from pathlib import Path

import bs4
import requests
import yaml
from tqdm import tqdm

# TODO fetch checksums
# TODO add missing old GUIDs


def load_yaml_file(filepath: str) -> dict:
    """
    Load a YAML file safely.
    Return an empty dictionary if the file does not exist.
    """
    path = Path(filepath)
    if path.exists():
        with path.open("r") as file:
            return yaml.safe_load(file) or {}
    return {}


def save_yaml_file(filepath: str, data: dict):
    """
    Save a dictionary as a YAML file.
    """
    with Path(filepath).open("w") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)


def fetch_docker_release_notes() -> bs4.BeautifulSoup:
    """
    Fetch and parse the Docker Desktop release notes page.
    """
    url = "https://docs.docker.com/desktop/release-notes"
    response = requests.get(url=url)
    return bs4.BeautifulSoup(markup=response.text, features="lxml")


def extract_version_details(title) -> tuple:
    """
    Extract version number and release date from an H2 title element.
    """
    version = title.text.strip()
    release_date = title.find_next_sibling().text.strip()
    return version, release_date


def extract_version_guid(blockquote) -> int:
    """
    Extract the GUID from a blockquote element.
    """
    GUID_REGEX = r"(?:https:\/\/desktop\.docker\.com\/(?:\w*?\/){3})(\d+)"
    for a in blockquote.find_all("a"):
        link = a.get("href")
        match = re.search(GUID_REGEX, link)
        if match:
            return int(match.group(1))
    return None


def fetch_available_guids() -> dict:
    """
    Scrape the Docker Desktop release notes page.
    Extract version GUIDs and release dates.
    """
    content = fetch_docker_release_notes()
    guids = []

    for title in tqdm(content.find_all("h2"), desc="Extracting GUIDs", unit="version"):
        version, release_date = extract_version_details(title)
        blockquote = title.find_next_sibling().find_next_sibling()
        if blockquote.name != "blockquote":
            continue

        guid = extract_version_guid(blockquote)
        if guid:
            guids.append((version, {"guid": guid, "release_date": release_date}))

    return dict(reversed(guids))


def update_guid_database() -> dict:
    """
    Fetch and update the GUIDs database.
    Only new GUIDs are added to the existing data in chronological order.
    """
    guids = fetch_available_guids()
    existing_guids = load_yaml_file("utils/guids.yaml")

    new_guids = {k: v for k, v in guids.items() if k not in existing_guids}
    if new_guids:
        updated_guids = {**existing_guids, **new_guids}  # Preserve order
        save_yaml_file("utils/guids.yaml", updated_guids)
        return updated_guids

    return existing_guids


def generate_download_urls(guids: dict) -> dict:
    """
    Generate download URLs using GUIDs based on 'utils/urls.yaml'.
    """
    url_templates = load_yaml_file("utils/urls.yaml")
    return {
        version: {
            type_: f"https://desktop.docker.com{url.format(guid=data['guid'])}" for type_, url in url_templates.items()
        }
        | {"release_date": data["release_date"]}
        for version, data in tqdm(guids.items(), desc="Generating URLs", unit="version")
    }


def check_url_availability(url: str) -> bool:
    """
    Check if a URL is reachable by making a HEAD request.
    """
    return requests.head(url, allow_redirects=True).status_code == 200


def filter_valid_urls(resources: dict):
    """
    Filter out invalid URLs and save verified ones in 'DockerDesktop.yaml'.
    """
    verified_resources = {
        version: {type_: url for type_, url in data.items() if type_ != "release_date" and check_url_availability(url)}
        | {"release_date": data["release_date"]}
        for version, data in tqdm(resources.items(), desc="Verifying URLs", unit="version")
        if any(check_url_availability(url) for type_, url in data.items() if type_ != "release_date")
    }
    save_yaml_file("DockerDesktop.yaml", verified_resources)


def main():
    """
    Main function to update GUIDs, generate URLs, and verify them.
    """
    guids = update_guid_database()
    generated_urls = generate_download_urls(guids)
    filter_valid_urls(generated_urls)


if __name__ == "__main__":
    main()
