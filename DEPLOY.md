# Running Nicomachus on a server (on when your machine is off)

The web app is a plain container. Any host that runs a `Dockerfile` will serve
it. Three routes below, cheapest and simplest first. **Every one needs you to
sign in to that host once** — I can't create accounts or enter payment
details, and a hosting account is tied to your identity and (sometimes) card.
Everything up to that point is done.

Whatever you pick, set two secrets on the host:

| secret | required? | value |
|---|---|---|
| `NICOMACHUS_TOKEN` | **yes** | any long random string — it's the password for the web page. The server refuses to face the internet without it. |
| `ANTHROPIC_API_KEY` | optional | `sk-ant-...` — enables written answers, note distillation, Reflect. Without it the site still does retrieval, library, search. |
| `GEMINI_API_KEY` | optional | `AIza...` — alternative to the above (free tier). |

Generate a token: run `python -c "import secrets;print(secrets.token_urlsafe(32))"`.

---

## 1. Render  — free, no credit card

Simplest no-card route. Sleeps after 15 min idle, ~50s to wake on next visit.

1. Account at **render.com** (sign in with GitHub is easiest).
2. **New → Web Service** → connect the repo `tmvarun55-maker/nicomachus`.
3. It detects the `Dockerfile`. Instance type: **Free**.
4. **Environment** → add:
   - `NICOMACHUS_TOKEN` = a long random string (the web-page password)
   - `ANTHROPIC_API_KEY` = `sk-ant-...`  (optional)
   - `PORT` = `10000`   (Render's expected port)
5. **Create Web Service**. First build takes a few minutes.
6. It serves at `https://nicomachus-XXXX.onrender.com`. Open it, enter the token.
7. **Settings → Health Checks** → set the path to `/healthz` and save. Without
   this, Render can't tell when the container is ready and traffic flaps
   between the instance and a `no-server` edge response.

> The default install no longer includes `google-genai` — it is heavy enough
> to push a 512MB free instance into memory pressure (the symptom is ~50% of
> requests returning `no-server` with nothing in the logs). If you want Gemini
> instead of Claude, uncomment it in `requirements.txt` and use a paid
> instance, or just set `ANTHROPIC_API_KEY`.

Enable **Auto-Deploy** so every push to `main` — including the nightly study
commits — rebuilds with the latest corpus.

> Note: HuggingFace Spaces used to be the free pick, but Docker Spaces now
> require a paid plan, so this is the free route instead.

---

## 2. Fly.io  — always-on (no sleep), needs a card on file (not charged within the free allowance)

1. Install flyctl: `iwr https://fly.io/install.ps1 -useb | iex`  (PowerShell)
2. `fly auth signup`  (or `fly auth login`)
3. From this folder:
   ```
   fly launch --no-deploy --copy-config --name nicomachus
   fly secrets set NICOMACHUS_TOKEN=your-random-string
   fly secrets set ANTHROPIC_API_KEY=sk-ant-...      # optional
   fly deploy
   ```
`fly.toml` here keeps one machine running (`min_machines_running = 1`) and
health-checks `/healthz`. The free allowance covers a single shared-cpu-1x.

---

## 3. Render  — free, no card, but sleeps after 15 min idle

1. Account at **render.com**.
2. **New → Web Service** → connect the GitHub repo `tmvarun55-maker/nicomachus`.
3. Environment: **Docker**. It reads the `Dockerfile`.
4. Add env vars `NICOMACHUS_TOKEN` (and optionally `ANTHROPIC_API_KEY`).
5. Create. First hit after idle takes ~50s to cold-start; fine for occasional use.

---

## Keeping the hosted copy current

The nightly GitHub Actions cycle commits new material to this repo. To feed
that into the hosted instance:

- **Hugging Face**: `git pull origin main && git push hf main` (a shell alias
  or a second scheduled action can do this).
- **Fly / Render**: they redeploy on push to `main` if you enable auto-deploy,
  which rebuilds the image with the latest committed corpus.

The hosted instance's *own* study cycles are not saved across restarts unless
you attach a persistent volume — treat the hosted copy as the read/ask
front end, and the GitHub cron as the thing that actually grows the corpus.
