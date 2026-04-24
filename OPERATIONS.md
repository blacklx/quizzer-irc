# Operations Runbook

This document is the day-to-day runtime guide for keeping `Quizzer` healthy.

## Recommended Runtime Model

Use `systemd` for unattended production operation.

- Preferred service template: `tools/quizzer.service.example`
- App entrypoint: `run.py`
- Validation command: `.venv/bin/python3 tools/validate.py`

`tools/startbot.sh` is still useful for manual starts, stops, and recovery, but it
should not be the only recovery mechanism after a fatal bot exit.

Do not supervise the same bot instance with both `systemd` and cron / `startbot.sh`
health checks at the same time. Pick one supervisor model.

## Log Locations

- Main bot runtime: `logs/Quizzer.log`
- Quiz lifecycle: `logs/quiz_game.log`
- Admin commands: `logs/admin_actions.log`
- Admin verification: `logs/admin_verification.log`
- Database activity: `logs/database.log`
- Wrapper/process management: `bot_management.log`

## First Checks When The Bot Is Down

1. Check whether the bot process is running.
2. Check whether a stale `screen` session exists without the real bot process.
3. Read `logs/Quizzer.log` for reconnect exhaustion, exceptions, or startup failure.
4. If using `systemd`, inspect the service status and recent journal output.

## Known Failure Modes

### Reconnect exhaustion

If IRC reconnect attempts are exhausted, the bot now exits nonzero on purpose so a
supervisor can restart it. Without a supervisor, it will remain down.

### Stale `screen` session

Historically, the wrapper could be left with a `screen` session while the real bot
process was already gone. `tools/startbot.sh` now cleans up that stale state before
declaring the bot healthy or trying to start it again.

### Interrupted quiz

If the bot disconnects mid-quiz, the active round is cancelled. On reconnect, the
bot announces that the previous quiz was interrupted and clears moderated channel
mode.

## Recovery Steps

### Manual recovery

```bash
.venv/bin/python3 tools/validate.py
./tools/startbot.sh status
./tools/startbot.sh start
```

Use the manual recovery flow only when the bot is being managed by `screen` /
`startbot.sh`, not when `quizzer.service` is active.

### `systemd` recovery

```bash
sudo systemctl status quizzer
sudo systemctl restart quizzer
```

If the bot is running under `systemd`, use `systemctl stop quizzer` to stop it.
Do not use `./tools/startbot.sh stop` or `./tools/startbot.sh restart` against a
live `quizzer.service`.

## Before Deploying Changes

Run:

```bash
.venv/bin/python3 tools/validate.py
```

If `config.yaml` is present locally, the validation script also performs a config
and database smoke check.
