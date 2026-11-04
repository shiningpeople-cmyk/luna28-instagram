const fs=require("fs");
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,PageBreak}=require("docx");
const F="游ゴシック";
const run=(t,o={})=>new TextRun({text:t,font:F,size:20,...o});
const p=(t,o={})=>new Paragraph({children:[run(t,o)],spacing:{after:80}});
const h1=(t)=>new Paragraph({children:[run(t,{bold:true,size:28})],spacing:{before:200,after:100}});
const cell=(t,w,fill)=>new TableCell({width:{size:w,type:WidthType.DXA},shading:fill?{type:ShadingType.CLEAR,fill,color:"auto"}:undefined,margins:{top:60,bottom:60,left:100,right:100},children:(Array.isArray(t)?t:[t]).map(x=>new Paragraph({children:[run(x,{size:19})],spacing:{after:30}}))});
const table=(rows)=>new Table({width:{size:9400,type:WidthType.DXA},columnWidths:[1400,8000],rows:rows.map(([a,b],i)=>new TableRow({children:[cell(a,1400,"EFE9DD"),cell(b,8000)]}))});
const kids=[new Paragraph({children:[run("LUNA28 Instagram 図鑑・リール原稿　確認用（27ルナ）",{bold:true,size:32})],spacing:{after:60}}),
 p("出典：ルナシート（2017年年運シート・pdf、luna_01〜28）。本文はシートの原文をそのまま切り出しています（言い換えなし）。相性はシートの「理想の異性／避けたい異性」の1位、ラッキーはシート記載。",{size:19,color:"555555"}),
 p("確認してほしい点：①切り出した文が投稿として適切か（特に恋愛）②相性の番号 ③リールの問いかけ（性質の1文目から）。直す場合はこの文書に赤字で。",{size:19,color:"555555"})];
for(let n=1;n<=28;n++){ if(n===20) continue;
 const z=JSON.parse(fs.readFileSync(`content/zukan_luna${String(n).padStart(2,"0")}.json`,"utf8"));
 const r=JSON.parse(fs.readFileSync(`content/reel_luna${String(n).padStart(2,"0")}.json`,"utf8"));
 kids.push(h1(`${n}のルナ『${z.name}』`));
 const rows=[["表紙",[z.catch]]];
 for(const pg of z.pages){ if(pg.title==="相性") rows.push(["相性",[`理想の異性1位：${pg.good.join("・")}のルナ`,`避けたい異性1位：${pg.care.join("・")}のルナ`,pg.note]]); else rows.push([pg.title,pg.lines]); }
 rows.push(["リール",[`問いかけ：${r.hook.join("")}`,`特徴：${r.traits.join("／")}`]]);
 kids.push(table(rows));
}
const doc=new Document({styles:{default:{document:{run:{font:F,size:20}}}},sections:[{properties:{page:{margin:{top:900,bottom:900,left:1100,right:1100}}},children:kids}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("out/LUNA28_図鑑リール原稿_確認用.docx",b);console.log("ok")});
