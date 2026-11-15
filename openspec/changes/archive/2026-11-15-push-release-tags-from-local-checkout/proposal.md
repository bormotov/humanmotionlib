# Proposal

## Why

The first attempted `0.3.1` publication received the tested wheel, then stopped when GitHub returned a draft with a temporary tag name. The publisher expected the final tag name before it had pushed the Git tag.

## What Changes

- After CI verifies a qualifying push and its wheel, create the version tag in the publisher's local checkout and push only that tag to `origin`.
- Create the GitHub Release for the existing tag, with the tested wheel and its checksum. A retry can continue from an already pushed tag on the same commit.
- Document the recovery decision for the existing `0.3.1` draft using evidence from the original run.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `release-publication` requires the version tag to be pushed before the publisher creates a release draft and defines retry behavior after the tag push.

## Impact

The release helper, its publish job and focused tests, and the contributor release instructions change. Ordinary build and test jobs, version eligibility, and the release artifact format stay in place. The visual gate does not apply to this publishing change.
