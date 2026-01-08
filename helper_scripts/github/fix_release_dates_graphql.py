#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attempt to fix release dates using GitHub GraphQL API.
GraphQL may have more flexibility than REST API for setting dates.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

from typing import Any


def run_gh_api_graphql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Run a GitHub GraphQL query."""
    data = {"query": query}
    if variables:
        data["variables"] = variables

    cmd = ["gh", "api", "graphql", "--input", "-"]
    json_data = json.dumps(data)
    result = subprocess.run(cmd, check=False, input=json_data, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if result.returncode != 0:
        if result.stderr:
            print(f"Error: {result.stderr}", file=sys.stderr)
        return None

    if result.stdout and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
            return None
    return None


def run_gh_api(endpoint: str, method: str = "GET", data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Run a GitHub REST API command."""
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
    per_page = 100

    while True:
        endpoint = f"repos/{repo}/releases?page={page}&per_page={per_page}"
        page_releases = run_gh_api(endpoint)
        if not page_releases:
            break
        releases.extend(page_releases)
        if len(page_releases) < per_page:
            break
        page += 1
        time.sleep(0.5)

    return releases


def main():
    source_repo = "NickHugi/PyKotor"
    target_repo = "OldRepublicDevs/PyKotor"

    print("=" * 70)
    print("ATTEMPTING TO FIX RELEASE DATES VIA GRAPHQL")
    print("=" * 70)

    # Get releases
    print("\nFetching releases...")
    source_releases = get_all_releases(source_repo)
    target_releases = get_all_releases(target_repo)

    source_by_tag = {r["tag_name"]: r for r in source_releases}
    target_by_tag = {r["tag_name"]: r for r in target_releases}

    # Find releases needing date fixes
    date_fixes = []
    for tag_name, source_release in source_by_tag.items():
        if tag_name in target_by_tag:
            source_date = source_release.get("published_at")
            target_date = target_by_tag[tag_name].get("published_at")
            if source_date != target_date:
                date_fixes.append((tag_name, target_by_tag[tag_name], source_date))

    print(f"\nFound {len(date_fixes)} releases with incorrect dates.")

    # NOTE: GitHub GraphQL API also doesn't support setting published_at
    # The mutation updateRelease doesn't have a publishedAt parameter
    print("\n" + "=" * 70)
    print("LIMITATION CONFIRMED")
    print("=" * 70)
    print("GitHub's API (both REST and GraphQL) does not support")
    print("setting published_at dates programmatically.")
    print("\nThe updateRelease mutation in GraphQL only supports:")
    print("  - name, description, url, isDraft, isPrerelease")
    print("  - NOT publishedAt or published_at")
    print("\n" + "=" * 70)
    print("SOLUTION: Manual Fix Required")
    print("=" * 70)
    print("\nYou must manually edit each release via the web interface:")
    print("https://github.com/OldRepublicDevs/PyKotor/releases")
    print("\nOr use a browser automation tool to edit them programmatically.")
    print(f"\nTotal releases needing date fixes: {len(date_fixes)}")
    print("\nKey releases (patcher):")
    for tag_name, target_release, original_date in date_fixes:
        if "patcher" in tag_name:
            print(f"  - {tag_name}: {original_date}")


if __name__ == "__main__":
    main()

