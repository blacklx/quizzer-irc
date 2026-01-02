# Rate Limit Fix

## Problem

The API was rate limiting even with 2 second delays, returning 429 "Too Many Requests" errors.

## Solution

Updated `fetch_all.py` with:

1. **Increased default delay** - Now 3 seconds (was 1.5)
2. **Exponential backoff** - When rate limited, waits 10s, 20s, 40s, etc.
3. **Better error handling** - Detects 429 errors and retries automatically
4. **Graceful degradation** - If rate limited too many times, moves to next category

## New Default Settings

- **Default delay:** 3 seconds (was 1.5)
- **Retry backoff:** 10 seconds initial, doubles each retry
- **Max retries:** 5 attempts before giving up

## Recommended Usage

### Conservative (Recommended)

```bash
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

5 seconds between requests is very safe and should avoid rate limits.

### Moderate

```bash
python3 fetch_all.py --output ../quiz_data --delay 3.0
```

3 seconds is the new default - should work but may occasionally hit limits.

### Aggressive (Not Recommended)

```bash
python3 fetch_all.py --output ../quiz_data --delay 2.0
```

2 seconds may still hit rate limits, but the script will handle them with backoff.

## How It Handles Rate Limits

When a 429 error occurs:

1. **Detects the error** immediately
2. **Waits with exponential backoff:**
   - 1st retry: 10 seconds
   - 2nd retry: 20 seconds
   - 3rd retry: 40 seconds
   - etc.
3. **Retries up to 5 times**
4. **If still rate limited:** Waits longer and moves to next category

## Example Output

```
  Request #1... Fetched 50, added 16 new questions
  Request #2... 
  ⚠ Rate limited! Waiting 10 seconds before retry... Retrying...
  Fetched 50, added 15 new questions
  Request #3... Fetched 50, added 5 new questions
```

## Tips

1. **Use 5 second delay** for safest operation
2. **Let it run overnight** - It will handle rate limits automatically
3. **Monitor occasionally** - Check if it's getting rate limited frequently
4. **Can be interrupted** - Safe to Ctrl+C and resume later

## Time Estimates

With 5 second delay:
- ~5 seconds per request
- Multiple requests per category
- **Estimated total time:** 8-12 hours for all categories

The script will automatically handle rate limits, so you can let it run unattended.

