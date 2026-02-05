# Undo/Redo機能の未保存状態管理 - 修正ガイド

## 📋 問題の詳細

### 現在の動作
- Ctrl+Z（元に戻す）やCtrl+Y（やり直す）を実行すると、保存した状態に戻っても **未保存マーク(*)が表示されたまま** になる

### 期待される動作
- Undo/Redoで保存時の状態に戻ったら、未保存マーク(*)が **消える** べき

## 🔍 原因分析

### 問題箇所1: `restoreState()` 関数
**場所**: index.html の約2050-2070行目

```javascript
// 【現在のコード】問題あり
function restoreState(state) {
    // ... 状態復元処理 ...
    
    // 保存状態をチェック
    if (lastSavedState) {
        const currentStateStr = JSON.stringify(state);
        const savedStateStr = JSON.stringify(lastSavedState);
        isSaved = (currentStateStr === savedStateStr);
        updateMapNameDisplay();
    }
}
```

**問題点**: 
- `state` パラメータと `lastSavedState` を比較しているが、`state` は履歴から取得したオブジェクト
- **現在のノードの状態を正しく反映していない可能性がある**

### 問題箇所2: 保存状態チェックロジックの分散
`saveState()` 関数内でも同じ判定ロジックが書かれており、コードが重複している

## ✅ 修正内容

### 修正1: `updateSavedStatus()` 関数を新規追加

```javascript
// 保存状態をチェックする専用関数
function updateSavedStatus() {
    if (!lastSavedState) {
        // 初期状態（まだ一度も保存していない）
        isSaved = false;
        updateMapNameDisplay();
        return;
    }
    
    // 現在の状態を取得
    const currentState = {
        nodes: JSON.parse(JSON.stringify(nodes.map(n => ({
            id: n.id,
            text: n.text,
            x: n.x,
            y: n.y,
            parent: n.parent,
            children: [...n.children],
            color: n.color
        })))),
        customLinks: JSON.parse(JSON.stringify(customLinks)),
        reversedConnections: [...reversedConnections]
    };
    
    // 最後に保存した状態と比較
    const currentStateStr = JSON.stringify(currentState);
    const savedStateStr = JSON.stringify(lastSavedState);
    isSaved = (currentStateStr === savedStateStr);
    
    updateMapNameDisplay();
}
```

**改善ポイント**:
- グローバル変数 `nodes`, `customLinks`, `reversedConnections` から **直接** 現在の状態を取得
- 一箇所で保存状態の判定を行うことで、ロジックの一貫性を保証

### 修正2: `saveState()` 関数の簡略化

```javascript
function saveState() {
    // ... 履歴保存処理 ...
    
    // 未保存フラグを更新（共通関数を呼び出す）
    updateSavedStatus();  // ← 新しい関数を使用
    updateUndoRedoButtons();
}
```

### 修正3: `restoreState()` 関数の簡略化

```javascript
function restoreState(state) {
    // ノードを復元
    nodes = state.nodes.map(n => {
        const node = new Node(n.id, n.text, n.x, n.y, n.parent);
        node.children = [...n.children];
        node.color = n.color || 'white';
        return node;
    });
    
    customLinks = JSON.parse(JSON.stringify(state.customLinks));
    reversedConnections = [...state.reversedConnections];
    
    // 選択をクリア
    clearMultiSelection();
    selectedNode = null;
    
    renderMap();
    
    // 未保存フラグを更新（共通関数を呼び出す）
    updateSavedStatus();  // ← 新しい関数を使用
}
```

## 🚀 適用手順

### 方法1: 手動で修正（推奨）

1. `index.html` を開く
2. `restoreState()` 関数を探す（約2050行目付近）
3. 関数内の保存状態チェック部分を削除
4. `updateSavedStatus()` 関数を追加（`restoreState()` の前後どこでもOK）
5. `saveState()` 関数内の重複コードを `updateSavedStatus()` 呼び出しに置き換え

### 方法2: `undo_redo_fix.js` のコードをコピペ

1. `undo_redo_fix.js` を開く
2. 該当する関数のコードをコピー
3. `index.html` の対応する関数を置き換え

### 方法3: バックアップから復元（最も簡単）

```bash
# 現在のindex.htmlをバックアップ
copy templates\index.html templates\index_backup.html

# 修正版をindex.htmlに上書き
# （修正版のindex.htmlを用意する必要あり）
```

## 🧪 動作確認手順

### テストケース1: 新規マップ作成→保存→編集→Undo

1. アプリを起動
2. ノードを追加・編集
   - **期待**: タイトルに `無題のマップ *` と表示（未保存）
3. Ctrl+S で保存、マップ名を入力
   - **期待**: タイトルに `マップ名` と表示（*が消える）
4. さらにノードを追加
   - **期待**: タイトルに `マップ名 *` と表示（未保存）
5. Ctrl+Z を数回押して保存時点まで戻る
   - **期待**: タイトルに `マップ名` と表示（*が消える）✅

### テストケース2: Redo後に再度Undoで保存状態に戻る

1. テストケース1の続きから
2. Ctrl+Y を数回押す（やり直す）
   - **期待**: 未保存状態になり `マップ名 *` と表示
3. 再度 Ctrl+Z で保存時点まで戻る
   - **期待**: `マップ名` と表示（*が消える）✅

### テストケース3: 複雑な編集→保存→Undo/Redo

1. ノードを10個追加し、色も変更
2. 保存（*が消える）
3. さらにノードを5個追加
4. Ctrl+Z を15回実行（保存時点より前まで戻る）
   - **期待**: `マップ名 *` と表示（未保存）
5. Ctrl+Y で保存時点まで進める
   - **期待**: `マップ名` と表示（*が消える）✅

## 📊 修正前後の比較

| 操作 | 修正前 | 修正後 |
|------|--------|--------|
| 新規作成後にノード追加 | `* 無題のマップ` | `* 無題のマップ` ✅ |
| 保存直後 | `マップ名` | `マップ名` ✅ |
| 保存後に編集 | `* マップ名` | `* マップ名` ✅ |
| Undoで保存状態に戻る | `* マップ名` ❌ | `マップ名` ✅ |
| Redoで未保存状態に進む | `マップ名` ❌ | `* マップ名` ✅ |

## 💡 補足情報

### なぜこの修正が必要なのか？

**Undo/Redo機能では**:
- 履歴の各エントリは「その時点での完全な状態のスナップショット」
- Undoすると、そのスナップショットがグローバル変数に復元される
- **復元後のグローバル変数の状態** と **保存状態** を比較する必要がある

**修正前の問題**:
- `restoreState(state)` で受け取った `state` パラメータを直接比較していた
- しかし、この `state` は復元**前**の状態を含む可能性があり、正確ではない

**修正後の改善**:
- グローバル変数 `nodes`, `customLinks`, `reversedConnections` から**直接**現在の状態を取得
- これにより、確実に**復元後の状態**を比較できる

### JSON比較の注意点

```javascript
const currentStateStr = JSON.stringify(currentState);
const savedStateStr = JSON.stringify(lastSavedState);
isSaved = (currentStateStr === savedStateStr);
```

この比較方法は、オブジェクトの**完全一致**を確認します。
- 小数点以下の微妙な違い（例: `100.0` vs `100`）
- プロパティの順序の違い
などがあると、一致しない可能性があります。

現在の実装では問題ありませんが、将来的にはより厳密な比較ロジックを検討する価値があります。

## 🎯 まとめ

### 修正のポイント
1. `updateSavedStatus()` 関数を新規追加して、保存状態チェックを一元化
2. `restoreState()` と `saveState()` から重複コードを削除
3. 常にグローバル変数の**現在の状態**を比較するようにする

### 期待される効果
- ✅ Undo/Redoで保存状態に戻ると、*（未保存マーク）が正しく消える
- ✅ コードの重複が減り、メンテナンス性が向上
- ✅ 保存状態の判定ロジックが一箇所に集約され、バグが減る

---

**作成日**: 2026-02-05  
**対象ファイル**: `templates/index.html`  
**修正内容**: Undo/Redo時の未保存状態管理の改善
