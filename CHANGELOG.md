# Changelog

All notable changes to this project are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Job sources: Himalayas, Remote OK, We Work Remotely, Jobicy, The Muse,
  Hacker News "Who is hiring?", JSearch, and TheirStack
- Y Combinator company marking from the yc-oss company list
- `fetch_jobs` command that runs every source, or one with `--source`,
  and keeps running when one source fails
- Filters for remote, open to US residents, closed, recruiting agency,
  blocked company, senior title, eligible role, Python developer job, and degree required
- Senior level filter that uses each source's job level field, keeping levels
  that also name a junior or entry level
- Security clearance filter that rejects jobs requiring a clearance
- `ALLOW_DEGREE_A_PLUS` setting to keep or reject jobs that call a degree "a plus"
- Unpaid job marking, with an `unpaid` API filter
- US location check using states, state codes, and US cities of 100,000+ people
- Read-only REST API at `/api/jobs/` with `source`, `yc`, `unpaid`, `q`, and `days` filters
- `/health/` endpoint that checks the database and returns `503` when it is down
- `send_digest` command that emails new jobs once each, with a `--dry-run` option
- `digest_sent_at` field that records when a job was sent in a digest
- Email backend that uses a fixed host name instead of the computer's name
  when greeting the mail server and in each Message-ID
- `Application` model with status, applied date, and notes; jobs with an
  application are protected from deletion
- Signed "Mark as applied" link for each job in the digest, opening a confirm page
  with a button, and expiring after 30 days
- `SITE_URL` setting for the links in the digest email
- Admin pages for applications, and an "Applied" column on the jobs list
- `applied` filter on `/api/jobs/`
- `scripts/run_daily.ps1` that runs `fetch_jobs` and `send_digest` at most once a day,
  starts and quits Docker Desktop when needed, and writes daily log files
- `scripts/register_task.ps1` that registers the Windows scheduled task for the daily run,
  at 6:00 AM and after sign-in
- `logs/` folder kept out of Git
- HTTP retries with backoff, and a timeout on every request
- Structured JSON logging, with a run ID on every log line from a fetch run
- Text fields cut to their database limits before saving
- Tests for every source, the filters, the location check, logging,
  the health endpoint, the email backend, the digest, and application tracking
- `.env.example`, `README.md`, and this changelog

### Changed

- Email settings use Django 6.1's `MAILERS` setting instead of the deprecated
  `EMAIL_*` settings
- Jobicy salaries are read from `salaryMin` and `salaryMax`, kept only when yearly