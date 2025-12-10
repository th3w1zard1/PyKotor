#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attempt to fix release dates using GitHub API.
Note: GitHub REST API doesn't support setting published_at directly.
This script will attempt to update releases, but dates may need manual fixing.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime

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


def update_release_with_date(target_repo: str, release_id: int, release_data: dict[str, Any], original_date: str) -> bool:
    """Attempt to update release - note: published_at cannot be set via REST API."""
    # GitHub REST API doesn't support setting published_at
    # We can only update other fields
    data = {
        "tag_name": release_data["tag_name"],
        "name": release_data.get("name", release_data["tag_name"]),
        "body": release_data.get("body", ""),
        "draft": release_data.get("draft", False),
        "prerelease": release_data.get("prerelease", False),
        # Note: published_at is not a valid field in PATCH /repos/{owner}/{repo}/releases/{release_id}
    }

    endpoint = f"repos/{target_repo}/releases/{release_id}"
    result = run_gh_api(endpoint, "PATCH", data)
    return result is not None


def main():
    source_repo = "NickHugi/PyKotor"
    target_repo = "OldRepublicDevs/PyKotor"

    print("=" * 70)
    print("RELEASE DATE FIX ATTEMPT")
    print("=" * 70)
    print("\nWARNING: GitHub REST API does not support setting published_at dates.")
    print("This script will update release metadata, but dates must be fixed manually.")
    print("\nAlternative solutions:")
    print("  1. Use GitHub CLI with GraphQL (may have limitations)")
    print("  2. Manually edit via web interface")
    print("  3. Use GitHub's release edit API with proper permissions")
    print("\n" + "=" * 70)

    # Get all releases
    print("\nFetching source releases...")
    source_releases = get_all_releases(source_repo)
    source_by_tag = {r["tag_name"]: r for r in source_releases}

    print("\nFetching target releases...")
    target_releases = get_all_releases(target_repo)
    target_by_tag = {r["tag_name"]: r for r in target_releases}

    # Find releases with wrong dates
    date_fixes_needed = []
    for tag_name, source_release in source_by_tag.items():
        if tag_name in target_by_tag:
            source_date = source_release.get("published_at")
            target_date = target_by_tag[tag_name].get("published_at")
            if source_date != target_date:
                date_fixes_needed.append((tag_name, target_by_tag[tag_name]["id"], source_release, source_date))

    print(f"\nFound {len(date_fixes_needed)} releases with incorrect dates.")
    print("\nGitHub REST API limitation: published_at cannot be set programmatically.")
    print("\nTo fix dates, you have these options:")
    print("\n1. MANUAL FIX (Recommended):")
    print("   Visit: https://github.com/OldRepublicDevs/PyKotor/releases")
    print("   Edit each release and set the correct date")
    print(f"\n2. Create a script using GitHub's web interface automation")
    print(f"\n3. Contact GitHub Support for bulk date correction")

    # Show the releases that need date fixes, sorted by original date
    print("\n" + "=" * 70)
    print("RELEASES NEEDING DATE FIXES (sorted by original date)")
    print("=" * 70)
    
    sorted_fixes = sorted(date_fixes_needed, key=lambda x: x[3] if x[3] else "")
    for tag_name, release_id, source_release, original_date in sorted_fixes:
        current_date = target_by_tag[tag_name].get("published_at")
        print(f"\n{tag_name}:")
        print(f"  Original date: {original_date}")
        print(f"  Current date:  {current_date}")
        print(f"  Edit URL: https://github.com/OldRepublicDevs/PyKotor/releases/edit/{tag_name}")

    print("\n" + "=" * 70)
    print("NOTE: v1.52-patcher exists but has wrong date")
    print("This is why v1.0 appears as latest - all dates are the same (today)")
    print("=" * 70)


if __name__ == "__main__":
    main()

