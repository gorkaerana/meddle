"""
Scrapped all .mdl files under the "veeva" GitHub user. Requires "GITHUB_TOKEN"
environment variable

Usage: `python3 scrape_mdl_files.py -o /path/to/wherever/you/want/the/scrapped/files`
"""
# TODO: how worth it is it to make this into a standalone script as per `uv`'s
# documentation? See https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies

from argparse import ArgumentParser
from base64 import b64decode
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from zipfile import ZipFile

import httpx


here = Path(__file__).parent


class GithubClient(httpx.Client):
    """A thin wrapper around `httpx.Client` with two goodies:
    1. It injects the host and/or scheme to the URL if the user does not provide it.
    2. It injects the authentication token to every request header.
    """

    scheme: str = "https"
    host: str = "api.github.com"

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


def user_repos(user: str, github_client: GithubClient) -> Generator[dict, None, None]:
    """Yields repository metadata from
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repositories-for-a-user
    """
    yield from github_client.get(f"/users/{user}/repos").json()


def repo_latest_commit(url: str, github_client: GithubClient) -> dict:
    """Fetch the last commit of a repo via
    https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28"""
    return github_client.get(f"{url}/commits", params={"per_page": 1}).json()[0]


def repo_files(url: str, github_client: GithubClient) -> Generator[dict, None, None]:
    """ "Iterates over all files in a GitHub repository.

    Only way to iterate through all files in a GitHub repo is to iterate the
    Git tree, for which we need a commit's SHA256. Here we just choose the
    latest repo commit.
    """
    commit_sha = repo_latest_commit(url, github_client)["sha"]
    response = github_client.get(
        f"{url}/git/trees/{commit_sha}", params={"recursive": True}
    )
    yield from response.json()["tree"]


def cli() -> Path:
    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        "-o",
        "--out-dir",
        help="Directory in which to place scrapped MDL files.",
    )
    arguments = argument_parser.parse_args()
    out_dir = (
        Path(__file__).parent.parent / "tests" / "mdl_examples" / "scrapped"
        if arguments.out_dir is None
        else Path(arguments.out_dir).resolve()
    )
    out_dir.mkdir(exist_ok=True)
    assert out_dir.is_dir()
    return out_dir


def download_mdl_file(metadata: dict, github_client: GithubClient, out_dir: Path):
    path, url = metadata["path"], metadata["url"]
    assert path.endswith(".mdl")
    out_path = out_dir / Path(path).name
    content_response = github_client.get(url)
    mdl_content = b64decode(content_response.json()["content"])
    out_path.write_bytes(mdl_content)
    print(f"Wrote {out_path}")
    return str(out_path.relative_to(out_dir)), url


def download_mdl_files_from_vpk(
    metadata: dict, github_client: GithubClient, out_dir: Path
):
    path, url = metadata["path"], metadata["url"]
    vpk_dir = out_dir / Path(path).stem
    assert path.endswith(".vpk")
    vpk_dir.mkdir(exist_ok=True)
    content_response = github_client.get(url)
    vpk_content = b64decode(content_response.json()["content"])
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / Path(path).stem
        tmp_path.write_bytes(vpk_content)
        with ZipFile(tmp_path) as zip_file:
            for file_name in zip_file.namelist():
                if (not file_name.endswith(".mdl")) or file_name.startswith("__MACOSX"):
                    # For the second clause above, see
                    # https://apple.stackexchange.com/questions/373450/why-are-almost-blank-files-being-created-by-macos-and-applications
                    continue
                with zip_file.open(file_name) as zipped_mdl_file:
                    out_path = vpk_dir / Path(file_name).name
                    out_path.write_bytes(zipped_mdl_file.read())
                    print(f"Wrote {out_path}")
                    yield str(out_path.relative_to(out_dir)), url


def main(out_dir: Path):
    """Iterate over all repositories and files under GitHub user `veeva`, and save
    to `out_dir` those with extension `.mdl`.
    """
    (out_dir / "README.md").write_text(
        f"Content scrapped with `{Path(__file__).relative_to(here.parent)}`"
    )
    outdir_to_url = {}
    github_client = GithubClient(os.environ["GITHUB_TOKEN"])
    for repo_metadata in user_repos("veeva", github_client):
        repo_url = repo_metadata["url"]
        for blob_metadata in repo_files(repo_url, github_client):
            path = blob_metadata["path"]
            if path.endswith(".vpk"):
                downloads = download_mdl_files_from_vpk(
                    blob_metadata, github_client, out_dir
                )
                outdir_to_url.update(downloads)
            elif path.endswith(".mdl"):
                out_path, url = download_mdl_file(blob_metadata, github_client, out_dir)
                outdir_to_url[out_path] = url
            else:
                continue
    sources_path = out_dir / "source_urls.json"
    sources_path.write_text(json.dumps(outdir_to_url, indent=4))
    print(f"Wrote {sources_path}")


if __name__ == "__main__":
    main(cli())
