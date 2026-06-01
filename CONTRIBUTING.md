# Contributing to dash-social-signin

Contributions are welcome. Bug reports, feature requests, documentation improvements, and code changes.

---

## Reporting a bug

1. Check the [existing issues](https://github.com/budescode/dash-social-signin/issues) first to avoid duplicates.
2. Open a new issue and include:
   - A clear title describing the problem
   - Steps to reproduce it
   - What you expected vs what actually happened
   - Your Python version, Dash version, and OS
   - Any relevant error messages or tracebacks

---

## Requesting a feature

Open an issue with the label `enhancement`. Describe:
- What you want to do that you currently can't
- Why it would be useful
- Any ideas on how it could work

---

## Submitting a pull request

**1. Fork the repo and create a branch**

```bash
git checkout -b fix/your-fix-name
# or
git checkout -b feat/your-feature-name
```

**2. Set up the dev environment**

```bash
pip install -e ".[examples]"
```

**3. Make your changes**

- Keep changes focused — one fix or feature per PR
- Don't change unrelated code
- Test your changes against the example app before submitting

**4. Open the pull request**

- Write a clear title and description explaining what changed and why
- Reference any related issue (e.g. `Closes #12`)

---

## Adding a new provider

Each provider is configured in `src/dash_social_signin/oauth.py` under `PROVIDER_CONFIG`. To add one:

1. Add the provider entry with its `auth_url`, `token_url`, `userinfo_url`, and `pkce` flag
2. Test the full flow (auth start → callback → userinfo)
3. Add it to the provider list in `README.md` and `docs/PROVIDERS.md`
4. Open a PR with the provider name in the title

---

## Questions

For general questions, open a [GitHub Discussion](https://github.com/budescode/dash-social-signin/discussions) rather than an issue.

---

## Code of conduct

Be respectful and constructive. We're here to build something useful together.
