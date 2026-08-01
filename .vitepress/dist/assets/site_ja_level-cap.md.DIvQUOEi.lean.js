import{C as s,o as e,c as n,E as a,k as d,j as i}from"./chunks/framework.Bmhw_dvp.js";const c=`<div class="contents">
<a id="contents_1"></a>
<ul class="list1 list-indent1"><li><a href="#content_1_0"> 概要 </a>
<ul class="list3 list-indent2"><li><a href="#content_1_1"> レベル上限の特殊仕様 </a></li></ul>
<ul class="list2 list-indent1"><li><a href="#content_1_2"> レベル上限UPの効果と強化に必要なアイテム数 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_3"> ※Lv105での上昇率について </a></li>
<li><a href="#content_1_4"> 上昇率が特殊なキャラクター </a></li>
<li><a href="#content_1_5"> ステータス計算式 </a></li></ul></li>
<li><a href="#content_1_6"> レベル上限UPの手順と方法 </a></li>
<li><a href="#content_1_7"> 効果と限界 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_8"> レベル上限UPの少し便利な使い方 </a></li></ul></li>
<li><a href="#content_1_9"> 必要アイテムの入手方法 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_10"> 壁に開限の入手性と運用について </a></li>
<li><a href="#content_1_11"> 「壁に開限・超昂」について </a></li>
<li><a href="#content_1_12"> 交換所(レベル上限UPアイテム交換所) </a></li>
<li><a href="#content_1_13"> 取引所 </a></li></ul></li></ul></li>
<li><a href="#content_1_14"> コメントフォーム </a></li></ul>
</div>
<br><br>
<h2 id="content_1_0">概要   <span id="l3ca63dd"></span> </h2>
<p>2023/03/22のアップデートで実装された。<br>
限界突破、覚醒強化に続くさらなるキャラクター強化の新要素。<br>
文字通りレベルの上限である100を突破し、最大でレベル150まで上げることができる。<br>
レベル100以降には105、110、120、130、150と5段階の閾があり、それぞれの段階で突破するための必要なアイテムが異なる。</p>
<ul class="list1 list-indent1"><li>更新履歴
<ul class="list2 list-indent1"><li>2025/05/21アップデートにより　壁に開限・超昂を含むレベル上限強化の場合にチェックを入れる工程の追加しました<br>
（貴重品である 壁に開限・超昂 を誤って消費しないようにする為の処置です）</li></ul></li></ul>
<h4 id="content_1_1">レベル上限の特殊仕様   <span id="p79d45a6"></span> </h4>
<p>上限開放を行った場合は、開放分が<strong>プレイヤーLvを上回った場合でも</strong>Lvの強化が可能となる。<br>
この仕様はプレイヤーLv100以下の状態であっても適用される。</p>
<ul class="list1 list-indent1"><li>例：プレイヤーLv101の状態でキャラクターLvを105にする等（2023/04/02確認）</li>
<li>例：プレイヤーLv70の状態でキャラクターLvを75にする等（2023/08/29確認）</li></ul>
<p>プレイヤーLv100以下の状態でレベル上限アップを適用した場合、プレイヤーレベルの上昇と連動してキャラクターレベルの上限も上がり続けるため、<br>
消費された「壁に開眼（レベル上限開放アイテム）」が無駄になる事はない。</p>
<h3 id="content_1_2">レベル上限UPの効果と強化に必要なアイテム数   <span id="ucbbb6aa"></span> </h3>
<p>レベルを120にまで上げる事によって、レベル100に対して最大で40%のステータスアップ<br>
上限値の150にまで達すると、レベル100に対して最大100%（2倍）のステータスアップ<br>
という驚異的な性能アップを遂げる事ができる。</p>
<p>ただし、レベル上限UPによって上昇するのは、通常のレベルアップと同様にステータス画面の左側に並ぶ</p>
<ul class="list1 list-indent1"><li>スタミナ</li>
<li>攻撃力</li>
<li>防御力</li>
<li>魔法力</li>
<li>魔法抵抗力</li></ul>
<p>のみとなりステータス画面右側の 命中力～必殺充填量 までの値は影響を受けない。<br>
（こちらは別途、装備や覚醒強化によって強化する／この点は限界突破も同様）</p>
<p>1レベル当たりによるステータスの上昇量は、Lv100まではキャラクター毎に設定された固定の値が加算されていたが、Lv100以降では異なる挙動を示す。<br>
例えばLv110のステータスはLv100と比較するとちょうど+20%であり、キャラクターによってこの上昇率は変わらない（ただし一部キャラクターは異なる）。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">Lv</th><th class="style_th">上昇率(Lv100比)</th><th class="style_th">消費アイテム</th></tr>
</thead><tbody><tr><th class="style_th">105</th><td class="style_td">+8～9.2%(※)</td><td class="style_td">壁に開限 10個</td></tr>
<tr><th class="style_th">110</th><td class="style_td">+20%</td><td class="style_td">壁に開限・銅 10個</td></tr>
<tr><th class="style_th">120</th><td class="style_td">+40%</td><td class="style_td">壁に開限・銀 10個</td></tr>
<tr><th class="style_th">130</th><td class="style_td">+60%</td><td class="style_td">壁に開限・金 10個</td></tr>
<tr><th class="style_th">150</th><td class="style_td">+100%</td><td class="style_td">壁に開限・超昂 10個</td></tr>
</tbody></table></div></div>

<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>Lv上限開放に必要なリソースのレート表</p>
</div><div class="rgn-content" style="display: none">
<p>開眼1個あたりに必要なリソースのレート表</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><td class="style_td"></td><th class="style_th">銀換算</th><th class="style_th">銅換算</th><th class="style_th">緑換算</th><th class="style_th">トークン換算</th></tr>
</thead><tbody><tr><th class="style_th">緑x1</th><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">5</td></tr>
<tr><th class="style_th">銅x1</th><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">5</td><td class="style_td" style="text-align:center;">25</td></tr>
<tr><th class="style_th">銀x1</th><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">5</td><td class="style_td" style="text-align:center;">25</td><td class="style_td" style="text-align:center;">125</td></tr>
<tr><th class="style_th">金x1</th><td class="style_td" style="text-align:center;">5</td><td class="style_td" style="text-align:center;">25</td><td class="style_td" style="text-align:center;">125</td><td class="style_td" style="text-align:center;">625</td></tr>
</tbody></table></div></div>
<p>Lv上限開放に必要なリソースのレート表</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">Lv</th><th class="style_th">金</th><th class="style_th">銀換算</th><th class="style_th">銅換算</th><th class="style_th">緑換算</th><th class="style_th">トークン換算</th></tr>
</thead><tbody><tr><th class="style_th">105</th><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">10</td><td class="style_td" style="text-align:center;">50</td></tr>
<tr><th class="style_th">110</th><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">10</td><td class="style_td" style="text-align:center;">50</td><td class="style_td" style="text-align:center;">250</td></tr>
<tr><th class="style_th">120</th><td class="style_td" style="text-align:center;">-</td><td class="style_td" style="text-align:center;">10</td><td class="style_td" style="text-align:center;">50</td><td class="style_td" style="text-align:center;">250</td><td class="style_td" style="text-align:center;">1250</td></tr>
<tr><th class="style_th">130</th><td class="style_td" style="text-align:center;">10</td><td class="style_td" style="text-align:center;">50</td><td class="style_td" style="text-align:center;">250</td><td class="style_td" style="text-align:center;">1250</td><td class="style_td" style="text-align:center;">6250</td></tr>
</tbody></table></div></div>
<p>上限130開放に必要な金開眼10個はトークンに換算して6250個分に相当する</p>
</div></div>
<h4 id="content_1_3">※Lv105での上昇率について   <span id="h514c261"></span> </h4>
<p>ステータス毎に+8%だったり、ときには+9.15%等、バラバラで不可解な値を示し、しかも各キャラ毎に全く異なる倍率のため一律の値が出せない。<br>
恐らくLvが10の倍数では+20%、+40%という値に収束するように設定されているが、そうでない場合はLv100までと同様に「キャラクター毎に設定された固定の値が加算」されている可能性がある。</p>
<h4 id="content_1_4">上昇率が特殊なキャラクター   <span id="z9d987a2"></span> </h4>
<p>一部のキャラクターは特殊な上昇をする。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><th class="style_th">レア</th><th class="style_th">キャラクター</th><th class="style_th">特殊な<br class="spacer">ステータス</th><th class="style_th">Lv150時の上昇率<br class="spacer">(Lv100比)</th><th class="style_th">Lv150(☆1)<br class="spacer">のパラメータ</th><th class="style_th">備考</th></tr>
<tr><td class="style_td">SSR</td><td class="style_td">一の神鍵アズエル</td><td class="style_td">スタミナ</td><td class="style_td" style="text-align:center;">+174%</td><td class="style_td" style="text-align:center;">6300</td><td class="style_td"></td></tr>
<tr><td class="style_td">SSR</td><td class="style_td">ビートアンスキルド・カナミ</td><td class="style_td">攻撃/防御/魔法/魔法抵抗</td><td class="style_td" style="text-align:center;">+171%/+122%/+171%/+123%</td><td class="style_td" style="text-align:center;">950/800/950/756</td><td class="style_td"></td></tr>
</tbody></table></div></div>
<h4 id="content_1_5">ステータス計算式   <span id="j5a49fff"></span> </h4>
<p>端数の切り捨てと切り上げが入り混じっているため少々ややこしい計算となる。</p>
<p>A=[基本ステータス*Lv上限突破(100+n%)]*限界突破(100+n%)<br>
※[]は端数切り捨て</p>
<p>B=[A*覚醒強化(n%)]<br>
※[]は小数点第二位を切り上げ?四捨五入?(データ不足)</p>
<p>C=A*装備強化(n%)</p>
<p>最終ステータス=A+B+C</p>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>計算実例</p>
</div><div class="rgn-content" style="display: none">
<ul class="list1 list-indent1"><li>超昂閃忍ナリカ
<ul class="list2 list-indent1"><li>Lv100時の攻撃力=521</li>
<li>Lv120(140%)</li>
<li>☆5(300%)</li>
<li>覚醒強化の攻撃11段階(11%)</li>
<li>衝撃のあるベルトRANK5(50%)</li></ul></li></ul>
<p>A=[521*140%]*300%=[729.42]*300%=729*300%=2187</p>
<p>B=[2187*11%]=[240.57]=240.6</p>
<p>C=2187*50%=1093.5</p>
<p>最終ステータス=2187+240.6+1093.5=3521.1<br>
<img alt="230403_01.png" height="255" loading="lazy" src="/img/526b8f5447f99e00.png" title="230403_01.png" width="502"></p>
<ul class="list1 list-indent1"><li>ビートソニック・アキレス
<ul class="list2 list-indent1"><li>Lv100時の攻撃力=475</li>
<li>Lv110(120%)</li>
<li>☆5(300%)</li>
<li>覚醒強化の攻撃1段階(1%)</li>
<li>謙信の兜RANK5(25%)</li></ul></li></ul>
<p>A=[475*120%]*300%=570*300%=1710</p>
<p>B=[1710*1%]=17.1</p>
<p>C=1710*25%=427.5</p>
<p>最終ステータス=1710+17.1+427.5=2154.6<br>
<img alt="230403_02.png" height="255" loading="lazy" src="/img/b3e3e1be37b4adfc.png" title="230403_02.png" width="502"></p>
</div></div>
<h3 id="content_1_6">レベル上限UPの手順と方法   <span id="m47f008c"></span> </h3>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td"><img alt="壁に開限.png" height="54" loading="lazy" src="/img/31d6f1061df34287.png" title="壁に開限.png" width="65"></td><td class="style_td"><img alt="壁に開限・銅.png" height="54" loading="lazy" src="/img/a30c34a137530bc5.png" title="壁に開限・銅.png" width="65"></td><td class="style_td"><img alt="壁に開限・銀.png" height="54" loading="lazy" src="/img/24a85903a0519540.png" title="壁に開限・銀.png" width="65"></td><td class="style_td"><img alt="壁に開限・金.png" height="54" loading="lazy" src="/img/83856d6f566cb345.png" title="壁に開限・金.png" width="65"></td><td class="style_td"><img alt="壁に開限・超昂.png" height="54" loading="lazy" src="/img/b27e69b64dcc9aff.png" title="壁に開限・超昂.png" width="65"></td></tr>
</tbody></table></div></div>
<p>専用アイテム「壁に開眼」シリーズを消費する事により、当該キャラクターのレベル上限を開放する事が可能となります。<br>
開眼系アイテムはゲーム内のコンテンツより入手可能です。</p>
<ul class="list1 list-indent1"><li>関連リンク：<a href="#k3665f01">必要アイテムの入手方法</a></li></ul>
<p>レベル上限アップを行いたい場合は</p>
<ol class="list1 list-indent1"><li>「ホーム画面」下の「キャラ強化」ボタンをクリック</li>
<li>表示されたキャラ一覧からレベル上限を開放したいキャラを選択</li>
<li>「Lv上限UP」ボタンをクリック
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td"><img alt="キャラ強化画面レベル上限アップ.jpg" height="224" loading="lazy" src="/img/4eb47e428c12828c.jpg" title="キャラ強化画面レベル上限アップ.jpg" width="384"></td></tr>
</tbody></table></div></div></li></ol>
<h3 id="content_1_7">効果と限界   <span id="nce84114"></span> </h3>
<p>レベル上限UPは、限界突破等によって既に育成が完了したキャラの性能を、さらに伸ばしていくための手段となる。<br>
各種育成や強化を行わずレベル上限UPのみを行っても、効果は限定的で効率はあまり良くない。<br>
よって、メインクエストの進行などに詰まった場合は、先に限界突破を行いキャラ性能の土台を伸ばすことが優先される。</p>
<ul class="list1 list-indent1"><li>関連リンク：低コストで☆5キャラを入手する</li></ul>
<p>特にレベルの上昇で強化されない固定ステータスには効果が無い事には注意。<br>
固定ステータスを伸ばしたい場合は覚醒強化や装備を強化していく必要がある。</p>
<ul class="list1 list-indent1"><li>関連リンク：レベルアップ や 限界突破 等に応じて成長するステータス</li></ul>
<p>仮に強化の目的がレイドバトルだとすると、レベルを上げても生存時間は伸びない。<br>
そのためメイン火力となるアタッカーキャラは十分な恩恵を受けられるが、ヒーラーやバッファー・デバッファーキャラに対しては費用対効果は悪い。<br>
（これは絵馬を使用するほうの「限界突破」とも共通する）。</p>
<ul class="list1 list-indent1"><li>関連リンク：レイドにおけるキャラステータスの働き</li></ul>
<p>強化の大まかな道筋</p>
<ul class="list1 list-indent1"><li><span>レベルアップ ⇒ Lv100 ⇒ 限界突破 ⇒ 覚醒強化 ⇒ <strong>レベル上限UP</strong>
</span><ul class="list2 list-indent1"><li>一般的な育成ルートを示したものです</li>
<li>どのような手順でキャラの強化を行っても最終的な性能に差は出ないため、必ずしも上記の手順通りに強化しなくてはならないという意味ではありません</li>
<li>将来的に絶対に強化すると決めているキャラなら、限界突破などより先に上限をUPさせても問題ありません</li></ul></li></ul>
<h4 id="content_1_8">レベル上限UPの少し便利な使い方   <span id="j81be382"></span> </h4>
<p>ゲーム内のソート機能が弱い為、手元キャラ数が増えると目当てのキャラのみを優先して表示する事が難しくなる。<br>
（現状ではソート実行時に複数のソート条件を同時に設定できない）<br>
そこで、主力メンバーだけでもLv105以上にレベルアップしておけば、ソート優先度を「レベル」に設定しておくだけで、<br>
普段使いの主力メンバーを集中して上位に表示できるようになるため、キャラ表示の利便性が若干向上する。</p>
<h3 id="content_1_9">必要アイテムの入手方法   <span id="k3665f01"></span> </h3>
<ul class="list1 list-indent1"><li>交換所(レベル上限UPアイテム交換所)
<ul class="list2 list-indent1"><li>最下級の「壁に開限」は毎月30個限定で要トークン。銅、銀、金は交換数の上限は設けられていないがそれぞれ一つ下の段階の壁に開限との交換。</li></ul></li>
<li>取引所
<ul class="list2 list-indent1"><li>23/06/21より、月替わりのリセットは無い回数制限付きでトークン・黒との交換が設けられた。詳細は<a href="#f066768c">下記へ</a>。</li></ul></li>
<li>デイリークエスト
<ul class="list2 list-indent1"><li>最下級の「壁に開眼」が毎週水曜日の確率ドロップ報酬に設定されている（ドロップ率40%）。</li></ul></li>
<li>ボックス系の敵の撃破
<ul class="list2 list-indent1"><li>クエスト難度100以上のメインクエスト(第2部19-1以降)で確率で発生する。<br>
この確率はステージ個別で分かれており、遭遇に失敗するたびに上昇していく。また確率の初期値はVIPランクに応じて上げられる。</li>
<li>NORMAL/HARD/EXTRAの各１面１回ずつで、取得済の面は「--%」表記に変わる。例えば第2部Area19は全12面なので、計36回という計算。<br>
なお取得済のステージのみ、毎週月曜日の午前4時にリセットされ、再び取得できるようになる。</li>
<li>ボックス系からは「壁に開眼」以外にも様々なアイテムがドロップするが、基本的にEXTRA出現のボックスが最も内容が良い。</li>
<li>NORMALから入手できる開限
<ul class="list3 list-indent1"><li>壁に開限(無印)</li></ul></li>
<li>HARDから入手できる開限
<ul class="list3 list-indent1"><li>壁に開限・銅、壁に開限・銀</li></ul></li>
<li>EXTRAから入手できる開限
<ul class="list3 list-indent1"><li>壁に開限・銅、壁に開限・銀、壁に開限・金</li></ul></li>
<li>詳細は「『トレジャーボックス』および『パンドラボックス』について」を参照のこと。</li></ul></li>
<li>課金
<ul class="list2 list-indent1"><li>現在は期間限定販売のみ。</li>
<li>販売例
<ul class="list3 list-indent1"><li>(不定期) 壁に開限200個 DMMポイント3,000 ※購入制限2回まで</li>
<li>(アニバーサリーイベントのみ) 壁に開限・金10個 DMMポイント9,000 ※購入制限2回まで</li>
<li>(アニバーサリーイベントのみ) 壁に開限・超昂10個 DMMポイント9,000 ※購入制限1回まで</li></ul></li></ul></li>
<li>レイド(報酬が一定とは限らない)
<ul class="list2 list-indent1"><li>「狂王」の討伐報酬。普40個、銅45個、銀25個、金10個。(第2回)</li>
<li>「グナガン」の討伐報酬。壁に開限2個。</li>
<li>「ゴールデンハニー」の討伐報酬。壁に開限5個。</li></ul></li>
<li>イベント
<ul class="list2 list-indent1"><li>アニバーサリーイベントのログインボーナス(壁に開限・金5個)</li>
<li>アニバーサリーイベントのパネルミッション(壁に開限・超昂5個)</li></ul></li></ul>
<h4 id="content_1_10">壁に開限の入手性と運用について   <span id="hd6e578d"></span> </h4>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><th class="style_th">Lv105</th><td class="style_td"><img alt="壁に開限.png" height="40" loading="lazy" src="/img/31d6f1061df34287.png" title="壁に開限.png" width="48"> 壁に開眼</td><td class="style_td">入手数は比較的多い<br class="spacer">気軽に使用して問題ない</td></tr>
<tr><th class="style_th">Lv110</th><td class="style_td"><img alt="壁に開限・銅.png" height="40" loading="lazy" src="/img/a30c34a137530bc5.png" title="壁に開限・銅.png" width="48"> 壁に開眼・銅</td><td class="style_td">入手数は比較的多い<br class="spacer">気軽に使用して問題ない</td></tr>
<tr><th class="style_th">Lv120</th><td class="style_td"><img alt="壁に開限・銀.png" height="40" loading="lazy" src="/img/24a85903a0519540.png" title="壁に開限・銀.png" width="48"> 壁に開眼・銀</td><td class="style_td">入手数は限られるため<br class="spacer">使用の判断は慎重に</td></tr>
<tr><th class="style_th">Lv130</th><td class="style_td"><img alt="壁に開限・金.png" height="40" loading="lazy" src="/img/83856d6f566cb345.png" title="壁に開限・金.png" width="48"> 壁に開眼・金</td><td class="style_td">入手数は限られるため<br class="spacer">使用の判断は慎重に</td></tr>
<tr><th class="style_th">Lv150</th><td class="style_td"><img alt="壁に開限・超昂.png" height="40" loading="lazy" src="/img/b27e69b64dcc9aff.png" title="壁に開限・超昂.png" width="48"> 壁に開眼・超昂</td><td class="style_td"><strong>超貴重品</strong><br class="spacer">投入先キャラについては十分な検討を</td></tr>
</tbody></table></div></div>
<p>プレイスタイルにもよるが、一般的に壁に開限・銀（Lv120）以上から入手難度が上がるため、<br>
投入先キャラはレイド用のエース編成に絞るなど、運用を考慮する必要がある。<br>
特に下記の壁に開限・超昂の稀少度は非常に高い。</p>
<h4 id="content_1_11">「壁に開限・超昂」について   <span id="w4bfd630"></span> </h4>
<p>常設の入手手段は無く、運営からはアニバーサリーイベントごとに配布予定と告知されている。(参照：<a href="https://www.alicesoft.com/information/2023/entry003307.html" rel="noopener" target="_blank">超昂大戦月間ブログ2023年12月号</a>)<br>
2.5周年の際は特別パネルミッション報酬(5個)、課金販売(10個、DMMポイント9,000で1セット限定)で提供された。<br>
配布だけで賄うなら1年に1体、課金も含めれば最大で3体までレベル150に出来る計算になる。<br>
Bユニバースの難易度VERYHARDで手に入る固有アイテムで各ボスにつき1個だけ交換できるようになった。</p>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>配布・販売履歴</p>
</div><div class="rgn-content" style="display: none">
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">配布販売日</th><th class="style_th">イベント名</th><th class="style_th">配布ミッション<br class="spacer">(配布個数)</th><th class="style_th">ショップ<br class="spacer">販売個数</th></tr>
</thead><tbody><tr><td class="style_td">2023/05/25</td><td class="style_td">2.5周年ハーフアニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
<tr><td class="style_td">2023/11/15</td><td class="style_td">3周年アニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
<tr><td class="style_td">2024/05/22</td><td class="style_td">3.5周年アニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
<tr><td class="style_td">2024/11/13</td><td class="style_td">4周年アニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
<tr><td class="style_td">2025/05/14</td><td class="style_td">4.5周年アニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
<tr><td class="style_td">2025/11/12</td><td class="style_td">5周年アニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
<tr><td class="style_td">2026/05/20</td><td class="style_td">5.5周年アニバーサリー</td><td class="style_td">パネルミッション(5個)</td><td class="style_td">10個</td></tr>
</tbody></table></div></div>
</div></div>
<h4 id="content_1_12">交換所(レベル上限UPアイテム交換所)   <span id="yee86a2a"></span> </h4>
<div class="includex" style="padding:0px;margin:0px;"></div>
<p>2023/03/22にレベル上限UP機能実装に伴い開設された交換所。<br>
レイドなどエンドコンテンツを見据えた中級者以上向け。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th" style="text-align:left;">交換アイテム</th><th class="style_th" style="text-align:center;">月制限</th><th class="style_th">必要アイテム</th><th class="style_th">備考</th><th class="style_th">（他との必要個数)</th></tr>
</thead><tbody><tr><th class="style_th" style="text-align:left;">壁に開限×1</th><td class="style_td" style="text-align:center;">30</td><td class="style_td">トークン 5個</td><td class="style_td">プレイヤーによっては常に不足するのでトークンに余裕があるなら積極的に交換したい。</td><td class="style_td"></td></tr>
<tr><th class="style_th" style="text-align:left;">壁に開限・銅×1</th><td class="style_td" style="text-align:center;"></td><td class="style_td">壁に開限 5個</td><td class="style_td">開眼・銅より通常開眼の方が入手機会が少ないので序盤は注意。</td><td class="style_td">トークン:25個</td></tr>
<tr><th class="style_th" style="text-align:left;">壁に開限・銀×1</th><td class="style_td" style="text-align:center;"></td><td class="style_td">壁に開限・銅 5個</td><td class="style_td">開眼・銅はたくさん手に入るので余ったら銀と交換していこう。</td><td class="style_td">トークン:125個<br class="spacer">壁に開限:25個</td></tr>
<tr><th class="style_th" style="text-align:left;">壁に開限・金×1</th><td class="style_td" style="text-align:center;">20</td><td class="style_td">壁に開限・銀 5個</td><td class="style_td">逸品ベルトを装備するエースアタッカー以外は、開眼・金10個でLv130を1人作るより<br class="spacer">開眼・銀50個でLv120を5人作った方が効率よく戦力（スコア）が増える。</td><td class="style_td">トークン:625個<br class="spacer">壁に開限:125個<br class="spacer">壁に開限・銅:25個</td></tr>
</tbody></table></div></div>
<p>トークンだけで賄おうとすると途方もない数が必要になってしまう。<br>
例えば「壁に開限・金」を10個集めようとした場合…<br>
トークンが<strong>6250個</strong>必要になり、毎月の上限数である壁に開限30個だけで交換しようとすると、およそ<strong>42ヶ月</strong>もかかってしまう。</p>
<h4 id="content_1_13">取引所   <span id="f066768c"></span> </h4>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">アイテム</th><th class="style_th">必要アイテム</th><th class="style_th">制限回数</th></tr>
</thead><tbody><tr><th class="style_th">壁に開限 10個</th><td class="style_td">トークン・黒 1個</td><td class="style_td">5回(最大50個)</td></tr>
<tr><th class="style_th">壁に開限・銅 10個</th><td class="style_td">トークン・黒 5個</td><td class="style_td">4回(最大40個)</td></tr>
</tbody></table></div></div>
<p>23/06/21に追加。月替わりによるリセットは無い。<br>
トークン・黒は1個につき通常のトークン30個分として換算すると、交換所のレートよりもお得である。<br>
ただし先述の通り月替わりによるリセットが無いため、交換所のトークンで交換できる分を無視してまでこちらを優先してしまうと、取得できる開限の総量は減ってしまう。<br>
急ぎの理由が無い限りはトークンに余裕ができた場合のみ交換していくのがよいだろう。</p>
<ul class="list1 list-indent1"><li>交換制限回数リセット履歴
<ul class="list2 list-indent1"><li>24/05/22 3.5周年ハーフアニバーサリー 同時期実装のその他のアイテムと同時にリセット</li>
<li>25/05/14 4.5周年ハーフアニバーサリー 同時期実装のその他のアイテムと同時にリセット</li>
<li>26/05/20 5.5周年ハーフアニバーサリー 同時期実装のその他のアイテムと同時にリセット</li></ul></li></ul>
<h2 id="content_1_14">コメントフォーム   <span id="la484b40"></span> </h2>

<ins class="adsbygoogle" data-ad-client="ca-pub-6756084042400545" data-ad-format="auto" data-ad-slot="2456832941" data-full-width-responsive="true" style="display:block"></ins>
<br>
<div class="pcomment">

<ul class="list1 list-indent1"><li class="pcmt" data-comment-id="comment_197c8223f61e4a97640725dbcf730d37"><span>『公式サイトHELP画像がLv75状態のものであるため、この仕様はプレイヤーLv100以下の状態であっても適用されると思われる。』 <br class="spacer">推測になっているのでご報告します。私はまだレベル70台のプレイヤーです。上限UPしたキャラのレベルが+5できる事と、プレイヤーレベルが上がる度にちゃんと+5の差が更新され続ける事を確認しました -- [tXxLT81rcCs] </span><span class="comment_date">2023-08-29 (火) 11:34:40</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_7af01e8f4d82770e0213ba0eec5117b3">いただいたコメントを元にページ内の表記を更新しておきました。情報ありがとうございました。 -- [mwEFdaVWiN2] <span class="comment_date">2023-09-29 (金) 15:11:24</span></li></ul></li></ul>
</div>
`,r={html:c},o=JSON.parse('{"title":"レベル上限UP","description":"","frontmatter":{"title":"レベル上限UP","layout":"doc","meta":{"sourceUrl":"https://escalationheroines.wikiru.jp/?%E3%83%AC%E3%83%99%E3%83%AB%E4%B8%8A%E9%99%90UP","sourceUpdated":"2026-06-08 (月) 03:07:13","synced":"2026-07-22","reviewed":false,"translated":false}},"headers":[],"relativePath":"site/ja/level-cap.md","filePath":"site/ja/level-cap.md"}'),y={name:"site/ja/level-cap.md"},g=Object.assign(y,{setup(h){return(_,t)=>{const l=s("MirrorContent");return e(),n("div",null,[a(l,{html:d(r).html},null,8,["html"]),t[0]||(t[0]=i("div",{class:"search-index",style:{display:"none"},"aria-hidden":"true"},"概要 レベル上限の特殊仕様 レベル上限UPの効果と強化に必要なアイテム数 ※Lv105での上昇率について 上昇率が特殊なキャラクター ステータス計算式 レベル上限UPの手順と方法 効果と限界 レベル上限UPの少し便利な使い方 必要アイテムの入手方法 壁に開限の入手性と運用について 「壁に開限・超昂」について 交換所(レベル上限UPアイテム交換所) 取引所 コメントフォーム 概要 2023/03/22のアップデートで実装された。 限界突破、覚醒強化に続くさらなるキャラクター強化の新要素。 文字通りレベルの上限である100を突破し、最大でレベル150まで上げることができる。 レベル100以降には105、110、120、130、150と5段階の閾があり、それぞれの段階で突破するための必要なアイテムが異なる。 更新履歴 2025/05/21アップデートにより 壁に開限・超昂を含むレベル上限強化の場合にチェックを入れる工程の追加しました （貴重品である 壁に開限・超昂 を誤って消費しないようにする為の処置です） レベル上限の特殊仕様 上限開放を行った場合は、開放分がプレイヤーLvを上回った場合でもLvの強化が可能となる。 この仕様はプレイヤーLv100以下の状態であっても適用される。 例：プレイヤーLv101の状態でキャラクターLvを105にする等（2023/04/02確認） 例：プレイヤーLv70の状態でキャラクターLvを75にする等（2023/08/29確認） プレイヤーLv100以下の状態でレベル上限アップを適用した場合、プレイヤーレベルの上昇と連動してキャラクターレベルの上限も上がり続けるため、 消費された「壁に開眼（レベル上限開放アイテム）」が無駄になる事はない。 レベル上限UPの効果と強化に必要なアイテム数 レベルを120にまで上げる事によって、レベル100に対して最大で40%のステータスアップ 上限値の150にまで達すると、レベル100に対して最大100%（2倍）のステータスアップ という驚異的な性能アップを遂げる事ができる。 ただし、レベル上限UPによって上昇するのは、通常のレベルアップと同様にステータス画面の左側に並ぶ スタミナ 攻撃力 防御力 魔法力 魔法抵抗力 のみとなりステータス画面右側の 命中力～必殺充填量 までの値は影響を受けない。 （こちらは別途、装備や覚醒強化によって強化する／この点は限界突破も同様） 1レベル当たりによるステータスの上昇量は、Lv100まではキャラクター毎に設定された固定の値が加算されていたが、Lv100以降では異なる挙動を示す。 例えばLv110のステータスはLv100と比較するとちょうど+20%であり、キャラクターによってこの上昇率は変わらない（ただし一部キャラクターは異なる）。 Lv上昇率(Lv100比)消費アイテム 105+8～9.2%(※)壁に開限 10個 110+20%壁に開限・銅 10個 120+40%壁に開限・銀 10個 130+60%壁に開限・金 10個 150+100%壁に開限・超昂 10個 Lv上限開放に必要なリソースのレート表 開眼1個あたりに必要なリソースのレート表 銀換算銅換算緑換算トークン換算 緑x1---5 銅x1--525 銀x1-525125 金x1525125625 Lv上限開放に必要なリソースのレート表 Lv金銀換算銅換算緑換算トークン換算 105---1050 110--1050250 120-10502501250 130105025012506250 上限130開放に必要な金開眼10個はトークンに換算して6250個分に相当する ※Lv105での上昇率について ステータス毎に+8%だったり、ときには+9.15%等、バラバラで不可解な値を示し、しかも各キャラ毎に全く異なる倍率のため一律の値が出せない。 恐らくLvが10の倍数では+20%、+40%という値に収束するように設定されているが、そうでない場合はLv100までと同様に「キャラクター毎に設定された固定の値が加算」されている可能性がある。 上昇率が特殊なキャラクター 一部のキャラクターは特殊な上昇をする。 レアキャラクター特殊なステータスLv150時の上昇率(Lv100比)Lv150(☆1)のパラメータ備考 SSR一の神鍵アズエルスタミナ+174%6300 SSRビートアンスキルド・カナミ攻撃/防御/魔法/魔法抵抗+171%/+122%/+171%/+123%950/800/950/756 ステータス計算式 端数の切り捨てと切り上げが入り混じっているため少々ややこしい計算となる。 A=[基本ステータス*Lv上限突破(100+n%)]*限界突破(100+n%) ※[]は端数切り捨て B=[A*覚醒強化(n%)] ※[]は小数点第二位を切り上げ?四捨五入?(データ不足) C=A*装備強化(n%) 最終ステータス=A+B+C 計算実例 超昂閃忍ナリカ Lv100時の攻撃力=521 Lv120(140%) ☆5(300%) 覚醒強化の攻撃11段階(11%) 衝撃のあるベルトRANK5(50%) A=[521*140%]*300%=[729.42]*300%=729*300%=2187 B=[2187*11%]=[240.57]=240.6 C=2187*50%=1093.5 最終ステータス=2187+240.6+1093.5=3521.1 ビートソニック・アキレス Lv100時の攻撃力=475 Lv110(120%) ☆5(300%) 覚醒強化の攻撃1段階(1%) 謙信の兜RANK5(25%) A=[475*120%]*300%=570*300%=1710 B=[1710*1%]=17.1 C=1710*25%=427.5 最終ステータス=1710+17.1+427.5=2154.6 レベル上限UPの手順と方法 専用アイテム「壁に開眼」シリーズを消費する事により、当該キャラクターのレベル上限を開放する事が可能となります。 開眼系アイテムはゲーム内のコンテンツより入手可能です。 関連リンク：必要アイテムの入手方法 レベル上限アップを行いたい場合は 「ホーム画面」下の「キャラ強化」ボタンをクリック 表示されたキャラ一覧からレベル上限を開放したいキャラを選択 「Lv上限UP」ボタンをクリック 効果と限界 レベル上限UPは、限界突破等によって既に育成が完了したキャラの性能を、さらに伸ばしていくための手段となる。 各種育成や強化を行わずレベル上限UPのみを行っても、効果は限定的で効率はあまり良くない。 よって、メインクエストの進行などに詰まった場合は、先に限界突破を行いキャラ性能の土台を伸ばすことが優先される。 関連リンク：低コストで☆5キャラを入手する 特にレベルの上昇で強化されない固定ステータスには効果が無い事には注意。 固定ステータスを伸ばしたい場合は覚醒強化や装備を強化していく必要がある。 関連リンク：レベルアップ や 限界突破 等に応じて成長するステータス 仮に強化の目的がレイドバトルだとすると、レベルを上げても生存時間は伸びない。 そのためメイン火力となるアタッカーキャラは十分な恩恵を受けられるが、ヒーラーやバッファー・デバッファーキャラに対しては費用対効果は悪い。 （これは絵馬を使用するほうの「限界突破」とも共通する）。 関連リンク：レイドにおけるキャラステータスの働き 強化の大まかな道筋 レベルアップ ⇒ Lv100 ⇒ 限界突破 ⇒ 覚醒強化 ⇒ レベル上限UP 一般的な育成ルートを示したものです どのような手順でキャラの強化を行っても最終的な性能に差は出ないため、必ずしも上記の手順通りに強化しなくてはならないという意味ではありません 将来的に絶対に強化すると決めているキャラなら、限界突破などより先に上限をUPさせても問題ありません レベル上限UPの少し便利な使い方 ゲーム内のソート機能が弱い為、手元キャラ数が増えると目当てのキャラのみを優先して表示する事が難しくなる。 （現状ではソート実行時に複数のソート条件を同時に設定できない） そこで、主力メンバーだけでもLv105以上にレベルアップしておけば、ソート優先度を「レベル」に設定しておくだけで、 普段使いの主力メンバーを集中して上位に表示できるようになるため、キャラ表示の利便性が若干向上する。 必要アイテムの入手方法 交換所(レベル上限UPアイテム交換所) 最下級の「壁に開限」は毎月30個限定で要トークン。銅、銀、金は交換数の上限は設けられていないがそれぞれ一つ下の段階の壁に開限との交換。 取引所 23/06/21より、月替わりのリセットは無い回数制限付きでトークン・黒との交換が設けられた。詳細は下記へ。 デイリークエスト 最下級の「壁に開眼」が毎週水曜日の確率ドロップ報酬に設定されている（ドロップ率40%）。 ボックス系の敵の撃破 クエスト難度100以上のメインクエスト(第2部19-1以降)で確率で発生する。 この確率はステージ個別で分かれており、遭遇に失敗するたびに上昇していく。また確率の初期値はVIPランクに応じて上げられる。 NORMAL/HARD/EXTRAの各１面１回ずつで、取得済の面は「--%」表記に変わる。例えば第2部Area19は全12面なので、計36回という計算。 なお取得済のステージのみ、毎週月曜日の午前4時にリセットされ、再び取得できるようになる。 ボックス系からは「壁に開眼」以外にも様々なアイテムがドロップするが、基本的にEXTRA出現のボックスが最も内容が良い。 NORMALから入手できる開限 壁に開限(無印) HARDから入手できる開限 壁に開限・銅、壁に開限・銀 EXTRAから入手できる開限 壁に開限・銅、壁に開限・銀、壁に開限・金 詳細は「『トレジャーボックス』および『パンドラボックス』について」を参照のこと。 課金 現在は期間限定販売のみ。 販売例 (不定期) 壁に開限200個 DMMポイント3,000 ※購入制限2回まで (アニバーサリーイベントのみ) 壁に開限・金10個 DMMポイント9,000 ※購入制限2回まで (アニバーサリーイベントのみ) 壁に開限・超昂10個 DMMポイント9,000 ※購入制限1回まで レイド(報酬が一定とは限らない) 「狂王」の討伐報酬。普40個、銅45個、銀25個、金10個。(第2回) 「グナガン」の討伐報酬。壁に開限2個。 「ゴールデンハニー」の討伐報酬。壁に開限5個。 イベント アニバーサリーイベントのログインボーナス(壁に開限・金5個) アニバーサリーイベントのパネルミッション(壁に開限・超昂5個) 壁に開限の入手性と運用について Lv105 壁に開眼入手数は比較的多い気軽に使用して問題ない Lv110 壁に開眼・銅入手数は比較的多い気軽に使用して問題ない Lv120 壁に開眼・銀入手数は限られるため使用の判断は慎重に Lv130 壁に開眼・金入手数は限られるため使用の判断は慎重に Lv150 壁に開眼・超昂超貴重品投入先キャラについては十分な検討を プレイスタイルにもよるが、一般的に壁に開限・銀（Lv120）以上から入手難度が上がるため、 投入先キャラはレイド用のエース編成に絞るなど、運用を考慮する必要がある。 特に下記の壁に開限・超昂の稀少度は非常に高い。 「壁に開限・超昂」について 常設の入手手段は無く、運営からはアニバーサリーイベントごとに配布予定と告知されている。(参照：超昂大戦月間ブログ2023年12月号) 2.5周年の際は特別パネルミッション報酬(5個)、課金販売(10個、DMMポイント9,000で1セット限定)で提供された。 配布だけで賄うなら1年に1体、課金も含めれば最大で3体までレベル150に出来る計算になる。 Bユニバースの難易度VERYHARDで手に入る固有アイテムで各ボスにつき1個だけ交換できるようになった。 配布・販売履歴 配布販売日イベント名配布ミッション(配布個数)ショップ販売個数 2023/05/252.5周年ハーフアニバーサリーパネルミッション(5個)10個 2023/11/153周年アニバーサリーパネルミッション(5個)10個 2024/05/223.5周年アニバーサリーパネルミッション(5個)10個 2024/11/134周年アニバーサリーパネルミッション(5個)10個 2025/05/144.5周年アニバーサリーパネルミッション(5個)10個 2025/11/125周年アニバーサリーパネルミッション(5個)10個 2026/05/205.5周年アニバーサリーパネルミッション(5個)10個 交換所(レベル上限UPアイテム交換所) 2023/03/22にレベル上限UP機能実装に伴い開設された交換所。 レイドなどエンドコンテンツを見据えた中級者以上向け。 交換アイテム月制限必要アイテム備考（他との必要個数) 壁に開限×130トークン 5個プレイヤーによっては常に不足するのでトークンに余裕があるなら積極的に交換したい。 壁に開限・銅×1壁に開限 5個開眼・銅より通常開眼の方が入手機会が少ないので序盤は注意。トークン:25個 壁に開限・銀×1壁に開限・銅 5個開眼・銅はたくさん手に入るので余ったら銀と交換していこう。トークン:125個壁に開限:25個 壁に開限・金×120壁に開限・銀 5個逸品ベルトを装備するエースアタッカー以外は、開眼・金10個でLv130を1人作るより開眼・銀50個でLv120を5人作った方が効率よく戦力（スコア）が増える。トークン:625個壁に開限:125個壁に開限・銅:25個 トークンだけで賄おうとすると途方もない数が必要になってしまう。 例えば「壁に開限・金」を10個集めようとした場合… トークンが6250個必要になり、毎月の上限数である壁に開限30個だけで交換しようとすると、およそ42ヶ月もかかってしまう。 取引所 アイテム必要アイテム制限回数 壁に開限 10個トークン・黒 1個5回(最大50個) 壁に開限・銅 10個トークン・黒 5個4回(最大40個) 23/06/21に追加。月替わりによるリセットは無い。 トークン・黒は1個につき通常のトークン30個分として換算すると、交換所のレートよりもお得である。 ただし先述の通り月替わりによるリセットが無いため、交換所のトークンで交換できる分を無視してまでこちらを優先してしまうと、取得できる開限の総量は減ってしまう。 急ぎの理由が無い限りはトークンに余裕ができた場合のみ交換していくのがよいだろう。 交換制限回数リセット履歴 24/05/22 3.5周年ハーフアニバーサリー 同時期実装のその他のアイテムと同時にリセット 25/05/14 4.5周年ハーフアニバーサリー 同時期実装のその他のアイテムと同時にリセット 26/05/20 5.5周年ハーフアニバーサリー 同時期実装のその他のアイテムと同時にリセット コメントフォーム 『公式サイトHELP画像がLv75状態のものであるため、この仕様はプレイヤーLv100以下の状態であっても適用されると思われる。』 推測になっているのでご報告します。私はまだレベル70台のプレイヤーです。上限UPしたキャラのレベルが+5できる事と、プレイヤーレベルが上がる度にちゃんと+5の差が更新され続ける事を確認しました -- [tXxLT81rcCs] 2023-08-29 (火) 11:34:40 いただいたコメントを元にページ内の表記を更新しておきました。情報ありがとうございました。 -- [mwEFdaVWiN2] 2023-09-29 (金) 15:11:24",-1))])}}});export{o as __pageData,g as default};
