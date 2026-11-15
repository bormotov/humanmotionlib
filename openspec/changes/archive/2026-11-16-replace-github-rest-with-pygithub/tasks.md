# Tasks

## 1. Dependency and setup

- [x] 1.1 Declare and lock a Python 3.14-compatible PyGithub release-tool group; verify a fresh locked installation, client import, dependency consistency and unchanged runtime wheel requirements.
- [x] 1.2 Provision the locked release environment for both workflow release commands and document contributor setup; verify the documented commands and workflow interpreter selection.
- [x] 1.3 Check the licenses and distribution conditions of PyGithub and its new dependencies; update the materials register and notices as needed, and verify each recorded source and condition.

## 2. GitHub integration

- [x] 2.1 Replace the custom GitHub HTTP client with PyGithub release history, creation, update and ID lookup operations; test pagination, missing results, permission failures, fresh reads and safe diagnostics.
- [x] 2.2 Migrate asset listing, upload and binary download to PyGithub; test wheel and checksum byte preservation, matching retries and conflicting assets.
- [x] 2.3 Replace HTTP-opener tests with controlled SDK fixtures and SDK-contract checks; verify no project-authored GitHub REST calls remain and Git-only commands work without the release group.
- [x] 2.4 Cover a create response followed by an `untagged-*` read by ID and a matching positive control; verify diagnostics contain expected and returned identities without secrets and conflicting drafts are not published.

## 3. Integration and review

- [x] 3.1 Run release-policy and workflow tests against clean locked environments and a controlled publication using the built wheel; verify source commit, wheel filename, checksum, release assets and successful/failed outcomes.
- [x] 3.2 Conduct the required nonvisual pre-freeze audit and independent review; record candidate identity, verification results, license evidence and role-owned cleanup in the change hand-off.
