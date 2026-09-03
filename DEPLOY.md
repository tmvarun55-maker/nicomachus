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

## 1. Hugging Face Spaces  — free, no credit card, persistent

Best fit for a personal always-on instance.

1. Make an account at **huggingface.co** (free, email only).
2. **New → Space**. Name it `nicomachus`. **SDK: Docker**. Visibility: Private.
3. It gives you a git URL. Push this repo to it:
   ```
   git remote add hf https://huggingface.co/spaces/<your-username>/nicomachus
   git push hf main
   ```
4. Space → **Settings → Variables and secrets** → add `NICOMACHUS_TOKEN`
   (and `ANTHROPIC_API_KEY` if you have one).
5. In the Space's `README.md`, make sure the top frontmatter has `app_port: 7860`
   (the Dockerfile already exposes 7860). Add it if missing:
   ```
   ---
   title: Nicomachus
   sdk: docker
   app_port: 7860
   ---
   ```
6. It builds and comes up at `https://<your-username>-nicomachus.hf.space`.
   Open it, enter the token.

Free Spaces sleep after ~48h with no visitors and wake on the next request
(a few seconds). Fine for personal use. The corpus is baked into the image,
so every `git push hf main` — including pulling the nightly GitHub commits
first — refreshes what it knows.

---

## 2. Fly.io  — always-on, needs a card on file (not charged within the free allowance)

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
