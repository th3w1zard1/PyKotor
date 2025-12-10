#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delete duplicate issues, keeping the oldest one."""

from __future__ import annotations

import json
import subprocess
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
        return None

    if result.stdout and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
    return None


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


def close_issue(repo: str, issue_number: int) -> bool:
    """Close an issue."""
    data = {"state": "closed"}
    endpoint = f"repos/{repo}/issues/{issue_number}"
    result = run_gh_api(endpoint, "PATCH", data)
    return result is not None


def main():
    repo = "OldRepublicDevs/PyKotor"
    
    print("Finding duplicate issues...")
    issues = get_all_issues(repo)
    
    # Group by title
    issue_titles = {}
    for issue in issues:
        title = issue["title"]
        if title not in issue_titles:
            issue_titles[title] = []
        issue_titles[title].append(issue)
    
    # Find duplicates
    duplicates_to_delete = []
    for title, issues_list in issue_titles.items():
        if len(issues_list) > 1:
            # Sort by created_at, keep oldest
            sorted_issues = sorted(issues_list, key=lambda x: x.get("created_at", ""))
            # Delete all but the oldest
            for issue in sorted_issues[1:]:
                duplicates_to_delete.append(issue)
    
    if not duplicates_to_delete:
        print("No duplicates found!")
        return
    
    print(f"\nFound {len(duplicates_to_delete)} duplicate issues to delete")
    print("Keeping oldest issue for each title, deleting newer duplicates")
    
    deleted = 0
    failed = 0
    
    for issue in duplicates_to_delete:
        print(f"\nClosing duplicate issue #{issue['number']}: {issue['title'][:50]}")
        print(f"  Created: {issue.get('created_at', 'N/A')}")
        if close_issue(repo, issue["number"]):
            print(f"  SUCCESS: Closed #{issue['number']}")
            deleted += 1
        else:
            print(f"  FAILED: Could not close #{issue['number']}")
            failed += 1
        time.sleep(0.5)
    
    print(f"\nDeleted: {deleted}, Failed: {failed}")


if __name__ == "__main__":
    main()

