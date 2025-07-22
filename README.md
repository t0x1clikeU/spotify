# Spotify Play-List Tool

---

## 🧾 必要環境

- Windows OS
- Python 3.x
- 下記 Python ライブラリ


## 🎧 主な機能

- 🎵 **ジャンルごとの曲検索（J-Pop、Rock、Hip-Hopなど）**
- 👤 **アーティスト名からの曲検索**
- 🔎 **曲名からの検索（手動で選曲）**
- ✂️ **特定キーワードを含む曲の除外**
- 📋 **自動でプレイリストを作成＆URLをクリップボードにコピー**

## 📂 ファイル構成
```
├─ main.py                # メインスクリプト
├─ spotify_config.json    # Spotify認証情報（初回入力後に自動生成）
```

```bash
pip install spotipy pyperclip
```

## 🔧 Spotify 開発者認証情報の取得

1. https://developer.spotify.com/dashboard にログイン
2. Create app を押す
3. App name / App description / Redirect URIs / を入力する


## 🛠️ 使い方
1. `main.py` を実行します。
2. spotifyの開発者認証情報を登録
3. 表示されるメニューから検索方法を選択します：

    ```
    ジャンルを選んでください:
    0: 歌手名で検索
    1: j-pop
    2: rock
    3: hip-hop
    4: edm
    5: jazz
    6: 認証情報登録
    7: 曲名で検索
    ```

4. 検索が完了すると、何曲プレイリストに入れるかを聞かれます。  
   任意の曲数を入力します（例：30）。

5. 「指定した言葉が入る曲を削除しますか？」という質問に「y」を入力すると、  
   キーワードによる除外フィルターを設定できます（例：Remix、Live など）。

6. プレイリストが自動で作成され、URLがクリップボードにコピーされます。

7. 追加した曲一覧を見るか確認されます。「y」で表示、「n」でスキップできます。


