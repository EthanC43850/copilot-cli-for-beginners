import sys

from books import Book, BookCollection


collection = BookCollection()


def show_books(books: list[Book]) -> None:
    """Display books in a user-friendly format."""
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")

    for index, book in enumerate(books, start=1):
        status = "✓" if book.read else " "
        print(f"{index}. [{status}] {book.title} by {book.author} ({book.year})")

    print()


def handle_list() -> None:
    books = collection.list_books()
    show_books(books)


def handle_add() -> None:
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


def handle_remove() -> None:
    print("\nRemove a Book\n")

    title = input("Enter the title of the book to remove: ").strip()
    collection.remove_book(title)

    print("\nBook removed if it existed.\n")


def handle_find() -> None:
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
    argument = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

    match command:
        case "list":
            handle_list()
        case "add":
            handle_add()
        case "remove":
            handle_remove()
        case "find":
            handle_find()
        case "mark":
            handle_mark_as_read(argument)
        case "search":
            handle_search(argument)
        case "filter":
            handle_filter(argument)
        case "help":
            show_help()
        case _:
            print("Unknown command.\n")
            show_help()


if __name__ == "__main__":
    main()
