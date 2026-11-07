import sys
import os
from pathlib import Path
from types import ModuleType
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import Book, BookCollection, get_book_statistics


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
