# Contributing

Changes must preserve the repository boundary:

- Put cross-System behavior and constellation-wide policy here.
- Put domain behavior in the narrowest owning System.
- Reference System contracts instead of copying their domain documentation.
- Commit no provider configuration, personal path, credential, or runtime state.
- Add no daemon, service, shared database, plugin registry, or synchronized
  constellation release manifest.

Before opening a pull request, run:

```sh
bash scripts/check.sh
git diff --check
```

Use a Conventional Commit title so the independent release workflow can derive
the correct semantic version.
