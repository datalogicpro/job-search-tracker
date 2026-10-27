# job-search-tracker

A Django REST API that collects remote, entry-level Python developer jobs from
free job APIs, filters out jobs that don't fit, serves the rest through one API,
emails a daily digest of new jobs, and tracks the jobs you apply to.

Built for finding remote, entry-level, self-taught-friendly Python backend jobs
open to US residents, with startups (Y Combinator companies) marked.

## Features

- Fetches jobs from 8 sources in one command, with retries and backoff
- Filters out jobs that are senior (by title or by the source's job level), not remote,
  not open to US residents, closed, from recruiting agencies, not Python developer roles,
  or that require a degree or a security clearance
- Marks Y Combinator companies and unpaid jobs, so you can filter on them
- Daily digest email with each new job's details, a short preview, and its apply link,
  with every job sent only once
- Application tracking: a signed "Mark as applied" link for each job in the digest,
  and admin pages for status and notes
- Emails never include the name of the computer they were sent from
- Daily run on Windows through Task Scheduler, at most once a day, that starts and
  quits Docker Desktop by itself
- Structured JSON logs, with one run ID on every log line from a run
- Read-only REST API with search, filters, and pagination
- Tests that run without calling any live API or sending real email

## Tech stack

- Python 3.13, Django 6.1, Django REST Framework 3.18
- PostgreSQL 17 (Docker Compose)
- requests with urllib3 Retry, defusedxml
- Gmail SMTP through Django's `MAILERS` setting
- Django's `signing` module for the "Mark as applied" links
- Windows Task Scheduler and PowerShell for the daily run
- pytest and pytest-django

## Setup

Requires Python 3.13 and Docker.

1. Clone the repo and create a virtual environment:

   ```
   git clone https://github.com/datalogicpro/job-search-tracker.git
   cd job-search-tracker
   python -m venv .venv
   ```

2. Activate it:

   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - macOS or Linux: `source .venv/bin/activate`

3. Install the packages:

   ```
   pip install -r requirements-dev.txt
   ```

4. Copy `.env.example` to `.env` and fill in your values.
   `POSTGRES_PASSWORD` and the password in `DATABASE_URL` must match.
   For the digest email, `EMAIL_HOST_PASSWORD` must be a Gmail app password,
   which needs 2-Step Verification on the Gmail account.

5. Start PostgreSQL and create the tables:

   ```
   docker compose up -d
   python manage.py migrate
   ```

6. Create the admin sign-in, used for the admin pages:

   ```
   python manage.py createsuperuser
   ```

## Usage

Fetch jobs from every source:

```
python manage.py fetch_jobs
```

Fetch from one source only:

```
python manage.py fetch_jobs --source himalayas
```

Set `LOG_LEVEL=DEBUG` in `.env` to log every rejected job and the reason.

Email the digest of jobs not sent yet:

```
python manage.py send_digest
```

Print the digest without sending it or marking any job as sent:

```
python manage.py send_digest --dry-run
```

Start the API:

```
python manage.py runserver
```

## Daily run (Windows)

`scripts/run_daily.ps1` runs `fetch_jobs`, then `send_digest`. It:

- runs at most once a day, and skips when a run already finished that day
- starts Docker Desktop when it isn't running, and quits it at the end
  only if the script started it
- starts PostgreSQL and waits until it is healthy
- still runs `send_digest` when `fetch_jobs` fails
- writes one log file per day to `logs/`, keeps 30 days, and exits with
  code `1` when any step fails

Register the scheduled task, which runs the script every day at 6:00 AM and
2 minutes after you sign in to Windows:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\register_task.ps1
```

The task wakes the computer to run, runs as soon as possible after a missed start,
and runs as your user without administrator rights.

Run the script by hand:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\run_daily.ps1
```

Remove the scheduled task:

```
Unregister-ScheduledTask -TaskName "job-search-tracker daily" -Confirm:$false
```

## Application tracking

Each job in the digest email has a **Mark as applied** link. The link opens a page
with a **Mark as applied** button. Opening the link alone changes nothing, because
email providers and security tools often open links in emails to scan them.
Clicking the button records the application with today's date.

The links are signed with Django's `signing` module and `DJANGO_SECRET_KEY`,
so no sign-in is needed, and they expire after 30 days. They start with `SITE_URL`,
so the server must be running at that address for them to work.

Change an application's status (applied, interviewing, offer, rejected, withdrawn)
or add notes in the admin pages at `/admin/`. Jobs with an application can't be
deleted, so fetching and clearing jobs never removes your tracking.

## API

| Endpoint | Description |
| --- | --- |
| `GET /api/jobs/` | List open jobs, newest first, 50 per page |
| `GET /api/jobs/<id>/` | One job, with its full description |
| `GET /health/` | `200` when the app and database are up, `503` when the database is down |
| `GET, POST /applications/mark/<token>/` | The "Mark as applied" page and button |

Query parameters for the list:

| Parameter | Example | Description |
| --- | --- | --- |
| `source` | `?source=hackernews` | Jobs from one source |
| `yc` | `?yc=true` | Only Y Combinator companies |
| `unpaid` | `?unpaid=false` | Hide unpaid jobs |
| `applied` | `?applied=false` | Hide jobs you applied to (`true` shows only those) |
| `q` | `?q=django` | Search job titles |
| `days` | `?days=7` | Jobs posted in the last N days |

## Tests

PostgreSQL must be running (`docker compose up -d`). pytest creates a separate
test database, so your saved jobs are not touched.

```
python -m pytest
```

## Data sources

Job data comes from these sources. Every job links back to its original posting,
and applications go through the source's own link.

- [Himalayas](https://himalayas.app): data from Himalayas
- [Remote OK](https://remoteok.com): jobs from Remote OK
- [We Work Remotely](https://weworkremotely.com): jobs from the We Work Remotely RSS feed
- [Jobicy](https://jobicy.com): jobs from Jobicy
- [The Muse](https://www.themuse.com): jobs from The Muse public API
- [Hacker News](https://news.ycombinator.com): monthly "Who is hiring?" posts, through
  [HN Search by Algolia](https://hn.algolia.com)
- [JSearch](https://rapidapi.com) on RapidAPI
- [TheirStack](https://theirstack.com)
- [yc-oss/api](https://github.com/yc-oss/api): Y Combinator company list

This project is not affiliated with any of these sources.

## Author

datalogicpro