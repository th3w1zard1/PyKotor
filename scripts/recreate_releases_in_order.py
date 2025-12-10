#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delete all releases and recreate them in exact chronological order.
This ensures releases are in the correct order even if dates can't be set.
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


def delete_release(target_repo: str, release_id: int) -> bool:
    """Delete a release."""
    endpoint = f"repos/{target_repo}/releases/{release_id}"
    result = run_gh_api(endpoint, "DELETE")
    return result is None  # DELETE returns 204 No Content on success


def create_metadata_footer(original_release: dict[str, Any], source_repo: str) -> str:
    """Create metadata footer with original release information."""
    footer = "\n\n---\n"
    footer += "**Migrated from:** "
    footer += f"[{source_repo}#{original_release['tag_name']}](https://github.com/{source_repo}/releases/tag/{original_release['tag_name']})\n"
    footer += f"**Original published:** {original_release.get('published_at', original_release.get('created_at', 'N/A'))}\n"
    footer += f"**Original author:** @{original_release.get('author', {}).get('login', 'N/A')}\n"
    
    if original_release.get("assets"):
        footer += f"**Original assets:** {len(original_release['assets'])} file(s) (not migrated - download from original release)\n"
    
    footer += "\n*Note: Release date cannot be preserved via GitHub API. This release was recreated to maintain chronological order.*"
    
    return footer


def create_release(target_repo: str, release_data: dict[str, Any], source_repo: str) -> bool:
    """Create a release in target repository with metadata footer."""
    # Add metadata footer to body
    body = release_data.get("body", "")
    footer = create_metadata_footer(release_data, source_repo)
    new_body = body + footer
    
    data = {
        "tag_name": release_data["tag_name"],
        "name": release_data.get("name", release_data["tag_name"]),
        "body": new_body,
        "draft": release_data.get("draft", False),
        "prerelease": release_data.get("prerelease", False),
    }

    endpoint = f"repos/{target_repo}/releases"
    result = run_gh_api(endpoint, "POST", data)
    return result is not None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Delete and recreate all releases in exact chronological order")
    parser.add_argument("--source", default="NickHugi/PyKotor", help="Source repository (default: NickHugi/PyKotor)")
    parser.add_argument("--target", default="OldRepublicDevs/PyKotor", help="Target repository (default: OldRepublicDevs/PyKotor)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    args = parser.parse_args()
    
    source_repo = args.source
    target_repo = args.target

    print("=" * 70)
    print("RECREATING ALL RELEASES IN EXACT CHRONOLOGICAL ORDER")
    print("=" * 70)

    # Get source releases
    print("\nFetching source releases...")
    source_releases = get_all_releases(source_repo)
    print(f"Found {len(source_releases)} releases in {source_repo}")

    # Sort by published_at date (oldest first)
    def get_published_date(release: dict[str, Any]) -> str:
        return release.get("published_at", release.get("created_at", "1970-01-01T00:00:00Z"))

    sorted_releases = sorted(source_releases, key=get_published_date)
    print("\nReleases sorted by original published date (oldest to newest):")
    for i, release in enumerate(sorted_releases, 1):
        date = get_published_date(release)
        print(f"  {i:2d}. {release['tag_name']:30s} - {date}")

    # Get target releases
    print("\nFetching target releases...")
    target_releases = get_all_releases(target_repo)
    print(f"Found {len(target_releases)} releases in {target_repo}")

    # Delete all target releases
    if args.dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN - WOULD DELETE ALL EXISTING RELEASES")
        print("=" * 70)
        print(f"Would delete {len(target_releases)} releases:")
        for release in target_releases:
            print(f"  - {release['tag_name']}")
        deleted = len(target_releases)
        failed = 0
    else:
        print("\n" + "=" * 70)
        print("DELETING ALL EXISTING RELEASES")
        print("=" * 70)

        deleted = 0
        failed = 0

        for release in target_releases:
            print(f"Deleting: {release['tag_name']}")
            if delete_release(target_repo, release["id"]):
                print(f"  SUCCESS: Deleted {release['tag_name']}")
                deleted += 1
            else:
                print(f"  FAILED: Could not delete {release['tag_name']}")
                failed += 1
            time.sleep(0.5)  # Rate limiting

        print(f"\nDeleted: {deleted}, Failed: {failed}")

        if failed > 0:
            print("\nWARNING: Some releases could not be deleted. Continuing anyway...")

        # Wait a moment for deletions to propagate
        print("\nWaiting 5 seconds for deletions to propagate...")
        time.sleep(5)

    # Recreate releases in exact chronological order
    print("\n" + "=" * 70)
    print("RECREATING RELEASES IN CHRONOLOGICAL ORDER")
    print("=" * 70)

    created = 0
    failed = 0

    for i, release in enumerate(sorted_releases, 1):
        print(f"\n[{i}/{len(sorted_releases)}] Creating: {release['tag_name']}")
        print(f"  Name: {release.get('name', 'N/A')[:50]}")
        print(f"  Original date: {get_published_date(release)}")

        if args.dry_run:
            print(f"  DRY RUN: Would create {release['tag_name']}")
            created += 1
        elif create_release(target_repo, release, source_repo):
            print(f"  SUCCESS: Created {release['tag_name']}")
            created += 1
        else:
            print(f"  FAILED: Could not create {release['tag_name']}")
            failed += 1

        # Wait between creations to ensure proper ordering
        # Longer wait for first few to ensure they're definitely in order
        if not args.dry_run:
            if i < 5:
                time.sleep(2)
            else:
                time.sleep(1)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Deleted: {deleted} releases")
    print(f"Created: {created} releases")
    print(f"Failed: {failed} releases")

    if failed == 0:
        print("\nSUCCESS: All releases recreated in exact chronological order!")
        print("Releases are now in the correct order based on creation time.")
    else:
        print(f"\nWARNING: {failed} releases failed to create.")

    if not args.dry_run:
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        print("Verifying final state...")

        final_releases = get_all_releases(target_repo)
        print(f"Final release count: {len(final_releases)}")

        if len(final_releases) == len(sorted_releases):
            print("SUCCESS: All releases present!")

            # Check order
            final_sorted = sorted(final_releases, key=lambda r: r.get("created_at", ""))
            print("\nReleases in order (by creation time):")
            for i, release in enumerate(final_sorted, 1):
                print(f"  {i:2d}. {release['tag_name']:30s} - {release.get('created_at', 'N/A')}")
        else:
            print(f"WARNING: Expected {len(sorted_releases)} releases, found {len(final_releases)}")


if __name__ == "__main__":
    main()
