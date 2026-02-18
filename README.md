# drb

**Read the Douay-Rheims Bible from your terminal.**

`73 Books · Vulgate Order · Public Domain`

A command-line tool for reading the Douay-Rheims Bible (Challoner revision) — the classic English translation of the Latin Vulgate, with all 73 books of the Catholic canon including the deuterocanonical books.

Inspired by [Luke Smith's kjv](https://github.com/LukeSmithxyz/kjv). Built for Catholics who live in the terminal.

---

## Quick Start

```
$ drb John 1:1-5
John
1:1     In the beginning was the Word: and the Word was with God: and the Word
        was God.
1:2     The same was in the beginning with God.
1:3     All things were made by him: and without him was made nothing that was
        made.
1:4     In him was life: and the life was the light of men.
1:5     And the light shineth in darkness: and the darkness did not comprehend
        it.
```

## Installation

### From source

```sh
git clone https://github.com/yourusername/drb.git
cd drb
make
sudo make install
```

To uninstall:

```sh
sudo make uninstall
```

### Package managers (coming soon)

```sh
# Homebrew (planned)
brew install yourusername/tap/drb

# AUR (planned)
yay -S drb
```

## Usage

```
drb [flags] [reference...]

  -l      list books
  -W      no line wrap
  -h      show help
```

### Single verse

```
$ drb Genesis 1:1
Genesis
1:1     In the beginning God created heaven, and earth.
```

### Full chapter

```
$ drb Wisdom 7
```

### Verse range

```
$ drb Romans 8:28-31
```

### Chapter range

```
$ drb Romans 8-9
```

### Multiple verses

```
$ drb John 3:16,17
```

### Cross-chapter range

```
$ drb John 1:1-2:5
```

### Deuterocanonical books

```
$ drb Wisdom 7:26
Wisdom
7:26    For she is the brightness of eternal light, and the unspotted mirror of
        God's majesty, and the image of his goodness.

$ drb Sirach 1:1-5
$ drb Tobit 1
$ drb 1 Maccabees 1
$ drb Baruch 3
```

### Search with regex

```
$ drb /grace
Genesis
6:8     But Noe found grace before the Lord.
...

$ drb John /bread of life
$ drb Psalms /mercy
```

### Piping

```sh
# Count verses mentioning "love" in 1 Corinthians
drb 1 Corinthians /love | grep -c "^"

# Extract just the text
drb John 1:1 | cut -f2

# Send a verse to a friend
drb Philippians 4:13 | mail -s "Daily verse" friend@example.com
```

### Interactive mode

Launch without arguments for a REPL:

```
$ drb
drb> John 1:1
drb> /love one another
drb> Wisdom 7
drb> Psalms 51:3-5
```

## ⚠️ A Note on Psalm Numbering

The Douay-Rheims Bible follows the **Vulgate/Septuagint (LXX) numbering** for the Psalms, which differs from the Hebrew/Protestant numbering used in most modern Bibles:

| Vulgate/LXX (DRB) | Hebrew/Protestant (KJV, ESV, etc.) |
|--------------------|-------------------------------------|
| Psalms 1–8         | Psalms 1–8                          |
| Psalms 9           | Psalms 9–10                         |
| Psalms 10–112      | Psalms 11–113                       |
| Psalms 113         | Psalms 114–115                      |
| Psalms 114–115     | Psalms 116                          |
| Psalms 116–145     | Psalms 117–146                      |
| Psalms 146–147     | Psalms 147                          |
| Psalms 148–150     | Psalms 148–150                      |

So if you're looking for "The Lord is my shepherd" (Protestant Psalm 23), you want:

```
$ drb Psalms 22
```

## Books

All 73 books in Douay-Rheims/Vulgate order, including:

- **Deuterocanonical books:** Tobit, Judith, Wisdom, Sirach (Ecclesiasticus), Baruch, 1 & 2 Maccabees
- **Extended versions** of Esther and Daniel

Run `drb -l` to see all books with their abbreviations.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PAGER` | Pager program | `less` |
| `DRB_NOLINEWRAP` | Disable line wrapping | unset |
| `DRB_MAX_WIDTH` | Maximum line width | terminal width |

## Source Text

The Douay-Rheims text (Challoner revision) is sourced from public domain transcriptions of the 1899 edition. More information: [Douay-Rheims Bible Online](https://www.drbo.org/).

## License

Public domain ([Unlicense](LICENSE)). The Douay-Rheims Bible text is itself in the public domain.

## Support

If this tool is useful to you, consider a lightning donation:

⚡ `your-lightning-address@example.com`

*Ad Maiorem Dei Gloriam.*
