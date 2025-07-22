import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pyperclip
import json
import os
from spotipy.exceptions import SpotifyException

CONFIG_FILE = "spotify_config.json"


def save_credentials(client_id, client_secret, redirect_uri):
    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)

def load_credentials():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def prompt_for_credentials():
    print("Spotify認証情報を入力してください。")
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    redirect_uri = input("Redirect URI（例: http://localhost:8888/callback）: ").strip()
    return client_id, client_secret, redirect_uri


def authenticate_spotify():
    while True:
        creds = load_credentials()
        if creds is None:
            creds = prompt_for_credentials()
            save_credentials(*creds)

        try:
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=creds['client_id'],
                client_secret=creds['client_secret'],
                redirect_uri=creds['redirect_uri'],
                scope="playlist-modify-public user-library-read"
            ))
            sp.me()
            return sp
        except (SpotifyException, KeyError) as e:
            print("\n認証情報が無効です。再入力してください。\n")
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)

sp = authenticate_spotify()

def get_tracks_by_genre(genre, total_limit=1000):
    all_tracks = []
    offset = 0
    while len(all_tracks) < total_limit:
        remaining = total_limit - len(all_tracks)
        batch_limit = min(50, remaining)
        results = sp.search(q=f'genre:"{genre}"', type='track', limit=batch_limit, offset=offset)
        items = results['tracks']['items']
        if not items:
            break
        all_tracks.extend(items)
        offset += batch_limit
    return all_tracks

def get_tracks_by_artist(artist_name, limit=1000):
    results = sp.search(q=f'artist:"{artist_name}"', type='artist', limit=1)
    artists = results['artists']['items']
    if not artists:
        print("アーティストが見つかりませんでした。")
        return []
    artist_id = artists[0]['id']

    top_tracks_data = sp.artist_top_tracks(artist_id, country='JP')
    tracks = top_tracks_data['tracks']

    return tracks[:limit]

def select_random_tracks(tracks, count=1000):
    return random.sample(tracks, min(count, len(tracks)))

def create_playlist_with_tracks(user_id, name, track_uris, track_objects):
    playlist = sp.user_playlist_create(user=user_id, name=name)
    print(f"プレイリスト作成中... {name}")

    seen_titles = set()
    unique_tracks = []
    for uri, track in zip(track_uris, track_objects):
        title = track['name'].lower().strip()
        artists = ", ".join([a['name'].lower().strip() for a in track['artists']])
        unique_key = f"{title} - {artists}"
        if unique_key not in seen_titles:
            seen_titles.add(unique_key)
            unique_tracks.append(uri)

    for i in range(0, len(unique_tracks), 100):
        batch = unique_tracks[i:i + 100]
        sp.playlist_add_items(playlist_id=playlist['id'], items=batch)

    return playlist['external_urls']['spotify']

def get_tracks_by_artist_full_filtered(artist_name, limit=1000):
    results = sp.search(q=f'artist:"{artist_name}"', type='artist', limit=1)
    artists = results['artists']['items']
    if not artists:
        print("アーティストが見つかりませんでした。")
        return []

    artist_id = artists[0]['id']
    tracks = []
    albums = []

    results = sp.artist_albums(artist_id, album_type='album,single', country='JP', limit=50)
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])

    seen_album_ids = set()
    for album in albums:
        if album['id'] in seen_album_ids:
            continue
        seen_album_ids.add(album['id'])

        album_tracks = sp.album_tracks(album['id'])
        tracks.extend(album_tracks['items'])
        if len(tracks) >= limit * 3:
            break

    filtered_tracks = filter_tracks_by_artist_name(tracks, artist_name)

    return filtered_tracks[:limit]

def filter_tracks_by_artist_name(tracks, artist_name):
    filtered = []
    lower_name = artist_name.lower()
    for track in tracks:
        for artist in track['artists']:
            if lower_name in artist['name'].lower():
                filtered.append(track)
                break
    return filtered

def get_multiple_artists_tracks():
    artist_names = []

    while True:
        artist = input("歌手名を入力してください: ").strip()
        if artist:
            artist_names.append(artist)
        else:
            print("空白は無効です。")

        more = input("他にアーティストを追加しますか？(y/n): ").strip().lower()
        if more == 'n':
            break
        elif more != 'y':
            print("y か n を入力してください。\n")

    print("-----------------")
    for a in artist_names:
        print(f"- {a}")

    all_tracks = []
    for artist in artist_names:
        print(f"{artist} の曲を検索中...")
        tracks = get_tracks_by_artist_full_filtered(artist)
        all_tracks.extend(tracks)
    random.shuffle(all_tracks)
    print(f"検索完了")
    return all_tracks, artist_names


def get_tracks_by_names_interactive():
    approved_tracks = []
    print("曲名を1つずつ入力してください（終了するには「x」と入力）:")

    while True:
        name = input("曲名: ")
        if name.lower() == 'x':
            break
        if not name.strip():
            continue

        res = sp.search(q=name.strip(), type='track', limit=20)
        items = res['tracks']['items']
        if not items:
            print(f"見つかりませんでした: {name}")
            continue

        print("\n検索結果:")
        for i, track in enumerate(items, 1):
            title = track['name']
            artists = ", ".join([a['name'] for a in track['artists']])
            album = track['album']['name']
            print(f"{i}. {title} - {artists} [{album}]")

        while True:
            decision = input("追加する曲の番号を入力してください（nでスキップ）: ").lower()
            if decision == 'n':
                print("スキップしました。")
                break
            elif decision.isdigit():
                idx = int(decision)
                if 1 <= idx <= len(items):
                    approved_tracks.append(items[idx - 1])
                    print("追加しました。")
                    break
                else:
                    print("有効な番号を入力してください。")
            else:
                print("数字または n を入力してください。")

    return approved_tracks





banner="""

      ______                   _    _     ___                _________               __   
    .' ____ \                 / |_ (_)  .' ..]              |  _   _  |             [  |  
    | (___ \_|_ .--.    .--. `| |-'__  _| |_  _   __  ______|_/ | | \_|.--.    .--.  | |  
     _.____`.[ '/'`\ \/ .'`\ \| | [  |'-| |-'[ \ [  ]|______|   | |  / .'`\ \/ .'`\ \| |  
    | \____) || \__/ || \__. || |, | |  | |   \ '/ /           _| |_ | \__. || \__. || |  
     \______.'| ;.__/  '.__.' \__/[___][___][\_:  /           |_____| '.__.'  '.__.'[___] 
             [__|                            \__.'                                        
           
      Dev t0x1c       
             
"""


def main():
    genres = ["j-pop", "rock", "hip-hop", "edm", "jazz"]
    print(banner)
    print("ジャンルを選んでください:")
    print("0: 歌手名で検索")   
    for i, g in enumerate(genres, 1):
        print(f"{i}: {g}")
    print("6: 認証情報登録")
    print("7: 曲名で検索") 

    while True:
        try:
            choice = int(input("数字を入力してください（例: 1）: "))
            if choice == 0:
                tracks, artist_names = get_multiple_artists_tracks()
                artist_name = " & ".join(artist_names)
                break
            elif choice == 6:
                prompt_for_credentials()
                return
            elif 1 <= choice <= len(genres):
                genre = genres[choice - 1]
                print(f"{genre} 検索中...")
                tracks = get_tracks_by_genre(genre)
                break
            elif choice == 7:
                tracks = get_tracks_by_names_interactive()
                if not tracks:
                    print("曲が追加されていません。")
                    return
                artist_name = "Custom Tracks"
                break
            else:
                print("正しい数字を入力してください。")
        except ValueError:
            print("数字を入力してください。")

    if not tracks:
        print("曲が見つかりませんでした。")
        input("何かのキーを押して終了")
        return

    print(f"{len(tracks)} 曲見つかりました。")
    select = input("何曲取得しますか？ : ")
    try:
        count = int(select)
        if count <= 0:
            print("1以上の数字を入力してください。")
            return
    except ValueError:
        print("数字を入力してください。")
        return

    selected = select_random_tracks(tracks, count)

    remove_keywords = []
    choice_remove = input("指定した言葉が入る曲を削除しますか？(y/n): ").strip().lower()
    if choice_remove == 'y':
        print("除外したいキーワードを入力してください（終了するには「x」）:")
        while True:
            word = input("キーワード: ").strip()
            if word.lower() == 'x':
                break
            if word:
                remove_keywords.append(word.lower())

        filtered = []
        for track in selected:
            title = track['name'].lower()
            if not any(keyword in title for keyword in remove_keywords):
                filtered.append(track)
        removed_count = len(selected) - len(filtered)
        selected = filtered
        print(f"{removed_count} 曲がキーワードによって除外されました。")

    uris = [track['uri'] for track in selected]

    user_id = sp.me()['id']
    playlist_name = f"{artist_name if choice == 0 or choice == 7 else genre} by t0XÌç-Tool"
    playlist_url = create_playlist_with_tracks(user_id, playlist_name, uris, selected)

    print("プレイリスト作成完了！")
    pyperclip.copy(playlist_url)
    print("\nクリップボードにコピー済み。")
    view = input("追加した曲を見ますか？（y / n）: ").lower()
    if view == 'y':
        print("\n追加された曲一覧:\n")
        for i, track in enumerate(selected, 1):
            title = track['name']
            artists = ", ".join([a['name'] for a in track['artists']])
            print(f"{i}. {title} - {artists}")
    input("何かのキーを押して終了。")


if __name__ == "__main__":
    main()