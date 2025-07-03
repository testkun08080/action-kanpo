# Work Guidelines

## Documentation Requirements
-   Update relevant documentation in /docs when modifying features
-   Keep README.md in sync with new capabilities
-   Maintain changelog entries in CHANGELOG.md

## Project purpose
官報の更新情報を毎日8:45分に確認するGitHubアクションを開発したいと思っています。

- 毎日8:45分に走る
- Pythonを使って、官報のページをスクレイピングする
- 更新されたページでその日の更新があれば続ける
- その日のものがあれば、全てのpdfを取得して、git へそのままコミットする(更新日の日付フォルダ以下に)
- 官報のページはこれ (https://www.kanpo.go.jp/index.html)

## 検索対象のサンプル
リンクは、`class="pdfDlb"`　クラスでフィルタリングして、そのあとで発見したページ並行して、そのページの中にあるpdfをダウンロードして。
<iframe src="./pdf/20250703h01499full00010032.pdf" title="一括PDF" scrolling="no"></iframe>
