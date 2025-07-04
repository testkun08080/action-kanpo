# 官報チェック🤖

## はじめに
[官報](https://www.kanpo.go.jp/index.html)のRSSを探していたところ、見つからなかったため、このプロジェクトを作成しました。官報の更新情報を毎日確認し、SNSなどで通知できるようにすることを目指しています。

## 目的
このリポジトリでは、官報のウェブサイトを毎日8:45分（および念のため9:00 JSTにもう一度）にスクレイピングし、当日の更新があるかを判断して、当日のURLやPDFを返すGitHub Actionを提供します。最終的には、官報の通知サービスをさまざまなSNSでPushできるようにするのが目的です。

## 特徴
- **定期実行**: 毎日8:45分（JST）に官報の更新をチェックするようにスケジュール設定されています。
- **スクレイピング**: Pythonを使用して官報のページを解析し、当日の更新情報を取得します。
- **PDFダウンロード**: 更新が見つかった場合、関連するPDFをダウンロードし、リポジトリにコミットします（日付ごとのフォルダに保存）。
- **GitHub Action**: 他のワークフローと統合可能なアクションとして提供され、出力結果を利用して通知や他の処理を行うことができます。

## 大まかな処理内容
- 毎日8:45分にGitHub Actionが実行されます。
- Pythonスクリプトを使用して、官報のページ（https://www.kanpo.go.jp/index.html）をスクレイピングします。
- 当日の更新が掲載されているかをチェックし、記事名やURLなどを返します。
- また、当日のデータがあれば、すべてのPDFを取得し、リポジトリにそのままコミットすることも可能です（更新日の日付フォルダ以下に保存）。。

## 使い方
このGitHub Actionを自分のワークフローに組み込むことで、官報の更新を自動的にチェックし、必要に応じてPDFをダウンロードすることができます。以下は、ワークフローでの使用例です。

### ワークフロー例
```yaml
name: Check Kanpo Updates
on:
  schedule:
    - cron: '45 8 * * *'  # 毎日8:45 JST
  workflow_dispatch:        # 手動実行も可能

jobs:
  check-kanpo:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Run Kanpo Fetch Action
        uses: testkun08080/action-kanpo@main
        with:
          dlpdf: 'false'  # PDFをダウンロードする場合は 'true'
          date: '2025-07-05'       # 特定の日付を指定する場合は 'YYYY-MM-DD' 形式で入力。空欄で当日を対象
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # コミット権限のために必要

      - name: Check Outputs
        run: |
          echo "Kanpo Found: ${{ steps.kanpo-fetch.outputs.kanpou_found }}"
          echo "PDF Infos: ${{ steps.kanpo-fetch.outputs.pdf_infos }}"
        if: always()
```

## 入力と出力
### 入力
- `dlpdf`: PDFをダウンロードするかどうか（デフォルト: `false`）。`true`に設定するとPDFをダウンロードします。
- `date`: 対象日付（例: `2025-07-05`）。指定しない場合は当日の日付を使用します。

### 出力
- `kanpou_found`: 官報が見つかったかどうかを示すブール値。
- `pdf_infos`: ダウンロードしたPDFの情報リスト（JSON形式）。

## セットアップと要件
- このアクションはDockerコンテナ内で実行されます（`Dockerfile`に基づいてビルド）。
- 特別なセットアップは不要ですが、ワークフローでリポジトリへのコミット権限が必要な場合は、`GITHUB_TOKEN`を環境変数として設定してください。
- ローカルでテストする場合は、Python環境と依存関係（`pyproject.toml`に記載）をインストールする必要があります。

## ライセンス
このプロジェクトのライセンスについては、[LICENSE](./LICENSE)ファイルを参照してください。

## 貢献
バグ報告や機能リクエスト、プルリクエストは大歓迎です。問題や提案がある場合は、GitHubのIssueを作成してください。
