---
name: roundtable
description: grilling（質問攻めで合意を作る手法）を HTML のフォームで行い、候補選択・自由入力・保留で内容を詰めて、最後に SPEC 形式で結果を出す。ユーザーが「HTML で grilling」「roundtable」と明示したときだけ使う。単に「grill して」と頼まれただけのときは使わない。
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/roundtable.py *) Bash(python "${CLAUDE_SKILL_DIR}/roundtable.py" *) Bash(python3 ${CLAUDE_SKILL_DIR}/roundtable.py *) Bash(python3 "${CLAUDE_SKILL_DIR}/roundtable.py" *)
---

# roundtable

計画や設計について、ユーザーに質問をラウンド単位で重ねて合意を作る（grilling）。質問と回答は HTML フォームでやり取りし、合意内容を SPEC にまとめる。以下の `python` は、環境に `python` コマンドがなければ `python3` に読み替える。

## ルール
出典: [mattpocock/skills の grilling](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)（MIT）を要約・翻案。design tree は、決定ごとにそれに依存する決定が枝分かれする木。frontier は、前提がすべて決着済みで推測なしに今聞ける決定の集まり。

- 決定事項を design tree として扱う。前提が決着済みで今聞ける質問（frontier）を、1ラウンドにまとめて出す。回答を待ってから次へ進む。
- 各質問に推奨案（`recommended` と `reason`）を付ける。選択式にして、トレードオフを `desc` に書く。
- 環境から調べられる事実はサブエージェントに調べさせ、ユーザーには聞かない。決定だけをユーザーに聞く。調査待ちの質問は後のラウンドに回す。
- 回答に `聞き返し` があった質問（状態「要確認」）は、決着していない。次のラウンドで、その質問への説明か補足質問を先頭に出す。聞き返しが残っている間は、frontier が空でも終わらない。
- 文脈が濃い質問は、`body` に背景を書いてよい（簡易 Markdown: 段落・箇条書き・コードブロック・インラインコード。長いと折りたたまれる）。選択肢で絞れない問いは `options` を省略し、自由記述で答えてもらう。
- frontier が空になるまで続ける。ユーザーが承認するまで、実行（実装・ファイル作成）に移らない。
- 質問 ID（`Q1`, `Q2`…）はセッション通しで一意にする（ラウンドでリセットしない）。

## 手順
1. セッション作成: `python "${CLAUDE_SKILL_DIR}/roundtable.py" init --theme "<テーマ>"` を実行する。テーマは ASCII の短い名前にする（Windows の Git Bash 経由の日本語引数は文字化けするため。例: `api-design`）。出力された絶対パス（以下 `<D>`）を控える。セッションのフォルダは `<親>/<日時>_roundtable_<テーマ>/` にできる。親は `--parent` > 環境変数 `ROUNDTABLE_DIR` > カレントフォルダの順で決まる（人が開くファイルなので、隠しフォルダには置かない）。
2. 事前確認（Round 0）: 通常の質問に入る前に、`--round 0` で次の3点を1ラウンドで確認する。依頼文や環境から分かる内容は推奨案として埋め、ユーザーには確認・修正だけしてもらう（毎回行う。小さい依頼でも省略しない）。質問 JSON・生成・回答の記録は手順3〜6と同じ。
   - 目的とゴール: 何のために行い、何ができたら完了か（完了の判定基準）。
   - 障壁: ゴールに至るまでの障害・懸念・つまずきそうな点を、ユーザーにヒアリングする。
   - 制約: 期限・予算・技術・既存資産・変更してはいけないもの・守るべきルールなど。
   回答は以降のラウンドの前提にし、SPEC では既存項目に吸収する（目的・ゴール→概要、障壁→リスク、制約→非目標・決定ログ）。
3. 質問 JSON を書く。置き場所はスクラッチパッド（なければ `<D>`）。形式は `roundtable.py` の docstring を参照（`title`, `intro`, `questions[]` = `id`, `title`, `body`, `multi`, `options[]`（省略可）= `key`, `label`, `desc`、`recommended[]`, `reason`）。
4. 生成: `python "${CLAUDE_SKILL_DIR}/roundtable.py" render --session-dir "<D>" --round <N> --input <json>` → `<D>/round-N.html`。
5. Playwright MCP で `browser_navigate` により `file://` URL を開く（Windows は `file:///C:/.../round-N.html` のようにスラッシュ区切りにする。macOS/Linux は `file:///home/.../round-N.html`）。ユーザーに「回答して『送信』を押してください」と伝える。
6. 送信を自動で待つ（ユーザーに「完了」と入力させない）。`browser_evaluate` で次の関数を実行すると、送信されるか約100秒たつまでブロックして結果を返す。
   `() => new Promise(res => { const t0 = Date.now(); const id = setInterval(() => { if (window.__submitted || Date.now() - t0 > 100000) { clearInterval(id); res({ submitted: !!window.__submitted, md: window.__answersMd }); } }, 500); })`
   - `submitted` が false なら、まだ送信されていない。同じ呼び出しを繰り返す（合計約30分、18回まで）。
   - ユーザーがターミナルに何か入力した場合は、待ちをやめてその内容に従う（「完了」なら即座に下の確認へ進む）。
   - 上限を超えたら、続行方法をユーザーに聞く。
   - `submitted` が true なら、`md` をそのまま `<D>/round-N.answers.md` に書く（Write）。
   - false（未送信・ウィンドウを閉じた等）なら、書かずに続行方法を聞く。コピーボタンで Markdown を貼ってもらう手もある。
7. 回答を読んで design tree を更新し、次のラウンド（手順3〜）へ。ラウンドごとに新しい HTML を生成する。
8. frontier が空になったら、合意内容を SPEC 案（概要・流れ・受入条件・非目標・リスク・決定ログ）にまとめ、`{"title","intro","summary"}` の JSON で `render --final --round <K>` を実行して `<D>/final-K.html` を開く。K は最終確認の版番号で、1 から始めて修正のたびに 1 増やす（前の版を上書きしない）。送信の待ち方と回答の記録は手順6と同じ（`<D>/final-K.answers.md` に書く）。
9. `承認` なら、承認された版の `summary` をそのまま `<D>/spec.md` に書く（Write）。別のセッションに SPEC を渡すときは、このファイルを使う。続けて、確認なしで `python "${CLAUDE_SKILL_DIR}/roundtable.py" cleanup --session-dir "<D>" --yes` を実行し、`spec.md` 以外の生成ファイル（`round-*.html`・`final-*.html`・回答）を自動で削除する（`cleanup` は既知の生成ファイル名だけを消し、`spec.md` と他のファイルには触れない）。削除したファイル名と、残ったのが `spec.md` だけであることを報告する。
   そのあと、必要なものだけを次の形式の**1通のメッセージ**で提案する（該当する項目がなければ出さない。「まだ実行していません」のような断りや内部用語は書かない）。
   ```
   SPEC を `<D>/spec.md` に保存し、それ以外の生成ファイルは削除しました。続けて次をしますか？（番号で答えてください。不要なら「なし」）
   1. `spec.md` を `docs/` にもコピーする — リポジトリ側にも残したいとき。
   2. `.gitignore` に追記する — セッションフォルダ（`*_roundtable_*/`）や `.playwright-mcp/` を Git の対象外にします。
   ```
   該当しない項目（Git リポジトリ外なら両方、`.playwright-mcp/` がなければその追記など）は載せず、番号を詰める。選ばれた項目だけ実行する（どちらもセッションフォルダの外に書くため、勝手に編集しない）。カレントフォルダに `.playwright-mcp/` ができていれば、README の「すでに Playwright MCP を登録している場合」の `--output-dir` 設定も一言案内する。
   `修正あり` ならコメントを反映し、K を 1 増やして手順8を繰り返す。

## 回答 Markdown の書式（ページ側が生成する）
```
---
session: <フォルダ名>
round: <N>
---
## Q1
- 選択: A        （複数は「, 」区切り）
- 自由入力: …
- 補足: …
- 聞き返し: …
- 状態: 回答 / 保留 / 要確認 / 未回答
```
最終確認は frontmatter が `round` ではなく `final: <K>`（版番号）で、本文は `## 承認` に `判定`（承認 / 修正あり）と `コメント`。

## 注意
- JS の `alert/confirm/prompt` は使わない（ブラウザ操作が止まる）。
- `file://` が開けない場合は、`--allow-unrestricted-file-access` 付きで Playwright MCP が設定されているかを確認する。
