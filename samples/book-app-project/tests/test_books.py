import sys
import os
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
