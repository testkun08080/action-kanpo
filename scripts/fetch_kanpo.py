#!/usr/bin/env python3
"""
官報自動取得スクリプト
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path


class KanpoFetcher:
    def __init__(self):
        self.base_url = "https://www.kanpo.go.jp"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    def get_today_date(self):
        """今日の日付を取得"""
        return datetime.now().strftime("%Y-%m-%d")

    def create_date_folder(self, date_str):
        """日付フォルダを作成"""
        folder_path = Path(f"kanpo/{date_str}")
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def fetch_main_page(self):
        """メインページを取得"""
        try:
            response = self.session.get(self.base_url + "/index.html")
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"メインページの取得に失敗: {e}")
            return None

    def find_today_kanpo_link(self, soup):
        """今日の官報のリンクを探す"""
        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")

        # 複数のパターンでリンクを探す
        patterns = [today_str, today.strftime("%Y-%m-%d"), today.strftime("%m月%d日"), today.strftime("%m/%d")]

        links = []
        for link in soup.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            for pattern in patterns:
                if pattern in link_text or pattern in link.get("href", ""):
                    links.append({"url": urljoin(self.base_url, link["href"]), "text": link_text})

        return links

    def fetch_kanpo_page(self, kanpo_url):
        """官報ページを取得してPDFリンクを抽出"""
        try:
            response = self.session.get(kanpo_url)
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

            return pdf_links
        except Exception as e:
            print(f"官報ページの取得に失敗 {kanpo_url}: {e}")
            return []

    def download_pdf(self, pdf_info, folder_path):
        """PDFファイルをダウンロード"""
        try:
            response = self.session.get(pdf_info["url"], stream=True)
            response.raise_for_status()

            # ファイル名を安全にする
            safe_filename = re.sub(r"[^\w\-_\.]", "_", pdf_info["filename"])
            if not safe_filename.endswith(".pdf"):
                safe_filename += ".pdf"

            file_path = folder_path / safe_filename

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"ダウンロード完了: {safe_filename}")
            return True

        except Exception as e:
            print(f"PDFダウンロードに失敗 {pdf_info['url']}: {e}")
            return False

    def create_readme(self, folder_path, pdf_list, date_str):
        """READMEファイルを作成"""
        readme_path = folder_path / "README.md"

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# 官報 {date_str}\n\n")
            f.write(f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## ダウンロードファイル\n\n")

            for pdf_info in pdf_list:
                f.write(f"- [{pdf_info['name']}]({pdf_info['filename']})\n")

    def run(self):
        """メイン処理"""
        print("官報自動取得を開始...")

        # メインページを取得
        soup = self.fetch_main_page()
        if not soup:
            print("メインページの取得に失敗しました")
            return False

        # 今日の官報リンクを探す
        today_links = self.find_today_kanpo_link(soup)
        if not today_links:
            print("今日の官報が見つかりませんでした")
            return False

        print(f"今日の官報リンクを {len(today_links)} 個発見")

        # 日付フォルダを作成
        today_str = self.get_today_date()
        folder_path = self.create_date_folder(today_str)

        all_pdfs = []

        # 各官報ページからPDFを取得
        for link_info in today_links:
            print(f"官報ページを処理中: {link_info['text']}")
            pdf_links = self.fetch_kanpo_page(link_info["url"])

            for pdf_info in pdf_links:
                if self.download_pdf(pdf_info, folder_path):
                    all_pdfs.append(pdf_info)
                time.sleep(1)  # サーバー負荷軽減

        if all_pdfs:
            self.create_readme(folder_path, all_pdfs, today_str)
            print(f"成功: {len(all_pdfs)} 個のPDFファイルを取得しました")
            return True
        else:
            print("PDFファイルが見つかりませんでした")
            return False


def main():
    fetcher = KanpoFetcher()
    success = fetcher.run()

    if success:
        print("官報の取得が完了しました")
    else:
        print("官報の取得に失敗しました")
        exit(1)


if __name__ == "__main__":
    main()
