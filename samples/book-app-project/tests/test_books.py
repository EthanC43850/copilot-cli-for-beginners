import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from types import ModuleType
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import Book, BookCollection, Review, get_book_statistics
from utils import print_books


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


def test_add_book():
    collection = BookCollection()
    initial_count = len(collection.books)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.books) == initial_count + 1
    book = collection.find_book_by_title("1984")
    assert book is not None
    assert book.author == "George Orwell"
    assert book.year == 1949
    assert book.read is False

def test_mark_book_as_read():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    result = collection.mark_as_read("Dune")
    assert result is True
    book = collection.find_book_by_title("Dune")
    assert book.read is True

def test_mark_book_as_read_invalid():
    collection = BookCollection()
    result = collection.mark_as_read("Nonexistent Book")
    assert result is False

def test_remove_book():
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    result = collection.remove_book("The Hobbit")
    assert result is True
    book = collection.find_book_by_title("The Hobbit")
    assert book is None

def test_remove_book_invalid():
    collection = BookCollection()
    result = collection.remove_book("Nonexistent Book")
    assert result is False


def test_get_book_statistics_mixed_books() -> None:
    oldest = Book("The Hobbit", "J.R.R. Tolkien", 1937, read=True)
    middle = Book("1984", "George Orwell", 1949)
    newest = Book("Dune", "Frank Herbert", 1965, read=True)
    book_list = [middle, newest, oldest]

    result = get_book_statistics(book_list)

    assert result == {
        "total": 3,
        "read": 2,
        "unread": 1,
        "oldest": oldest,
        "newest": newest,
    }
    assert book_list == [middle, newest, oldest]


def test_get_book_statistics_empty_list() -> None:
    assert get_book_statistics([]) == {
        "total": 0,
        "read": 0,
        "unread": 0,
        "oldest": None,
        "newest": None,
    }


@pytest.mark.parametrize("read", [False, True])
def test_get_book_statistics_single_book(read: bool) -> None:
    book = Book("Dune", "Frank Herbert", 1965, read=read)

    assert get_book_statistics([book]) == {
        "total": 1,
        "read": int(read),
        "unread": int(not read),
        "oldest": book,
        "newest": book,
    }


def test_get_book_statistics_tied_years() -> None:
    first = Book("First", "Author", 2000)
    second = Book("Second", "Author", 2000)

    result = get_book_statistics([first, second])

    assert result["oldest"] is first
    assert result["newest"] is first


def test_get_book_statistics_includes_zero_year() -> None:
    unknown = Book("Unknown year", "Author", 0)
    dated = Book("Dated", "Author", 2000)

    result = get_book_statistics([dated, unknown])

    assert result["oldest"] is unknown
    assert result["newest"] is dated


@pytest.mark.parametrize("invalid_books", [None, "Dune", [None]])
def test_get_book_statistics_invalid_input(invalid_books: object) -> None:
    with pytest.raises(TypeError, match="books must be a list of Book objects"):
        get_book_statistics(invalid_books)


class TestPrintBooks:
    def test_empty_collection(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        print_books([])

        assert capsys.readouterr().out == "No books found.\n"

    def test_book_details_and_ratings(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_list = [
            Book("The Hobbit", "J.R.R. Tolkien", 1937, read=True),
            Book("Dune", "Frank Herbert", 1965, reviews=[Review("Alice", 4)]),
            Book(
                "1984", "George Orwell", 1949,
                reviews=[Review("Alice", 4), Review("Bob", 5)],
            ),
        ]

        print_books(book_list)

        assert capsys.readouterr().out == (
            "\nYour Book Collection:\n\n"
            "1. [✓] The Hobbit by J.R.R. Tolkien (1937)"
            " - Not rated (0 reviews)\n"
            "2. [ ] Dune by Frank Herbert (1965) - 4.0/5 (1 review)\n"
            "3. [ ] 1984 by George Orwell (1949) - 4.5/5 (2 reviews)\n\n"
        )


@pytest.fixture
def book_app_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    import book_app

    monkeypatch.setattr(book_app, "collection", BookCollection())
    return book_app


class TestMarkCommand:
    @pytest.mark.parametrize("title_args", [
        [],
        ["The Hobbit"],
        ["The", "Hobbit"],
        ["  the hobbit  "],
    ])
    def test_add_mark_reload_list(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        title_args: list[str],
    ) -> None:
        answers = iter(["The Hobbit", "J.R.R. Tolkien", "1937"])
        monkeypatch.setattr("builtins.input", lambda _: next(answers))
        monkeypatch.setattr(sys, "argv", ["book_app.py", "add"])
        book_app_module.main()
        capsys.readouterr()

        monkeypatch.setattr(sys, "argv", ["book_app.py", "list"])
        book_app_module.main()
        assert "[ ] The Hobbit" in capsys.readouterr().out

        def get_title(prompt: str) -> str:
            assert not title_args, "Inline titles must not prompt for input."
            return "  The Hobbit  "

        monkeypatch.setattr("builtins.input", get_title)
        monkeypatch.setattr(sys, "argv", ["book_app.py", "mark", *title_args])
        book_app_module.main()
        assert "marked as read successfully" in capsys.readouterr().out

        monkeypatch.setattr(book_app_module, "collection", BookCollection())
        monkeypatch.setattr(sys, "argv", ["book_app.py", "list"])
        book_app_module.main()
        assert "[✓] The Hobbit" in capsys.readouterr().out

    @pytest.mark.parametrize("title_args", [[], ["Nonexistent Book"]])
    def test_missing_book(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        title_args: list[str],
    ) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "Nonexistent Book")
        monkeypatch.setattr(sys, "argv", ["book_app.py", "mark", *title_args])

        book_app_module.main()

        assert 'Book "Nonexistent Book" not found.' in capsys.readouterr().out
        assert book_app_module.collection.list_books() == []

    @pytest.mark.parametrize("title_args, prompted_title", [
        ([], ""),
        ([], "   "),
        ([""], None),
        (["   "], None),
    ])
    def test_blank_title(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        title_args: list[str],
        prompted_title: str | None,
    ) -> None:
        book = book_app_module.collection.add_book("", "Author", 2000)

        def get_title(prompt: str) -> str:
            assert prompted_title is not None, "Blank arguments must not prompt."
            return prompted_title

        monkeypatch.setattr("builtins.input", get_title)
        monkeypatch.setattr(sys, "argv", ["book_app.py", "mark", *title_args])

        book_app_module.main()

        assert "Book title cannot be empty" in capsys.readouterr().out
        assert book.read is False
        assert BookCollection().list_books()[0].read is False

    def test_already_read_book(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_app_module.collection.add_book("Dune", "Frank Herbert", 1965)
        book_app_module.collection.mark_as_read("Dune")
        monkeypatch.setattr(sys, "argv", ["book_app.py", "mark", "Dune"])

        book_app_module.main()

        assert "marked as read successfully" in capsys.readouterr().out
        assert BookCollection().list_books()[0].read is True

    def test_help(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["book_app.py", "help"])

        book_app_module.main()

        output = capsys.readouterr().out
        assert "mark [title]" in output
        assert "omit title to be prompted" in output


@pytest.fixture
def populated_collection() -> BookCollection:
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.add_book("Tolkien Essays", "Tolkien", 2000)
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.mark_as_read("The Hobbit")
    collection.mark_as_read("1984")
    return collection


class TestSearchBooks:
    @pytest.mark.parametrize("query, expected_titles", [
        ("hob", ["The Hobbit"]),
        ("  TOLKIEN  ", ["The Hobbit", "Tolkien Essays"]),
        ("George Orwell", ["1984"]),
        ("nonexistent", []),
    ])
    def test_matches(
        self,
        populated_collection: BookCollection,
        query: str,
        expected_titles: list[str],
    ) -> None:
        results = populated_collection.search_books(query)

        assert [book.title for book in results] == expected_titles

    @pytest.mark.parametrize("query", ["", "   "])
    def test_blank_query(self, query: str) -> None:
        with pytest.raises(ValueError, match="Search text cannot be empty"):
            BookCollection().search_books(query)

    def test_empty_collection(self) -> None:
        assert BookCollection().search_books("hobbit") == []


class TestFilterByReadStatus:
    @pytest.mark.parametrize("read, expected_titles", [
        (True, ["The Hobbit", "1984"]),
        (False, ["Tolkien Essays", "Dune"]),
    ])
    def test_matching_status(
        self,
        populated_collection: BookCollection,
        read: bool,
        expected_titles: list[str],
    ) -> None:
        results = populated_collection.filter_by_read_status(read)

        assert [book.title for book in results] == expected_titles

    @pytest.mark.parametrize("read", [True, False])
    def test_no_matching_status(
        self, populated_collection: BookCollection, read: bool,
    ) -> None:
        for book in populated_collection.books:
            book.read = not read

        assert populated_collection.filter_by_read_status(read) == []

    @pytest.mark.parametrize("read", [True, False])
    def test_empty_collection(self, read: bool) -> None:
        assert BookCollection().filter_by_read_status(read) == []


class TestSearchAndFilterCommands:
    @pytest.mark.parametrize("args, prompted_input, expected_titles", [
        (["search"], "tolkien", ["The Hobbit", "Tolkien Essays"]),
        (["search", "hob"], None, ["The Hobbit"]),
        (["search", "George Orwell"], None, ["1984"]),
        (["search", "George", "Orwell"], None, ["1984"]),
        (["search", "  TOLKIEN  "], None, ["The Hobbit", "Tolkien Essays"]),
        (["filter"], " read ", ["The Hobbit", "1984"]),
        (["filter", "READ"], None, ["The Hobbit", "1984"]),
        (["filter", "  unread  "], None, ["Tolkien Essays", "Dune"]),
    ])
    def test_results_are_read_only(
        self,
        book_app_module: ModuleType,
        populated_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        args: list[str],
        prompted_input: str | None,
        expected_titles: list[str],
    ) -> None:
        data_file = Path(books.DATA_FILE)
        saved_data = data_file.read_bytes()
        original_books = [
            vars(book).copy() for book in populated_collection.list_books()
        ]
        monkeypatch.setattr(book_app_module, "collection", populated_collection)

        def get_input(prompt: str) -> str:
            assert prompted_input is not None, "Inline arguments must not prompt."
            return prompted_input

        def reject_save() -> None:
            pytest.fail("Search and filter must not save books.")

        monkeypatch.setattr("builtins.input", get_input)
        monkeypatch.setattr(populated_collection, "save_books", reject_save)
        monkeypatch.setattr(sys, "argv", ["book_app.py", *args])

        book_app_module.main()

        output = capsys.readouterr().out
        result_lines = [
            line for line in output.splitlines() if ". [" in line
        ]
        expected_books = [
            book for book in populated_collection.books
            if book.title in expected_titles
        ]
        assert result_lines == [
            f"{index}. [{'✓' if book.read else ' '}] "
            f"{book.title} by {book.author} ({book.year})"
            " - Not rated (0 reviews)"
            for index, book in enumerate(expected_books, start=1)
        ]
        assert [
            vars(book) for book in populated_collection.list_books()
        ] == original_books
        assert data_file.read_bytes() == saved_data

    @pytest.mark.parametrize("args, prompted_input, error", [
        (["search"], "", "Search text cannot be empty"),
        (["search"], "   ", "Search text cannot be empty"),
        (["search", ""], None, "Search text cannot be empty"),
        (["search", "   "], None, "Search text cannot be empty"),
        (["filter"], "", "Read status must be 'read' or 'unread'"),
        (["filter"], "finished", "Read status must be 'read' or 'unread'"),
        (["filter", ""], None, "Read status must be 'read' or 'unread'"),
        (["filter", "   "], None, "Read status must be 'read' or 'unread'"),
        (["filter", "finished"], None, "Read status must be 'read' or 'unread'"),
        (["filter", "read", "unread"], None,
         "Read status must be 'read' or 'unread'"),
    ])
    def test_invalid_input(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        args: list[str],
        prompted_input: str | None,
        error: str,
    ) -> None:
        def get_input(prompt: str) -> str:
            assert prompted_input is not None, "Blank arguments must not prompt."
            return prompted_input

        monkeypatch.setattr("builtins.input", get_input)
        monkeypatch.setattr(sys, "argv", ["book_app.py", *args])

        book_app_module.main()

        assert f"Error: {error}." in capsys.readouterr().out

    @pytest.mark.parametrize("args", [
        ["search", "hobbit"],
        ["filter", "read"],
        ["filter", "unread"],
    ])
    @pytest.mark.parametrize("missing_file", [False, True])
    def test_empty_collection(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        args: list[str],
        missing_file: bool,
    ) -> None:
        data_file = Path(books.DATA_FILE)
        if missing_file:
            data_file.unlink()
            monkeypatch.setattr(book_app_module, "collection", BookCollection())
        monkeypatch.setattr(sys, "argv", ["book_app.py", *args])

        book_app_module.main()

        assert capsys.readouterr().out.strip() == "No books found."
        assert data_file.exists() is not missing_file

    def test_search_without_matches(
        self,
        book_app_module: ModuleType,
        populated_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(book_app_module, "collection", populated_collection)
        monkeypatch.setattr(sys, "argv", ["book_app.py", "search", "nonexistent"])

        book_app_module.main()

        assert capsys.readouterr().out.strip() == "No books found."

    def test_help(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["book_app.py", "help"])

        book_app_module.main()

        output = capsys.readouterr().out
        assert "search [text]" in output
        assert "omit text to be prompted" in output
        assert "filter [read|unread]" in output
        assert "omit status to be prompted" in output


@pytest.fixture
def review_collection() -> BookCollection:
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.add_book("Dune", "Frank Herbert", 1965)
    return collection


class TestReviews:
    def test_multiple_readers_edit_remove_and_reload(
        self, review_collection: BookCollection,
    ) -> None:
        book = review_collection.books[0]
        assert book.average_rating is None
        review_collection.add_review(" the hobbit ", " Alice ", 1, " Good ")
        review_collection.add_review("The Hobbit", "Bob", 5)

        assert book.average_rating == 3
        assert book.reviews == [Review("Alice", 1, "Good"), Review("Bob", 5)]
        assert review_collection.books[1].reviews == []

        edited = review_collection.update_review("THE HOBBIT", " aLiCe ", 3)
        assert edited == Review("Alice", 3)
        assert book.average_rating == 4
        reloaded = BookCollection()
        assert reloaded.books[0] == book
        assert reloaded.books[0].average_rating == 4

        reloaded.remove_review("The Hobbit", " ALICE ")
        assert reloaded.books[0].average_rating == 5
        reloaded.remove_review("The Hobbit", "bob")
        assert BookCollection().books[0].average_rating is None
        assert BookCollection().list_reviews("The Hobbit") == []

    @pytest.mark.parametrize("operation", ["add", "update"])
    @pytest.mark.parametrize("field, value", [
        ("rating", 0), ("rating", 6), ("rating", 2.5), ("rating", 3.0),
        ("rating", True), ("rating", False), ("rating", "4"),
        ("rating", None), ("reader", ""), ("reader", "   "),
        ("reader", None), ("reader", 42), ("text", None), ("text", 42),
    ])
    def test_invalid_review_does_not_mutate_or_save(
        self,
        review_collection: BookCollection,
        operation: str,
        field: str,
        value: object,
    ) -> None:
        review_collection.add_review("The Hobbit", "Alice", 4, "Original")
        before = asdict(review_collection.books[0])
        saved = Path(books.DATA_FILE).read_bytes()
        values = {
            "reader": "Alice" if operation == "update" else "Bob",
            "rating": 5,
            "text": "Replacement",
        }
        values[field] = value
        method = (
            review_collection.add_review if operation == "add"
            else review_collection.update_review
        )

        with pytest.raises(ValueError):
            method("The Hobbit", **values)

        assert asdict(review_collection.books[0]) == before
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("reader", ["Alice", " alice ", "ALICE"])
    def test_duplicate_reader_is_rejected(
        self, review_collection: BookCollection, reader: str,
    ) -> None:
        review_collection.add_review("The Hobbit", "Alice", 4)
        saved = Path(books.DATA_FILE).read_bytes()

        with pytest.raises(ValueError, match="use review-edit"):
            review_collection.add_review("The Hobbit", reader, 5)

        assert review_collection.list_reviews("The Hobbit") == [
            Review("Alice", 4),
        ]
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("operation", [
        "list_reviews", "get_review", "add_review",
        "update_review", "remove_review",
    ])
    @pytest.mark.parametrize("title", ["", "   ", None, 42, "Missing"])
    def test_invalid_or_missing_book(
        self, review_collection: BookCollection, operation: str, title: object,
    ) -> None:
        saved = Path(books.DATA_FILE).read_bytes()
        arguments = {
            "list_reviews": (), "get_review": ("Alice",),
            "add_review": ("Alice", 4), "update_review": ("Alice", 4),
            "remove_review": ("Alice",),
        }

        with pytest.raises(ValueError):
            getattr(review_collection, operation)(title, *arguments[operation])

        assert all(book.reviews == [] for book in review_collection.books)
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("operation", [
        "get_review", "update_review", "remove_review",
    ])
    def test_missing_review(
        self, review_collection: BookCollection, operation: str,
    ) -> None:
        saved = Path(books.DATA_FILE).read_bytes()
        arguments = (
            ("Alice", 4) if operation == "update_review" else ("Alice",)
        )

        with pytest.raises(ValueError, match="Review.*not found"):
            getattr(review_collection, operation)("The Hobbit", *arguments)

        assert Path(books.DATA_FILE).read_bytes() == saved

    def test_save_only_on_successful_changes(
        self,
        review_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        saves = []
        monkeypatch.setattr(
            review_collection, "save_books", lambda: saves.append(1),
        )

        review_collection.add_review("The Hobbit", "Alice", 4)
        assert len(saves) == 1
        review_collection.list_reviews("The Hobbit")
        review_collection.get_review("The Hobbit", "Alice")
        assert len(saves) == 1
        review_collection.update_review("The Hobbit", "Alice", 5)
        assert len(saves) == 2
        review_collection.remove_review("The Hobbit", "Alice")
        assert len(saves) == 3

    def test_same_reader_on_different_books_and_book_removal(
        self, review_collection: BookCollection,
    ) -> None:
        review_collection.add_review("The Hobbit", "Alice", 4)
        review_collection.add_review("Dune", "Alice", 5)

        review_collection.remove_book("The Hobbit")

        reloaded = BookCollection()
        assert [book.title for book in reloaded.books] == ["Dune"]
        assert reloaded.list_reviews("Dune") == [Review("Alice", 5)]


class TestReviewPersistence:
    def test_legacy_books_load_without_migration(self) -> None:
        data_file = Path(books.DATA_FILE)
        data_file.write_text(json.dumps([
            {"title": "The Hobbit", "author": "Tolkien", "year": 1937,
             "read": True},
            {"title": "Dune", "author": "Herbert", "year": 1965},
        ]))
        saved = data_file.read_bytes()

        collection = BookCollection()

        assert collection.books == [
            Book("The Hobbit", "Tolkien", 1937, True),
            Book("Dune", "Herbert", 1965),
        ]
        assert all(book.average_rating is None for book in collection.books)
        assert data_file.read_bytes() == saved

    def test_unicode_review_round_trip(
        self, review_collection: BookCollection,
    ) -> None:
        reader = "Ren\u00e9e"
        text = "Tr\u00e8s bien \U0001f4da"
        review_collection.add_review("Dune", reader, 5, text)

        reloaded = BookCollection()

        assert reloaded.get_review("Dune", reader) == Review(reader, 5, text)
        assert reloaded.books[1].average_rating == 5
        saved = json.loads(Path(books.DATA_FILE).read_text(encoding="utf-8"))
        assert saved[1]["reviews"] == [
            {"reader": reader, "rating": 5, "text": text},
        ]
        assert "average_rating" not in saved[1]

    @pytest.mark.parametrize("raw_reviews", [
        None, {}, [None], [4], [{"reader": "Alice"}],
        [{"reader": "Alice", "rating": 0}],
        [{"reader": "Alice", "rating": True}],
        [{"reader": "Alice", "rating": 2.5}],
        [{"reader": " ", "rating": 5}],
        [{"reader": "Alice", "rating": 5, "text": None}],
        [{"reader": "Alice", "rating": 5, "unexpected": True}],
        [{"reader": "Alice", "rating": 5},
         {"reader": " alice ", "rating": 3}],
    ])
    def test_malformed_reviews_preserve_file_and_existing_collection(
        self, review_collection: BookCollection, raw_reviews: object,
    ) -> None:
        data_file = Path(books.DATA_FILE)
        original_books = review_collection.books.copy()
        records = [asdict(book) for book in original_books]
        records[1]["reviews"] = raw_reviews
        data_file.write_text(json.dumps(records))
        saved = data_file.read_bytes()

        with pytest.raises(ValueError):
            review_collection.load_books()
        with pytest.raises(ValueError):
            BookCollection()

        assert review_collection.books == original_books
        assert data_file.read_bytes() == saved


class TestReviewCommands:
    @pytest.mark.parametrize("title_args", [
        [], ["The Hobbit"], ["The", "Hobbit"], ["  the hobbit  "],
    ])
    def test_review_lifecycle(
        self,
        book_app_module: ModuleType,
        review_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        title_args: list[str],
    ) -> None:
        monkeypatch.setattr(book_app_module, "collection", review_collection)

        def run(command: str, fields: list[str]) -> str:
            answers = iter(fields if title_args else [" The Hobbit ", *fields])
            monkeypatch.setattr("builtins.input", lambda _: next(answers))
            monkeypatch.setattr(
                sys, "argv", ["book_app.py", command, *title_args],
            )
            book_app_module.main()
            monkeypatch.setattr(
                book_app_module, "collection", BookCollection(),
            )
            return capsys.readouterr().out

        added = run("review-add", ["Alice", "1", "Good"])
        assert "added successfully" in added
        assert "added successfully" in run("review-add", ["Bob", "5", ""])
        viewed = run("reviews", [])
        assert "3.0/5 (2 reviews)" in viewed
        assert "Alice: 1/5\n  Good" in viewed
        assert "Bob: 5/5" in viewed

        edited = run("review-edit", [" aLiCe ", "3", ""])
        assert "Current rating: 1/5" in edited
        assert "Current review: Good" in edited
        assert "updated successfully" in edited
        viewed = run("reviews", [])
        assert "4.0/5 (2 reviews)" in viewed
        assert "Alice: 3/5" in viewed
        assert "Good" not in viewed

        assert "removed successfully" in run("review-remove", ["ALICE"])
        assert "5.0/5 (1 review)" in run("reviews", [])
        assert "removed successfully" in run("review-remove", ["Bob"])
        viewed = run("reviews", [])
        assert "Not rated (0 reviews)" in viewed
        assert "No reviews yet." in viewed

    @pytest.mark.parametrize("command", ["review-add", "review-edit"])
    @pytest.mark.parametrize("rating", ["", "abc", "2.5", "0", "6"])
    def test_invalid_rating(
        self,
        book_app_module: ModuleType,
        review_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        command: str,
        rating: str,
    ) -> None:
        review_collection.add_review("The Hobbit", "Alice", 4, "Original")
        monkeypatch.setattr(book_app_module, "collection", review_collection)
        saved = Path(books.DATA_FILE).read_bytes()
        before = asdict(review_collection.books[0])
        answers = iter(["Alice", rating, "Replacement"])
        monkeypatch.setattr("builtins.input", lambda _: next(answers))
        monkeypatch.setattr(
            sys, "argv", ["book_app.py", command, "The Hobbit"],
        )

        book_app_module.main()

        assert (
            "Rating must be a whole number from 1 to 5"
            in capsys.readouterr().out
        )
        assert asdict(review_collection.books[0]) == before
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("command", [
        "reviews", "review-add", "review-edit", "review-remove",
    ])
    @pytest.mark.parametrize("title", ["", "   ", "Missing"])
    def test_invalid_book(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        command: str,
        title: str,
    ) -> None:
        def reject_input(prompt: str) -> str:
            pytest.fail(
                "Invalid inline titles must fail before further prompts."
            )

        monkeypatch.setattr("builtins.input", reject_input)
        monkeypatch.setattr(sys, "argv", ["book_app.py", command, title])
        saved = Path(books.DATA_FILE).read_bytes()

        book_app_module.main()

        assert "Error:" in capsys.readouterr().out
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("command, reader, error", [
        ("review-add", "   ", "Reader name must be a nonblank string"),
        ("review-edit", "", "Reader name must be a nonblank string"),
        ("review-remove", "", "Reader name must be a nonblank string"),
        ("review-add", " alice ", "use review-edit"),
        ("review-edit", "Missing", "not found"),
        ("review-remove", "Missing", "not found"),
    ])
    def test_reader_errors(
        self,
        book_app_module: ModuleType,
        review_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        command: str,
        reader: str,
        error: str,
    ) -> None:
        review_collection.add_review("The Hobbit", "Alice", 4)
        monkeypatch.setattr(book_app_module, "collection", review_collection)
        answers = iter([reader, "5", "Replacement"])
        monkeypatch.setattr("builtins.input", lambda _: next(answers))
        monkeypatch.setattr(
            sys, "argv", ["book_app.py", command, "The Hobbit"],
        )
        saved = Path(books.DATA_FILE).read_bytes()

        book_app_module.main()

        assert error in capsys.readouterr().out
        assert review_collection.list_reviews("The Hobbit") == [
            Review("Alice", 4),
        ]
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("has_reviews", [False, True])
    def test_view_reviews_is_read_only(
        self,
        book_app_module: ModuleType,
        review_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        has_reviews: bool,
    ) -> None:
        if has_reviews:
            review_collection.add_review("Dune", "Alice", 4, "Good")
        monkeypatch.setattr(book_app_module, "collection", review_collection)
        before = [asdict(book) for book in review_collection.books]
        saved = Path(books.DATA_FILE).read_bytes()

        def reject_save() -> None:
            pytest.fail("Viewing reviews must not save books.")

        monkeypatch.setattr(review_collection, "save_books", reject_save)
        monkeypatch.setattr(sys, "argv", ["book_app.py", "reviews", "Dune"])

        book_app_module.main()

        expected = (
            "4.0/5 (1 review)" if has_reviews else "Not rated (0 reviews)"
        )
        assert expected in capsys.readouterr().out
        assert [asdict(book) for book in review_collection.books] == before
        assert Path(books.DATA_FILE).read_bytes() == saved

    @pytest.mark.parametrize("args", [
        ["list"], ["search", "Dune"], ["filter", "unread"], ["find"],
    ])
    def test_book_listings_show_rating_summary(
        self,
        book_app_module: ModuleType,
        review_collection: BookCollection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        args: list[str],
    ) -> None:
        review_collection.add_review("Dune", "Alice", 4)
        review_collection.add_review("Dune", "Bob", 5)
        monkeypatch.setattr(book_app_module, "collection", review_collection)
        monkeypatch.setattr("builtins.input", lambda _: "Frank Herbert")
        monkeypatch.setattr(sys, "argv", ["book_app.py", *args])
        saved = Path(books.DATA_FILE).read_bytes()

        book_app_module.main()

        assert (
            "[ ] Dune by Frank Herbert (1965) - 4.5/5 (2 reviews)"
            in capsys.readouterr().out
        )
        assert Path(books.DATA_FILE).read_bytes() == saved

    def test_review_help(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["book_app.py", "help"])

        book_app_module.main()

        output = capsys.readouterr().out
        for command in [
            "review-add", "reviews", "review-edit", "review-remove",
        ]:
            assert f"{command} [title]" in output
        assert "omit title to be prompted" in output
        assert "blank text clears" in output
