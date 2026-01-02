# Admin Verification System Design

## Overview

This document describes the proposed multi-method admin verification system that allows administrators to choose between different verification methods based on their IRC network and security requirements.

## Current System

The bot currently uses **NickServ-based verification**:
1. User sends admin command
2. Bot checks if nickname is in admin list
3. Bot requests NickServ INFO
4. Bot verifies account matches and user is online
5. Command executes if verified

**Limitations:**
- Requires NickServ to be available
- Network-dependent (waits for NickServ response)
- May not work on all IRC networks

## Proposed System

### Verification Methods

#### 1. NickServ (Default - Most Secure)
- **How it works:** Same as current system
- **Pros:** Most secure, uses IRC network's authentication
- **Cons:** Requires NickServ, network-dependent
- **Use case:** Networks with NickServ

#### 2. Password-Based (Recommended Alternative)
- **How it works:**
  1. User sends: `!admin verify <password>`
  2. Bot hashes password and compares with stored hash
  3. If correct, grants session token (expires after timeout)
  4. Subsequent admin commands check session
- **Pros:** Works everywhere, secure with strong password, no network dependency
- **Cons:** Password sent in PM (but SSL encrypted), requires session management
- **Use case:** Networks without NickServ, or as backup

#### 3. Hostmask-Based (Automatic)
- **How it works:**
  1. Bot checks user's hostmask against allowed list
  2. If matches, grants access
  3. No password needed
- **Pros:** Automatic, no password needed
- **Cons:** Hostmasks can be spoofed (requires server access), less flexible
- **Use case:** Trusted networks, or combined with other methods

#### 4. Combined (Flexible)
- **How it works:** Tries multiple methods (e.g., password OR hostmask)
- **Pros:** Most flexible, fallback options
- **Cons:** More complex
- **Use case:** Maximum flexibility

### Configuration

```yaml
admin_settings:
  # Verification method: "nickserv", "password", "hostmask", or "combined"
  verification_method: "nickserv"
  
  # Admin nicknames (required for all methods)
  admins: ["AdminNick1", "AdminNick2"]
  
  # Password method settings
  password_settings:
    # Passwords (will be hashed on first use)
    # Format: "nickname": "plaintext_password" (hashed automatically)
    passwords:
      "AdminNick1": "$2b$12$hashed_password_here"
      "AdminNick2": "$2b$12$another_hashed_password"
    session_timeout: 3600  # seconds (1 hour)
    max_attempts: 3  # max failed attempts before lockout
    lockout_duration: 300  # seconds (5 minutes)
  
  # Hostmask method settings
  hostmask_settings:
    # Format: "nickname": ["hostmask1", "hostmask2"]
    # Wildcards: *!*@host.com, *!user@*.domain.com
    hostmasks:
      "AdminNick1": ["*!*@trusted.host", "*!*@*.example.com"]
      "AdminNick2": ["*!admin@*.network.org"]
  
  # Combined method settings
  combined_settings:
    # Try methods in order until one succeeds
    methods: ["password", "hostmask"]  # or ["hostmask", "password"]
    require_all: false  # if true, all methods must pass
```

### Security Features

1. **Password Hashing:**
   - Use `bcrypt` or `argon2` for password hashing
   - Never store plaintext passwords
   - Salt included in hash

2. **Session Management:**
   - Time-based session tokens
   - Automatic expiration
   - Session stored in memory (not persistent)

3. **Rate Limiting:**
   - Max failed verification attempts
   - Temporary lockout after failures
   - Prevents brute force attacks

4. **Logging:**
   - Log all verification attempts
   - Log successful and failed authentications
   - Log session creation/expiration

5. **Case-Insensitive Matching:**
   - Nickname matching is case-insensitive
   - Hostmask matching supports wildcards

### Implementation Plan

1. **Create `admin_verifier.py` module:**
   - `AdminVerifier` class
   - Methods for each verification type
   - Session management
   - Password hashing utilities

2. **Update `admin.py`:**
   - Integrate `AdminVerifier`
   - Keep existing NickServ logic
   - Add password/hostmask verification

3. **Update `bot.py`:**
   - Use `AdminVerifier` for all admin commands
   - Handle `!admin verify` command
   - Session checking

4. **Update `config.py`:**
   - Load new admin settings
   - Validate configuration

5. **Backward Compatibility:**
   - Default to "nickserv" if not specified
   - Existing configs continue to work

### Example Usage

**Password Method:**
```
User: !admin verify mypassword123
Bot: ✓ Admin verification successful. Session valid for 1 hour.
User: !admin stop_game
Bot: Game stopped.
```

**Hostmask Method:**
```
User: !admin stop_game
Bot: ✓ Verified via hostmask. Game stopped.
```

**Combined Method:**
```
User: !admin stop_game
Bot: (Tries password session first, then hostmask)
Bot: ✓ Verified. Game stopped.
```

### Migration Path

1. **Phase 1:** Add password method alongside NickServ
2. **Phase 2:** Add hostmask method
3. **Phase 3:** Add combined method
4. **Phase 4:** Make configurable, default to NickServ

### Security Considerations

1. **Password Storage:**
   - Never log passwords
   - Hash immediately on config load
   - Use strong hashing algorithm

2. **Session Security:**
   - Random session tokens
   - Time-based expiration
   - Clear on bot restart

3. **Hostmask Spoofing:**
   - Warn users that hostmasks can be spoofed
   - Recommend using password or NickServ for critical networks
   - Use combined method for defense in depth

4. **Rate Limiting:**
   - Prevent brute force attacks
   - Lockout after failed attempts
   - Log suspicious activity

