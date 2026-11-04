# Config & Profiles Calibration

Java 21 • Spring Boot 4.0.0 • Maven 3.9+ • MySQL 8.4 • RabbitMQ 4.1

This is an enrollment policy calibration project, built from scratch. It deliberately
contains only the API needed to observe non-secret business rules; it is not an
entire enrollment CRUD application. No H2 database is used.

## Run

1. Install Java 21, Maven 3.9+, Python 3 and Docker with Compose.
2. Copy `.env.example` to `.env`. Fill in unique local database and broker usernames
   and passwords, including a separate MySQL root password. Never commit `.env`.
   Do not use `root` as `DB_USER`.
3. Start dependencies: `docker compose up -d`.
4. Export the values from `.env` into the shell that launches Java. Compose reads
   `.env` automatically; Java does not. On Bash, use `set -a`, then `source .env`,
   then `set +a`. On PowerShell set each `$env:DB_USER`, `$env:DB_PASSWORD`,
   `$env:BROKER_USER`, and `$env:BROKER_PASSWORD` to your local values.
5. Build once: `mvn -B verify`.
6. Run: `java -jar target/config-profiles-1.0.0.jar --spring.profiles.active=local`.
7. Inspect `http://localhost:8080/api/rules` and `/actuator/health`.

Stop the app before running `python3 scripts/verify.py` (Windows: `python`). It
builds nothing, launches eight sequential JVMs on available ports, checks six
precedence cases, checks both profiles against the same jar, and verifies an
additional failing startup. Set `REQUIRE_HEALTH_UP=true` in the environment to
require live database and broker success. Without it, DOWN is accepted but both
real health components must still exist. Results and process logs go to `evidence/`.
The pipeline always requires UP against its real dependency containers.

## Drill 1: validated records

`EnrollmentRules` is a `@ConfigurationProperties` record with `@Validated` and
Jakarta constraints. `@ConfigurationPropertiesScan` registers constructor binding.
`EnrollmentPolicy` injects the record rather than reading environment variables,
using `@Value`, or embedding configurable limits. Its three rules are waitlist
capacity, maximum credits, and registration window length. The window includes
its start and excludes its end. Zero waitlist capacity disables waitlisting.

Try `java -jar target/config-profiles-1.0.0.jar --enrollment.rules.max-waitlist-size=-1`.
Spring must exit unsuccessfully and name `enrollment.rules.max-waitlist-size`.
Unit tests cover binding failure and policy boundaries; the process verifier checks
the actual Boot failure analyzer message.

## Drill 2: real property sources

Read `docs/precedence-predictions.md`. Its commit precedes all implementation/test
commits. Git history is included in this distribution to preserve that evidence.
The process verifier uses real packaged config, profile config, an external file,
OS environment, `-D` and `--` arguments. It does not manually create an ordered
list of fake sources. Case 1 activates an empty `baseline` profile so the default
local profile cannot override the packaged base value. External files are created
outside the repository in a temporary directory and removed after verification.

## Drill 3: one jar

Run local and prod by changing `--spring.profiles.active`, without rebuilding.
The script computes SHA-256 before and after all executions and records the same
hash for every case. Local waitlist capacity is 20; prod is 100. Database and broker
addresses and credentials come from the environment, not separate compiled code.

## Drill 4: history scan

Install Gitleaks 8.24.3 and run `bash scripts/scan-secrets.sh`. The script rejects
shallow clones, scans all refs with `--all --full-history`, and scans the working
tree. CI checks out `fetch-depth: 0` and runs the same script before building.
There are no scanner exclusions or suppressed findings. CI generates ephemeral
credentials in memory and GitHub's runtime environment; it masks them in logs.
Scanner success establishes no findings under its rules, not a mathematical
proof that arbitrary text cannot be a credential. Before pushing, scan again.

## Drill 5: Actuator

Exactly three endpoint IDs are opted into access and HTTP exposure: `health`,
`info`, and `metrics`. All others default to no access; JMX is closed and HTTP
discovery is disabled. `/actuator/env` and other sensitive endpoints return 404.
Health exposes component names/status, never connection details or credentials.
Boot's real `DataSourceHealthIndicator` (`db`) executes a JDBC validation query;
`RabbitHealthIndicator` (`rabbit`) checks the actual RabbitMQ connection. Neither
is a hard-coded UP response. Failed dependencies report DOWN and HTTP 503.

The server binds to loopback by default. The calibration has no login system;
use a protected management network or add authentication before exposing these
operational endpoints publicly. Database and broker Compose ports also bind only
to loopback. `info.app.environment` distinguishes profile runs.

## CI and evidence

`.github/workflows/verify.yml` scans full history, creates runtime credentials,
starts MySQL/RabbitMQ, waits for them, builds/tests once, runs process checks, and
uploads evidence even on failure. Copy/push this repository to GitHub to execute it.
No GitHub pipeline run is claimed merely because a workflow file is present.

See `docs/verification-status.md` for what was actually verified during delivery.

## References

- [Spring Boot externalized configuration](https://docs.spring.io/spring-boot/4.0/reference/features/external-config.html)
- [Spring Boot Actuator endpoint access and exposure](https://docs.spring.io/spring-boot/4.0/reference/actuator/endpoints.html)
- [Gitleaks CLI](https://github.com/gitleaks/gitleaks)
