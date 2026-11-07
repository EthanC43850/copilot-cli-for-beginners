import sys
from books import BookCollection


# Global collection instance
collection = BookCollection()


def show_books(books):
    """Display books in a user-friendly format."""
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")

    for index, book in enumerate(books, start=1):
        status = "✓" if book.read else " "
        print(f"{index}. [{status}] {book.title} by {book.author} ({book.year})")

    print()


def handle_list():
    books = collection.list_books()
    show_books(books)


def handle_add():
    print("\nAdd a New Book\n")

    title = input("Title: ").strip()
    author = input("Author: ").strip()
    year_str = input("Year: ").strip()

    try:
        year = int(year_str) if year_str else 0
        collection.add_book(title, author, year)
        print("\nBook added successfully.\n")
    except ValueError as e:
        print(f"\nError: {e}\n")


def handle_remove():
    print("\nRemove a Book\n")

    title = input("Enter the title of the book to remove: ").strip()
    collection.remove_book(title)

    print("\nBook removed if it existed.\n")


def handle_find():
    print("\nFind Books by Author\n")

    author = input("Author name: ").strip()
    books = collection.find_by_author(author)

    show_books(books)


def handle_mark_as_read(title: str | None = None) -> None:
    if title is None:
        title = input("Enter the title of the book to mark as read: ")

    title = title.strip()
    if not title:
        print("\nError: Book title cannot be empty.\n")
        return

    if collection.mark_as_read(title):
        print(f'\nBook "{title}" marked as read successfully.\n')
    else:
        print(f'\nBook "{title}" not found.\n')


def handle_search(query: str | None = None) -> None:
    if query is None:
        query = input("Search title or author: ")

    try:
        books = collection.search_books(query)
    except ValueError as e:
        print(f"\nError: {e}\n")
        return

    show_books(books)


def handle_filter(status: str | None = None) -> None:
    if status is None:
        status = input("Read status (read/unread): ")

    status = status.strip().lower()
    if status not in ("read", "unread"):
        print("\nError: Read status must be 'read' or 'unread'.\n")
        return

    books = collection.filter_by_read_status(status == "read")
    show_books(books)


def show_help() -> None:
    print("""
Book Collection Helper

Commands:
  list     - Show all books
  add      - Add a new book
  remove   - Remove a book by title
  find     - Find books by author
  mark [title] - Mark a book as read; omit title to be prompted
  search [text] - Search titles or authors; omit text to be prompted
  filter [read|unread] - Show books by read status; omit status to be prompted
  help     - Show this help message
""")


def main() -> None:
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "list":
        handle_list()
    elif command == "add":
        handle_add()
    elif command == "remove":
        handle_remove()
    elif command == "find":
        handle_find()
    elif command == "mark":
        title = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        handle_mark_as_read(title)
    elif command == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        handle_search(query)
    elif command == "filter":
        status = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        handle_filter(status)
    elif command == "help":
        show_help()
    else:
        print("Unknown command.\n")
        show_help()


if __name__ == "__main__":
    main()
