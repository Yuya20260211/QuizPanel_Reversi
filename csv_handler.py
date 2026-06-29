import os
import csv
import random
from datetime import datetime


class CSVHandlerError(Exception):
    """Custom exception for CSV validation errors."""
    pass


class CSVHandler:
    REQUIRED_COLUMNS = ("ジャンル", "問題文", "答え")
    ENCODINGS = ("utf-8-sig", "cp932", "utf-8")
    COLUMN_ALIASES = {
        "ジャンル": {"ジャンル", "ジャンル名", "カテゴリ", "カテゴリー", "分類", "種別", "種類",
                    "genre", "category", "type", "subject", "topic", "field"},
        "問題文": {"問題文", "問題", "問い", "設問", "質問", "出題", "クイズ",
                  "question", "quiz", "q", "問"},
        "答え": {"答え", "解答", "回答", "正解", "正答", "解",
                "answer", "correct", "a"},
    }

    @staticmethod
    def load_and_process_csv(file_path: str, rows: int, cols: int, shuffle_type: str) -> tuple[list[dict], str]:
        """
        Loads, validates, shuffles (if requested), and processes the quiz CSV.
        Returns:
            A tuple of (list of question dicts, path of the CSV file actually used).
        Raises:
            CSVHandlerError: If validation fails.
        """
        if not os.path.exists(file_path):
            raise CSVHandlerError(f"CSVファイルが見つかりません:\n{file_path}")

        raw_questions = CSVHandler._load_raw_questions(file_path)

        required_count = rows * cols
        if len(raw_questions) < required_count:
            raise CSVHandlerError(
                f"CSVの初期問題が足りません。\n"
                f"必要数: {required_count}問 (盤面: {rows}×{cols})\n"
                f"現在の問題数: {len(raw_questions)}問\n"
                f"盤面サイズを小さくするか、問題数を増やしてください。"
            )

        shuffled_questions = []
        is_shuffled = False

        if shuffle_type == "シャッフルなし":
            shuffled_questions = raw_questions.copy()
        elif shuffle_type == "シャッフルあり":
            shuffled_questions = raw_questions.copy()
            random.shuffle(shuffled_questions)
            is_shuffled = True
        else:
            raise CSVHandlerError(f"無効なシャッフル設定です: {shuffle_type}")

        for idx, q in enumerate(shuffled_questions, start=1):
            q["id"] = idx

        final_csv_path = file_path
        if is_shuffled:
            dir_name, file_name = os.path.split(file_path)
            base_name, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shuffled_file_name = f"{base_name}_shuffled_{timestamp}{ext}"
            final_csv_path = os.path.join(dir_name, shuffled_file_name)

            try:
                with open(final_csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(CSVHandler.REQUIRED_COLUMNS))
                    writer.writeheader()
                    for q in shuffled_questions:
                        writer.writerow({
                            "ジャンル": q["genre"],
                            "問題文": q["question"],
                            "答え": q["answer"],
                        })
            except Exception as e:
                raise CSVHandlerError(f"シャッフルCSVの保存に失敗しました:\n{str(e)}")

        return shuffled_questions, final_csv_path

    @staticmethod
    def _row_is_likely_data(row: list[str]) -> bool:
        """Heuristic: True if the row looks like quiz content rather than column headers.

        A data row tends to contain at least one cell that is either long (>15 chars),
        contains Japanese sentence characters, or contains any non-ASCII characters
        (kanji, hiragana, katakana, etc.).  Short ASCII-only cells — typical of English
        column names like "Category" or "Answer" — return False.
        """
        sentence_chars = frozenset('。、！？…')
        for cell in row:
            cleaned = CSVHandler._clean_cell(cell)
            if not cleaned:
                continue
            if len(cleaned) > 15:
                return True
            if any(c in cleaned for c in sentence_chars):
                return True
            if any(ord(c) > 0x7F for c in cleaned):
                return True
        return False

    @staticmethod
    def _load_raw_questions(file_path: str) -> list[dict]:
        rows = CSVHandler._read_csv_rows(file_path)
        if not rows:
            raise CSVHandlerError("CSVファイルが空です。")

        header = [CSVHandler._clean_cell(cell) for cell in rows[0]]
        column_map = CSVHandler._resolve_columns(header)

        raw_questions = []
        if column_map:
            missing = [col for col in CSVHandler.REQUIRED_COLUMNS if col not in column_map]
            if missing:
                raise CSVHandlerError(
                    "CSVの必須列が足りません。\n"
                    f"必要な列: {', '.join(CSVHandler.REQUIRED_COLUMNS)}\n"
                    f"見つかった列: {', '.join(header)}\n"
                    f"不足している列: {', '.join(missing)}"
                )

            for line_idx, row in enumerate(rows[1:], start=2):
                if not any(CSVHandler._clean_cell(cell) for cell in row):
                    continue
                genre = CSVHandler._row_value(row, column_map["ジャンル"])
                question = CSVHandler._row_value(row, column_map["問題文"])
                answer = CSVHandler._row_value(row, column_map["答え"])
                raw_questions.append(CSVHandler._make_question(line_idx, genre, question, answer))
            return raw_questions

        if len(header) < 3:
            raise CSVHandlerError(
                "CSVの列を判別できません。\n"
                "1行目を「ジャンル,問題文,答え」にするか、ヘッダーなしの場合は3列で作成してください。"
            )

        # column_map is empty: no alias matched. Determine whether row 0 is actual
        # quiz data (headerless CSV) or an unrecognized header row.
        if not CSVHandler._row_is_likely_data(rows[0]):
            raise CSVHandlerError(
                "CSVの1行目の列名を認識できませんでした。\n"
                f"検出された1行目: {', '.join(header)}\n"
                "以下の列名が使用できます:\n"
                "  ジャンル列: ジャンル, ジャンル名, カテゴリ, genre, category\n"
                "  問題文列:   問題文, 問題, question, quiz\n"
                "  答え列:     答え, 解答, 回答, 正解, answer\n"
                "ヘッダーなしCSVの場合は、1行目からデータを直接入力してください（ヘッダー行不要）。"
            )

        for line_idx, row in enumerate(rows, start=1):
            if not any(CSVHandler._clean_cell(cell) for cell in row):
                continue
            genre = CSVHandler._row_value(row, 0)
            question = CSVHandler._row_value(row, 1)
            answer = CSVHandler._row_value(row, 2)
            raw_questions.append(CSVHandler._make_question(line_idx, genre, question, answer))
        return raw_questions

    @staticmethod
    def _read_csv_rows(file_path: str) -> list[list[str]]:
        last_error = None
        for encoding in CSVHandler.ENCODINGS:
            try:
                with open(file_path, mode="r", encoding=encoding, newline="") as f:
                    return list(csv.reader(f))
            except UnicodeDecodeError as e:
                last_error = e
        raise CSVHandlerError(f"CSVの文字コードを判別できませんでした:\n{last_error}")

    @staticmethod
    def _resolve_columns(header: list[str]) -> dict[str, int]:
        resolved = {}
        normalized_aliases = {
            canonical: {CSVHandler._normalize_header(alias) for alias in aliases}
            for canonical, aliases in CSVHandler.COLUMN_ALIASES.items()
        }
        for idx, name in enumerate(header):
            normalized = CSVHandler._normalize_header(name)
            for canonical, aliases in normalized_aliases.items():
                if normalized in aliases:
                    resolved[canonical] = idx
                    break
        return resolved

    @staticmethod
    def _make_question(line_idx: int, genre: str, question: str, answer: str) -> dict:
        genre = genre or "ノージャンル"
        if not question:
            raise CSVHandlerError(f"{line_idx}行目: 問題文が空欄です。")
        if not answer:
            raise CSVHandlerError(f"{line_idx}行目: 答えが空欄です。")
        return {
            "genre": genre,
            "question": question,
            "answer": answer,
        }

    @staticmethod
    def _row_value(row: list[str], index: int) -> str:
        if index >= len(row):
            return ""
        return CSVHandler._clean_cell(row[index])

    @staticmethod
    def _clean_cell(value) -> str:
        if value is None:
            return ""
        return str(value).replace("\ufeff", "").strip()

    @staticmethod
    def _normalize_header(value: str) -> str:
        return CSVHandler._clean_cell(value).replace("　", " ").replace(" ", "").lower()
