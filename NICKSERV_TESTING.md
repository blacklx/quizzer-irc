# NickServ Response Testing Guide

## Why We Need This

Different IRC networks have different NickServ implementations and response formats. To properly verify admin commands, we need to know exactly how your network (UmbrellaNet) responds to `INFO` commands.

## Current Implementation

The bot currently expects these formats:

### Account Registration Check
- `Account: {nick}`
- `Account name: {nick}`
- `is registered under account: {nick}`
- `account {nick}`

### Online Status Check
- `{nick} is currently online.`
- `{nick} is online`
- `{nick} is currently logged in`
- `is online` (with nick in context)

## How to Test

### Step 1: Enable Debug Logging

Make sure `config.yaml` has:
```yaml
bot_log_settings:
  enable_logging: True
  enable_debug: True
  log_filename: "logs/Quizzer.log"
```

### Step 2: Run the Bot

```bash
python3 run.py
```

### Step 3: Send Admin Command

As an admin user, send via PM to the bot:
```
!admin stop_game
```

### Step 4: Check Logs

Look for these log entries in `logs/Quizzer.log`:

```
NickServ notice: [actual response text]
Full NickServ INFO response: [response parts]
NickServ INFO response for {nick}: [all response lines]
```

### Step 5: Manual Test (Optional)

You can also manually test by connecting to IRC and sending:
```
/msg N INFO YourNick
```

This will show you the exact format NickServ uses.

## What to Look For

1. **Response format**: Single line or multiple lines?
2. **Account field**: How is the account name shown?
   - `Account: blackroot`
   - `Account name: blackroot`
   - `Registered as: blackroot`
   - Something else?
3. **Online status**: How is online status indicated?
   - `blackroot is currently online.`
   - `is online`
   - `is logged in`
   - Something else?
4. **Response structure**: Is it one NOTICE or multiple?

## Example Responses from Different Networks

### Network A (typical)
```
-N- INFO blackroot:
-N- Account: blackroot
-N- Registered: Jan 01 2024
-N- blackroot is currently online.
```

### Network B (compact)
```
-N- blackroot is registered (Account: blackroot) and is online.
```

### Network C (multi-line)
```
-N- Information on blackroot:
-N- Account: blackroot
-N- Status: Online
```

## After Testing

Once you know the exact format, we can:

1. **Update the parsing logic** to match your network's format exactly
2. **Add specific handling** for UmbrellaNet if needed
3. **Improve security** by ensuring verification works correctly

## Current Status

The bot now has:
- ✅ Enhanced response parsing (handles multiple formats)
- ✅ Debug logging to see actual responses
- ✅ Better error handling

But we need to **test on your actual network** to see the exact format!

