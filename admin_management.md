# Admin Management Workflow

## How to Add Admins

### Initial Setup (First Admin)

**Step 1: Add nickname to config.yaml**
```yaml
admin_settings:
  admins: ["AdminNick"]  # Add your nickname here
```

**Step 2: Add password to .env file**
```bash
# .env
ADMIN_PASSWORD_AdminNick=your_secure_password_here
```

**Step 3: Restart bot**
```bash
./tools/startbot.sh restart
```

**Step 4: Verify (first time)**
```
You: !admin verify your_secure_password_here
Bot: ✓ Admin verification successful. Session valid for 1 hour.
```

**What happens:**
- Bot detects plaintext password in `.env`
- Bot hashes password with bcrypt
- Bot saves hash to `admin_passwords.yaml`
- Bot never stores plaintext again

---

### Adding Additional Admins

#### Option A: Manual (Same as Initial Setup)

**Step 1: Edit config.yaml**
```yaml
admin_settings:
  admins: ["AdminNick", "NewAdminNick"]  # Add new nickname
```

**Step 2: Edit .env**
```bash
# .env
ADMIN_PASSWORD_AdminNick=existing_password
ADMIN_PASSWORD_NewAdminNick=new_password_here  # Add new password
```

**Step 3: Restart bot**
```bash
./tools/startbot.sh restart
```

**Step 4: New admin verifies**
```
NewAdmin: !admin verify new_password_here
Bot: ✓ Admin verification successful. Session valid for 1 hour.
```

---

#### Option B: Command-Based (Convenient)

**Existing admin adds new admin:**
```
AdminNick: !admin add_admin NewAdminNick new_password_123
Bot: ✓ Admin 'NewAdminNick' added successfully.
Bot: Password hashed and saved. New admin can verify now.
```

**What happens:**
- Bot adds nickname to `config.yaml` (admins list)
- Bot adds password to `.env` (plaintext, will be hashed)
- Bot hashes password immediately
- Bot saves hash to `admin_passwords.yaml`
- No restart needed

**New admin verifies:**
```
NewAdminNick: !admin verify new_password_123
Bot: ✓ Admin verification successful. Session valid for 1 hour.
```

---

### Changing Passwords

**Admin changes their own password:**
```
AdminNick: !admin set_password AdminNick new_secure_password
Bot: ✓ Password updated for AdminNick.
```

**Admin changes another admin's password:**
```
AdminNick: !admin set_password OtherAdmin new_password
Bot: ✓ Password updated for OtherAdmin.
```

**What happens:**
- Bot verifies you're an admin (session or NickServ)
- Bot updates password in `.env`
- Bot hashes new password immediately
- Bot updates hash in `admin_passwords.yaml`
- Old password invalidated

---

### Removing Admins

**Option A: Manual**
```yaml
# config.yaml
admin_settings:
  admins: ["AdminNick"]  # Remove nickname from list
```

**Option B: Command**
```
AdminNick: !admin remove_admin OtherAdmin
Bot: ✓ Admin 'OtherAdmin' removed successfully.
```

**What happens:**
- Bot removes nickname from `config.yaml`
- Bot removes password from `.env`
- Bot removes hash from `admin_passwords.yaml`
- Admin immediately loses access

---

## Configuration Files

### config.yaml
```yaml
admin_settings:
  verification_method: "password"  # or "nickserv", "hostmask", "combined"
  admins: ["AdminNick", "OtherAdmin"]  # List of admin nicknames
  
  password_settings:
    session_timeout: 3600  # 1 hour
    max_attempts: 3
    lockout_duration: 300  # 5 minutes
```

### .env
```bash
# Admin passwords (plaintext, auto-hashed on first load)
ADMIN_PASSWORD_AdminNick=password123
ADMIN_PASSWORD_OtherAdmin=password456
```

### admin_passwords.yaml (auto-generated)
```yaml
# Auto-generated - DO NOT EDIT MANUALLY
# Passwords are hashed - plaintext never stored here
passwords:
  "AdminNick": "$2b$12$hashed_password_here"
  "OtherAdmin": "$2b$12$another_hashed_password"
```

---

## Admin Commands

### Verification
```
!admin verify <password>
```
- Verifies password and grants session
- Session valid for configured timeout (default: 1 hour)

### Add Admin
```
!admin add_admin <nickname> <password>
```
- Adds new admin (requires existing admin session)
- Adds to config and .env
- Hashes password immediately

### Remove Admin
```
!admin remove_admin <nickname>
```
- Removes admin (requires existing admin session)
- Removes from config, .env, and hash file

### Set Password
```
!admin set_password <nickname> <new_password>
```
- Changes admin password (requires existing admin session)
- Updates .env and hash file
- Old password invalidated

### List Admins
```
!admin list_admins
```
- Lists all admin nicknames
- Does not show passwords (security)

---

## Security Considerations

### First Admin Setup
- **Must be done manually** (no command available)
- Ensures initial security
- Requires file access (prevents remote attacks)

### Adding Admins
- **Command-based:** Convenient but requires existing admin
- **Manual:** More secure, requires file access
- Both methods hash passwords immediately

### Password Requirements
- **Recommended:** Strong passwords (12+ characters, mixed case, numbers, symbols)
- **Enforcement:** Optional (can be added)
- **Storage:** Always hashed (never plaintext after first load)

### File Permissions
```bash
chmod 600 .env                    # Owner read/write only
chmod 600 admin_passwords.yaml    # Owner read/write only
chmod 644 config.yaml             # Readable by all (no passwords)
```

---

## Example Workflow

### Scenario: Setting up bot for first time

1. **Initial admin setup:**
   ```yaml
   # config.yaml
   admin_settings:
     admins: ["blackroot"]
   ```
   ```bash
   # .env
   ADMIN_PASSWORD_blackroot=MySecurePass123!
   ```

2. **Start bot:**
   ```bash
   ./tools/startbot.sh start
   ```

3. **Verify:**
   ```
   blackroot: !admin verify MySecurePass123!
   Bot: ✓ Admin verification successful. Session valid for 1 hour.
   ```

4. **Add second admin:**
   ```
   blackroot: !admin add_admin Admin2 SecurePass456!
   Bot: ✓ Admin 'Admin2' added successfully.
   ```

5. **Second admin verifies:**
   ```
   Admin2: !admin verify SecurePass456!
   Bot: ✓ Admin verification successful. Session valid for 1 hour.
   ```

---

## Troubleshooting

### "Admin not found"
- Check nickname is in `config.yaml` admins list
- Check nickname spelling (case-sensitive)
- Restart bot after adding to config

### "Password incorrect"
- Check password in `.env` file
- Check if password was hashed (should start with `$2b$`)
- Try setting password again: `!admin set_password <nick> <new_pass>`

### "Session expired"
- Verify again: `!admin verify <password>`
- Session timeout is configurable (default: 1 hour)

### "Too many attempts"
- Wait for lockout period (default: 5 minutes)
- Check if password is correct
- Contact bot owner if locked out

