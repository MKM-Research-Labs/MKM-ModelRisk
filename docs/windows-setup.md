# Setting up MKM-ModelRisk on Windows

A step-by-step guide for Windows 10/11 that assumes **no prior setup** — no
Python, no database, and no experience with a command line. You will not need to
type any commands.

Everything installs into your own user account and the repo folder. You do not
need to be an administrator, though Windows will ask permission once to install
the database.

---

## Step 1 — Download the code

1. Open the project page on GitHub in your browser.
2. Click the green **Code** button.
3. Click **Download ZIP**.

> If the page asks you to sign in, the repository is private — ask David for
> access first, then come back to this step.

## Step 2 — Unzip it

1. Find the downloaded file (usually in your **Downloads** folder). It is called
   something like `MKM-ModelRisk-main.zip`.
2. **Right-click** it and choose **Extract All…**
3. Change the destination to somewhere simple, such as `C:\ModelRisk`, and click
   **Extract**.

You should end up with a folder containing files like `README.md`, `app.py` and
**`START-HERE.bat`**.

## Step 3 — Run the starter

1. Open that folder.
2. **Double-click `START-HERE.bat`.**

A black window opens and tells you what it is doing. Leave it open.

> **"Windows protected your PC"** — Windows blocks files downloaded from the
> internet. Click **More info**, then **Run anyway**. This is expected.

**The first run installs Python and PostgreSQL.** Windows will pop up a box
asking *"Do you want to allow this app to make changes to your device?"* — click
**Yes**. This can take several minutes.

When it finishes it will say:

```
Installation finished.
Please DOUBLE-CLICK THIS FILE ONE MORE TIME to finish setup.
```

3. **Double-click `START-HERE.bat` again.** (Newly installed programs are not
   visible to the first window; running it again picks them up.)

This time it sets up the database and starts the application. It will ask:

```
Identity your changes are attributed to [david.kelly@mkmresearchlabs.com]:
```

Type your email address and press **Enter**. Everything you change in the system
is recorded against this name, so use your real address.

## Step 4 — Open it

When you see a line like `Running on http://127.0.0.1:5015`, open your browser
and go to:

**http://127.0.0.1:5015**

That is the application. Keep the black window open while you use it — closing
it stops the app.

---

## Using it again later

Double-click **`START-HERE.bat`** whenever you want to use it. It skips
everything already installed and just starts the application, which takes a few
seconds.

To stop the application, close the black window.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| "Windows protected your PC" | Click **More info** → **Run anyway**. |
| "winget was not found" | Open the **Microsoft Store**, search for **App Installer**, install/update it, then double-click `START-HERE.bat` again. |
| "Could not install Python automatically" | Install it manually from <https://www.python.org/downloads/windows/> and **tick "Add python.exe to PATH"** during setup. Then run `START-HERE.bat` again. |
| "Could not install PostgreSQL automatically" | Install it manually from <https://www.postgresql.org/download/windows/>, accepting the defaults. Then run `START-HERE.bat` again. |
| `initdb: cannot be run as Administrator` | You started it with **Run as administrator**. Close it and just double-click the file normally. |
| The window flashes and disappears | Right-click `START-HERE.bat` → **Edit** to confirm it is the real file, or ask David — the window is meant to stay open. |
| Anything else | Take a photo or screenshot of the black window and send it to David. The message in it says what failed. |

> **Note.** The database runs on port **5433**, deliberately not the usual 5432,
> so it will not interfere with any other PostgreSQL already on the machine.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
