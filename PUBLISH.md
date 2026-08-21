# Publish to GitHub as `stavanio/bhujab601`

## Option A — GitHub CLI

Install/authenticate `gh` if needed, then from the repo directory:

```bash
cd bhujab601
git init
git add .
git commit -m "Initial B601-RS bring-up and troubleshooting baseline"

gh auth login
gh repo create stavanio/bhujab601 --private --source=. --remote=origin --push
```

Change `--private` to `--public` only if you intentionally want this documentation public.

## Option B — create the empty repo in GitHub UI

Create an empty repository named:

```text
bhujab601
```

under:

```text
stavanio
```

Do not initialize it with a README, license, or `.gitignore`, because this bundle already contains them where appropriate.

Then:

```bash
cd bhujab601
git init
git add .
git commit -m "Initial B601-RS bring-up and troubleshooting baseline"
git branch -M main
git remote add origin git@github.com:stavanio/bhujab601.git
git push -u origin main
```

If using HTTPS instead of SSH:

```bash
git remote add origin https://github.com/stavanio/bhujab601.git
```

## Recommended repository visibility

Start **private** while the notes still contain setup-specific observations. Make it public later if desired.

## No license included

No open-source license is included by default. That means the repository remains copyrighted with no automatic grant of reuse rights. Add a license later only if you intentionally want to permit reuse.
