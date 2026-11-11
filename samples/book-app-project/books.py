import json
from dataclasses import asdict, dataclass, field
from typing import List, Optional

DATA_FILE = "data.json"


def _normalize_reader(reader: str) -> str:
    if not isinstance(reader, str) or not reader.strip():
        raise ValueError("Reader name must be a nonblank string.")
    return reader.strip()


@dataclass
class Review:
    reader: str
    rating: int
    text: str = ""

    def __post_init__(self) -> None:
        self.reader = _normalize_reader(self.reader)
        if type(self.rating) is not int or not 1 <= self.rating <= 5:
            raise ValueError("Rating must be a whole number from 1 to 5.")
        if not isinstance(self.text, str):
            raise ValueError("Review text must be a string.")
        self.text = self.text.strip()


@dataclass
class Book:
    title: str
    author: str
    year: int
    read: bool = False
    reviews: list[Review] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Book title must be a nonblank string.")
        if not isinstance(self.author, str) or not self.author.strip():
            raise ValueError("Book author must be a nonblank string.")
        if type(self.year) is not int or self.year < 0:
            raise ValueError(
                "Publication year must be a whole number of 0 or greater."
            )
        if type(self.read) is not bool:
            raise ValueError("Read status must be a boolean (true or false).")
        if not isinstance(self.reviews, list) or any(
            not isinstance(review, Review) for review in self.reviews
        ):
            raise ValueError("Reviews must be a list of Review objects.")
        readers = [review.reader.casefold() for review in self.reviews]
        if len(readers) != len(set(readers)):
            raise ValueError(
                "Reader already has a review; use review-edit instead."
            )

    @property
    def average_rating(self) -> float | None:
        if not self.reviews:
            return None
        total = sum(review.rating for review in self.reviews)
        return total / len(self.reviews)


def get_book_statistics(books: list[Book]) -> dict[str, int | Book | None]:
    """Return counts and books with the lowest/highest year, including year 0.

    Empty lists return None for oldest/newest; tied years use the first book.
    """
    if not isinstance(books, list) or any(
        not isinstance(book, Book) for book in books
    ):
        raise TypeError("books must be a list of Book objects.")

    total = len(books)
    read = sum(book.read for book in books)
    return {
        "total": total,
        "read": read,
        "unread": total - read,
        "oldest": min(books, key=lambda book: book.year, default=None),
        "newest": max(books, key=lambda book: book.year, default=None),
    }


class BookCollection:
    def __init__(self) -> None:
        self.books: List[Book] = []
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON file if it exists."""
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded_books = []
            for record in data:
                book_data = dict(record)
                raw_reviews = book_data.pop("reviews", [])
                if not isinstance(raw_reviews, list):
                    raise ValueError("Saved reviews must be a list.")
                try:
                    reviews = [Review(**review) for review in raw_reviews]
                    loaded_books.append(Book(**book_data, reviews=reviews))
                except (TypeError, ValueError) as e:
                    raise ValueError(
                        f"Invalid saved book or review: {e}"
                    ) from e
            self.books = loaded_books
        except FileNotFoundError:
            self.books = []
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Cannot load {DATA_FILE}: invalid JSON. "
                "Repair the file or restore a backup before restarting; "
                "the file has not been changed."
            ) from e

    def save_books(self) -> None:
        """Save the current book collection to JSON."""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([asdict(b) for b in self.books], f, indent=2)

    def add_book(self, title: str, author: str, year: int) -> Book:
        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def mark_as_read(self, title: str) -> bool:
        book = self.find_book_by_title(title)
        if book:
            book.read = True
            self.save_books()
            return True
        return False

    def remove_book(self, title: str) -> bool:
        """Remove a book by title."""
        book = self.find_book_by_title(title)
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False

    def find_by_author(self, author: str) -> List[Book]:
        """Find books whose authors contain the query, ignoring case."""
        if not isinstance(author, str) or not author.strip():
            raise ValueError("Author name must be a nonblank string.")
        author = author.strip().lower()
        return [b for b in self.books if author in b.author.lower()]

    def search_books(self, query: str) -> List[Book]:
        query = query.strip().lower()
        if not query:
            raise ValueError("Search text cannot be empty.")

        return [
            book for book in self.books
            if query in book.title.lower() or query in book.author.lower()
        ]

    def filter_by_read_status(self, read: bool) -> List[Book]:
        return [book for book in self.books if book.read == read]

    def _get_review_book(self, title: str) -> Book:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Book title must be a nonblank string.")
        book = self.find_book_by_title(title.strip())
        if book is None:
            raise ValueError(f'Book "{title.strip()}" not found.')
        return book

    def list_reviews(self, title: str) -> list[Review]:
        return list(self._get_review_book(title).reviews)

    def get_review(self, title: str, reader: str) -> Review:
        book = self._get_review_book(title)
        reader = _normalize_reader(reader)
        for review in book.reviews:
            if review.reader.casefold() == reader.casefold():
                return review
        raise ValueError(f'Review by "{reader}" not found.')

    def add_review(
        self, title: str, reader: str, rating: int, text: str = "",
    ) -> Review:
        book = self._get_review_book(title)
        review = Review(reader, rating, text)
        if any(
            existing.reader.casefold() == review.reader.casefold()
            for existing in book.reviews
        ):
            raise ValueError(
                "Reader already has a review; use review-edit instead."
            )
        book.reviews.append(review)
        self.save_books()
        return review

    def update_review(
        self, title: str, reader: str, rating: int, text: str = "",
    ) -> Review:
        review = self.get_review(title, reader)
        replacement = Review(review.reader, rating, text)
        review.rating = replacement.rating
        review.text = replacement.text
        self.save_books()
        return review

    def remove_review(self, title: str, reader: str) -> None:
        book = self._get_review_book(title)
        review = self.get_review(title, reader)
        book.reviews.remove(review)
        self.save_books()
