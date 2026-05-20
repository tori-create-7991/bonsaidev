"""Tests for atomic .answer.tmp -> .answer rename (must 2)."""

import threading

from bonsai.state.state_io import read_answer, write_answer


class TestWriteAnswer:
    def test_creates_answer_file(self, tmp_path):
        write_answer(tmp_path, "Use approach A.")
        assert (tmp_path / ".answer").exists()
        assert not (tmp_path / ".answer.tmp").exists()

    def test_content_is_preserved(self, tmp_path):
        write_answer(tmp_path, "The answer is 42.")
        assert (tmp_path / ".answer").read_text() == "The answer is 42."

    def test_atomic_no_tmp_visible(self, tmp_path):
        # After write_answer, no .answer.tmp should remain
        write_answer(tmp_path, "done")
        assert not (tmp_path / ".answer.tmp").exists()

    def test_overwrite_existing(self, tmp_path):
        write_answer(tmp_path, "first")
        write_answer(tmp_path, "second")
        assert (tmp_path / ".answer").read_text() == "second"

    def test_concurrent_writes_are_safe(self, tmp_path):
        errors = []

        def do_write(i: int) -> None:
            try:
                write_answer(tmp_path, f"answer-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_write, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        # Final file should contain one valid answer
        content = (tmp_path / ".answer").read_text()
        assert content.startswith("answer-")


class TestReadAnswer:
    def test_returns_none_when_missing(self, tmp_path):
        assert read_answer(tmp_path) is None

    def test_returns_content(self, tmp_path):
        write_answer(tmp_path, "here it is")
        assert read_answer(tmp_path) == "here it is"

    def test_consume_removes_file(self, tmp_path):
        write_answer(tmp_path, "consume me")
        result = read_answer(tmp_path, consume=True)
        assert result == "consume me"
        assert not (tmp_path / ".answer").exists()

    def test_consume_false_leaves_file(self, tmp_path):
        write_answer(tmp_path, "keep me")
        read_answer(tmp_path, consume=False)
        assert (tmp_path / ".answer").exists()
