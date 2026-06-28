import os
import tempfile
import unittest
from csv_handler import CSVHandler, CSVHandlerError
from game_state import GameState

class TestQuizOthello(unittest.TestCase):
    def setUp(self):
        # Create a small dummy CSV file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, "test_quiz.csv")
        self.rows = 4
        self.cols = 4 # 16 questions needed
        
        # 20 questions total
        self.dummy_questions = [
            ("アニメ", f"問題{i}", f"答え{i}") for i in range(1, 21)
        ]
        
        import csv
        with open(self.csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ジャンル", "問題文", "答え"])
            for row in self.dummy_questions:
                writer.writerow(row)
                
        self.players = [
            {"name": "Player1", "color": "#ff0000"},
            {"name": "Player2", "color": "#00ff00"}
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_csv_loading_and_validation(self):
        # Test valid CSV loading without shuffle
        questions, final_path = CSVHandler.load_and_process_csv(
            self.csv_path, self.rows, self.cols, "シャッフルなし"
        )
        self.assertEqual(len(questions), 20)
        self.assertEqual(final_path, self.csv_path)
        self.assertEqual(questions[0]["id"], 1)
        self.assertEqual(questions[0]["genre"], "アニメ")
        self.assertEqual(questions[0]["question"], "問題1")
        self.assertEqual(questions[0]["answer"], "答え1")

        # Test validation failure for small count
        with self.assertRaises(CSVHandlerError):
            # Needs 36 questions (6x6), but only has 20
            CSVHandler.load_and_process_csv(
                self.csv_path, 6, 6, "シャッフルなし"
            )

    def test_csv_shuffle_saving(self):
        # Test shuffle all
        questions, final_path = CSVHandler.load_and_process_csv(
            self.csv_path, self.rows, self.cols, "シャッフルあり"
        )
        self.assertNotEqual(final_path, self.csv_path)
        self.assertTrue(os.path.exists(final_path))
        os.remove(final_path)

    def test_game_state_flow_and_othello(self):
        questions, _ = CSVHandler.load_and_process_csv(
            self.csv_path, self.rows, self.cols, "シャッフルなし"
        )
        state = GameState(
            rows=self.rows,
            cols=self.cols,
            csv_path=self.csv_path,
            original_csv_path=self.csv_path,
            shuffle_type="シャッフルなし",
            questions=questions,
            players=self.players
        )
        
        p1 = self.players[0]["color"] # Red
        p2 = self.players[1]["color"] # Green
        
        # Select cell (0, 0)
        q = state.select_cell(0, 0)
        self.assertIsNotNone(q)
        self.assertEqual(q["id"], 1) # First cell, initial ID is 1
        
        # Answer by p1
        state.resolve_question_with_winner(p1)
        self.assertEqual(state.board[0][0]["color"], p1)
        self.assertEqual(state.turn, 1)
        self.assertIn(1, state.used_questions_ids)
        used_records = state.get_used_question_records()
        self.assertEqual(used_records[0]["id"], 1)
        self.assertEqual(used_records[0]["genre"], questions[0]["genre"])
        self.assertEqual(used_records[0]["question"], questions[0]["question"])
        self.assertEqual(used_records[0]["answer"], questions[0]["answer"])
        self.assertIn("used_question_records", state.save_to_dict())
        self.assertIn("started_at", state.save_to_dict())
        self.assertRegex(state.elapsed_text(), r"^\d+:\d{2}:\d{2}$")
        
        # Select cell (0, 1), answer by p2
        state.select_cell(0, 1)
        state.resolve_question_with_winner(p2)
        self.assertEqual(state.board[0][1]["color"], p2)
        
        # Select cell (0, 2), answer by p1. This should sandwich (0, 1) and flip it to p1!
        state.select_cell(0, 2)
        state.resolve_question_with_winner(p1)
        self.assertEqual(state.board[0][2]["color"], p1)
        self.assertEqual(state.board[0][1]["color"], p1) # Flipped!
        
        # Test score counting
        scores = state.get_scores()
        self.assertEqual(scores[p1], 3)
        self.assertEqual(scores[p2], 0)

        # Test Undo
        self.assertTrue(state.undo())
        # Should rollback to before cell (0, 2) was answered. (0, 1) should be p2, and (0, 2) should be None.
        self.assertEqual(state.board[0][2]["color"], None)
        self.assertEqual(state.board[0][1]["color"], p2)
        self.assertEqual(state.turn, 2)
        
        # Test gray restore
        state.gray_restore_cell(0, 1)
        self.assertEqual(state.board[0][1]["color"], None)
        # Check that undoing gray restore works
        state.undo()
        self.assertEqual(state.board[0][1]["color"], p2)

    def test_reserve_question_rules(self):
        questions, _ = CSVHandler.load_and_process_csv(
            self.csv_path, self.rows, self.cols, "シャッフルなし"
        )
        state = GameState(
            rows=self.rows,
            cols=self.cols,
            csv_path=self.csv_path,
            original_csv_path=self.csv_path,
            shuffle_type="シャッフルなし",
            questions=questions,
            players=self.players
        )
        p1 = self.players[0]["color"]
        
        # Click (0, 0)
        state.select_cell(0, 0)
        state.resolve_question_with_winner(p1) # ID 1 is now used
        
        # Restore (0, 0) to gray
        state.gray_restore_cell(0, 0)
        self.assertEqual(state.board[0][0]["color"], None)
        
        # Click (0, 0) again. It should fetch a reserve question (ID > 16)
        q = state.select_cell(0, 0)
        self.assertIsNotNone(q)
        self.assertGreater(q["id"], 16) # Should be 17
        self.assertEqual(q["id"], 17)
        self.assertEqual(state.board[0][0]["initial_id"], 1)
        self.assertEqual(state.board[0][0]["display_genre"], q["genre"])

    def test_reserve_question_uses_csv_order_and_updates_display(self):
        questions = []
        for i in range(1, 17):
            questions.append({
                "id": i,
                "genre": "アニメ" if i == 1 else "歴史",
                "question": f"問題{i}",
                "answer": f"答え{i}",
            })
        questions.extend([
            {"id": 17, "genre": "スポーツ", "question": "予備17", "answer": "答え17"},
            {"id": 18, "genre": "アニメ", "question": "予備18", "answer": "答え18"},
        ])
        state = GameState(
            rows=self.rows,
            cols=self.cols,
            csv_path=self.csv_path,
            original_csv_path=self.csv_path,
            shuffle_type="シャッフルなし",
            questions=questions,
            players=self.players
        )
        p1 = self.players[0]["color"]

        state.select_cell(0, 0)
        state.resolve_question_with_winner(p1)
        state.gray_restore_cell(0, 0)

        q = state.select_cell(0, 0)
        self.assertEqual(q["id"], 17)
        self.assertEqual(q["genre"], "スポーツ")
        self.assertEqual(state.board[0][0]["initial_id"], 1)
        self.assertEqual(state.board[0][0]["display_genre"], "スポーツ")

if __name__ == "__main__":
    unittest.main()
