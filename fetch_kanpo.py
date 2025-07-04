"""
官報のページを見に行き、当日のデータがあるかどうかを確認するかどうかをチェックするPythonスクリプトです。
GitHub Actionとして実行され、結果を出力します。
時間は日本時間（Asia/Tokyo）で取得されます。
"""

import os
import re
import time
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def str2bool(v):
    """文字列を真偽値に変換するヘルパー関数"""
    return str(v).lower() in ("true")


class KanpoFetcher:
    def __init__(self, target_date=None):
        """官報のページを取得し、PDFファイルをダウンロードするクラス
        Args:
            test_mode (bool, optional): _description_. Defaults to True.
            target_date (datetime, optional): _description_. Defaults to None.
        """
        self.base_url = "https://www.kanpo.go.jp"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self.target_date = target_date or datetime.now(ZoneInfo("Asia/Tokyo"))  # 日本時間（Asia/Tokyo）で現在時刻

    def get_target_date(self):
        """検索対象の日付文字列(YYYY-MM-DD)を取得

        Returns:
            str: 日付文字列（YYYY-MM-DD）
        """

        return self.target_date.strftime("%Y-%m-%d")

    def create_date_folder(self, date_str):
        """日付に基づいてフォルダを作成します

        Args:
            date_str (str): 日付文字列（YYYY-MM-DD）

        Returns:
            str: 作成されたフォルダのパス
        """
        base_folder = Path("kanpo")
        folder_path = base_folder / date_str
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def fetch_main_page(self):
        """官報のメインページを取得します

        Returns:
            BeautifulSoup: メインページのBeautifulSoupオブジェクト
        """
        try:
            print("🌐 官報メインページにアクセス中...")
            response = self.session.get(self.base_url + "/index.html", timeout=10)
            response.raise_for_status()
            print("✅ メインページ取得成功")
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"❌ メインページの取得に失敗: {e}")
            return None

    def find_kanpo_link(self, soup, class_filter=None):
        """官報の発行リンクを検索します

        Args:
            soup (BeautifulSoup): BeautifulSoupオブジェクト
            class_filter (str, optional): 検索用のクラス名フィルタ. Defaults to None.

        Returns:
            _type_: _description_
        """

        print("🔍 官報リンクを検索中...")

        patterns = [self.target_date.strftime("%Y%m%d")]
        print(f"📅 検索パターン: {patterns}")
        print(f"🎯 使用するクラスフィルター: {class_filter}")

        links = []
        link_candidates = (
            soup.find_all("a", href=True, class_=class_filter) if class_filter else soup.find_all("a", href=True)
        )

        for link in link_candidates:
            link_text = link.get_text(strip=True)
            href = link.get("href", "")
            for pattern in patterns:
                if pattern in link_text or pattern in href:
                    full_url = urljoin(self.base_url, href)
                    links.append({"url": full_url, "text": link_text, "pattern_matched": pattern})
                    print(f"  ✅ 発見: {link_text} (パターン: {pattern})")
                    break

        if not links:
            print("⚠️ 官報リンクが見つかりません")
            for i, link in enumerate(link_candidates[:10]):
                text = link.get_text(strip=True)
                if text and len(text) > 3:
                    print(f"    {i + 1}. {text}")
        return links

    def fetch_kanpo_page(self, kanpo_url):
        """官報のページを取得し、PDFリンクを抽出します

        Args:
            kanpo_url (str): 官報のURL

        Returns:
            list: 官報ページから抽出したPDFリンクのリスト
        """

        print(f"📖 官報ページを処理中: {kanpo_url}")

        try:
            response = self.session.get(kanpo_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            pdf_links = []
            date_text = None

            date_element = soup.find("p", class_="date")
            if date_element:
                date_text = date_element.get_text(strip=True)
                print(f"📅 官報の日付: {date_text}")
            else:
                print("⚠️ p に date クラスがありません")

            for iframe in soup.find_all("iframe", src=True):
                src = iframe["src"]
                if src.lower().endswith(".pdf"):
                    pdf_url = urljoin(kanpo_url, src)
                    pdf_name = os.path.basename(urlparse(src).path)
                    pdf_links.append({"url": pdf_url, "name": date_text, "filename": pdf_name, "source": "iframe"})
                    print(f"  📄 PDF発見 (<iframe>): {pdf_name}")

            print(f"📊 PDF数: {len(pdf_links)}")
            return pdf_links
        except Exception as e:
            print(f"❌ 官報ページの取得に失敗: {e}")
            return []

    def download_pdf(self, pdf_info, folder_path):
        """官報のPDFダウンロードします

        Args:
            pdf_info (dict): pdfの情報（URL、名前、ファイル名など）
            folder_path (str): フォルダパス

        Returns:
            bool: ダウンロードが成功したかどうか
        """

        try:
            print(f"📥 ダウンロード開始: {pdf_info['name']}")
            response = self.session.get(pdf_info["url"], stream=True, timeout=30)
            response.raise_for_status()
            file_path = folder_path / re.sub(r"[^\w\-_\.]", "_", pdf_info["filename"])
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ✅ 完了: {file_path.name}")
            return True
        except Exception as e:
            print(f"  ❌ ダウンロード失敗: {e}")
            return False

    def create_readme(self, folder_path, pdf_list, date_str):
        """官報ページのダウンロード履歴をReadme.mdとして記録します

        Args:
            folder_path (str): フォルダーパス
            pdf_list (list): pdfの情報リスト
            date_str (str): 日付用 文字列（YYYY-MM-DD）
        """
        readme_path = folder_path / f"官報_{date_str}.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# 官報 {date_str}\n\n")
            f.write(f"取得日時: {datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("## ダウンロードファイル\n\n")
            for pdf in pdf_list:
                f.write(f"- [{pdf['name']}]({pdf['filename']})\n")
                f.write(f"  - URL: {pdf['url']}\n")
        print(f"📝 README作成完了: {readme_path}")

    def run(self):
        """メインのランナー関数

        Returns:
            bool: 指定した日付で、官報を見つけられたかどうか(検索から90日以内ならヒットするはず)
            list: PDFのリンクリスト
        """
        print("🚀 官報取得開始")
        all_pdfs = []
        soup = self.fetch_main_page()
        if not soup:
            return False, []

        kanpo_links = self.find_kanpo_link(soup, "pdfDlb")
        if not kanpo_links:
            return False, []

        date_str = self.get_target_date()
        folder_path = self.create_date_folder(date_str)

        for link_info in kanpo_links:
            print(f"\n📖 処理中: {link_info['text']}")
            pdf_links = self.fetch_kanpo_page(link_info["url"])
            for pdf_info in pdf_links:
                if self.download_pdf(pdf_info, folder_path):
                    all_pdfs.append(pdf_info)
                time.sleep(1)

        if all_pdfs:
            self.create_readme(folder_path, all_pdfs, date_str)
        else:
            return False, []

        return True, all_pdfs

    def test_run(self):
        """テスト用のランナー関数(ページをフェッチして、pdfのリンクだけを取得する)

        Returns:
            bool: 指定した日付で、官報を見つけられたかどうか(検索から90日以内ならヒットするはず)
            list: PDFのリンクリスト
        """
        print("🚀 官報リンク取得開始")
        all_pdfs = []
        soup = self.fetch_main_page()
        if not soup:
            return False, all_pdfs

        kanpo_links = self.find_kanpo_link(soup, "pdfDlb")
        if not kanpo_links:
            print("⚠️ 発行された官報のURL(クラス名:pdfDlb)が見つかりませんでした")
            return False, all_pdfs

        for link_info in kanpo_links:
            print(f"\n📖 処理中: {link_info['text']}")
            pdf_links = self.fetch_kanpo_page(link_info["url"])
            for pdf_info in pdf_links:
                all_pdfs.append(pdf_info)
                time.sleep(1)

        if not all_pdfs:
            print("⚠️ PDFリンクが見つかりませんでした")
            return False, all_pdfs

        return True, all_pdfs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="官報PDF自動取得ツール")
    parser.add_argument("--dlpdf", type=str2bool, nargs="?", const=True, default=False, help="PDFをダウンロードするか")
    parser.add_argument("--date", type=str, help="対象日付 (例: 2025-07-03)")
    args = parser.parse_args()

    kanpou_found = False
    pdf_infos = []

    try:
        if args.date:
            try:
                target_date = datetime.strptime(args.date, "%Y-%m-%d")
            except ValueError:
                print("❌ 日付の形式が不正です。例: YYYY-MM-DD")
                print(f"入力された日付: {args.date}")
                exit(1)
        else:
            target_date = datetime.now(ZoneInfo("Asia/Tokyo"))

        fetcher = KanpoFetcher(target_date=target_date)

        if args.dlpdf:
            print("🚀 本番モード: 官報PDFをダウンロードします")
            kanpou_found, pdf_infos = fetcher.run()
        else:
            print("🔍 確認モード: 官報リンクのみを取得します")
            kanpou_found, pdf_infos = fetcher.test_run()

        if kanpou_found:
            print(f"📄 kanpou_found: {kanpou_found}")
            print("🎉 官報取得成功")
        else:
            print("⚠️ 官報が見つかりませんでした")

        if len(pdf_infos) > 0:
            print(f"📄 PDFリンク数: {len(pdf_infos)}")
            for pdf in pdf_infos:
                print(f"PDF情報:{pdf}")

    except KeyboardInterrupt:
        print("👋 中断されました")
    except Exception as e:
        print(f"❌ 実行時エラー: {e}")

    # Make outputs
    if "GITHUB_OUTPUT" in os.environ:
        output_path = os.environ.get("GITHUB_OUTPUT")
        print("GITHUB_OUTPUT 環境変数が設定されています。出力を行います。")
        with open(output_path, "a") as fh:
            print(f"kanpou_found={kanpou_found}", file=fh)
            print(f"pdf_infos={pdf_infos}", file=fh)

        if output_path:
            print(f"GITHUB_OUTPUT のパス: {output_path}")
            try:
                with open(output_path, "r") as f:
                    content = f.read()
                print("GITHUB_OUTPUT ファイルの中身:")
                print(content)
            except Exception as e:
                print(f"ファイル読み込みエラー: {e}")
        else:
            print("GITHUB_OUTPUT 環境変数が設定されていません。")
    else:
        print("GITHUB_OUTPUT 環境変数が設定されていません。出力は行われません。")
