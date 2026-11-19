# Security policy

## Supported versions

Security fixes go into the latest release only. ESO Armory is in beta, and the
[changelog](../CHANGELOG.md) says when an upgrade needs care.

## Reporting a vulnerability

**Please don't open a public issue.** Report it privately through GitHub:
go to the repository's **Security** tab and choose **Report a vulnerability**
([direct link](https://github.com/spanthetree/eso-armory/security/advisories/new)).

Include what you can of:

- the version or commit, and how the server is run (behind which reverse proxy, if any);
- the steps to reproduce it, and what an attacker gains.

You should get a reply within a week. Once a fix is released, the advisory is
published with credit to you, unless you'd rather not be named.

## What counts

[docs/architecture.md](../docs/architecture.md#security-model) describes the
boundaries the server is meant to keep. A way across one of them is a
vulnerability, for example:

- reading, changing or deleting another account's workspace without its
  password, session or share code;
- getting admin rights without being a configured, password-protected admin account;
- script injection through uploaded SavedVariables, imported build codes or
  any other user-supplied text;
- reading or writing files outside the upload folder, or running commands,
  from an uploaded file.

Not vulnerabilities on their own:

- Claiming an account that has **no password** by uploading a file that names
  it. Account names come from files the user controls; a password is what
  proves ownership. Set one after your first upload.
- Plain HTTP. The server expects a reverse proxy with TLS in front of it.
- Issues in a third-party dependency, unless ESO Armory's own use of it makes
  them exploitable. Report those upstream.
