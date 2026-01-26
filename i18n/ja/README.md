# HyoDo (孝道) - AIコード品質自動化

> **コード品質自動チェック + 50-70%コスト削減**

<p align="center">
  <a href="../../README.md">English</a> •
  <a href="../ko/README.md">한국어</a> •
  <a href="../zh/README.md">中文</a>
</p>

## 30秒クイックスタート

```bash
/start              # ヘルプ
/check              # コード品質チェック
/score              # スコア確認 (90+ = 安全)
/safe               # 安全検査
/cost "タスク説明"  # コスト予測
```

**以上です！** これだけ知っていれば十分です。

---

## スコアリングシステム

| スコア | ステータス | アクション |
|--------|----------|----------|
| 90+ | ✅ 安全 | すぐに進める |
| 70-89 | ⚠️ 注意 | 確認後に進める |
| 70未満 | ❌ 危険 | 修正が必要 |

---

## 五柱の哲学 (眞善美孝永)

HyoDoは**Trinity Score**でコードの完成度を測定します。

| 柱 | 意味 | 重み | 担当 |
| :--- | :--- | :---: | :--- |
| **眞** (真実) | 技術的正確性 | 35% | 丁若鎔 / 蔣英實 |
| **善** (善良) | 倫理と安定性 | 35% | 柳成龍 / 李舜臣 |
| **美** (美しさ) | ナラティブとUX | 20% | 許浚 / 申師任堂 |
| **孝** (静寂) | 平和の守護 | 8% | 丞相 |
| **永** (永遠) | 持続可能性 | 2% | 丞相 / 金庾信 |

---

## インストール

```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
```

またはワンクリックインストール：
```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install.sh | bash
```

---

## ドキュメント

| ドキュメント | 説明 |
|------------|------|
| [QUICK_START.md](QUICK_START.md) | クイックスタート |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 貢献ガイド |
| [ROADMAP.md](ROADMAP.md) | ロードマップ |

---

## ライセンス

MIT - [LICENSE](../../LICENSE)

---

*初めての方は `/start` から始めましょう！*
