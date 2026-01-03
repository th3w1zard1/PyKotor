#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate releases, issues, and discussions from one GitHub repository to another.
Preserves all metadata possible (GitHub API limitations prevent exact timestamps/authors).

This script handles:
- Migrating releases with all metadata
- Migrating issues with comments, labels, assignees, and states
- Adding metadata footers to migrated issues (original link, author, dates)
- Fixing issue states (closing issues that were closed in source)
- Verifying and fixing any remaining issues

Usage:
    python scripts/migrate_repo_metadata.py [--source SOURCE] [--target TARGET] [--fix-only]
"""

from __future__ import annotations

import argparse
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


def get_all_releases(source_repo: str) -> list[dict[str, Any]]:
    """Get all releases from source repository."""
    releases = []
    page = 1
    per_page = 100

    while True:
        endpoint = f"repos/{source_repo}/releases?page={page}&per_page={per_page}"
        page_releases = run_gh_api(endpoint)
        if not page_releases:
            break
        releases.extend(page_releases)
        if len(page_releases) < per_page:
            break
        page += 1
        time.sleep(0.5)  # Rate limiting

    return releases


def create_release_metadata_footer(original_release: dict[str, Any], source_repo: str) -> str:
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


def create_release(target_repo: str, release_data: dict[str, Any], source_repo: str = "") -> bool:
    """Create a release in target repository."""
    body = release_data.get("body", "")
    
    # Add metadata footer if source_repo is provided
    if source_repo:
        footer = create_release_metadata_footer(release_data, source_repo)
        body = body + footer
    
    data = {
        "tag_name": release_data["tag_name"],
        "name": release_data.get("name", release_data["tag_name"]),
        "body": body,
        "draft": release_data.get("draft", False),
        "prerelease": release_data.get("prerelease", False),
    }

    endpoint = f"repos/{target_repo}/releases"
    result = run_gh_api(endpoint, "POST", data)
    return result is not None


def delete_release(target_repo: str, release_id: int) -> bool:
    """Delete a release."""
    endpoint = f"repos/{target_repo}/releases/{release_id}"
    result = run_gh_api(endpoint, "DELETE")
    return result is None  # DELETE returns 204 No Content on success


def get_all_issues(source_repo: str, state: str = "all") -> list[dict[str, Any]]:
    """Get all issues from source repository."""
    issues = []
    page = 1
    per_page = 100

    while True:
        endpoint = f"repos/{source_repo}/issues?state={state}&page={page}&per_page={per_page}"
        page_issues = run_gh_api(endpoint)
        if not page_issues:
            break
        # Filter out pull requests (they have pull_request field)
        page_issues = [i for i in page_issues if "pull_request" not in i]
        issues.extend(page_issues)
        if len(page_issues) < per_page:
            break
        page += 1
        time.sleep(0.5)  # Rate limiting

    return issues


def get_issue_comments(source_repo: str, issue_number: int) -> list[dict[str, Any]]:
    """Get all comments for an issue."""
    comments = []
    page = 1
    per_page = 100

    while True:
        endpoint = f"repos/{source_repo}/issues/{issue_number}/comments?page={page}&per_page={per_page}"
        page_comments = run_gh_api(endpoint)
        if not page_comments:
            break
        comments.extend(page_comments)
        if len(page_comments) < per_page:
            break
        page += 1
        time.sleep(0.5)  # Rate limiting

    return comments


def get_issue(source_repo: str, issue_num: int) -> dict[str, Any] | None:
    """Get issue data."""
    endpoint = f"repos/{source_repo}/issues/{issue_num}"
    return run_gh_api(endpoint)


def create_issue(target_repo: str, issue_data: dict[str, Any], skip_milestone: bool = False) -> dict[str, Any] | None:
    """Create an issue in target repository."""
    data = {"title": issue_data["title"], "body": issue_data["body"], "state": issue_data.get("state", "open")}

    if issue_data.get("labels"):
        data["labels"] = [label["name"] for label in issue_data["labels"]]

    if issue_data.get("assignees"):
        data["assignees"] = [assignee["login"] for assignee in issue_data["assignees"]]

    if not skip_milestone and issue_data.get("milestone") and issue_data["milestone"]:
        # Try to get or create milestone
        milestone_num = issue_data["milestone"].get("number")
        if milestone_num:
            data["milestone"] = milestone_num

    endpoint = f"repos/{target_repo}/issues"
    result = run_gh_api(endpoint, "POST", data)
    return result


def create_issue_comment(target_repo: str, issue_number: int, comment_data: dict[str, Any]) -> bool:
    """Create a comment on an issue."""
    data = {"body": comment_data["body"]}

    endpoint = f"repos/{target_repo}/issues/{issue_number}/comments"
    result = run_gh_api(endpoint, "POST", data)
    return result is not None


def create_metadata_footer(original_issue: dict[str, Any], source_repo: str) -> str:
    """Create metadata footer with original issue information."""
    footer = "\n\n---\n"
    footer += "**Migrated from:** "
    owner, repo = source_repo.split("/")
    footer += f"[{source_repo}#{original_issue['number']}](https://github.com/{source_repo}/issues/{original_issue['number']})\n"
    footer += f"**Original author:** @{original_issue['user']['login']}\n"
    footer += f"**Original created:** {original_issue['created_at']}\n"

    if original_issue.get("closed_at"):
        footer += f"**Original closed:** {original_issue['closed_at']}\n"
        if original_issue.get("closed_by"):
            footer += f"**Closed by:** @{original_issue['closed_by']['login']}\n"

    if original_issue.get("milestone"):
        footer += f"**Original milestone:** {original_issue['milestone']['title']}\n"

    return footer


def update_issue_body(target_repo: str, issue_number: int, new_body: str) -> bool:
    """Update issue body."""
    data = {"body": new_body}
    endpoint = f"repos/{target_repo}/issues/{issue_number}"
    result = run_gh_api(endpoint, "PATCH", data)
    return result is not None


def close_issue(target_repo: str, issue_number: int) -> bool:
    """Close an issue."""
    data = {"state": "closed"}
    endpoint = f"repos/{target_repo}/issues/{issue_number}"
    result = run_gh_api(endpoint, "PATCH", data)
    return result is not None


def get_all_discussions(source_repo: str) -> list[dict[str, Any]]:
    """Get all discussions from source repository using GraphQL."""
    discussions = []
    cursor = None

    owner, repo = source_repo.split("/")

    query = """
    query($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        discussions(first: 100, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            id
            number
            title
            body
            category {
              name
              slug
            }
            author {
              login
            }
            createdAt
            updatedAt
            isAnswered
            answerChosenAt
            answer {
              id
            }
            comments(first: 100) {
              nodes {
                id
                body
                author {
                  login
                }
                createdAt
              }
            }
          }
        }
      }
    }
    """

    variables = {"owner": owner, "repo": repo, "cursor": cursor}

    while True:
        data = {"query": query, "variables": variables}
        result = run_gh_api("graphql", "POST", data)
        if not result or "data" not in result or not result["data"].get("repository"):
            break

        discussions_data = result["data"]["repository"]["discussions"]
        if not discussions_data:
            break

        discussions.extend(discussions_data["nodes"])

        if not discussions_data["pageInfo"]["hasNextPage"]:
            break
        variables["cursor"] = discussions_data["pageInfo"]["endCursor"]
        time.sleep(0.5)  # Rate limiting

    return discussions


def migrate_releases(source_repo: str, target_repo: str, recreate_in_order: bool = False) -> tuple[int, int]:
    """Migrate all releases from source to target.
    
    If recreate_in_order is True, deletes all existing releases and recreates
    them in exact chronological order to ensure proper sorting.
    """
    print("=" * 60)
    print("STEP 1: MIGRATING RELEASES")
    print("=" * 60)
    
    releases = get_all_releases(source_repo)
    print(f"Found {len(releases)} releases in source repository")

    # Sort by published_at date (oldest first) for chronological order
    def get_published_date(release: dict[str, Any]) -> str:
        return release.get("published_at", release.get("created_at", "1970-01-01T00:00:00Z"))
    
    sorted_releases = sorted(releases, key=get_published_date)
    
    if recreate_in_order:
        print("\nRECREATE MODE: Deleting all existing releases and recreating in chronological order")
        
        # Get and delete all existing releases
        existing_releases = get_all_releases(target_repo)
        print(f"Found {len(existing_releases)} existing releases to delete")
        
        deleted = 0
        failed = 0
        
        for release in existing_releases:
            print(f"  Deleting: {release['tag_name']}")
            if delete_release(target_repo, release["id"]):
                print(f"    SUCCESS: Deleted {release['tag_name']}")
                deleted += 1
            else:
                print(f"    FAILED: Could not delete {release['tag_name']}")
                failed += 1
            time.sleep(0.5)  # Rate limiting
        
        print(f"\nDeleted: {deleted}, Failed: {failed}")
        
        if failed > 0:
            print("\nWARNING: Some releases could not be deleted. Continuing anyway...")
        
        # Wait for deletions to propagate
        print("\nWaiting 5 seconds for deletions to propagate...")
        time.sleep(5)
        
        # Recreate in exact chronological order
        print("\nRecreating releases in chronological order (oldest to newest):")
        migrated_releases = 0
        skipped_releases = 0
        
        # Wait a bit more and verify deletions
        print("Verifying all releases are deleted...")
        time.sleep(2)
        remaining_releases = get_all_releases(target_repo)
        if remaining_releases:
            print(f"WARNING: {len(remaining_releases)} releases still exist. Attempting to delete again...")
            for release in remaining_releases:
                delete_release(target_repo, release["id"])
                time.sleep(0.5)
            time.sleep(3)
        
        for i, release in enumerate(sorted_releases, 1):
            print(f"\n[{i}/{len(sorted_releases)}] Creating: {release['tag_name']}")
            print(f"  Name: {release.get('name', 'N/A')[:50]}")
            print(f"  Original date: {get_published_date(release)}")
            
            # Double-check it doesn't exist (idempotency)
            existing = get_all_releases(target_repo)
            existing_tags = {r["tag_name"] for r in existing}
            if release["tag_name"] in existing_tags:
                print(f"    SKIP: {release['tag_name']} already exists (idempotency check)")
                skipped_releases += 1
                continue
            
            if create_release(target_repo, release, source_repo):
                print(f"    SUCCESS: Created {release['tag_name']}")
                migrated_releases += 1
            else:
                print(f"    FAILED: Could not create {release['tag_name']}")
                skipped_releases += 1
            
            # Wait between creations to ensure proper ordering
            if i < 5:
                time.sleep(2)  # Longer wait for first few
            else:
                time.sleep(1)
        
        print(f"\nReleases: {migrated_releases} created, {skipped_releases} skipped/failed")
    else:
        # Standard migration (skip existing) - IDEMPOTENT
        existing_releases_list = get_all_releases(target_repo)
        existing_releases = {r["tag_name"] for r in existing_releases_list}
        print(f"Found {len(existing_releases)} existing releases in target repository")

        migrated_releases = 0
        skipped_releases = 0

        for release in sorted_releases:
            if release["tag_name"] in existing_releases:
                print(f"  SKIP: {release['tag_name']} (already exists - idempotency)")
                skipped_releases += 1
                continue

            print(f"  Creating: {release['tag_name']} - {release.get('name', 'N/A')[:50]}")
            
            # Double-check before creating (idempotency)
            current_existing = {r["tag_name"] for r in get_all_releases(target_repo)}
            if release["tag_name"] in current_existing:
                print(f"    SKIP: {release['tag_name']} was created by another process")
                skipped_releases += 1
                continue
            
            if create_release(target_repo, release, source_repo):
                print(f"    SUCCESS: Created {release['tag_name']}")
                migrated_releases += 1
            else:
                print(f"    FAILED: Could not create {release['tag_name']}")
                skipped_releases += 1
            time.sleep(1)  # Rate limiting

        print(f"\nReleases: {migrated_releases} migrated, {skipped_releases} skipped")
    
    return migrated_releases, skipped_releases


def get_existing_issue_by_title(target_repo: str, title: str) -> dict[str, Any] | None:
    """Check if an issue with the same title already exists."""
    issues = get_all_issues(target_repo)
    for issue in issues:
        if issue["title"] == title:
            return issue
    return None


def get_existing_comments(target_repo: str, issue_number: int) -> list[dict[str, Any]]:
    """Get all existing comments for an issue."""
    return get_issue_comments(target_repo, issue_number)


def migrate_issues(source_repo: str, target_repo: str) -> tuple[int, int, int]:
    """Migrate all issues from source to target. Idempotent - checks for existing issues."""
    print("\n" + "=" * 60)
    print("STEP 2: MIGRATING ISSUES")
    print("=" * 60)
    issues = get_all_issues(source_repo)
    print(f"Found {len(issues)} issues in source repository")

    # Get existing issues by title for idempotency (including closed ones)
    print("Checking for existing issues (including closed)...")
    existing_issues = get_all_issues(target_repo)
    # Map by title, preferring open issues if duplicates exist
    existing_by_title = {}
    for issue in existing_issues:
        title = issue["title"]
        if title not in existing_by_title:
            existing_by_title[title] = issue
        elif issue["state"] == "open" and existing_by_title[title]["state"] == "closed":
            # Prefer open issue if we have both open and closed
            existing_by_title[title] = issue
    print(f"Found {len(existing_by_title)} unique issue titles in target repository")

    migrated_issues = 0
    skipped_issues = 0
    failed_issues = 0

    for idx, issue in enumerate(issues, 1):
        print(f"\n[{idx}/{len(issues)}] Issue #{issue['number']}: {issue['title'][:60]}")

        # Check if issue already exists (idempotency)
        if issue["title"] in existing_by_title:
            existing_issue = existing_by_title[issue["title"]]
            print(f"  SKIP: Issue already exists (#{existing_issue['number']})")
            skipped_issues += 1
            
            # Check if metadata footer is missing and add it
            body = existing_issue.get("body") or ""
            if "Migrated from:" not in body:
                print("  Adding missing metadata footer...")
                footer = create_metadata_footer(issue, source_repo)
                new_body = body + footer
                update_issue_body(target_repo, existing_issue["number"], new_body)
            
            # Check if comments need to be migrated
            source_comments = get_issue_comments(source_repo, issue["number"])
            existing_comments = get_existing_comments(target_repo, existing_issue["number"])
            
            if source_comments and len(source_comments) > len(existing_comments):
                print(f"  Migrating {len(source_comments) - len(existing_comments)} missing comments...")
                for comment in source_comments[len(existing_comments):]:
                    if create_issue_comment(target_repo, existing_issue["number"], comment):
                        pass  # Success
                    time.sleep(0.5)
            continue

        # Issue doesn't exist, create it
        # Try with milestone first, then without if it fails
        new_issue = create_issue(target_repo, issue, skip_milestone=False)
        if not new_issue:
            # Retry without milestone
            print("  Retrying without milestone...")
            new_issue = create_issue(target_repo, issue, skip_milestone=True)

        if new_issue:
            print(f"  SUCCESS: Created issue #{new_issue['number']}")
            migrated_issues += 1

            # Add metadata footer
            body = issue.get("body") or ""
            footer = create_metadata_footer(issue, source_repo)
            new_body = body + footer
            update_issue_body(target_repo, new_issue["number"], new_body)

            # Migrate comments
            comments = get_issue_comments(source_repo, issue["number"])
            if comments:
                print(f"  Migrating {len(comments)} comments...")
                for comment in comments:
                    if create_issue_comment(target_repo, new_issue["number"], comment):
                        pass  # Success
                    time.sleep(0.5)
                print(f"  Completed: {len(comments)} comments migrated")
        else:
            print("  FAILED: Could not create issue")
            failed_issues += 1

        time.sleep(1)  # Rate limiting

    print(f"\nIssues: {migrated_issues} migrated, {skipped_issues} skipped, {failed_issues} failed")
    return migrated_issues, skipped_issues, failed_issues


def fix_migrated_issues(source_repo: str, target_repo: str) -> tuple[int, int, int]:
    """Fix migrated issues to preserve all metadata."""
    print("\n" + "=" * 60)
    print("STEP 3: FIXING MIGRATED ISSUES - PRESERVING ALL METADATA")
    print("=" * 60)

    # Get all source issues
    print("\nFetching source issues...")
    source_issues = get_all_issues(source_repo)
    print(f"Found {len(source_issues)} issues in source repository")

    # Create mapping by title (best we can do to match)
    source_by_title = {issue["title"]: issue for issue in source_issues}

    # Get all target issues
    print("\nFetching target issues...")
    target_issues = get_all_issues(target_repo)
    print(f"Found {len(target_issues)} issues in target repository")

    # Match issues by title
    matched = 0
    updated = 0
    closed = 0
    failed = 0

    for target_issue in target_issues:
        title = target_issue["title"]
        if title not in source_by_title:
            continue

        matched += 1
        source_issue = source_by_title[title]

        print(f"\n[{matched}/{len(target_issues)}] Issue #{target_issue['number']}: {title[:60]}")

        # Check if body needs metadata footer
        body = target_issue.get("body") or ""
        needs_footer = "Migrated from:" not in body

        # Check if state needs to be fixed
        needs_close = source_issue["state"] == "closed" and target_issue["state"] == "open"

        if needs_footer or needs_close:
            # Add metadata footer if needed
            if needs_footer:
                footer = create_metadata_footer(source_issue, source_repo)
                new_body = body + footer
                print("  Adding metadata footer...")
                if update_issue_body(target_repo, target_issue["number"], new_body):
                    print("    SUCCESS: Body updated")
                    updated += 1
                else:
                    print("    FAILED: Could not update body")
                    failed += 1

            # Close issue if needed
            if needs_close:
                print("  Closing issue (was closed in original)...")
                if close_issue(target_repo, target_issue["number"]):
                    print("    SUCCESS: Issue closed")
                    closed += 1
                else:
                    print("    FAILED: Could not close issue")
                    failed += 1
        else:
            print("  Already correct (metadata present, state matches)")

        time.sleep(1)  # Rate limiting

    print(f"\nFix: {matched} matched, {updated} updated, {closed} closed, {failed} failed")
    return matched, updated, closed


def verify_and_fix_remaining(source_repo: str, target_repo: str) -> int:
    """Verify all issues are correctly closed and fix any remaining."""
    print("\n" + "=" * 60)
    print("STEP 4: VERIFYING AND FIXING REMAINING ISSUES")
    print("=" * 60)
    print("Verifying issue states...")

    # Get source closed issues
    source_closed = get_all_issues(source_repo, "closed")
    source_closed_titles = {issue["title"]: issue for issue in source_closed}

    # Get target open issues
    target_open = get_all_issues(target_repo, "open")

    # Find open issues that should be closed
    to_close = []
    for target_issue in target_open:
        title = target_issue["title"]
        if title in source_closed_titles:
            to_close.append((target_issue["number"], title))

    closed_count = 0
    if to_close:
        print(f"\nFound {len(to_close)} open issues that should be closed:")
        for num, title in to_close:
            print(f"  #{num}: {title[:60]}")
            if close_issue(target_repo, num):
                print(f"    Closed")
                closed_count += 1
            time.sleep(1)
    else:
        print("\nAll issue states are correct!")

    print(f"\nTotal source closed issues: {len(source_closed)}")
    print(f"Total target open issues: {len(target_open)}")
    return closed_count


def migrate_discussions(source_repo: str, target_repo: str) -> int:
    """Migrate discussions (note: limited API support)."""
    print("\n" + "=" * 60)
    print("STEP 5: MIGRATING DISCUSSIONS")
    print("=" * 60)
    print("NOTE: Discussions require GraphQL and may have limitations")

    discussions = get_all_discussions(source_repo)
    print(f"Found {len(discussions)} discussions in source repository")

    if discussions:
        print("WARNING: Discussion migration requires manual setup or GitHub Support")
        print("         Discussions cannot be migrated via API automatically")
        print(f"         Found {len(discussions)} discussions that need manual migration")
    else:
        print("No discussions found to migrate")

    return len(discussions)


def main():
    parser = argparse.ArgumentParser(description="Migrate repository metadata between GitHub repositories")
    parser.add_argument("--source", default="NickHugi/PyKotor", help="Source repository (default: NickHugi/PyKotor)")
    parser.add_argument("--target", default="OldRepublicDevs/PyKotor", help="Target repository (default: OldRepublicDevs/PyKotor)")
    parser.add_argument("--fix-only", action="store_true", help="Only fix existing migrated issues, don't migrate new ones")
    parser.add_argument("--recreate-releases", action="store_true", help="Delete all existing releases and recreate in exact chronological order")
    args = parser.parse_args()

    source_repo = args.source
    target_repo = args.target

    print("=" * 60)
    print("MIGRATING ALL METADATA FROM SOURCE TO TARGET")
    print("=" * 60)
    print(f"Source: {source_repo}")
    print(f"Target: {target_repo}")
    print("\nNOTE: GitHub API limitations prevent preserving exact timestamps")
    print("      and original authors. All other metadata will be preserved.\n")

    if args.fix_only:
        # Only fix existing issues
        matched, updated, closed = fix_migrated_issues(source_repo, target_repo)
        verify_and_fix_remaining(source_repo, target_repo)
    else:
        # Full migration
        migrated_releases, skipped_releases = migrate_releases(source_repo, target_repo, recreate_in_order=args.recreate_releases)
        migrated_issues, skipped_issues, failed_issues = migrate_issues(source_repo, target_repo)
        matched, updated, closed = fix_migrated_issues(source_repo, target_repo)
        verify_and_fix_remaining(source_repo, target_repo)
        discussions_count = migrate_discussions(source_repo, target_repo)

        # Summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Releases:  {migrated_releases} migrated, {skipped_releases} skipped")
        print(f"Issues:    {migrated_issues} migrated, {skipped_issues} skipped, {failed_issues} failed")
        print(f"Fixed:     {matched} matched, {updated} updated, {closed} closed")
        print(f"Discussions: {discussions_count} found (require manual migration)")
        print("\nMigration complete!")


if __name__ == "__main__":
    main()

