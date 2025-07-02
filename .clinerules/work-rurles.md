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
以下のhtmlは https://www.kanpo.go.jp/index.html の中にある、当日の一例です。
```html
<div id="todayProducts" class="todayBox">
			<dl>
				<dt>令和 7年7月2日<br><a href="./20250702/20250702.fullcontents.html">全体目次はこちら</a></dt>
				<dd>
					<ul>
						<li class="articleBox"><a href="./20250702/20250702h01498/20250702h014980000f.html" class="articleTop">本紙<br>(第1498号)</a>
							<a href="./20250702/20250702h01498/20250702h01498full00010032f.html" class="pdfDlb"><img src="images/icon-file-pdf.png" alt="PDF">1-32頁[6MB]</a>
						</li>
						<li class="articleBox"><a href="./20250702/20250702g00151/20250702g001510000f.html" class="articleTop">号外<br>(第151号)</a>
							<a href="./20250702/20250702g00151/20250702g00151full00010160f.html" class="pdfDlb"><img src="images/icon-file-pdf.png" alt="PDF">1-160頁[12MB]</a>
						</li>
						<li class="articleBox"><a href="./20250702/20250702c00121/20250702c001210000f.html" class="articleTop">政府調達<br>(第121号)</a>
							<a href="./20250702/20250702c00121/20250702c00121full00010032f.html" class="pdfDlb"><img src="images/icon-file-pdf.png" alt="PDF">1-32頁[1MB]</a>
						</li>
					</ul>
				</dd>
			</dl>
		</div>
```