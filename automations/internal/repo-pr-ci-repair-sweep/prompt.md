# Repo PR CI Repair Sweep

Run a daily CI repair and merge-conflict sweep across repositories owned by the authenticated GitHub user and their organizations. Treat existing local repositories as read-only context. Put every mutable PR checkout in a fresh temporary directory and remove only automation-created temporary checkouts after use.

## Scope

- Repo PRs are open pull requests in repositories owned by the authenticated user or an organization returned by `gh api user/orgs`.
- Inbox PRs are Repo PRs assigned to `@me`, requesting review from `@me`, reporting failing checks, or reporting merge conflicts or non-mergeability.
- Process only clearly internal PRs. Accept proof from owner/member/collaborator association, a same-repository branch, a head repository owned by a discovered owner, or a trusted dependency automation account in an owner repository.
- A CI candidate has failing GitHub Actions checks. External check providers are report-only unless the same failure is reproduced in GitHub Actions logs.
- A merge-conflict candidate is reported as not cleanly mergeable after check failures and review-only blockers are excluded.
- Classify every discovered Inbox PR as green, pending, fixed, rebased, rerun, skipped, or blocked with a concrete reason.

## Start and discover

1. Run `gh auth status`, resolve the login with `gh api user --jq .login`, and list organization owners with `gh api user/orgs --paginate --jq '.[].login'`.
2. Read applicable agent instructions. When an installed GitHub CI-fix skill is available, read it and use its inspection helpers after checkout; never locate it through a workspace source path.
3. For each owner, run these owner-scoped searches and deduplicate by URL:

   - `gh search prs --owner <owner> --state open --review-requested @me --json url,repository,title,author,updatedAt -L 200`
   - `gh search prs --owner <owner> --state open --assignee @me --json url,repository,title,author,updatedAt -L 200`
   - `gh search prs --owner <owner> --state open --checks failure --json url,repository,title,author,updatedAt -L 200`

   Mark truncated searches blocked while continuing with complete results.
4. Fetch full PR metadata, including base and head OIDs, repository ownership, author association, draft state, merge state, and status checks. Use the pull-request API when the CLI omits author association.

## Classify

Inspect the check rollup and `gh pr checks`. For failing Actions checks, inspect the run and logs and retain the failing command plus the smallest useful excerpt. Report pending-only and external-only checks without changing them. Rerun failed jobs once only when evidence identifies transient infrastructure.

Always inspect mergeability. Missing checks or reviews are pending, not conflicts. A conflicted branch may only be rebased onto the current base. If rebase conflicts occur, abort immediately and report the conflicted files and command output. Do not resolve conflicts manually or create merge commits.

## Repair

For each processable candidate, create an isolated checkout with `mktemp -d`, fetch the inspected head, and verify local `HEAD` equals the inspected head OID before mutation. Read the repository instructions and relevant setup, package-manager, and test documentation.

Fix only the observed CI cause, such as a dependency lockfile, generated metadata, a small compatibility change, or a test fixture whose dependency behavior clearly changed. Block changes that require product judgment or broad refactoring.

Run the smallest repository-native reproduction or validation command. Commit only a small relevant diff after validation, using `Fix CI for PR <number>`. Push only to the inspected PR head branch. For a clean rebase, create no commit; use `--force-with-lease` only for trusted automation branches owned by a discovered owner. Never merge, approve, close, or change repository settings.

After any push, rebase, or rerun, refresh checks and merge metadata.

## Report

Start with counts for owners searched, PRs discovered, processable PRs, CI candidates, merge-conflict candidates, fixed, rebased, rerun, skipped, and blocked. For every non-green classification, include the PR URL, repository, observed signal, cause or skip reason, validation command, pushed SHA when applicable, and current state.

State explicitly when authentication, search truncation, push access, missing secrets, external providers, rebase conflicts, or force-push restrictions prevented a fix. Do not claim completion until every discovered Inbox PR has a terminal classification.
