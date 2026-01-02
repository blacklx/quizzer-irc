# Admin Verification System

## How Admin Verification Works

The bot uses a **two-step verification process** to determine if someone is authorized to use admin commands:

### Step 1: Nickname Check
- Checks if the user's **nickname** is in the `admin_settings.admins` list in `config.yaml`
- This is a quick initial check

### Step 2: NickServ Verification
- When an admin command is received, the bot sends `INFO <nick>` to NickServ
- NickServ responds with information about the account
- The bot verifies:
  1. **Account matches**: The response contains `Account: {nick}` (user is registered)
  2. **User is online**: The response contains `{nick} is currently online.`
- Only if **BOTH** conditions are met AND the nick is in the admin list, the command executes

## Current Implementation

### Admin List (config.yaml)
```yaml
admin_settings:
  admins: ["blackroot"]  # List of admin nicknames
```

### Verification Flow

1. **User sends admin command** (via PM):
   ```
   !admin stop_game
   ```

2. **Bot checks nickname** (`is_admin(nick)`):
   - Checks if `nick` is in `admin_settings.admins` list
   - If not in list → command rejected

3. **Bot requests NickServ info**:
   - Sends: `PRIVMSG N :INFO blackroot`
   - Stores pending command in `pending_admin_commands`

4. **NickServ responds** (via NOTICE):
   - Response might contain: `Account: blackroot` and `blackroot is currently online.`

5. **Bot verifies** (`process_nickserv_response()`):
   - Checks if account matches: `Account: {nick}` in response
   - Checks if user is online: `{nick} is currently online.` in response
   - Both must be true

6. **Command executes**:
   - Only if nickname is in admin list AND NickServ verification passes

## Code Locations

### Admin List Check
**File:** `admin.py`
```python
def is_admin(self, user):
    # Check if a user is an admin
    return user in self.admin_nicks
```

### NickServ Verification
**File:** `admin.py`
```python
def process_nickserv_response(self, nick, responses):
    is_registered = False
    is_online = False

    for response in responses:
        if f"Account: {nick}" in response:
            is_registered = True
        if f"{nick} is currently online." in response:
            is_online = True

    return is_registered and is_online
```

### Command Processing
**File:** `bot.py` - `on_privmsg()` and `on_notice()`

## Important Notes

1. **Nickname-based**: The system checks the **nickname**, not the account name
   - If someone uses an admin's nickname, they could potentially bypass verification
   - NickServ verification helps prevent this, but the initial check is nickname-based

2. **NickServ dependency**: Admin commands require NickServ to be working
   - If NickServ is down or not responding, admin commands won't work

3. **Case sensitivity**: Nickname matching is case-sensitive
   - `"blackroot"` ≠ `"Blackroot"` ≠ `"BLACKROOT"`

## Potential Security Issue

The current implementation has a potential security flaw:

- Some commands check `is_admin(nick)` **before** NickServ verification
- This means if someone uses an admin's nickname, they might be able to execute some commands before NickServ verification completes
- However, most critical commands (stop, restart) go through the full NickServ verification

## Recommendations

1. **Always use NickServ verification** for all admin commands
2. **Check account name** instead of just nickname (if NickServ provides it)
3. **Add logging** for failed admin command attempts
4. **Consider case-insensitive** nickname matching

