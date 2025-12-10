#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix release dates and migrate missing releases.
GitHub API doesn't allow setting published_at directly, but we can ensure
all releases exist and note the date issue.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

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
        if result.stderr and "rate limit" not in result.stderr.lower():
            print(f"Error: {result.stderr}", file=sys.stderr)
        return None

    if result.stdout and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
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


def create_release(target_repo: str, release_data: dict[str, Any]) -> bool:
    """Create a release in target repository."""
    data = {
        "tag_name": release_data["tag_name"],
        "name": release_data.get("name", release_data["tag_name"]),
        "body": release_data.get("body", ""),
        "draft": release_data.get("draft", False),
        "prerelease": release_data.get("prerelease", False),
    }

    endpoint = f"repos/{target_repo}/releases"
    result = run_gh_api(endpoint, "POST", data)
    return result is not None


def main():
    source_repo = "NickHugi/PyKotor"
    target_repo = "OldRepublicDevs/PyKotor"

    print("=" * 70)
    print("FIXING MISSING RELEASES AND DATE ISSUES")
    print("=" * 70)

    # Get all releases
    print("\nFetching source releases...")
    source_releases = get_all_releases(source_repo)
    print(f"Found {len(source_releases)} releases in {source_repo}")

    print("\nFetching target releases...")
    target_releases = get_all_releases(target_repo)
    print(f"Found {len(target_releases)} releases in {target_repo}")

    # Create mappings
    source_by_tag = {r["tag_name"]: r for r in source_releases}
    target_by_tag = {r["tag_name"]: r for r in target_releases}

    # Find missing releases
    missing = []
    for tag_name, source_release in source_by_tag.items():
        if tag_name not in target_by_tag:
            missing.append(source_release)
            print(f"\nMISSING: {tag_name} (published: {source_release.get('published_at', 'N/A')})")

    # Check date issues
    print("\n" + "=" * 70)
    print("CHECKING RELEASE DATES")
    print("=" * 70)

    date_issues = []
    for tag_name in source_by_tag:
        if tag_name in target_by_tag:
            source_date = source_by_tag[tag_name].get("published_at")
            target_date = target_by_tag[tag_name].get("published_at")
            if source_date != target_date:
                date_issues.append((tag_name, source_date, target_date))
                print(f"  DATE MISMATCH: {tag_name}")
                print(f"    Source: {source_date}")
                print(f"    Target: {target_date}")

    # Migrate missing releases
    if missing:
        print("\n" + "=" * 70)
        print("MIGRATING MISSING RELEASES")
        print("=" * 70)

        migrated = 0
        failed = 0

        for release in missing:
            print(f"\nCreating: {release['tag_name']}")
            print(f"  Name: {release.get('name', 'N/A')}")
            print(f"  Published: {release.get('published_at', 'N/A')}")
            if create_release(target_repo, release):
                print(f"  SUCCESS: Created {release['tag_name']}")
                migrated += 1
            else:
                print(f"  FAILED: Could not create {release['tag_name']}")
                failed += 1
            time.sleep(1)

        print(f"\nMigrated: {migrated}, Failed: {failed}")

    # Note about dates
    if date_issues:
        print("\n" + "=" * 70)
        print("IMPORTANT: RELEASE DATE LIMITATION")
        print("=" * 70)
        print("GitHub API does not allow setting published_at dates directly.")
        print("When releases are created via API, they get the current date.")
        print(f"\nFound {len(date_issues)} releases with incorrect dates.")
        print("\nTo fix dates, you must:")
        print("  1. Use GitHub's web interface to edit each release")
        print("  2. Or use GitHub's release API with proper authentication")
        print("  3. Or manually edit via: https://github.com/OldRepublicDevs/PyKotor/releases")
        print("\nReleases with date issues:")
        for tag, source_date, target_date in date_issues[:10]:  # Show first 10
            print(f"  - {tag}: {source_date} -> {target_date}")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

