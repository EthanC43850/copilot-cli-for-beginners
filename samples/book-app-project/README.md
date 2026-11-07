# Book Collection App

*(This README is intentionally rough so you can improve it with GitHub Copilot CLI)*

A Python app for managing books you have or want to read.
It can add, remove, and list books. Also mark them as read, search titles and
authors, and filter by read status.

---

## Current Features

* Reads books from a JSON file (our database)
* Input checking is weak in some areas
* Some tests exist but probably not enough

---

## Files

* `book_app.py` - Main CLI entry point
* `books.py` - BookCollection class with data logic
* `utils.py` - Helper functions for UI and input
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

## Running Tests

```bash
python -m pytest tests/
```

---

## Notes

* Not production-ready (obviously)
* Some code could be improved
* Could add more commands later
