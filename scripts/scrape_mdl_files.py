"""
Scrapped all .mdl files under the "veeva" GitHub user. Requires "GITHUB_TOKEN"
environment variable
"""
from argparse import ArgumentParser
from base64 import b64decode
import json
import os
from pathlib import Path

import httpx

from mdl import Command


class GithubClient(httpx.Client):
    host: str = "api.github.com"
    scheme: str = "https"

    def __init__(self, token: str, *args, **kwargs):
        self.token = token
        super().__init__(*args, **kwargs)

    @property
    def auth_header(self):
        return {
            "Authorization": f"Bearer {self.token}",
        }

    def request(self, method, url, *args, **kwargs):
        # Insert "Authorization" header
        headers = kwargs.pop("headers") or {}
        headers |= self.auth_header
        kwargs["headers"] = headers
        # Allow the user to only provide the URL path
        provided_url = httpx.URL(url)
        if not provided_url.path:
            raise ValueError(
                f"Argument `url` ought to contain at least a path. Provided: {url}"
            )
        clean_url = provided_url.copy_with(
            scheme=provided_url.scheme or self.scheme,
            host=provided_url.host or self.host,
            path=provided_url.path,
        )
        return super().request(method, clean_url, **kwargs)


def user_repos(user: str, github_client: GithubClient):
    yield from github_client.get(f"/users/{user}/repos").json()


def repo_latest_commit(url: str, github_client: GithubClient):
    return github_client.get(f"{url}/commits", params={"per_page": 1}).json()[0]


def repo_files(url: str, github_client: GithubClient):
    # Only way to iterate through all files in a GitHub repo is to iterate the
    # Git tree, for which we need a commit's SHA256. Here we just choose the
    # latest repo commit
    commit_sha = repo_latest_commit(url, github_client)["sha"]
    response = github_client.get(
        f"{url}/git/trees/{commit_sha}", params={"recursive": True}
    )
    yield from response.json()["tree"]


def cli() -> Path:
    argument_parser = ArgumentParser()
    argument_parser.add_argument("-o", "--out-dir", help="Directory in which to place scrapped MDL files.", required=True)
    arguments = argument_parser.parse_args()
    out_dir = Path(arguments.out_dir).resolve()
    return out_dir
    

def main(out_dir):
    outdir_to_url = {}
    github_client = GithubClient(os.environ["GITHUB_TOKEN"])
    for repo_metadata in user_repos("veeva", github_client):
        repo_url = repo_metadata["url"]
        for blob_metadata in repo_files(repo_url, github_client):
            path, url = blob_metadata["path"], blob_metadata["url"]
            if not path.endswith(".mdl"):
                continue
            out_path = out_dir / Path(path).name
            content_response = github_client.get(url)
            mdl_content = b64decode(content_response.json()["content"])
            out_path.write_bytes(mdl_content)
            print(f"Wrote {out_path}")
            outdir_to_url[str(out_path.name)] = url
    sources_path = out_dir / "source_urls.json"
    sources_path.write_text(json.dumps(outdir_to_url))
    print(f"Wrote {sources_path}")


if __name__ == "__main__":
    main(cli())
