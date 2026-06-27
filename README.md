# QuizPanel Reversi

QuizPanel Reversi は、クイズ大会や配信企画で使える、アタック25風のクイズ用オセロ盤アプリです。

出題者用パネルと回答者用パネルを分けて表示でき、問題文や答えは出題者側だけに表示されます。回答者側には番号とジャンルだけが表示されるため、参加者に見せながらスムーズに進行できます。

CSVから問題を読み込み、正解者の色でマスを取得し、オセロのように挟んだマスをひっくり返します。スコア表示、Undo、灰色戻し、途中保存、再開、画像保存にも対応しています。

## 主な機能

- 出題者側と回答者側の2ウィンドウ表示
- CSVから問題を読み込み
- 盤面サイズを指定可能
- シャッフルなし、予備問題のみシャッフル、全体シャッフルに対応
- 正解者あり、正解者なしに対応
- オセロ判定によるマスの反転
- スコア表示
- Undo
- 灰色戻し
- JSON保存、再開
- 盤面画像保存

## CSV形式

CSVの基本形式は次の3列です。

```csv
ジャンル,問題文,答え
スポーツ,野球でバッターがノーヒットで出塁する四球を英語で何と言う？,フォアボール
歴史,鎌倉幕府を開いた人物は？,源頼朝
```

補足:

- 問題番号列は不要です。CSVの行順から自動で番号が付きます。
- ジャンルが空欄の場合は `ノージャンル` として扱います。
- 問題文と答えは空欄にできません。
- Excel由来の CP932 / Shift-JIS CSV も読み込みに対応しています。

## 実行方法

```powershell
pip install -r requirements.txt
python main.py
```

## exe化

PyInstallerで単体exeを作成できます。

```powershell
python -m PyInstaller -y --noconsole --onefile --icon assets\app_icon.ico --name QuizPanel_Reversi main.py
```

生成されるexe:

```text
dist\QuizPanel_Reversi.exe
```
