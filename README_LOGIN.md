# Flex Diagram - ログイン機能とSQLite3対応版

## 📝 変更内容

### 1. ログイン認証機能
- ユーザー名とパスワードでログイン
- セッション管理（24時間有効）
- ログアウト機能

### 2. データベース（SQLite3）
- JSONファイルからSQLite3に変更
- ユーザーごとにデータを分離して保存
- テーブル構成:
  - `users`: ユーザー情報
  - `mindmaps`: マインドマップデータ（ユーザーごと）

### 3. 将来のLDAP対応
- `authenticate_ldap()` 関数を用意済み
- 本番環境では簡単に切り替え可能

## 🚀 セットアップ

### 1. 古いapp.pyをバックアップ
```bash
mv app.py app_old.py
```

### 2. 新しいapp.pyに置き換え
```bash
mv app_new.py app.py
```

### 3. アプリケーションを起動
```bash
python app.py
```

### 4. ブラウザでアクセス
```
http://localhost:5000
```

## 🔐 デモアカウント

**ユーザー名**: `admin`  
**パスワード**: `admin123`

## 📂 ファイル構成

```
mindmap/
├── app.py                    # 新しいバックエンド（ログイン＋SQLite3）
├── mindmap.db               # SQLite3データベース（自動作成）
├── templates/
│   ├── index.html           # メインページ（更新済み）
│   └── login.html           # ログインページ（新規）
└── README_LOGIN.md          # このファイル
```

## 🔧 LDAP認証への切り替え方法

### app.py の修正箇所

```python
# login() 関数内（行97付近）

# 現在（ダミー認証）
user = authenticate_user(username, password)

# LDAP認証に変更
user = authenticate_ldap(username, password)
```

### LDAP認証関数の実装例

```python
def authenticate_ldap(username, password):
    """LDAP認証API"""
    import requests
    
    try:
        response = requests.post(
            'https://your-ldap-api.com/auth',
            json={'username': username, 'password': password},
            timeout=5
        )
        
        if response.status_code == 200:
            user_data = response.json()
            
            # ユーザーがDBに存在しなければ作成
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)',
                    (username, 'ldap')  # パスワードは使わない
                )
                conn.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user[0]
            
            conn.close()
            return {'id': user_id, 'username': username}
        
        return None
        
    except Exception as e:
        print(f'LDAP authentication error: {e}')
        return None
```

## 📊 データベーススキーマ

### users テーブル
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### mindmaps テーブル
```sql
CREATE TABLE mindmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

## ✨ 新機能

1. **ユーザー表示**: ヘッダーにログインユーザー名を表示
2. **ログアウトボタン**: 右上にログアウトボタンを追加
3. **自動ログインチェック**: セッション切れ時は自動的にログインページへ
4. **ユーザー別データ**: 各ユーザーが独自のマインドマップを保存

## 🔒 セキュリティ注意事項

### 本番環境での対応が必要な項目

1. **シークレットキーの変更**
   ```python
   app.secret_key = 'your-secret-key-change-this-in-production'
   # → 強力なランダム文字列に変更
   ```

2. **HTTPS通信**
   - 本番環境では必ずHTTPSを使用

3. **パスワードのハッシュ化**
   - LDAP認証を使う場合は不要
   - ローカル認証を使う場合は`bcrypt`などでハッシュ化

4. **セッションタイムアウト**
   - 現在24時間（必要に応じて調整）

5. **SQLインジェクション対策**
   - プレースホルダー使用済み（対策済み）

## 📝 トラブルシューティング

### データベースが作成されない
```bash
# 手動で初期化
python -c "from app import init_db; init_db()"
```

### ログインできない
1. データベースファイルを確認: `mindmap.db`が存在するか
2. デモアカウントで試す: `admin` / `admin123`
3. ログを確認: コンソールのエラーメッセージを確認

### セッションが切れる
- ブラウザのCookieを確認
- `app.secret_key`が変更されていないか確認

## 🎉 完成！

これでログイン機能付き、SQLite3対応のFlex Diagramが完成しました！

本番環境へのデプロイ時は、LDAP認証への切り替えを忘れずに行ってください。
