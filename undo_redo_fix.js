// ===================================
// Undo/Redo機能の修正版
// index.htmlの該当部分を以下のコードに置き換えてください
// ===================================

// 状態を保存する関数（修正版）
function saveState() {
    // 現在の状態をスナップショットとして保存
    const state = {
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
    
    // 現在の位置以降の履歴を削除
    history = history.slice(0, historyIndex + 1);
    
    // 新しい状態を追加
    history.push(state);
    
    // 最大履歴数を超えたら古いものを削除
    if (history.length > MAX_HISTORY) {
        history.shift();
    } else {
        historyIndex++;
    }
    
    // 未保存フラグを更新
    updateSavedStatus();
    updateUndoRedoButtons();
}

// 状態を復元する関数（修正版）
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
    
    // 未保存フラグを更新
    updateSavedStatus();
}

// 保存状態をチェックする関数（新規追加）
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

// Undo関数（変更なし - 確認用）
function undo() {
    if (historyIndex <= 0) return;
    
    historyIndex--;
    restoreState(history[historyIndex]);
    updateUndoRedoButtons();
}

// Redo関数（変更なし - 確認用）
function redo() {
    if (historyIndex >= history.length - 1) return;
    
    historyIndex++;
    restoreState(history[historyIndex]);
    updateUndoRedoButtons();
}

// Undo/Redoボタンの状態を更新する関数（変更なし）
function updateUndoRedoButtons() {
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');
    
    undoBtn.disabled = historyIndex <= 0;
    redoBtn.disabled = historyIndex >= history.length - 1;
}

// ===================================
// 使用例・テストケース
// ===================================

/*
テスト手順:

1. 新規マップを作成
   → 「無題のマップ *」と表示される（未保存）

2. ノードを追加・編集
   → 「無題のマップ *」のまま（未保存）

3. 保存（Ctrl+S または 💾ボタン）
   → 「無題のマップ」と表示される（保存済み、*が消える）

4. さらにノードを編集
   → 「無題のマップ *」と表示される（未保存）

5. Ctrl+Z（元に戻す）を何度か実行して、保存時点まで戻る
   → 「無題のマップ」と表示される（保存済み、*が消える）

6. Ctrl+Y（やり直す）で進める
   → 「無題のマップ *」と表示される（未保存）

7. 再度Ctrl+Zで保存時点まで戻る
   → 「無題のマップ」と表示される（保存済み）

期待される動作:
- Undo/Redoで保存した状態に戻ると、*（未保存マーク）が消える
- 保存後の編集では*が表示される
- 保存していない新規マップでは*が表示される
*/
