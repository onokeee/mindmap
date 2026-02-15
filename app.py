from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # 本番環境では変更してください
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# データベースファイル
DB_FILE = 'mindmap.db'

def init_db():
    """データベースの初期化"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # ユーザーテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # マインドマップテーブル（複数保存対応）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mindmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, name)
        )
    ''')
    
    # ダミーユーザーを作成（本番環境ではLDAP認証に置き換え）
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                      ('admin', 'admin123'))  # ダミーパスワード
    
    conn.commit()
    conn.close()

def login_required(f):
    """ログイン必須デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(username, password):
    """
    ユーザー認証（ダミー実装）
    本番環境ではLDAP認証APIに置き換えてください
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', 
                  (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {'id': user[0], 'username': user[1]}
    return None

# LDAP認証API用の関数（将来実装用）
def authenticate_ldap(username, password):
    """
    LDAP認証API（将来実装用）
    
    使用例:
    import requests
    response = requests.post('https://your-ldap-api.com/auth', 
                           json={'username': username, 'password': password})
    if response.status_code == 200:
        return response.json()
    return None
    """
    pass

@app.route('/')
def index():
    """メインページ（ログインチェック）"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session.get('username'))

@app.route('/login')
def login_page():
    """ログインページ"""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    """ログインAPI"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # ユーザー認証（本番ではauthenticate_ldapに置き換え）
    user = authenticate_user(username, password)
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True
        return jsonify({'status': 'success', 'username': user['username']})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """ログアウトAPI"""
    session.clear()
    return jsonify({'status': 'success'})

@app.route('/api/mindmaps/list', methods=['GET'])
@login_required
def list_mindmaps():
    """保存されたマインドマップ一覧を取得"""
    user_id = session['user_id']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, updated_at 
        FROM mindmaps 
        WHERE user_id = ? 
        ORDER BY updated_at DESC
    ''', (user_id,))
    
    maps = []
    for row in cursor.fetchall():
        # UTCからJST（UTC+9時間）に変換
        utc_time = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
        jst_time = utc_time + timedelta(hours=9)
        
        maps.append({
            'id': row[0],
            'name': row[1],
            'updated_at': jst_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    conn.close()
    return jsonify({'maps': maps})

@app.route('/api/mindmap/<int:map_id>', methods=['GET'])
@login_required
def get_mindmap_by_id(map_id):
    """指定IDのマインドマップを取得"""
    user_id = session['user_id']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT data, name FROM mindmaps WHERE id = ? AND user_id = ?', 
                  (map_id, user_id))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        data = json.loads(result[0])
        data['map_name'] = result[1]
        data['map_id'] = map_id
        return jsonify(data)
    else:
        return jsonify({'error': 'Map not found'}), 404

@app.route('/api/mindmap', methods=['POST'])
@login_required
def save_mindmap():
    """マインドマップを名前を付けて保存"""
    user_id = session['user_id']
    request_data = request.json
    
    map_name = request_data.get('name', '無題のマップ')
    map_data = request_data.get('data')
    map_id = request_data.get('id')  # 既存マップの更新用
    
    if not map_data:
        return jsonify({'error': 'Data is required'}), 400
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        if map_id:
            # 既存マップの更新
            cursor.execute('''
                UPDATE mindmaps 
                SET data = ?, name = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (json.dumps(map_data, ensure_ascii=False), map_name, map_id, user_id))
        else:
            # 新規保存
            cursor.execute('''
                INSERT INTO mindmaps (user_id, name, data) 
                VALUES (?, ?, ?)
            ''', (user_id, map_name, json.dumps(map_data, ensure_ascii=False)))
            map_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'id': map_id, 'name': map_name})
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'マップ名が既に存在します'}), 400

@app.route('/api/mindmap/<int:map_id>', methods=['DELETE'])
@login_required
def delete_mindmap(map_id):
    """マインドマップを削除"""
    user_id = session['user_id']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM mindmaps WHERE id = ? AND user_id = ?', (map_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if deleted:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Map not found'}), 404

@app.route('/api/check_session', methods=['GET'])
def check_session():
    """セッション確認API"""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True, 
            'username': session.get('username')
        })
    return jsonify({'logged_in': False})

#LAN用の実行コマンド
#if __name__ == '__main__':
#    init_db()
#    app.run(debug=True, host='0.0.0.0', port=5000)

#render用の実行コマンド。gunicornで実行するので、これだけでOKらしい。
init_db()