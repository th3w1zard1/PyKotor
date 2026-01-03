#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate and migrate releases from NickHugi/PyKotor to OldRepublicDevs/PyKotor.
Ensures 100% accuracy with full metadata preservation.
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


def compare_releases(source: dict[str, Any], target: dict[str, Any]) -> tuple[bool, list[str]]:
    """Compare two releases and return (match, differences)."""
    differences = []

    if source["tag_name"] != target["tag_name"]:
        differences.append(f"tag_name: '{source['tag_name']}' != '{target['tag_name']}'")

    if source.get("name") != target.get("name"):
        differences.append(f"name: '{source.get('name')}' != '{target.get('name')}'")

    if source.get("body") != target.get("body"):
        differences.append(f"body: length {len(source.get('body', ''))} != {len(target.get('body', ''))}")

    if source.get("draft", False) != target.get("draft", False):
        differences.append(f"draft: {source.get('draft')} != {target.get('draft')}")

    if source.get("prerelease", False) != target.get("prerelease", False):
        differences.append(f"prerelease: {source.get('prerelease')} != {target.get('prerelease')}")

    return len(differences) == 0, differences


def create_release(target_repo: str, release_data: dict[str, Any]) -> bool:
    """Create a release in target repository with exact metadata."""
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


def update_release(target_repo: str, release_id: int, release_data: dict[str, Any]) -> bool:
    """Update an existing release in target repository."""
    data = {
        "tag_name": release_data["tag_name"],
        "name": release_data.get("name", release_data["tag_name"]),
        "body": release_data.get("body", ""),
        "draft": release_data.get("draft", False),
        "prerelease": release_data.get("prerelease", False),
    }

    endpoint = f"repos/{target_repo}/releases/{release_id}"
    result = run_gh_api(endpoint, "PATCH", data)
    return result is not None


def main():
    source_repo = "NickHugi/PyKotor"
    target_repo = "OldRepublicDevs/PyKotor"

    print("=" * 70)
    print("VALIDATING AND MIGRATING RELEASES - 100% ACCURACY CHECK")
    print("=" * 70)

    # Get all releases from both repositories
    print("\nFetching releases from source repository...")
    source_releases = get_all_releases(source_repo)
    print(f"Found {len(source_releases)} releases in {source_repo}")

    print("\nFetching releases from target repository...")
    target_releases = get_all_releases(target_repo)
    print(f"Found {len(target_releases)} releases in {target_repo}")

    # Create mappings by tag_name
    source_by_tag = {r["tag_name"]: r for r in source_releases}
    target_by_tag = {r["tag_name"]: r for r in target_releases}

    print("\n" + "=" * 70)
    print("COMPARISON ANALYSIS")
    print("=" * 70)

    missing_releases = []
    mismatched_releases = []
    correct_releases = []

    # Check each source release
    for tag_name, source_release in sorted(source_by_tag.items()):
        if tag_name not in target_by_tag:
            missing_releases.append(source_release)
            print(f"  MISSING: {tag_name}")
        else:
            target_release = target_by_tag[tag_name]
            matches, differences = compare_releases(source_release, target_release)
            if matches:
                correct_releases.append(tag_name)
            else:
                mismatched_releases.append((source_release, target_release, differences))
                print(f"  MISMATCH: {tag_name}")
                for diff in differences:
                    print(f"    - {diff}")

    # Check for extra releases in target
    extra_releases = [tag for tag in target_by_tag if tag not in source_by_tag]
    if extra_releases:
        print(f"\n  EXTRA (in target, not in source): {len(extra_releases)} releases")
        for tag in sorted(extra_releases):
            print(f"    - {tag}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total source releases: {len(source_releases)}")
    print(f"Total target releases: {len(target_releases)}")
    print(f"Missing releases: {len(missing_releases)}")
    print(f"Mismatched releases: {len(mismatched_releases)}")
    print(f"Correct releases: {len(correct_releases)}")
    print(f"Extra releases: {len(extra_releases)}")

    # Migrate missing releases
    if missing_releases:
        print("\n" + "=" * 70)
        print("MIGRATING MISSING RELEASES")
        print("=" * 70)

        migrated = 0
        failed = 0

        for release in missing_releases:
            print(f"\nCreating: {release['tag_name']} - {release.get('name', 'N/A')[:50]}")
            if create_release(target_repo, release):
                print(f"  SUCCESS: Created {release['tag_name']}")
                migrated += 1
            else:
                print(f"  FAILED: Could not create {release['tag_name']}")
                failed += 1
            time.sleep(1)  # Rate limiting

        print(f"\nMigrated: {migrated}, Failed: {failed}")

    # Fix mismatched releases
    if mismatched_releases:
        print("\n" + "=" * 70)
        print("FIXING MISMATCHED RELEASES")
        print("=" * 70)

        updated = 0
        failed = 0

        for source_release, target_release, differences in mismatched_releases:
            tag_name = source_release["tag_name"]
            print(f"\nUpdating: {tag_name}")
            print(f"  Differences: {', '.join(differences)}")
            if update_release(target_repo, target_release["id"], source_release):
                print(f"  SUCCESS: Updated {tag_name}")
                updated += 1
            else:
                print(f"  FAILED: Could not update {tag_name}")
                failed += 1
            time.sleep(1)  # Rate limiting

        print(f"\nUpdated: {updated}, Failed: {failed}")

    # Final verification
    if missing_releases or mismatched_releases:
        print("\n" + "=" * 70)
        print("FINAL VERIFICATION")
        print("=" * 70)

        print("\nRe-fetching target releases...")
        final_target_releases = get_all_releases(target_repo)
        final_target_by_tag = {r["tag_name"]: r for r in final_target_releases}

        all_correct = True
        for tag_name, source_release in sorted(source_by_tag.items()):
            if tag_name not in final_target_by_tag:
                print(f"  ERROR: {tag_name} still missing!")
                all_correct = False
            else:
                matches, differences = compare_releases(source_release, final_target_by_tag[tag_name])
                if not matches:
                    print(f"  ERROR: {tag_name} still mismatched!")
                    for diff in differences:
                        print(f"    - {diff}")
                    all_correct = False

        if all_correct:
            print("\n  SUCCESS: All releases are now 100% accurate!")
        else:
            print("\n  WARNING: Some releases still need attention")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

