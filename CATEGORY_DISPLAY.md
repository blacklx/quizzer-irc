# Smart Category Display System

## Problem

With many categories, listing them all in IRC would:
- Flood the channel with messages
- Exceed IRC message length limits
- Be hard to read and navigate

## Solution

A smart category display system with multiple modes:

### 1. **Grouped Mode (Default)** ✅
Groups categories by type for easy browsing.

**Usage:** `!categories` or `!categories grouped`

**Example Output:**
```
Entertainment (10): Board Games, Books, Cartoon Animations, Comics, Film, Japanese Anime Manga, Music, Musicals Theatres, Television, Video Games
General (10): Animals, Art, Celebrities, General Knowledge, Geography, History, Mythology, Politics, Sports, Vehicles
Science (4): Computers, Gadgets, Mathematics, Nature
```

**Benefits:**
- Compact - only 3-4 messages
- Easy to scan
- Shows counts per group
- Shortened names (Entertainment → Ent., Science → Sci.)

### 2. **Search Mode** 🔍
Search for categories by name.

**Usage:** `!categories search music` or `!categories search film`

**Example Output:**
```
Found 2 categories matching 'music':
Ent. Music, Ent. Musicals Theatres
```

**Benefits:**
- Fast category finding
- Case-insensitive search
- Shows partial matches

### 3. **Pagination Mode** 📄
View categories page by page.

**Usage:** `!categories 1` or `!categories 2`

**Example Output:**
```
Categories (page 1/3):
Categories: Animals, Art, Celebrities, Entertainment Board Games, Entertainment Books, Entertainment Cartoon Animations, Entertainment Comics, Entertainment Film, Entertainment Japanese Anime Manga, Entertainment Music
Use !categories 2 for next page, or !categories grouped for grouped view.
```

**Benefits:**
- Handles any number of categories
- Easy navigation
- Shows page numbers

### 4. **Compact Mode** 📋
Simple comma-separated list (for small category sets).

**Usage:** `!categories compact` or `!categories all`

**Benefits:**
- Simple format
- Good for small lists

---

## Command Reference

| Command | Description |
|---------|-------------|
| `!categories` | Show grouped categories (default) |
| `!categories grouped` | Show grouped categories |
| `!categories search <term>` | Search for categories |
| `!categories <number>` | Show specific page (e.g., `!categories 2`) |
| `!categories compact` | Show compact list |
| `!categories all` | Show all in compact format |

---

## Features

✅ **Smart Grouping** - Categories grouped by type (Entertainment, Science, General)  
✅ **Search Functionality** - Find categories quickly  
✅ **Pagination** - Handle unlimited categories  
✅ **Shortened Names** - "Entertainment" → "Ent.", "Science" → "Sci."  
✅ **Message Length Limits** - Respects IRC limits (400 chars)  
✅ **User-Friendly** - Clear, readable format  

---

## Examples

### Example 1: Default (Grouped)
```
User: !categories
Bot: Entertainment (10): Board Games, Books, Cartoon Animations, Comics, Film, Japanese Anime Manga, Music, Musicals Theatres, Television, Video Games
Bot: General (10): Animals, Art, Celebrities, General Knowledge, Geography, History, Mythology, Politics, Sports, Vehicles
Bot: Science (4): Computers, Gadgets, Mathematics, Nature
```

### Example 2: Search
```
User: !categories search video
Bot: Found 1 categories matching 'video':
Bot: Categories: Entertainment Video Games
```

### Example 3: Pagination
```
User: !categories 1
Bot: Categories (page 1/3):
Bot: Categories: Animals, Art, Celebrities, Entertainment Board Games, Entertainment Books, Entertainment Cartoon Animations, Entertainment Comics, Entertainment Film, Entertainment Japanese Anime Manga, Entertainment Music
Bot: Use !categories 2 for next page, or !categories grouped for grouped view.
```

---

## Implementation Details

- **Max message length:** 400 characters (IRC safe)
- **Categories per page:** 10 (pagination mode)
- **Auto-shortening:** Long category names automatically shortened
- **Case-insensitive:** Search works regardless of case
- **Backward compatible:** Old `!categories` command still works

---

## Future Enhancements (Optional)

- Send full list via PM instead of channel
- Show question counts per category
- Show most popular categories first
- Category aliases (e.g., "games" → "Entertainment Video Games")

