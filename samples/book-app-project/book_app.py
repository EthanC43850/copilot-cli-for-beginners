import sys

from books import BookCollection
from utils import print_books, rating_summary


collection = BookCollection()


def handle_list() -> None:
    books = collection.list_books()
    print_books(books)


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

    print_books(books)


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

    print_books(books)


def handle_filter(status: str | None = None) -> None:
    if status is None:
        status = input("Read status (read/unread): ")

    status = status.strip().lower()
    if status not in ("read", "unread"):
        print("\nError: Read status must be 'read' or 'unread'.\n")
        return

    books = collection.filter_by_read_status(status == "read")
    print_books(books)


def handle_reviews(title: str | None = None) -> None:
    if title is None:
        title = input("Book title: ")

    try:
        reviews = collection.list_reviews(title)
    except ValueError as e:
        print(f"\nError: {e}\n")
        return

    book = collection.find_book_by_title(title.strip())
    print(f"\nReviews for {book.title} - {rating_summary(book)}\n")
    if not reviews:
        print("No reviews yet.\n")
        return
    for review in reviews:
        print(f"{review.reader}: {review.rating}/5")
        if review.text:
            print(f"  {review.text}")
    print()


def handle_review_change(action: str, title: str | None = None) -> None:
    if title is None:
        title = input("Book title: ")

    try:
        collection.list_reviews(title)
        reader = input("Reader name: ")
        if action == "review-remove":
            collection.remove_review(title, reader)
            print("\nReview removed successfully.\n")
            return
        if action == "review-edit":
            current = collection.get_review(title, reader)
            print(f"Current rating: {current.rating}/5")
            print(f"Current review: {current.text or '(no text)'}")
        try:
            rating = int(input("Rating (whole number, 1-5): ").strip())
        except ValueError:
            raise ValueError(
                "Rating must be a whole number from 1 to 5."
            ) from None
        text = input(
            "Review text (optional; blank clears text when editing): "
        )
        if action == "review-add":
            collection.add_review(title, reader, rating, text)
            print("\nReview added successfully.\n")
        else:
            collection.update_review(title, reader, rating, text)
            print("\nReview updated successfully.\n")
    except ValueError as e:
        print(f"\nError: {e}\n")


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
  review-add [title] - Add a reader rating and optional review
  reviews [title] - Show reader reviews and the average rating
  review-edit [title] - Replace a reader's rating and review text
  review-remove [title] - Remove a reader's rating and review
  help     - Show this help message

Review commands: omit title to be prompted; changes prompt for reader details.
Ratings are whole numbers from 1 to 5; blank text clears a review when editing.
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
        case "reviews":
            handle_reviews(argument)
        case "review-add" | "review-edit" | "review-remove":
            handle_review_change(command, argument)
        case "help":
            show_help()
        case _:
            print("Unknown command.\n")
            show_help()


if __name__ == "__main__":
    main()
