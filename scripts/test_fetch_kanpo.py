#!/usr/bin/env python3
"""
fetch_kanpo.py のローカルテスト実行
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 元のfetch_kanpo.pyの内容をコピー（テスト用に一部修正）
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from urllib.parse import urljoin, urlparse
import re


class KanpoFetcher:
    def __init__(self, test_mode=True):
        self.base_url = "https://www.kanpo.go.jp"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        self.test_mode = test_mode

    def get_today_date(self):
        """今日の日付を取得"""
        return datetime.now().strftime("%Y-%m-%d")

    def create_date_folder(self, date_str):
        """日付フォルダを作成"""
        if self.test_mode:
            # テストモードでは一時フォルダを使用
            base_folder = Path(tempfile.gettempdir()) / "kanpo_test"
        else:
            base_folder = Path("kanpo")

        folder_path = base_folder / date_str
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def fetch_main_page(self):
        """メインページを取得"""
        try:
            print("🌐 官報メインページにアクセス中...")
            response = self.session.get(self.base_url + "/index.html", timeout=10)
            response.raise_for_status()
            print("✅ メインページ取得成功")
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"❌ メインページの取得に失敗: {e}")
            return None

    def find_today_kanpo_link(self, soup):
        """今日の官報のリンクを探す"""
        print("🔍 今日の官報リンクを検索中...")
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # 複数のパターンでリンクを探す
        patterns = [
            today.strftime("%Y年%m月%d日"),
            today.strftime("%Y-%m-%d"),
            today.strftime("%m月%d日"),
            today.strftime("%m/%d"),
            yesterday.strftime("%Y年%m月%d日"),  # 昨日も含める
            yesterday.strftime("%Y-%m-%d"),
            yesterday.strftime("%m月%d日"),
        ]

        print(f"📅 検索パターン: {patterns}")

        links = []
        for link in soup.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            href = link.get("href", "")

            for pattern in patterns:
                if pattern in link_text or pattern in href:
                    full_url = urljoin(self.base_url, href)
                    links.append({"url": full_url, "text": link_text, "pattern_matched": pattern})
                    print(f"  ✅ 発見: {link_text} (パターン: {pattern})")
                    break

        if not links:
            print("⚠️  今日・昨日の官報リンクが見つかりません")
            print("💡 利用可能なリンクの例:")
            for i, link in enumerate(soup.find_all("a", href=True)[:10]):
                text = link.get_text(strip=True)
                if text and len(text) > 3:
                    print(f"    {i + 1}. {text}")

        return links

    def fetch_kanpo_page(self, kanpo_url):
        """官報ページを取得してPDFリンクを抽出"""
        print(f"📖 官報ページを処理中: {kanpo_url}")
        try:
            response = self.session.get(kanpo_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            pdf_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.lower().endswith(".pdf"):
                    pdf_url = urljoin(kanpo_url, href)
                    pdf_name = link.get_text(strip=True) or os.path.basename(urlparse(href).path)
                    pdf_links.append({
                        "url": pdf_url,
                        "name": pdf_name,
                        "filename": os.path.basename(urlparse(href).path),
                    })
                    print(f"  📄 PDF発見: {pdf_name}")

            print(f"📊 このページで {len(pdf_links)} 個のPDFを発見")
            return pdf_links

        except Exception as e:
            print(f"❌ 官報ページの取得に失敗 {kanpo_url}: {e}")
            return []

    def download_pdf(self, pdf_info, folder_path):
        """PDFファイルをダウンロード"""
        try:
            print(f"📥 ダウンロード開始: {pdf_info['name']}")

            if self.test_mode:
                # テストモード: ヘッダー情報のみ取得
                response = self.session.head(pdf_info["url"], timeout=10)
                response.raise_for_status()

                content_length = response.headers.get("Content-Length", "不明")
                content_type = response.headers.get("Content-Type", "不明")

                print(f"  ✅ ファイル確認成功")
                print(f"  📊 サイズ: {content_length} bytes")
                print(f"  📋 タイプ: {content_type}")

                # テスト用に空のファイルを作成
                safe_filename = re.sub(r"[^\w\-_\.]", "_", pdf_info["filename"])
                if not safe_filename.endswith(".pdf"):
                    safe_filename += ".pdf"

                file_path = folder_path / safe_filename
                file_path.write_text(f"テストファイル - {pdf_info['name']}\n作成日時: {datetime.now()}")

                return True
            else:
                # 実際のダウンロード
                response = self.session.get(pdf_info["url"], stream=True, timeout=30)
                response.raise_for_status()

                safe_filename = re.sub(r"[^\w\-_\.]", "_", pdf_info["filename"])
                if not safe_filename.endswith(".pdf"):
                    safe_filename += ".pdf"

                file_path = folder_path / safe_filename

                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"  ✅ ダウンロード完了: {safe_filename}")
                return True

        except Exception as e:
            print(f"  ❌ PDFダウンロードに失敗 {pdf_info['url']}: {e}")
            return False

    def create_readme(self, folder_path, pdf_list, date_str):
        """READMEファイルを作成"""
        readme_path = folder_path / "README.md"

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# 官報 {date_str}\n\n")
            f.write(f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"テストモード: {'有効' if self.test_mode else '無効'}\n\n")
            f.write("## ダウンロードファイル\n\n")

            for pdf_info in pdf_list:
                f.write(f"- [{pdf_info['name']}]({pdf_info['filename']})\n")
                f.write(f"  - URL: {pdf_info['url']}\n")

        print(f"📝 README.md を作成: {readme_path}")

    def run(self):
        """メイン処理"""
        print("🚀 官報自動取得テストを開始...")
        print("=" * 60)

        # メインページを取得
        soup = self.fetch_main_page()
        if not soup:
            print("❌ メインページの取得に失敗しました")
            return False

        # 今日の官報リンクを探す
        today_links = self.find_today_kanpo_link(soup)
        if not today_links:
            print("❌ 今日の官報が見つかりませんでした")
            return False

        print(f"\n📋 処理対象: {len(today_links)} 個の官報リンク")

        # 日付フォルダを作成
        today_str = self.get_today_date()
        folder_path = self.create_date_folder(today_str)
        print(f"📁 保存先フォルダ: {folder_path}")

        all_pdfs = []

        # 各官報ページからPDFを取得
        for i, link_info in enumerate(today_links):
            print(f"\n--- 官報ページ {i + 1}/{len(today_links)} ---")
            print(f"📖 処理中: {link_info['text']}")

            pdf_links = self.fetch_kanpo_page(link_info["url"])

            for pdf_info in pdf_links:
                if self.download_pdf(pdf_info, folder_path):
                    all_pdfs.append(pdf_info)
                time.sleep(1)  # サーバー負荷軽減

        # 結果のまとめ
        print("\n" + "=" * 60)
        print("📊 実行結果")
        print("=" * 60)

        if all_pdfs:
            self.create_readme(folder_path, all_pdfs, today_str)
            print(f"✅ 成功: {len(all_pdfs)} 個のPDFファイルを取得しました")
            print(f"📁 保存場所: {folder_path}")

            # ファイル一覧を表示
            print("\n📄 取得したファイル:")
            for i, pdf in enumerate(all_pdfs, 1):
                print(f"  {i}. {pdf['name']}")

            return True
        else:
            print("❌ PDFファイルが見つかりませんでした")
            return False


def main():
    print("官報取得システム - ローカルテスト")
    print("=" * 60)

    # テストモードの選択
    mode = input(
        "実行モードを選択してください:\n"
        "1. テストモード（ヘッダー情報のみ取得、推奨）\n"
        "2. 実際のダウンロード\n"
        "番号を入力: "
    ).strip()

    if mode == "2":
        test_mode = False
        print("⚠️  実際のダウンロードモードで実行します")
        confirm = input("本当に実行しますか？ (y/N): ").strip().lower()
        if confirm != "y":
            print("👋 実行を中止しました")
            return
    else:
        test_mode = True
        print("💡 テストモード（推奨）で実行します")

    print("\n🚀 テスト開始...")

    fetcher = KanpoFetcher(test_mode=test_mode)
    success = fetcher.run()

    print("\n" + "=" * 60)
    if success:
        print("🎉 テスト完了！")
        if test_mode:
            print("💡 実際の運用では GitHub Actions が同様の処理を自動実行します")
        else:
            print("✅ 実際のファイルダウンロードが成功しました")
    else:
        print("⚠️  問題が検出されました")
        print("🔧 以下を確認してください:")
        print("  - インターネット接続")
        print("  - 官報サイトの構造変更")
        print("  - 今日が官報発行日か（土日祝日は通常発行されません）")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 テストを中断しました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback

        traceback.print_exc()
