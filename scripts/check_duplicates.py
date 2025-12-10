#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check for duplicates in releases and issues."""

from __future__ import annotations

import json
import subprocess

from typing import Any


def run_gh_api(endpoint: str, method: str = "GET", data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Run a GitHub API command and return JSON result."""
    cmd = ["gh", "api", endpoint, "--method", method]
    if data:
        cmd.extend(["--input", "-"])
        json_data = json.dumps(data)
        result = subprocess.run(cmd, check=False, input=json_data, capture_output=True, text=True, encoding="utf-8", errors="replace")
    else:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if result.returncode != 0:
        return None

    if result.stdout and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
    return None


def get_all_releases(repo: str) -> list[dict[str, Any]]:
    """Get all releases from repository."""
    releases = []
    page = 1
    while True:
        endpoint = f"repos/{repo}/releases?page={page}&per_page=100"
        page_releases = run_gh_api(endpoint)
        if not page_releases:
            break
        releases.extend(page_releases)
        if len(page_releases) < 100:
            break
        page += 1
    return releases


def get_all_issues(repo: str) -> list[dict[str, Any]]:
    """Get all issues from repository."""
    issues = []
    page = 1
    while True:
        endpoint = f"repos/{repo}/issues?state=all&page={page}&per_page=100"
        page_issues = run_gh_api(endpoint)
        if not page_issues:
            break
        page_issues = [i for i in page_issues if "pull_request" not in i]
        issues.extend(page_issues)
        if len(page_issues) < 100:
            break
        page += 1
    return issues


def main():
    repo = "OldRepublicDevs/PyKotor"

    print("Checking for duplicates...")

    # Check releases
    releases = get_all_releases(repo)
    release_tags = {}
    for release in releases:
        tag = release["tag_name"]
        if tag not in release_tags:
            release_tags[tag] = []
        release_tags[tag].append(release)

    duplicate_releases = {tag: releases for tag, releases in release_tags.items() if len(releases) > 1}

    if duplicate_releases:
        print(f"\nDUPLICATE RELEASES FOUND: {len(duplicate_releases)}")
        for tag, releases_list in duplicate_releases.items():
            print(f"\n  {tag}: {len(releases_list)} copies")
            for r in releases_list:
                print(f"    - ID: {r['id']}, Created: {r.get('created_at', 'N/A')}")
    else:
        print(f"\nNo duplicate releases found ({len(releases)} total)")

    # Check issues
    issues = get_all_issues(repo)
    issue_titles = {}
    for issue in issues:
        title = issue["title"]
        if title not in issue_titles:
            issue_titles[title] = []
        issue_titles[title].append(issue)

    duplicate_issues = {title: issues_list for title, issues_list in issue_titles.items() if len(issues_list) > 1}

    if duplicate_issues:
        print(f"\nDUPLICATE ISSUES FOUND: {len(duplicate_issues)}")
        for title, issues_list in duplicate_issues.items():
            print(f"\n  {title[:60]}: {len(issues_list)} copies")
            for i in issues_list:
                print(f"    - #{i['number']}, Created: {i.get('created_at', 'N/A')}")
    else:
        print(f"\nNo duplicate issues found ({len(issues)} total)")


if __name__ == "__main__":
    main()
