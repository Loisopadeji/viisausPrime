# ViisausPrime: Step-by-Step Deployment Guide

This guide takes you from the folder on your computer to a live web link you
can put in your presentation. It assumes you have never deployed anything
before. Follow it in order and do not skip steps.

**Total time: about 20 minutes. Total cost: zero.**

---

## Before you start: what you need

1. A **GitHub account** (free): https://github.com/signup
2. **Git** installed on your computer: https://git-scm.com/downloads
   - During installation just click Next on every screen, the defaults are fine.
3. This project folder on your computer.

---

## PART 1: Test the app on your own computer first

Always check it works locally before deploying. If it breaks later, you will
know the problem is the deployment, not the code.

**Step 1.** Open your terminal.
- Windows: press the Start key, type `cmd`, press Enter.
- Mac: press Cmd + Space, type `terminal`, press Enter.

**Step 2.** Navigate into the project folder. Type `cd ` (with a space), then
drag the `viisausprime` folder onto the terminal window and press Enter.

**Step 3.** Install the libraries the app needs:

```
pip install -r requirements.txt
```

Wait for it to finish. It may take two or three minutes.

**Step 4.** Start the app:

```
streamlit run streamlit_app.py
```

Your browser should open automatically at `http://localhost:8501` and show the
Executive Dashboard. Click through every page in the sidebar to check they all
load.

**Step 5.** To stop the app, click the terminal window and press `Ctrl + C`.

> **If you get an error at this stage**, read the last line of the red text in
> the terminal. It usually names the exact problem, most often a missing
> library. Running Step 3 again fixes most issues.

---

## PART 2: Put your project on GitHub

Streamlit Cloud does not read files from your computer. It reads them from
GitHub. So the project has to live there first.

**Step 1.** Go to https://github.com/new

**Step 2.** Fill in the form:
- **Repository name:** `viisausprime`
- **Description:** Predictive business intelligence for internal Operations
- **Public or Private:** choose **Public**.
  - Public is required for unlimited free apps. Free accounts only get one
    private app. Your data here is an internal operations dataset, so if that
    is sensitive, choose Private and accept the one-app limit.
- **Do NOT tick** "Add a README file". Leave all three checkboxes empty.

**Step 3.** Click **Create repository**.

**Step 4.** GitHub now shows you a setup page. Ignore it and come back to your
terminal. Make sure you are still inside the `viisausprime` folder, then run
these commands **one line at a time**, pressing Enter after each:

```
git init
git add .
git commit -m "ViisausPrime v1"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/viisausprime.git
git push -u origin main
```

**Replace `YOUR-USERNAME` with your actual GitHub username** in that second-to-last
line. If your username is `loisidam`, the line becomes:

```
git remote add origin https://github.com/loisidam/viisausprime.git
```

**Step 5.** Git will ask you to sign in. A browser window opens, click
**Authorize**. If it asks for a password in the terminal instead, note that
GitHub no longer accepts your account password there. You need a Personal
Access Token: go to GitHub, click your profile picture, then Settings,
Developer settings, Personal access tokens, Tokens (classic), Generate new
token. Tick the `repo` box, generate it, copy the token, and paste that as the
password.

**Step 6.** Refresh your GitHub repository page in the browser. You should now
see all your files listed: `streamlit_app.py`, `requirements.txt`, the `src`
folder and the `data` folder. If `data` is missing, the app will not work, so
check it is there.

---

## PART 3: Deploy to Streamlit Community Cloud

**Step 1.** Go to https://share.streamlit.io

**Step 2.** Click **Sign in with GitHub** and authorise the connection.

**Step 3.** Click the **Create app** button (top right).

**Step 4.** Choose **Deploy a public app from GitHub**.

**Step 5.** Fill in the three fields:
- **Repository:** `YOUR-USERNAME/viisausprime`
- **Branch:** `main`
- **Main file path:** `streamlit_app.py`

**Step 6.** Click **Advanced settings** and set **Python version** to `3.11`.
This avoids version conflicts with the libraries.

**Step 7.** Click **Deploy**.

You will see a build log scrolling. This takes three to five minutes on the
first deploy, because it is installing every library from scratch. Do not close
the tab.

**Step 8.** When it finishes, your app is live at a link like:

```
https://viisausprime.streamlit.app
```

**That is the link you share with your CEO and put in your submission.**

---

## PART 4: Updating your app later

You do not redeploy. Just push your changes and the live app updates itself,
usually within a minute.

```
git add .
git commit -m "describe what you changed"
git push
```

---

## Things to know before you present

**The app sleeps.** On the free tier, if nobody opens the app for 12 hours it
goes to sleep. The next visitor sees a "waking up" screen for roughly 30
seconds, then it loads normally. **Open your app yourself 10 minutes before
your presentation** so it is already awake when your audience clicks in.

**Free tier limits.** Roughly 1 GB of memory, unlimited public apps but only
one private app, and no custom domain, so your address will end in
`.streamlit.app`. None of this matters for a presentation or an internal
pilot. If the tool later becomes something clients use daily, Render or
Railway offer always-on hosting for a few dollars a month.

**Your data is in the repository.** If you chose a public repo, anyone with
the link can see the CSV. If that is a problem, delete the repo and redo Part 2
choosing Private instead.

---

## If something goes wrong

**The app shows a red error about a missing file.**
The `data` folder did not upload. Check it appears on GitHub. If `.gitignore`
is blocking it, remove any line mentioning `data` from that file, then push
again.

**The app shows "ModuleNotFoundError".**
A library is missing from `requirements.txt`. Add the missing name to the
file, push, and the app rebuilds automatically.

**The build log fails on installing packages.**
Set the Python version to 3.11 in Advanced settings, then click Reboot app
from the app menu.

**The app is stuck on "waking up".**
Go to share.streamlit.io, find your app, click the three dots, and choose
**Reboot app**.
