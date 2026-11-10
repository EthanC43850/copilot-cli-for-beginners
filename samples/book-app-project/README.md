# Book Collection App

*(This README is intentionally rough so you can improve it with GitHub Copilot CLI)*

A Python app for managing books you have or want to read.
It can add, remove, and list books. Also mark them as read, search titles and
authors, and filter by read status. Multiple readers can rate and review each
book, with an average rating shown in book listings.

---

## Current Features

* Reads books from a JSON file (our database)
* Adds, shows, edits, and removes reader ratings and optional written reviews
* Validates book fields when adding books and loading saved data
* Some tests exist but probably not enough

---

## Files

* `book_app.py` - Main CLI entry point
* `books.py` - BookCollection class with data logic
* `utils.py` - Shared book display and rating summaries, plus input helpers
* `data.json` - Sample book data
* `tests/test_books.py` - Starter pytest tests

---

## Running the App

```bash
python book_app.py list
python book_app.py add
python book_app.py find
python book_app.py remove
python book_app.py mark
python book_app.py mark "The Hobbit"
python book_app.py search
python book_app.py search "hobbit"
python book_app.py search "George Orwell"
python book_app.py filter
python book_app.py filter read
python book_app.py filter unread
python book_app.py help
```

Run `mark` alone to be prompted for a book title, or include the title after
the command. Titles match without regard to uppercase or lowercase letters.
Blank titles show an error, and missing books show a not-found message.
Marking an already-read book is also successful.

When adding a book, title and author must contain text. The publication year
must be a whole number of `0` or greater; leave it blank to save `0` for an
unknown year. Future years are allowed. Saved books follow the same rules,
and their read status must be a JSON boolean (`true` or `false`), not text
or a number. Invalid book fields raise an error without changing saved data.
If loading fails, repair the invalid fields in `data.json` before restarting.
The sample uses `Unknown Author` when an author's name is unavailable.

If `data.json` contains invalid JSON, the app stops with an error instead of
starting an empty collection. The damaged file is left unchanged; repair it
or restore a backup before restarting. A missing file still starts an empty
collection, and adding the first book creates it.

The read status is saved to `data.json`. Run `python book_app.py list` to see
a checkmark next to books marked as read.

Run `search` alone to be prompted, or include your search text after the command.
Search finds partial matches in either a title or an author name, ignoring
uppercase or lowercase letters. For example, `search "tolkien"` finds books by
`J.R.R. Tolkien`. The existing `find` command still requires the full author name.

Run `filter` alone to be prompted, or use `filter read` or `filter unread`.
Filter status also ignores capitalization. Both commands ignore surrounding
spaces, preserve book order, and leave your books and saved data unchanged.
Blank search text and invalid filters show errors. If nothing matches, the app
prints `No books found.`.

## Ratings and Reviews

Run these commands from `samples/book-app-project`:

```bash
python book_app.py review-add "The Hobbit"
python book_app.py reviews "The Hobbit"
python book_app.py review-edit "The Hobbit"
python book_app.py review-remove "The Hobbit"
```

Omit the title from any review command to be prompted for it. Titles match
without regard to capitalization and ignore surrounding spaces, just like
reader names. If several books have the same title, the first match is used.
Blank titles and missing books show errors.

`review-add` prompts for a reader name, a whole-number rating from **1 to 5**,
and optional written review text. Press Enter at the text prompt to leave it
empty. Each reader can have one review per book: `Alice`, `alice`, and
` Alice ` identify the same reader. Adding a duplicate shows an error; use
`review-edit` to change it.

`reviews` shows each reader's rating and any written text, plus the average
and review count. Book listings, author lookup, search, and status filtering
also show a summary such as `4.5/5 (2 reviews)`. Every rating counts toward the
average, including entries without written text. A book with no reviews shows
`Not rated (0 reviews)`.

`review-edit` asks for the reader name, shows the current values, and prompts
for a replacement rating and text. A rating is always required; **blank text
clears the previous written review**. The reader name stays unchanged.
`review-remove` asks for the reader name and removes their rating and text.
Removing a book also removes its reviews.

Changes are saved in `data.json` and remain after restarting the app. Existing
book files without reviews still load without manual changes. Invalid input
and missing review targets show errors without changing saved data.

**Local labels, not accounts:** reader names do not verify anyone's identity.
Anyone who can use this local app and access its data can edit or remove any
reader's review. This feature does not provide sign-in or permissions.

## Running Tests

```bash
python -m pytest tests/
```

---

## Notes

* Not production-ready (obviously)
* Some code could be improved
* Could add more commands later
