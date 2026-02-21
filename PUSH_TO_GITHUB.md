# Push this project to GitHub

Run these commands **in your terminal** from the project folder. (Cursor’s sandbox can’t run git write/network for you.)

## 1. Go to the project folder

```bash
cd /Users/ch4nbin/stigma-dei-policy-pipeline
```

## 2. Create a new git repo here (ignore parent repo)

```bash
git init
```

## 3. Add all files (`.gitignore` excludes data files and __pycache__)

```bash
git add .
git status
```

## 4. First commit

```bash
git commit -m "Initial commit: Chronicle DEI scraper"
```

## 5. Point at your GitHub repo and push

```bash
git remote add origin https://github.com/ch4nbin/stigma-dei-policy-pipeline.git
git branch -M main
git push -u origin main
```

If GitHub asks for auth, use a **Personal Access Token** as the password (or SSH if you have it set up).

---

## Done

- **Credentials:** Your Chronicle email/password were removed from the code. To run the scraper, pass them each time:
  ```bash
  python3 scraper.py --email your-email@example.com --password your-password
  ```
  or set env vars and change the script to read them.
- **Scraped data:** `chronicle_dei_data.csv`, `.json`, and `.xlsx` are in `.gitignore` so they won’t be pushed (keeps the repo small and avoids publishing scraped data). Remove those lines from `.gitignore` if you want to commit sample data.
