const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, ShadingType, LevelFormat } = require("docx");
const FONT = "游ゴシック";
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 21, ...o });
const p = (t, o = {}) => new Paragraph({ children: [run(t, o)], spacing: { after: 110 } });
const h1 = (t) => new Paragraph({ children: [run(t, { bold: true, size: 30 })], spacing: { before: 280, after: 140 } });
const h2 = (t) => new Paragraph({ children: [run(t, { bold: true, size: 25 })], spacing: { before: 200, after: 100 } });
const mono = (t) => new Paragraph({ children: [new TextRun({ text: t, font: "Consolas", size: 19 })], spacing: { after: 60 }, shading: { type: ShadingType.CLEAR, fill: "F3F0F7", color: "auto" } });
const table = (headers, rows, widths) => new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: "3B2A6B", color: "auto" }, margins: { top: 70, bottom: 70, left: 110, right: 110 }, children: [new Paragraph({ children: [run(h, { bold: true, color: "FFFFFF", size: 19 })] })] })) }), ...rows.map((r) => new TableRow({ children: r.map((c, i) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, margins: { top: 70, bottom: 70, left: 110, right: 110 }, children: (Array.isArray(c) ? c : [c]).map((l) => new Paragraph({ children: [run(l, { size: 19 })], spacing: { after: 30 } })) })) }))] });
const mk = (ref) => ({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] });
const refs = ["a", "b", "c", "d", "e", "f", "g"];
const step = (ref, t) => new Paragraph({ children: [run(t)], numbering: { reference: ref, level: 0 }, spacing: { after: 90 } });

const doc = new Document({
  numbering: { config: refs.map(mk) },
  styles: { default: { document: { run: { font: FONT, size: 21 } } } },
  sections: [{ properties: { page: { margin: { top: 1100, bottom: 1100, left: 1200, right: 1200 } } }, children: [
    new Paragraph({ children: [run("LUNA28 Instagram 自動投稿　設定手順書", { bold: true, size: 34 })], spacing: { after: 60 } }),
    p("作成日：2026年11月3日　　対象：@luna28.japan　　所要時間：約30分（1回だけ）", { size: 19, color: "555555" }),

    h1("1　何が自動になるか"),
    table(["いつ", "何を", "誰が"], [
      ["毎日 7:00", "ストーリーズ動画（15秒・ランキング→ひとこと→プロフィールへ）", "自動"],
      ["水 20:00", "リール（質問型・16秒）", "自動（原稿は月1回）"],
      ["日 20:00", "カルーセル（27のルナ図鑑・6枚）", "自動（原稿は月1回）"],
      ["月1回＋随時", "予定表に翌月の行を入れ、準備できた投稿のプレビューを見て OK を入れる", "松島"],
      ["随時", "特別な投稿・イベント", "松島（アプリから手動）"],
    ], [1600, 5400, 2000]),
    p("画像・動画・音源はすべてプログラムで描画・合成（AI画像生成なし、ファイルにメタデータなし）。Instagram の「AI情報」ラベルは付きません。", { size: 19 }),

    h1("2　予定表スプレッドシート（作成済み）"),
    p("「LUNA28_Instagram自動投稿」https://docs.google.com/spreadsheets/d/1dUBDkSp0mNqM6OPgqOoMuQlJzlVEJRB1JsMqGfArQ48/edit"),
    p("12月分は火曜12:00の図鑑カルーセル5本・金曜20:00のリール4本を入力済み（1のルナ以外は原稿待ちで「停止」）。", { size: 19 }),
    table(["タブ", "役割"], [
      ["予定表", "1行＝1投稿。日付・時刻・種類（ストーリーズ／リール／カルーセル）・1位〜3位・ひとこと・原稿キー。状態列が空の行だけ投稿される。「停止」で飛ばす"],
      ["承認(OK)列", "準備ができた行は「確認待ち」になりプレビュー列にURLが入る。中身を見て OK を入れた行だけ投稿される。OK が無いまま予定を過ぎると「見送り」になり通知が届く"],
      ["設定", "Instagramのトークンとユーザーid（手順3で入れる）"],
    ], [1600, 7400]),

    h1("3　Instagram API の準備（Meta for Developers）"),
    step("a", "https://developers.facebook.com/ に Facebook アカウントでログイン →「マイアプリ」→「アプリを作成」"),
    step("a", "アプリの種類は「ビジネス」。用途を聞かれたら Instagram 関連を選ぶ。アプリ名「LUNA28 Auto」、連絡先メールを入力して作成"),
    step("a", "左メニュー「Instagram」→「Instagramビジネスログインを使用したAPI設定」を開く"),
    step("a", "「アクセストークンを生成」で @luna28.japan を追加 → Instagram にログイン →「トークンを生成」→ 表示されたトークンをコピー（60日有効。プログラムが7日ごとに自動延長）"),
    step("a", "同じ画面の Instagram ユーザーID（数字）を控える"),
    step("a", "予定表の「設定」タブに access_token と ig_user_id を貼る"),
    p("自分のアカウントに投稿するだけなので、アプリレビュー申請は不要（開発モードのままで動きます）。", { size: 19 }),

    h1("4　Google の準備（プログラムに予定表を読ませる）"),
    step("b", "https://console.cloud.google.com/ → 新しいプロジェクト（名前は LUNA28 など）"),
    step("b", "「APIとサービス」→「ライブラリ」→ Google Sheets API →「有効にする」"),
    step("b", "「認証情報」→「認証情報を作成」→「サービスアカウント」→ 名前を付けて作成"),
    step("b", "作成したサービスアカウントを開き「キー」タブ →「鍵を追加」→「新しい鍵を作成」→ JSON → ダウンロード"),
    step("b", "予定表スプレッドシートの「共有」に、JSONの中の client_email（…@….iam.gserviceaccount.com）を「編集者」で追加"),

    h1("5　GitHub の準備（プログラムを動かす場所・無料）"),
    step("c", "https://github.com/ でアカウント作成（無料）"),
    step("c", "「New repository」→ 名前 luna28-instagram → Public を選んで作成（動画の公開URLに使うため Public）"),
    step("c", "ZIP「luna28_instagram_auto.zip」を展開し、「Add file」→「Upload files」で中身を全部ドラッグ → Commit"),
    step("c", "「Settings」→「Secrets and variables」→「Actions」→「New repository secret」で2つ登録：GOOGLE_SA_JSON（手順4のJSONの中身を全部貼る）、SHEET_ID（1dUBDkSp0mNqM6OPgqOoMuQlJzlVEJRB1JsMqGfArQ48）"),
    step("c", "「Actions」タブ →「LUNA28 Instagram 自動投稿」→「Run workflow」→ dry_run に 1 → Run。緑のチェックになれば生成まで成功"),
    step("c", "予定表に「今日・今から50分後・カルーセル・zukan_luna01」の行を足して dry_run 0 で Run workflow → 行が「確認待ち」になりプレビューが入るので、見て OK を入れ、もう一度 Run workflow → 実際に投稿されるのを確認"),
    p("確認が済んだら、あとは毎日 6:40・11:40・19:40 に自動で起動します（投稿枠は 7:00・12:00・20:00）。失敗すると GitHub から登録メールに通知が届き、予定表の「処理ログ」列に理由が書かれます。", { size: 19 }),

    h1("6　毎月の作業（10分）"),
    step("d", "ルナツールで翌月の1位〜3位を出し、予定表の D〜F 列に貼る"),
    step("d", "ひとこと31本と図鑑・リールの原稿を用意（Claudeに「12月分の原稿」と言えば書き出し、JSON化まで行う）"),
    step("d", "「確認待ち」になった行のプレビューを見て、承認(OK)列に OK を入れる（予定の前日まで）"),

    h1("7　飯田さんへの連絡"),
    p("Instagram の投稿はこちらの仕組みに移すので、飯田さんの投稿表では Instagram の行を「検討」にするか、Instagram 投稿を止めてもらう（X はそのまま）。12月分から切り替え。11月中は両方動かないよう、切替日を決めて伝える。", { size: 19 }),

    h1("8　できないこと・注意"),
    step("e", "ストーリーズに「リンクスタンプ」はAPIから付けられない（Instagramの仕様）。動画内の「プロフィールのリンクから」で誘導"),
    step("e", "Instagramの楽曲ライブラリはAPI投稿では使えない。音源は自前で合成したもの（著作権の問題なし）"),
    step("e", "APIの投稿上限は24時間で100件。通常1日2〜3件なので問題なし"),
    step("e", "トークンが無効になった場合（パスワード変更など）は手順3-4をやり直して貼り替える"),
  ] }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("/home/claude/ig_auto/out/LUNA28_Instagram自動投稿_設定手順書.docx", b); console.log("ok"); });
