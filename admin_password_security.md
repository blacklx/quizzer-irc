# Admin Password Security Analysis

## Security Concerns & Solutions

### Where to Store Passwords

#### ❌ Option 1: config.yaml (NOT RECOMMENDED)
```yaml
admin_settings:
  passwords:
    "AdminNick": "plaintext_password"  # BAD!
```

**Problems:**
- Plaintext visible in file
- Could be committed to git accidentally
- Anyone with file read access can see passwords
- **Exploitable:** YES - Very easy

#### ⚠️ Option 2: Separate passwords.yaml (BETTER, but still risky)
```yaml
# passwords.yaml (in .gitignore)
passwords:
  "AdminNick": "$2b$12$hashed_password"
```

**Problems:**
- Still a file that can be read
- If file permissions wrong (644 instead of 600), readable by others
- **Exploitable:** YES - If file permissions are wrong

#### ✅ Option 3: Environment Variables (RECOMMENDED)
```bash
# .env file (in .gitignore)
ADMIN_PASSWORD_AdminNick=plaintext_password
# OR
ADMIN_PASSWORD_HASH_AdminNick=$2b$12$hashed_password
```

**Advantages:**
- Not in git
- Can use hashed or plaintext (auto-hash on first use)
- Standard practice (like NickServ password)
- **Exploitable:** Only if .env file is readable (mitigate with chmod 600)

#### ✅✅ Option 4: Auto-Hash System (MOST SECURE)
```yaml
# config.yaml (example only, not actual passwords)
admin_settings:
  password_settings:
    # User sets plaintext initially
    passwords:
      "AdminNick": "my_secure_password"  # Plaintext first time only
```

**How it works:**
1. User sets plaintext password in config (first time)
2. Bot loads config, detects plaintext
3. Bot hashes password immediately
4. Bot replaces plaintext with hash in config
5. Bot saves config (plaintext removed)
6. Future loads only see hash

**Advantages:**
- Plaintext never stored permanently
- User-friendly (set once, auto-hashed)
- Hash stored in config (safe, can't reverse)
- **Exploitable:** NO - Hash can't be reversed

## Recommended Implementation

### Hybrid Approach (Best Security + Usability)

**Storage:**
1. **Primary:** `.env` file (like NickServ password)
   ```bash
   # .env
   ADMIN_PASSWORD_blackroot=my_secure_password_123
   ```
2. **Auto-hash:** On first load, hash and store in separate file
   ```yaml
   # admin_passwords.yaml (auto-generated, in .gitignore)
   passwords:
     "blackroot": "$2b$12$hashed_password_here"
   ```
3. **Future loads:** Use hash file, never touch .env plaintext again

**Security Features:**
- ✅ Passwords in `.env` (not in git)
- ✅ Auto-hashed on first use
- ✅ Hash stored separately (can't reverse)
- ✅ File permissions enforced (chmod 600)
- ✅ Rate limiting (prevent brute force)
- ✅ Session management (time-based expiration)

## Potential Exploits & Mitigations

### 1. File Read Access
**Attack:** Attacker reads `.env` or `admin_passwords.yaml`

**Mitigation:**
- File permissions: `chmod 600` (owner read/write only)
- Store in `.env` (already in `.gitignore`)
- Use hashed passwords (can't reverse)
- Separate password file (not in main config)

**Risk Level:** LOW (if permissions correct)

### 2. Brute Force Attack
**Attack:** Attacker tries many passwords via `!admin verify`

**Mitigation:**
- Rate limiting: Max 3 attempts per 5 minutes
- Lockout: Temporary ban after failed attempts
- Strong password requirements (optional)
- Logging: Track all attempts

**Risk Level:** LOW (with rate limiting)

### 3. Plaintext Transmission
**Attack:** Attacker intercepts password in PM

**Mitigation:**
- SSL/TLS encryption (bot uses SSL)
- Password only sent once (then session used)
- Session tokens (not passwords) for subsequent commands

**Risk Level:** LOW (with SSL)

### 4. Session Hijacking
**Attack:** Attacker steals session token

**Mitigation:**
- Random session tokens (cryptographically secure)
- Time-based expiration (1 hour default)
- Session stored in memory (not persistent)
- Clear on bot restart

**Risk Level:** LOW (short-lived sessions)

### 5. Hash Cracking
**Attack:** Attacker gets hash, tries to crack it

**Mitigation:**
- bcrypt (slow by design, prevents brute force)
- Strong passwords (user responsibility)
- Salt included in hash (unique per password)

**Risk Level:** LOW (with strong passwords)

## Implementation Plan

### Step 1: Password Storage
```python
# Load from .env first
admin_password = os.getenv('ADMIN_PASSWORD_blackroot')

# If not in .env, check hash file
if not admin_password:
    # Load from admin_passwords.yaml (hashed)
    admin_password = load_hashed_password('blackroot')
```

### Step 2: Auto-Hashing
```python
def hash_password_if_needed(password):
    # Check if already hashed (starts with $2b$)
    if password.startswith('$2b$'):
        return password  # Already hashed
    
    # Hash plaintext password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    # Save hash to file (replace plaintext)
    save_hashed_password('blackroot', hashed.decode())
    
    return hashed.decode()
```

### Step 3: Verification
```python
def verify_password(plaintext, hashed):
    return bcrypt.checkpw(plaintext.encode(), hashed.encode())
```

### Step 4: File Permissions
```python
# Ensure secure file permissions
os.chmod('.env', 0o600)  # rw-------
os.chmod('admin_passwords.yaml', 0o600)  # rw-------
```

## Configuration Example

### .env file
```bash
# Admin passwords (plaintext, auto-hashed on first use)
ADMIN_PASSWORD_blackroot=my_secure_password_123
ADMIN_PASSWORD_AdminNick2=another_secure_password
```

### config.yaml
```yaml
admin_settings:
  verification_method: "password"
  admins: ["blackroot", "AdminNick2"]
  
  password_settings:
    session_timeout: 3600  # 1 hour
    max_attempts: 3
    lockout_duration: 300  # 5 minutes
    # Passwords stored in .env, not here
```

### admin_passwords.yaml (auto-generated)
```yaml
# Auto-generated file - DO NOT EDIT MANUALLY
# Passwords are hashed - plaintext never stored here
passwords:
  "blackroot": "$2b$12$hashed_password_here"
  "AdminNick2": "$2b$12$another_hashed_password"
```

## Security Checklist

- [ ] Passwords stored in `.env` (not in git)
- [ ] `.env` in `.gitignore`
- [ ] File permissions: `chmod 600 .env`
- [ ] Passwords auto-hashed on first use
- [ ] Hash file separate from config
- [ ] Rate limiting implemented
- [ ] Session expiration enforced
- [ ] Logging of all attempts
- [ ] SSL/TLS required for bot connection
- [ ] Strong password recommendations in docs

## Conclusion

**Recommended Approach:**
1. Store passwords in `.env` file (like NickServ password)
2. Auto-hash on first load
3. Store hash in separate file (`admin_passwords.yaml`)
4. Use bcrypt for hashing
5. Enforce file permissions
6. Implement rate limiting
7. Use session management

**Security Level:** HIGH (with proper implementation)
**Exploitability:** LOW (with mitigations in place)

