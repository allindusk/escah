import{C as s,o as e,c as a,E as d,k as n,j as i}from"./chunks/framework.Bmhw_dvp.js";const c=`<div style="text-align:right">最終更新日時:2026-04-09 (木) 20:30:09</div>
<h2 id="content_1_0">戦闘   <span id="a533712c"></span> </h2>
<div class="contents">
<a id="contents_1"></a>
<ul class="list1 list-indent1"><li><a href="#content_1_0"> 戦闘 </a></li>
<li><a href="#content_1_1"> 戦闘について </a>
<ul class="list3 list-indent2"><li><a href="#content_1_2"> 戦闘速度の調整方法 </a></li>
<li><a href="#content_1_3"> 戦闘の一時停止方法 </a></li>
<li><a href="#content_1_4"> 特定の敵をロックオンする方法 </a></li>
<li><a href="#content_1_5"> 特定のキャラのみを撤退させる方法 </a></li>
<li><a href="#content_1_6"> 必殺技の自動設定方法 </a></li>
<li><a href="#content_1_7"> バトルをリトライしたい </a></li></ul>
<ul class="list2 list-indent1"><li><a href="#content_1_8"> 助っ人について </a>
<ul class="list3 list-indent1"><li><a href="#content_1_9"> 助っ人の選択方法 </a></li>
<li><a href="#content_1_10"> 助っ人の設定方法 </a></li></ul></li></ul></li>
<li><a href="#content_1_11"> 戦闘の基礎知識 </a>
<ul class="list2 list-indent1"><li><a href="#content_1_12"> 各種パラメータ </a></li>
<li><a href="#content_1_13"> 物理攻撃と魔法攻撃 </a></li>
<li><a href="#content_1_14"> スタミナとダメージ </a></li>
<li><a href="#content_1_15"> 出撃 </a></li>
<li><a href="#content_1_16"> 出撃可能人数 </a></li>
<li><a href="#content_1_17"> 優先出撃設定 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_18"> 出撃パーティーの固定方法 </a></li></ul></li>
<li><a href="#content_1_19"> 前列／後列と近距離攻撃／遠距離攻撃 </a></li>
<li><a href="#content_1_20"> 撤退 </a></li>
<li><a href="#content_1_21"> 必殺技と固有効果 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_22"> 必殺技 </a></li>
<li><a href="#content_1_23"> 敵の必殺技 </a></li>
<li><a href="#content_1_24"> 必殺技ゲージの計算式 </a></li>
<li><a href="#content_1_25"> 必殺技発動までの主な時間 </a></li>
<li><a href="#content_1_26"> 固有効果 </a></li></ul></li>
<li><a href="#content_1_27"> 対象ロック </a></li>
<li><a href="#content_1_28"> 攻撃、連撃、反撃、命中・回避判定、クリティカル </a>
<ul class="list3 list-indent1"><li><a href="#content_1_29"> 攻撃 </a></li>
<li><a href="#content_1_30"> 連撃 </a></li>
<li><a href="#content_1_31"> 反撃 </a></li>
<li><a href="#content_1_32"> 命中判定、回避判定 </a></li>
<li><a href="#content_1_33"> クリティカル(レイドのみ) </a></li></ul></li>
<li><a href="#content_1_34"> 状態異常（状態変化） </a></li>
<li><a href="#content_1_35"> バフ（強化）／デバフ（弱化） </a>
<ul class="list3 list-indent1"><li><a href="#content_1_36"> キャラクター対象「バフ／デバフ」 </a></li>
<li><a href="#content_1_37"> フィールド対象「バフ／デバフ」 </a></li>
<li><a href="#content_1_38"> 効果の重複について </a></li>
<li><a href="#content_1_39"> 効果の上書きについて </a></li>
<li><a href="#content_1_40"> バフ／デバフ一覧 </a></li>
<li><a href="#content_1_41"> 特殊状態 </a></li></ul></li>
<li><a href="#content_1_42"> 戦闘中における装備アイテムのアイコン表示 </a></li>
<li><a href="#content_1_43"> パラメータ強化の限界 </a></li>
<li><a href="#content_1_44"> 所属勢力 </a></li>
<li><a href="#content_1_45"> 属性 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_46"> 弱点効果 </a></li></ul></li>
<li><a href="#content_1_47"> 特殊属性 </a></li>
<li><a href="#content_1_48"> ダメージ補正 </a></li></ul></li>
<li><a href="#content_1_49"> クエストをクリアするための基本的な考え </a>
<ul class="list2 list-indent1"><li><a href="#content_1_50"> 優先出撃キャラクターに精鋭を配置する </a></li>
<li><a href="#content_1_51"> 前列と後列を意識する </a></li>
<li><a href="#content_1_52"> 固有効果や必殺技を把握する </a></li>
<li><a href="#content_1_53"> 戦線を守る </a></li></ul></li>
<li><a href="#content_1_54"> 基本戦術 </a>
<ul class="list2 list-indent1"><li><a href="#content_1_55"> 一番体力の少ない敵をロックする </a></li>
<li><a href="#content_1_56"> 必殺ゲージを持つ敵から倒す </a></li>
<li><a href="#content_1_57"> 状態異常を引き起こす敵を優先的に狙う </a></li>
<li><a href="#content_1_58"> スタミナを揃えない </a></li>
<li><a href="#content_1_59"> バフを使う </a></li>
<li><a href="#content_1_60"> 助っ人のゲージを見る </a></li></ul></li>
<li><a href="#content_1_61"> 発展的な戦術 </a>
<ul class="list2 list-indent1"><li><a href="#content_1_62"> 戦線を崩壊させないための考え方 </a></li>
<li><a href="#content_1_63"> 敵の出現方法の種類 </a>
<ul class="list3 list-indent1"><li><a href="#content_1_64"> ラッシュへの対応 </a></li></ul></li>
<li><a href="#content_1_65"> 戦線の立て直し </a></li></ul></li>
<li><a href="#content_1_66"> コメントフォーム </a></li></ul>
</div>
<br><br>
<h2 id="content_1_1">戦闘について   <span id="w4860f89"></span> </h2>
<p>手持ちのキャラクターを使用して戦闘を行います。<br>
基本的に戦闘は自動で出撃、自動で接敵、自動で攻撃と、ほぼフルオートで行われます。<br>
味方全員のスタミナが尽きるより前に全ての敵を倒せば勝利となります。</p>
<ul class="list1 list-indent1"><li>必殺技の発動も全てオートに設定すれば完全自動戦闘になります。</li>
<li>手動戦闘を行う場合は戦況を見て、適時必殺技を運用する形になりますが<br>
キャラ育成の進んでいない序盤の段階では、必殺技のチャージに相応の時間が必要になります。<br>
（戦力の育成が進むにつれ、必殺技を撃ちまくれるようになります）</li></ul>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td" style="background-color:white;"><img alt="戦闘画面.jpg" height="360" loading="lazy" src="/img/b902f1524767267d.jpg" title="戦闘画面.jpg" width="640"></td></tr>
</tbody></table></div></div>
<p>戦闘には制限時間(画面左上)があり、残り時間が無くなると戦闘敗北となります。<br>
また戦闘中、戦果を判定するタイミングが何回か存在します。(途中判定の無い戦闘も存在します)<br>
画面左端のバー(戦況ゲージ)がそれらを表しており、左の緑色ゲージは時間経過で上昇し、右の橙色ゲージは敵にダメージを与えると上昇します。<br>
左ゲージが砂時計マークのラインまで上昇した時点で右ゲージが砂時計のラインを通過していない場合その時点で戦闘敗北となります。<br>
あまり攻撃出来ていないと味方が全滅してなくても負けちゃうよ、ということです。⇒関連リンク：戦闘に勝てない時は？<br>
なお、クエストに失敗(全滅、タイムアップ、撤退問わず)しても、その時点までドロップしていた資金、宝箱、到達度に応じたEXPを獲得できます。</p>
<h4 id="content_1_2">戦闘速度の調整方法   <span id="p699c100"></span> </h4>
<p>画面左下の▶ボタンで戦闘速度を3段階(速度1～3)に切り替える事が可能です。<br>
<span style="background-color:#ffff99">▶ボタンが1か2段階の状態で<strong>Ctrlを押す</strong>と、押し続けている間だけ速度3(3倍速)に加速できるのでレイド戦にて手動戦闘する場合などに便利。</span><br>
また、<strong>Ctrl+Shiftの長押し</strong>で速度3+必殺アニメーション再生設定を「再生しない」状態にすることができます。</p>
<h4 id="content_1_3">戦闘の一時停止方法   <span id="u79fa323"></span> </h4>
<p>画面左下の「必殺設定」ボタンをクリックする事によって戦闘画面を一時停止状態にする事ができます。</p>
<h4 id="content_1_4">特定の敵をロックオンする方法   <span id="f5a8acf2"></span> </h4>
<p>対象の敵をワンクリックする事により、敵にロックマークが付き味方がその敵を集中して狙うようになります。<br>
（クリックで大丈夫です。マウスボタンを押し続ける必要はありません）<br>
⇒関連リンク：対象ロック</p>
<h4 id="content_1_5">特定のキャラのみを撤退させる方法   <span id="c0b55751"></span> </h4>
<p>対象キャラの顔アイコンを画面下方向に向けドラッグさせれば戦場から撤退し、後続のキャラと入れ替わります。<br>
戦線の崩壊によるもぐら叩き状態を防いだり、一部固有効果の早期発動を狙う際に使用します。<br>
⇒関連リンク：撤退</p>
<h4 id="content_1_6">必殺技の自動設定方法   <span id="pc7fadb5"></span> </h4>
<p>画面下のキャラクター顔アイコンを1クリックする事で、キャラが自動で必殺技を撃つようになります。<br>
（初期設定はクリックによる手動発動）<br>
画面左下の「全員AUTO」ボタンをonにする事によって、全キャラクターの必殺技が完全自動発動されるようになります。<br>
⇒関連リンク：必殺技</p>
<h4 id="content_2_0">必殺技の演出設定</h4>
<p>画面左下の必殺設定ボタンで必殺技のアニメーションの再生方法を設定することが出来ます。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">再生設定</th><th class="style_th">説明</th></tr>
</thead><tbody><tr><th class="style_th">全て再生</th><td class="style_td">全ての必殺技を通常再生します</td></tr>
<tr><th class="style_th">1日1度再生</th><td class="style_td">当日に再生されたキャラクターの必殺技をスキップします。</td></tr>
<tr><th class="style_th">初回のみ再生</th><td class="style_td">過去に再生されたキャラクターの必殺技をスキップします</td></tr>
<tr><th class="style_th">再生しない</th><td class="style_td">味方の全ての必殺技をスキップします</td></tr>
</tbody></table></div></div>
<h4 id="content_1_7">バトルをリトライしたい   <span id="v8426aed"></span> </h4>
<p>操作ミスやアクシデントによって予定外の敗北を迎えそうな場合には、<br>
戦闘の決着が着く前にブラウザのタブを閉じてゲームを開き直せば、その戦闘を無かった事にして再挑戦できます。<br>
（アプリ版の場合はアプリの強制終了）</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td">「再戦する」ボタンを選択します<br class="spacer">「キャンセル」ボタンを押した場合はST等を消費の上で敗北扱いとなります<br class="spacer"> <img alt="再戦画面.jpg" height="238" loading="lazy" src="/img/4c94fea17d437d41.jpg" title="再戦画面.jpg" width="423"></td></tr>
</tbody></table></div></div>
<h3 id="content_1_8">助っ人について   <span id="dbbcc2b5"></span> </h3>
<p>助っ人（他のプレイヤーが助っ人に設定しているキャラクター）を使用することができる。<br>
戦闘に行き詰まった際は気軽に利用して問題ない。<br>
一日の助っ人利用回数には上限があり、初期値では5回までとなっている。<br>
⇒関連リンク：助っ人として呼ぶのに適切なキャラクターを教えて</p>
<ul class="list1 list-indent1"><li><strong>使用回数について</strong>
<ul class="list2 list-indent1"><li>助っ人の使用回数は午前4時にリセットされる。</li>
<li>1日に使用できる助っ人の回数は初期は5回だがVIPランクにより増やすことが出来る。</li>
<li>助っ人を使い切った場合でもアイテム「4回転エテ公」を消費することで追加して助っ人を使用することができる。
<ul class="list3 list-indent1"><li>自軍戦力の整わないゲーム序盤のうちは、特に出し惜しみする事無く消費して問題ない。<br>
（アイテムの消費を警戒して進行が滞るより、早期攻略を進めて戦力を整えたほうがトータルでの効率は良くなる）</li></ul></li>
<li>助っ人の使用回数が「達成宝箱」のポイントを得る条件のひとつになっているので、無料分は毎日上限まで使っておくとよい。</li></ul></li></ul>
<ul class="list1 list-indent1"><li><strong>助っ人の装備について</strong>
<ul class="list2 list-indent1"><li>「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%8F%E3%83%8B%E3%83%BC%E3%82%B8%E3%83%83%E3%83%9D" rel="noopener" target="_blank">ハニージッポ</a>」など一部の装備は助っ人では効果を発揮せず、装備画面でロックされて表示される。</li>
<li>助っ人キャラの装備は助っ人プレイヤーが現在装備させているものがリアルタイムで反映される。</li></ul></li></ul>
<ul class="list1 list-indent1"><li><strong>助っ人の性能について</strong>
<ul class="list2 list-indent1"><li>自身のプレイヤーレベル以上のレベル150(☆1～☆5)までのキャラが出現する。(2023/11/29のアップデート)</li>
<li>プレイヤーレベル100以上の場合、出現するキャラのレベルは100～150で固定される。
<ul class="list3 list-indent1"><li>たとえ自身のレベルが低くても、プレイヤー人口の影響かレベル99以下の助っ人はほとんど表示されることがない。</li></ul></li></ul></li></ul>
<ul class="list1 list-indent1"><li><strong>その他</strong>
<ul class="list2 list-indent1"><li>助っ人はキャラアイコンをクリックして必殺技を不使用にすることは出来ず、ゲージが溜まればオートで必殺技を撃つ。</li>
<li>助っ人の出すダメージはイベントの最大ダメージボーナスの対象にならない。</li>
<li>助っ人はステージに設定されている出撃<strong>属性の制限を受けない</strong>。</li>
<li>自身の助っ人キャラの設定や、助っ人被使用回数は「キャラクター」の「助っ人設定」から確認可能。</li>
<li>ログインしたり戦闘(時短含む)を行うことで自身の設定した助っ人は借りる側のリストの先頭に並ぶようになる。
<ul class="list3 list-indent1"><li>時間帯により更新スピードが違い、夜や休日等のアクティブプレイヤーの多い時間帯はリストのキャラクターが流れやすい。</li></ul></li></ul></li></ul>

<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>助っ人関連の旧仕様</p>
</div><div class="rgn-content" style="display: none">
<p>助っ人関連の古い仕様</p>
<ul class="list1 list-indent1"><li>2021/12のアップデートで他のユーザーに自分の助っ人が使用された場合D2Pが獲得（上限月30ポイント）できるようになった。</li>
<li>自身の所持キャラクターの最大☆数までの助っ人キャラクターしか表示されない制限があった。(2022/12/21に撤廃)</li>
<li>助っ人リストに表示されるキャラは、自分のプレイヤーレベルの-2～+2の範囲のキャラクターレベルの助っ人キャラだった。(2023/11/29に仕様変更)</li>
<li>一度使用した助っ人キャラはしばらくの間は再度助っ人リストに出て来ないので、連続使用はできない。</li>
<li>2022/05のアップデートで時短戦闘をメインにするなどプレイスタイル次第では他のプレイヤーの助っ人リストに並びにくかった点を調整。
<ul class="list2 list-indent1"><li>2023/01/11のアップデートで表示されるキャラの選出アルゴリズムが調整され、開くたびに違う助っ人が表示されることが多くなった。</li></ul></li>
<li>2024/04/03のアップデートで使用した助っ人プレイヤーを同日には表示しない制限を撤廃。
</li></ul></div></div>
<h4 id="content_1_9">助っ人の選択方法   <span id="nd76e007"></span> </h4>
<p>助っ人を選択する際は、助っ人キャラの「<strong>名前の書かれた部分</strong>」をクリックする。<br>
顔アイコンをクリックした場合、助っ人の持つ必殺技や性能が表示される（選択は行われない）。<br>
レベルが高く、顔アイコンの上に並ぶ☆の数が多いほど性能は強化されている。<br>
自軍戦力が整わない段階では、敵に対して直接的な打撃を与える必殺技を持つ助っ人が助けになる。</p>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p><strong>助っ人選択画面のサンプルを開く</strong></p>
</div><div class="rgn-content" style="display: none">
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td" style="background-color:white;"><img alt="助っ人画面.jpg" height="310" loading="lazy" src="/img/029962dea670c4ab.jpg" title="助っ人画面.jpg" width="540"> <br class="spacer">助っ人アイコン右下に「助」の文字が入っているキャラは当該イベントの報酬ボーナスがUP <br class="spacer"> 赤アイコン→15%　オレンジアイコン→10%　緑アイコン→5%</td></tr>
</tbody></table></div></div>
</div></div>
<h4 id="content_1_10">助っ人の設定方法   <span id="tf440bb5"></span> </h4>
<p>自分の出した助っ人が他人に使用される事により、使用された回数に応じて翌月に一括でD2Pを獲得できる。</p>
<ul class="list1 list-indent1"><li><span>獲得量の上限は毎月30。毎月1日の4時に更新される。<br>
自身の出す助っ人の設定は<strong>「ホーム画面」→「キャラクター」→「助っ人設定」</strong>から行う。
</span><div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td"><img alt="ホーム_キャラクター.jpg" height="213" loading="lazy" src="/img/4d9f90dc8efbba97.jpg" title="ホーム_キャラクター.jpg" width="400"></td></tr>
</tbody></table></div></div></li></ul>
<ul class="list1 list-indent1"><li>安定して助っ人に選ばれやすいキャラクターの傾向
<ul class="list2 list-indent1"><li><a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%E4%B8%80%E8%A6%A7/%E9%96%8B%E5%82%AC%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88" rel="noopener" target="_blank" title="イベント一覧/開催イベント">開催中のイベント</a>のピックアップ対象SSRキャラ（イベント出撃メンバーに組み込むと報酬にボーナスが付くため）</li>
<li>Wドリル状態（<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%82%B9%E3%83%BC%E3%83%91%E3%83%BC%E3%83%89%E3%83%AA%E3%83%AB" rel="noopener" target="_blank" title="スーパードリル">ドリル</a>系装備を2本装備）の閃忍ツカサ（必殺技が覚醒されているとさらに採用率が上がる）</li>
<li>限界突破され高レベルの超昂閃忍ナリカなど攻略で使いやすいキャラ</li></ul></li></ul>
<h2 id="content_1_11">戦闘の基礎知識   <span id="ed5f3d74"></span> </h2>
<h3 id="content_1_12">各種パラメータ   <span id="s60c38ee"></span> </h3>
<p><strong>パラメータ画面例</strong><br>
<img alt="限界突破_ステータス説明用画面.png" height="244" loading="lazy" src="/img/fd4efbe99e68da4f.png" title="限界突破_ステータス説明用画面.png" width="480"></p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td" colspan="2" style="background-color:#CACAFF; text-align:left;"><strong>画面左側：レベルアップ や 限界突破 等に応じて成長するステータス</strong></td></tr>
<tr><th class="style_th">スタミナ</th><td class="style_td" style="text-align:left;">これが無くなるとキャラは撤退する。ヒットポイント。<br class="spacer">敵からダメージを受ける以外にも、ステージ毎に設定された消耗量によって自動的に減っていく。</td></tr>
<tr><th class="style_th">攻撃力/魔法力</th><td class="style_td" style="text-align:left;">物理攻撃タイプは攻撃力が、魔法攻撃タイプは魔法力が設定されている。<br class="spacer">両方設定されているキャラもいる（通常攻撃は物理判定・必殺技は魔法判定等のパターン）</td></tr>
<tr><th class="style_th">防御力/魔法抵抗力</th><td class="style_td" style="text-align:left;">防御力は物理攻撃の、魔法抵抗力は魔法攻撃の受けるダメージを減らす。レイドでは無意味。</td></tr>
<tr><td class="style_td" colspan="2" style="background-color:#CACAFF; text-align:left;"><strong>画面右側：ステータス固定：装備 と 覚醒強化 によってのみ上昇するステータス</strong></td></tr>
<tr><th class="style_th">命中力</th><td class="style_td" style="text-align:left;">通常攻撃の命中しやすさの目安となる。１００なら必中。レイドでは無意味。 <br class="spacer">仕様により、例えば値が40だからといって、40%しか命中しないという意味にはならない。</td></tr>
<tr><th class="style_th">回避力</th><td class="style_td" style="text-align:left;">どれだけ回避力が高くても敵の命中力が高いと回避できない。レイドでは無意味。</td></tr>
<tr><th class="style_th">連撃率</th><td class="style_td" style="text-align:left;">通常攻撃時に連続攻撃を行う確率。<br class="spacer">火力は上昇するが連続攻撃時はゲージの充填が行われず、必殺技の発動が遅くなるなどデメリットも大きい。</td></tr>
<tr><th class="style_th">反撃率</th><td class="style_td" style="text-align:left;">通常攻撃を受けた時に敵に反撃を行う確率。<br class="spacer">レイドでは無意味(効果は発動しているがレイドの仕様上無視して問題ない)</td></tr>
<tr><th class="style_th">スタン発動率</th><td class="style_td" style="text-align:left;">攻撃時に敵をスタン状態にするかどうかの目安となる。</td></tr>
<tr><th class="style_th">スタン抵抗率</th><td class="style_td" style="text-align:left;">攻撃を受けた時のスタン状態のなりやすさの目安となる。 <br class="spacer"><a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%82%B9%E3%82%BF%E3%83%B3%E5%B8%BD%E5%AD%90" rel="noopener" target="_blank" title="スタン帽子">装備</a>で簡単に防げるため気にする必要は無い。</td></tr>
<tr><th class="style_th">移動速度</th><td class="style_td" style="text-align:left;">キャラクターが出撃可能になって画面端から戦場に到着するまでの時間。</td></tr>
<tr><th class="style_th">出撃速度</th><td class="style_td" style="text-align:left;">キャラクターがNEXTから出撃可能になるまでの時間。</td></tr>
<tr><th class="style_th">行動速度</th><td class="style_td" style="text-align:left;">通常攻撃を行う頻度のこと。<strong>最重要。</strong> この値が遅いキャラほど戦闘で不利になる。<br class="spacer">最速のキャラで3秒。この値が6秒以上のキャラは非常に遅い。初期値では4秒となっているキャラが最も多い。<br class="spacer">3秒のキャラは、6秒のキャラが1回攻撃する間に2回弱攻撃できる事になる。</td></tr>
<tr><th class="style_th">必殺充填量</th><td class="style_td" style="text-align:left;">通常攻撃の度に増加する必殺技ゲージの量。<strong>重要。</strong><br class="spacer">その仕組み上、行動速度との相乗効果が非常に大きい。<br class="spacer">未強化状態の場合、RとSRは7.5%、SSRは10%のキャラが最も多い。<br class="spacer">10%未満だと必殺技の発動は目に見えて遅くなり、6%を切ると味方や装備の補助無しで単独で必殺技を撃つのは難しくなる。</td></tr>
</tbody></table></div></div>
<p>それぞれのステータスは「装備」「限界突破」「覚醒強化」「レベル上限UP」などで強化する事ができる。</p>
<h3 id="content_1_13">物理攻撃と魔法攻撃   <span id="c2852847"></span> </h3>
<p>物理攻撃なら攻撃力を、魔法攻撃なら魔法力を参照してダメージを与える。<br>
攻撃を受ける側も、防御力や物理耐性で物理ダメージを、魔法抵抗や魔法耐性で魔法ダメージを減らす。<br>
通常攻撃と必殺技の物理／魔法が一致しているキャラが大半だが、たまに通常攻撃が物理で必殺技が魔法のキャラもいる。通常が魔法で必殺が物理のキャラは今のところいない。</p>
<p>魔法攻撃の通常攻撃は命中が99で基本的に必中であるメリットと、ダメージが0.8倍になるデメリットがある。魔法攻撃の必殺技には0.8倍は適応されない。</p>
<p>ハニー系と呼ばれるハニワのような敵は、魔法ダメージと魔法キャラが使用した自身へのデバフと状態異常を無効にする。<br>
例外的にゴールデンハニーのみ、魔法ダメージを半減し、デバフと状態異常は無効にしない。<br>
<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%8F%E3%83%8B%E5%99%9B%E3%81%BF%E7%8E%8B%E5%AD%90" rel="noopener" target="_blank">ハニ噛み王子</a>という装備を持つと、この無効や半減を打ち消しつつ、更に魔法ダメージを1.1～2倍にすることができる。</p>
<h3 id="content_1_14">スタミナとダメージ   <span id="c9ece5df"></span> </h3>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td" style="background-color:white;"><img alt="スタミナゲージ.png" height="164" loading="lazy" src="/img/14fbb3e295fc5fcd.png" title="スタミナゲージ.png" width="164"></td><th class="style_th" style="text-align:left;">黄色部分……残りHP<br class="spacer">赤色部分……被ダメージ部分（ヒーラースキルで回復可能分）<br class="spacer">黒色部分……時間経過によるスタミナ消費分（回復不可能・一部例外あり）<br class="spacer"><br class="spacer">外周部分……必殺技ゲージ</th></tr>
</tbody></table></div></div>
<p>キャラクターにはスタミナがあり、キャラクターアイコンの黄色いバーがスタミナゲージになっている。<br><br>
スタミナは1秒経過するごとに減少していく。(減少量はステージごとに「スタミナ減少量 ○/sec」と表示されている)<br>
よって戦場に立つキャラクターは、たとえ敵からの攻撃がノーダメージであっても、最終的には時間経過により自動撤退する。<br>
（ただし超昂閃忍ナリカなど一部には固有効果により自動撤退適用外の例外キャラも存在する）</p>
<p><span style="color:red">時間経過により自然減少したスタミナは基本的に回復させる手段が無い</span>のでスタミナ最大値が減るのとほぼ同義である。(<strong>※</strong>こちらも一部例外あり)<br>
消費アイテムである「<strong><a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%8F%E3%83%8B%E3%83%BC%E3%82%B8%E3%83%83%E3%83%9D" rel="noopener" target="_blank">ハニージッポ</a></strong>」が効果を発揮した場合のみ、ゼロになったスタミナが1度だけ最大値まで回復する。<br>
キャラクターが敵の攻撃を受けるとスタミナゲージに赤い部分が出来るが、これがダメージである。この赤い部分だけを各キャラの固有効果や必殺技により回復することができる。<br><br>
自然減少＋ダメージによりスタミナゲージの黄色いバーが無くなってしまうと戦闘からキャラが離脱する。<br>
上述のように、たとえダメージを一切受けず自然減少だけでスタミナが0になっても戦闘から離脱してしまう。<br>
(スタミナが0になってもダメージを受けるまでは離脱しない固有効果を持ったキャラや超昂閃忍ナリカなどの例外を除き、全てのキャラは自然減少でいつか退場する運命にある)</p>
<p><strong>（※）</strong>……ビートプレジデント・シーラの必殺技や「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%81%8A%E8%8C%B6%E4%BC%9A%E3%82%BB%E3%83%83%E3%83%88" rel="noopener" target="_blank">お茶会セット</a>」の効果など一部に例外があるが非常に稀。</p>
<h3 id="content_1_15">出撃   <span id="oaa870bb"></span> </h3>
<p>画面右下に表示されているキャラクターは出撃準備中のキャラクターであり、<br>
逆時計回りの赤色のタイマーが一周してキャラクターアイコンがモノクロからカラー(GO!表示)になると出撃準備が完了し、<br>
フィールドに空きスペースがあれば自動で出撃を開始する。<br>
出撃開始後、画面右端から前列／後列の「戦闘可能位置」にキャラクターが移動し終わって初めて行動可能になる。<br>
この行動可能になった瞬間を固有効果などの説明文にある「出撃完了時」と呼ぶ。<br>
出撃準備時間は「出撃速度」、その後の移動時間を「移動速度」として各キャラクターごとにパラメータが設定されている。</p>
<p>出撃開始から行動可能になるまでの移動時間は時間経過によるスタミナ減少は発生しないが、敵の攻撃は容赦なく襲ってくる。<br>
自軍フィールドにキャラがいなくなり、出撃するキャラが移動中に敵から一方的に攻撃される状況のことを「モグラ叩き」と表現することがある。</p>
<h3 id="content_1_16">出撃可能人数   <span id="je8a3f65"></span> </h3>
<p>メインクエスト各ステージにおける出撃可能人数は30人が標準となっている。<br>
属性制限ステージなど、条件によっては変動するケースがある。<br>
初期状態では、自軍の手持ちユニットの中からランダムで出撃が行われる為、戦力バランスに著しい偏りが発生する。<br>
これを防ぐため<strong><span style="background-color:#ffff99">下記の「</span></strong><a href="#zc22c974"><span style="background-color:#ffff99">優先設定</span></a><strong><span style="background-color:#ffff99">」機能を利用し、自軍の出撃メンバーを指定する</span></strong>事が必須となる。</p>
<p>戦闘開始時における自軍ユニットの初期配置数は2～4人。<br>
こちらも同様に、条件によって変動するケースがある。（最低人数は1人から）<br>
また、デイリークエストの場合は5人での出撃となる。</p>
<p>ステージ毎の出撃人数・初期配置等に関しては「メインクエスト」から確認する事ができる。</p>
<p>助っ人は開始時の配置人数の制限には含まれないため、一般的なメインクエストにおける最大初期配置人数は自軍4人+助っ人1人の5人となる。<br>
また捕獲対象キャラは、初期出撃人数の制限に含まれる。</p>
<h3 id="content_1_17">優先出撃設定   <span id="zc22c974"></span> </h3>
<p>自軍メンバーの出撃順番を制御するための機能です。<br>
<strong>「ホーム画面」→「キャラクター」→「優先出撃設定」</strong><br>
の順に画面を選択する事で設定画面が開きます。</p>
<p><img alt="優先出撃画面.jpg" height="216" loading="lazy" src="/img/d233c436a68f3c5f.jpg" title="優先出撃画面.jpg" width="384"></p>
<p>自軍主力メンバーを優先出撃に指定する事により戦力の偏りを防ぎます。<br>
所持するキャラが3人増える毎に、優先出撃キャラに設定できる人数が1人増えます。<br>
優先1は5人、優先2は15人が上限で、最大20人を優先設定することが可能です。<br>
またアイテム「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%98%E3%83%93%E3%83%BC%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%A1%E3%83%B3" rel="noopener" target="_blank">ヘビースターメン</a>」を装備したキャラは優先１よりも早く最優先で出撃対象となります。<br>
プレイヤー装備の「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E8%B6%85%E6%98%82%E4%BA%BA%E3%83%AD%E3%83%83%E3%82%AF" rel="noopener" target="_blank">超昂人ロック</a>」があればロックしたキャラクターを完全出撃不可(最大50人まで)に設定できる。</p>
<h4 id="content_1_18">出撃パーティーの固定方法   <span id="zcacc4cb"></span> </h4>
<dl class="list1 list-indent1"><dt>5麺方式</dt>
<dd>　①最初に出撃させたいメンバー5人に「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%98%E3%83%93%E3%83%BC%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%A1%E3%83%B3" rel="noopener" target="_blank">ヘビースターメン</a>」を装備させる<br>
　②「優先1」出撃メンバーとして5人を指定する<br>
　③「優先2」出撃メンバーとして5人を指定する<br>
上記の方法で最大3パーティー15人までの出撃編成を確実に固定できる。<br>
出撃順番は 麺メンバー → 優先1 → 優先2<br>
「麺メンバー」や「優先2」を6人以上設定した場合は、指定された6人以上がランダムな順番で出撃する。<br>
（このケースで優先1や優先2に<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?DENAI" rel="noopener" target="_blank">DENAI</a>を装備させても優先効果は無視されDENAIの効果で上書きされる<br>
　出撃順序は 麺→優先1→優先2→ランダムメンバー→DENAI となる）</dd></dl>
<dl class="list1 list-indent1"><dt>35麺（多麺）方式</dt>
<dd>主にレイドバトルにおいて使用される、出撃メンバーの固定方法。<br>
　①出撃人数50人のうちの35人に「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%98%E3%83%93%E3%83%BC%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%A1%E3%83%B3" rel="noopener" target="_blank">ヘビースターメン</a>」を装備させる<br>
　②「優先1」出撃メンバーとして5人を指定する<br>
　③「優先2」出撃メンバーとして10人を指定する<br>
　④ ③で指定した10人のうち後半で出撃させたい5人に「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?DENAI" rel="noopener" target="_blank">DENAI</a>」を装備させる<br>
この方法によって出撃メンバー50人すべてを固定する事ができる。<br>
出撃順番は、<br>
最初に「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%98%E3%83%93%E3%83%BC%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%A1%E3%83%B3" rel="noopener" target="_blank">ヘビースターメン</a>」を装備した35人（麺メンバー）がランダムに出撃する。<br>
麺メンバーの出撃後に「優先1」の5人が<br>
優先1 の出撃後に「優先2」の5人が<br>
優先2 の出撃後に「優先2 + DENAI」メンバー5人が出撃する。<br>
ここでは例としてレイド（50人編成）を挙げたが、優先1+2 合計15人以外の余分な出撃枠を麺メンバーで埋めれば、あらゆる戦闘において出撃メンバーを固定する事ができる。<br>
（麺を使用して出撃メンバーを人数上限にまで固定した場合にのみ限って出撃順序が 優先2 → 優先2+DENAI という形に固定される）</dd></dl>
<h3 id="content_1_19">前列／後列と近距離攻撃／遠距離攻撃   <span id="t72c7616"></span> </h3>
<p><strong>注：ユーザー間では近距離攻撃キャラのことを前衛、遠距離攻撃キャラのことを後衛と表すことがあります。</strong><br>
戦闘中にキャラクターがフィールドに配置される枠は、前列3枠／後列3枠 の合計6枠。<br>
ただし、フィールドの最大同時出撃数は５人までとなっており、<br>
「前２ ＋ 後３」もしくは「前３＋後２」の組み合わせとなる。</p>
<p>前列配置キャラは、ヘイトの初期値が増加しており敵からの攻撃を受けやすくなる。<br>
後列に配置したキャラは、敵によっては反撃を受けないメリットがある。</p>
<p><img alt="陣形画面.jpg" height="688" loading="lazy" src="/img/8b7e7263c1e345e6.jpg" title="陣形画面.jpg" width="608"></p>
<p>各キャラクターにはステータスとして「近距離攻撃／遠距離攻撃」が設定されており、近距離攻撃のキャラは前列にしか立つ事ができない。<br>
遠距離攻撃のキャラは、前列と後列の両方に立つ事ができる。（遠距離攻撃キャラが前列に立つ事がありえる）<br>
ただし、遠距離攻撃キャラは傾向として撃たれ弱いタイプが多い。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td"><img alt="前列後列アイコン.jpg" height="168" loading="lazy" src="/img/a8ecc5d939079615.jpg" title="前列後列アイコン.jpg" width="282"></td></tr>
</tbody></table></div></div>
<p>''キャラクターアイコンの左上の欠けた部分が<span style="background-color:yellow">黄色</span>なら近距離攻撃、<span style="color:blue">青色</span>なら遠距離攻撃を表している。<br>
戦闘中の表示は装備「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E7%B8%9B%E3%82%8A%E4%BA%80%E7%94%B2" rel="noopener" target="_blank">縛り亀甲</a>」の状況が反映する。（近距離攻撃キャラでも「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E7%B8%9B%E3%82%8A%E4%BA%80%E7%94%B2" rel="noopener" target="_blank">縛り亀甲</a>」装備中は青くなる）</p>
<ul class="list1 list-indent1"><li><span><strong>近距離攻撃のキャラクターは前列にしか出撃することができない</strong>。<br>
この制限により、近距離攻撃キャラは最大でも同時に3人までしかフィールドに出撃する事はできない。
</span><ul class="list2 list-indent1"><li>例外的に「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E7%B8%9B%E3%82%8A%E4%BA%80%E7%94%B2" rel="noopener" target="_blank">縛り亀甲</a>」を装備した場合のみ、近距離攻撃キャラクターであっても後列への出撃が可能となる。</li>
<li>近距離攻撃キャラを後列に配置しても攻撃力低下などのペナルティは発生しない。</li></ul></li>
<li><span>前列3人の枠が既に埋まっている状態で、更に追加で近距離攻撃キャラが出撃しようとすると、5人出撃していなくても<br>
「配置スペースなし」となり出撃することができず出撃待機中の状態となる。<span style="color:red">少ない人数で戦闘をすることになり、不利</span>。
</span><ul class="list2 list-indent1"><li>近距離攻撃キャラに上述の「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E7%B8%9B%E3%82%8A%E4%BA%80%E7%94%B2" rel="noopener" target="_blank">縛り亀甲</a>」を装備させる事によって対策可能。</li></ul></li>
<li><strong>遠距離攻撃のキャラクターは、前列にも出撃することが可能</strong>。</li>
<li>遠距離攻撃キャラは後列から優先して配置され、後列が既に3枠埋まっている状態で新たに出撃する場合のみ前列に配置される。<br>
5人遠距離攻撃キャラで順番に出撃する場合、前列0人/後列3人→前列1人/後列3人→前列2人/後列3人という順番で配置される。</li>
<li>後列に空きがなくて前列に配置されてしまった遠距離攻撃キャラは、後列に空きができれば自動で後列に移動する。<br>
ただし、後列に空きができた際に「出撃準備完了状態の遠距離攻撃キャラ」がいる場合は、そのキャラが空いた後列に配置され前列のキャラはその場所から動かない。</li>
<li>前列に遠距離攻撃キャラが2人いる状態で後列に空きができた場合、後列に移動するキャラは出撃順ではない不明な法則で毎回決まっている。</li></ul>
<p>なお、敵側にも前列／後列の概念はあり、味方の必殺技や固有効果で前列／後列を対象にしたものが存在する。</p>
<h3 id="content_1_20">撤退   <span id="se539a5d"></span> </h3>
<p>キャラクターのスタミナが0になる前にキャラクターのアイコンを下にスワイプすることで個別に撤退させることが出来る。<br>
出撃準備中(アイコンがモノクロ)のときに撤退させることは出来ないが、出撃待機中(アイコンにGO!表示)のキャラクターに対しては可能。<br>
2021年9月のアップデートにより必殺技演出中に「個別撤退」が可能となった。<br>
ただし撤退は必殺技を撃った後に行われるため、必殺技中の撤退操作で必殺技のダメージに撤退時の固有効果を載せるといったことはできない。<br>
画面右上の「全軍撤退」を押すと戦闘をその時点で終了し、敗北扱いとなる。</p>
<h3 id="content_1_21">必殺技と固有効果   <span id="i630b518"></span> </h3>
<p>各キャラクターは、それぞれ1つづつ「必殺技」と「固有効果」を持っており、<br>
その内容が各キャラクターの個性付となっている。<br>
覚醒強化を行うことにより、性能を大幅に強化する事ができる。</p>
<ul class="list1 list-indent1"><li>関連リンク：キャラクターの役割分け</li></ul>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td">必殺技・固有効果　確認画面<br class="spacer"> <img alt="キャラ画面_必殺・固有.jpg" height="353" loading="lazy" src="/img/627c4c743fba57f3.jpg" title="キャラ画面_必殺・固有.jpg" width="440"></td></tr>
</tbody></table></div></div>
<h4 id="content_1_22">必殺技   <span id="xaf0df4c"></span> </h4>
<p>必殺技は、戦闘中にキャラクターアイコン外周ゲージがMAXになる事で任意に発動可能が可能となる。<br>
発動方法は、アイコンのクリック。もしくはオート。（設定で切り替え可能）<br>
ゲージがMAX状態ではない時にキャラクターアイコンをクリックすると、キャラごとの必殺技のオート発動設定をON/OFF出来る。<br>
画面左下の「全員AUTO」ボタンでキャラクター全員のAUTO使用のON/OFFも可能。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td" style="background-color:white;"><img alt="スタミナゲージ.png" height="124" loading="lazy" src="/img/14fbb3e295fc5fcd.png" title="スタミナゲージ.png" width="124"></td><th class="style_th">外周部分……必殺技ゲージ</th></tr>
</tbody></table></div></div>
<p>赤いゲージに先行して黄色に点滅している部分はステータスの必殺充填量を表している。<br>
通常攻撃を行うと必殺充填量分の必殺技ゲージが増加する。<br>
必殺技の発動後に攻撃周期はリセットされる。<br>
味方キャラクターがスタン中は必殺技ゲージは溜まらない。<br>
攻撃をミスしても命中した時と同様にゲージは増える。反撃、連撃中の追加攻撃ではゲージは増えない。</p>
<p>攻撃タイプの必殺技は次の3タイプに分類され、例外もあるが概ねこのような特徴を持つ。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">タイプ</th><th class="style_th">攻撃対象</th><th class="style_th">ダメージ倍率<br class="spacer">(覚醒強化時)</th></tr>
</thead><tbody><tr><td class="style_td" style="text-align:center;">敵単体</td><td class="style_td" style="text-align:center;">1体</td><td class="style_td" style="text-align:center;">6倍<br class="spacer">(9倍)</td></tr>
<tr><td class="style_td" style="text-align:center;">敵横一列</td><td class="style_td" style="text-align:center;">最大3体<br class="spacer">(前列1体+後列2体)</td><td class="style_td" style="text-align:center;">4倍<br class="spacer">(6倍)</td></tr>
<tr><td class="style_td" style="text-align:center;">敵全体</td><td class="style_td" style="text-align:center;">最大5体<br class="spacer">(敵の「かばう」無効)</td><td class="style_td" style="text-align:center;">2倍<br class="spacer">(4倍)</td></tr>
</tbody></table></div></div>
<h4 id="content_1_23">敵の必殺技   <span id="e26a1ddf"></span> </h4>
<p>2021/12/22のアップデートで敵キャラクターの必殺ゲージが可視化された。<br>
長い体力バーの右横にランプがあり、黒(無点灯)→<span style="color:blue">青</span>→<span style="color:green">緑</span>→<span style="color:orange">橙</span>→<span style="color:red">赤</span>と進行していき、最後の赤ランプが点灯すると必殺技を撃たれる。<br>
ただし、必ず黒から始まるわけではなく、出現時にいずれかの色のランプが点灯している敵も居り出現と同時に必殺技を撃たれるケースも存在する。<br>
ランプが無い敵は必殺技を撃ってくることは無い。<br>
敵の必殺技は撃ち放題というわけでは無いらしく、何度か撃つとゲージが消失するケースがある。</p>
<h4 id="content_1_24">必殺技ゲージの計算式   <span id="s7b2c19d"></span> </h4>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>必殺技ゲージの計算方法</p>
</div><div class="rgn-content" style="display: none">
<p>・キャラクターが通常攻撃を行うと必殺充填量％分増加する。(増加するタイミングは攻撃モーションが終わった瞬間)<br>
・必殺技ゲージは1%/secで自然増加していく。<br>
・攻撃モーション中は攻撃周期は停止する。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td">必殺技ゲージがMAXまで溜まる時間 = 攻撃回数 × (行動速度 + 攻撃モーション時間) + α - 初期配置ボーナス<br class="spacer">α &gt; 行動速度 の場合 = (攻撃回数 + 1) × (行動速度 + 攻撃モーション時間) - 初期配置ボーナス</td></tr>
<tr><td class="style_td">攻撃回数 = (100 - 必殺ゲージ初期値) / (必殺充填量 + 行動速度 + 攻撃モーション時間) ※小数点以下四捨五入</td></tr>
<tr><td class="style_td">α = 100 - 必殺ゲージ初期値 - 必殺充填量 × 攻撃回数 - (行動速度 + 攻撃モーション時間) × 攻撃回数</td></tr>
</tbody></table></div></div>
<ul class="list1 list-indent1"><li>攻撃モーション時間：各キャラごとの攻撃モーションにかかる時間（ツカサ0.5秒、デュエル0.65秒程度など）</li>
<li>必殺ゲージ初期値：ドリル系、ノノノ固有、イザナエル固有などの合計値<br>
アルゴルの必殺技(+30%)を途中で撃つと想定する場合も初期値として扱って計算してよい。(対象キャラのゲージが70%になる前に撃つものとする)</li>
<li>α：最後の攻撃からゲージMAXまでにかかる自然増加の秒数<br>
ただし、α ＞ 行動速度 の場合は攻撃回数を+1してMAXまでの時間を計算し、αは除く。(自然増加でMAXになる前に次の攻撃が先にくるため)</li>
<li>初期配置ボーナス(期待値) = 行動速度 × 0.5　※初期配置の場合<br>
初期配置キャラには初期配置人数によって枠ごとに決まる80%から20%の攻撃周期ゲージから始まる。<br>
初期配置人数によらず1キャラあたり期待値50%になっている。<br>
後から出てくる場合は0、助っ人は70～80%、助っ人を呼んだ場合のそれ以外のキャラの期待値は30～42%程度に下がる。</li></ul>
<p><span style="color:blue">▼例：行動速度6sec 必殺充填量3.5 のキャラクター(閃忍ツカサ)でスーパードリルLV5(初期値+40)を装備して途中出撃した場合</span></p>
<p>攻撃回数 = (100 - 必殺ゲージ初期値40) / (必殺充填量3.5 + 行動速度6 + 攻撃モーション時間0.5) ※小数点以下四捨五入<br>
60 / 10 = 6<br>
攻撃回数は6回。割り切れない場合は小数点以下は切り捨てる。</p>
<p>必殺技ゲージがMAXまで溜まる時間 = 攻撃回数6 × (行動速度6 + 攻撃モーション時間0.5) + α- 初期配置ボーナス0<br>
6 × 6.5 + α - 0 = 39 + α<br>
溜まる時間は39秒 + α。</p>
<p>α = 100 - 必殺ゲージ初期値40 - 必殺充填量3.5 × 攻撃回数6 - (行動速度6 + 攻撃モーション時間0.5) × 攻撃回数6<br>
α ＝０<br><br>
計算上は6回目の攻撃と同時、39秒ジャストでゲージがMAXになるはずである。<br>
実際の計測でも39秒過ぎ、6回目の攻撃が終わるとすぐにゲージがMAXになるので、概ね正しいと分かる。</p>
<ul class="list1 list-indent1"><li>ゲージがMAXになるまでの時間が計算と違うのは何故か？
<ul class="list2 list-indent1"><li>計算に使用した攻撃モーション時間が正確ではない</li>
<li>攻撃のタイミングで敵フィールドに攻撃対象が存在しない時は攻撃を行わずに攻撃周期が進んでしまいゲージが増加しない</li>
<li>魔女ユウガや狂の秋道姫路といった通常攻撃の代わりに固有効果が発動するタイプの場合はその分ゲージが増加しない</li>
<li>連撃が発生して攻撃モーション時間が延びた</li>
<li>敵の攻撃でスタンした</li>
<li>速度バフ/速度フィールドバフの影響</li>
<li>初期配置ボーナスの影響</li>
<li>敵に通常攻撃を高頻度で当て続けるとずっと食らいモーションのままで攻撃されないことがあり(エロコマンダーが再現しやすい)、<br>
味方の場合そこまで攻撃が集中されるケースがまず無いがもし起こればその場合は必殺技ゲージも遅延すると想像できる。<br>
etc.</li></ul></li></ul>
</div></div>
<h4 id="content_1_25">必殺技発動までの主な時間   <span id="y9cefe91"></span> </h4>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>早見</p>
</div><div class="rgn-content" style="display: none">
<p>あくまで目安として参考程度に</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td">必殺充填量</td><td class="style_td">10</td><td class="style_td">10.5</td><td class="style_td">11</td><td class="style_td">11.5</td><td class="style_td">12</td><td class="style_td">12.5</td><td class="style_td">13</td><td class="style_td">13.5</td><td class="style_td">14</td><td class="style_td">14.5</td><td class="style_td">15</td><td class="style_td"></td></tr>
<tr><td class="style_td">行動速度1.5</td><td class="style_td">18(9)</td><td class="style_td">16(8)</td><td class="style_td">16(8)</td><td class="style_td">16(8)</td><td class="style_td">16(8)</td><td class="style_td">14(7)</td><td class="style_td">14(7)</td><td class="style_td">14(7)</td><td class="style_td">14(7)</td><td class="style_td">14(7)</td><td class="style_td">12(6)</td><td class="style_td">※14.8から6回攻撃で技発動</td></tr>
</tbody></table></div></div>
<p>()の中は攻撃回数<br>
※攻撃モーション時間0.5。ゲージ配布、連撃、反撃は無視。</p>
</div></div>
<h4 id="content_1_26">固有効果   <span id="nfe1f895"></span> </h4>
<p>パッシブスキル以外に出撃完了時、撤退時、一定量のスタミナ減少時など様々なタイミングで効果が発動する。<br>
「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%8F%E3%83%8B%E3%83%BC%E3%82%B8%E3%83%83%E3%83%9D" rel="noopener" target="_blank">ハニージッポ</a>」を装備し発動条件を再度満たしても1回のみと限定されているものは発動できない。(必殺技も同様)<br>
なお、撤退時に発動するタイプの固有効果は出撃待機中(GO!表示)のキャラを手動で撤退させても効果を発揮する。<br>
戦闘開始直後の味方キャラの固有効果は出撃順番通りに左側のキャラアイコンから右側に向かって発動する。</p>
<p>2023/4/26のアップデートにより、<br>
戦闘において、同じ値に影響を及ぼす固有効果が敵と味方で同時に発生した場合、処理の順番が敵→味方、だったものを、味方→敵、に変更となった。</p>
<h3 id="content_1_27">対象ロック   <span id="of77bce3"></span> </h3>
<p>敵キャラクターのアイコンをクリックすることでその敵キャラクターを集中して攻撃させることができる。<br>
もう1度クリックするとロックが解除される。<br>
敵キャラクターの中には「かばう」能力を持っているキャラクターがおり、その場合は「かばう」が優先される。</p>
<h3 id="content_1_28">攻撃、連撃、反撃、命中・回避判定、クリティカル   <span id="x12b240a"></span> </h3>
<h4 id="content_1_29">攻撃   <span id="t9e8068c"></span> </h4>
<p>キャラクターのアイコンの周りを回っている☆が一周するとキャラクターが攻撃する。(☆が一周してもそのタイミングで攻撃可能な敵がいないと攻撃せずに次の周回が始まる)<br>
自分の必殺技を発動すると☆は初期位置に戻る。（☆がもう少しで一周しそうなタイミングでも攻撃せずに次の周回が始まる）<br>
1回の攻撃ごとにかかる時間はキャラクターごとに設定された行動速度の値を参照し、速度UP・DOWNのバフ・デバフで変化する。<br>
攻撃モーション中は攻撃周期の☆は停止するのでステータスの行動速度より実際の行動速度は遅くなる。(連撃発生中は攻撃モーションが長くなるので特に遅延する)<br>
攻撃は物理と魔法の2タイプがあり、それぞれ攻撃力と防御力が設定されている。<br>
魔法タイプの攻撃は必中だが与えるダメージが20%減衰(ただし必殺技は表記どおりの倍率で減衰しない)する。<br>
初期出撃のキャラは左から順に☆の開始位置が先になっており(初期出撃人数が多いほど早い)、最初の一撃に限り早く攻撃出来る。</p>
<h4 id="content_1_30">連撃   <span id="o9b0b77f"></span> </h4>
<p>通常攻撃時、キャラクターごとに設定された連撃率を参照し、連続で攻撃することがある。<br>
連撃するごとに与えるダメージが20%減衰するが、<del>下限は30％になるので、40％からの減衰は20％ではなく10％となる。(80%⇒60%⇒40%⇒30%⇒30%⇒…)</del><br>
ダメージ減衰は<strong>70%</strong>まで。(2021-03-24のアップデートで変更)<br>
必殺充填量による必殺ゲージの増加、命中判定、スタン発動率の判定、レイドバトルでのクリティカルは連撃では発生しない。</p>
<ul class="list1 list-indent1"><li><span>通常攻撃及び連撃中は行動ゲージが進まないので連撃が発生しすぎると行動周期が遅くなり結果、<strong>必殺技の発動が遅くなる</strong>。
</span><ul class="list2 list-indent1"><li>キャラが攻撃中に敵味方問わず誰かが必殺技を発動すると、連撃含めた攻撃モーションが終わるまで戦闘そのものが一時停止しこのデメリットを踏み倒す。<br>
この挙動は必殺が飛び交う戦闘では勝手に発生しているが、手動操作で狙って発生させることもできる。<br>
この現象による硬直時間の短縮期待値は硬直時間の二乗に比例する。つまり連撃に特化したキャラほど連撃率を延ばす事による恩恵が大きい。</li></ul></li></ul>
<ul class="list1 list-indent1"><li>連撃は発生する度、連撃率を10%ずつ減らして再判定している。※ゲーム内に説明はなく高連撃率キャラの行動約500回分からの推定<br>
この仕様は固有効果等で1回は必ず連撃する効果を持つキャラでも連撃1回目から適用される。（必ず連撃するキャラの連撃率が50%の場合、連撃1回目は確定、連撃2回目の発生率は40%)</li></ul>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>連撃期待値計算表(10%刻み)</p>
</div><div class="rgn-content" style="display: none">
<p>連撃期待値計算表(10%刻み)<br>
・水色セルがその連撃数に到達できる確率。<br>
・2026/2時点での最大連撃率は連撃率70%キャラにコンボ+<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%81%E3%83%A7%E3%82%B3%E3%83%83%E3%83%88GPT" rel="noopener" target="_blank">チョコットGPT</a>を装備した150%。必ず6連撃する。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th" style="text-align:right;">連撃数</th><th class="style_th" style="text-align:right;">1</th><th class="style_th" style="text-align:right;">2</th><th class="style_th" style="text-align:right;">3</th><th class="style_th" style="text-align:right;">4</th><th class="style_th" style="text-align:right;">5</th><th class="style_th" style="text-align:right;">6</th><th class="style_th" style="text-align:right;">7</th><th class="style_th" style="text-align:right;">8</th><th class="style_th" style="text-align:right;">9</th><th class="style_th" style="text-align:right;">10</th><th class="style_th" style="text-align:right;">11</th><th class="style_th" style="text-align:right;">12</th><th class="style_th" style="text-align:right;">13</th><th class="style_th" style="text-align:right;">14</th><th class="style_th" style="text-align:right;">15</th><th class="style_th" style="text-align:right;">連撃期待値</th></tr>
</thead><tbody><tr><th class="style_th" style="text-align:right;">連撃率10%</th><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">10%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.1回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率20%</th><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">20%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.22回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率30%</th><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">30%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.36回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率40%</th><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">40%</td><td class="style_td" style="background-color:Cyan; text-align:right;">12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.54回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率50%</th><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">50%</td><td class="style_td" style="background-color:Cyan; text-align:right;">20%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.2%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.77回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率60%</th><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">60%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30%</td><td class="style_td" style="background-color:Cyan; text-align:right;">12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">3.6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.08%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.06回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率70%</th><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">70%</td><td class="style_td" style="background-color:Cyan; text-align:right;">42%</td><td class="style_td" style="background-color:Cyan; text-align:right;">21%</td><td class="style_td" style="background-color:Cyan; text-align:right;">8.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.52%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.51%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.06%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.44回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率80%</th><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">80%</td><td class="style_td" style="background-color:Cyan; text-align:right;">56%</td><td class="style_td" style="background-color:Cyan; text-align:right;">33.6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">16.8%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.02%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.41%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.95回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率90%</th><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率100%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">3.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率110%</th><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">4.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率120%</th><td class="style_td" style="text-align:right;">120%</td><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72.01%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">5.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率130%</th><td class="style_td" style="text-align:right;">130%</td><td class="style_td" style="text-align:right;">120%</td><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.61%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率140%</th><td class="style_td" style="text-align:right;">140%</td><td class="style_td" style="text-align:right;">130%</td><td class="style_td" style="text-align:right;">120%</td><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">7.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">連撃率150%</th><td class="style_td" style="text-align:right;">150%</td><td class="style_td" style="text-align:right;">140%</td><td class="style_td" style="text-align:right;">130%</td><td class="style_td" style="text-align:right;">120%</td><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">8.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率30%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">20%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.22回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率40%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.36回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率50%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">40%</td><td class="style_td" style="background-color:Cyan; text-align:right;">12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.54回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率60%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50%</td><td class="style_td" style="background-color:Cyan; text-align:right;">20%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.2%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.77回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率70%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">60%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30%</td><td class="style_td" style="background-color:Cyan; text-align:right;">12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">3.6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.08%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.06回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率80%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">70%</td><td class="style_td" style="background-color:Cyan; text-align:right;">42%</td><td class="style_td" style="background-color:Cyan; text-align:right;">21%</td><td class="style_td" style="background-color:Cyan; text-align:right;">8.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.52%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.51%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.06%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.44回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率90%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">70%</td><td class="style_td" style="background-color:Cyan; text-align:right;">42%</td><td class="style_td" style="background-color:Cyan; text-align:right;">21%</td><td class="style_td" style="background-color:Cyan; text-align:right;">8.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.52%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.51%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.06%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">3.44回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率100%</th><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">80%</td><td class="style_td" style="background-color:Cyan; text-align:right;">56%</td><td class="style_td" style="background-color:Cyan; text-align:right;">33.6%</td><td class="style_td" style="background-color:Cyan; text-align:right;">16.8%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">2.02%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.41%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">3.95回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率110%</th><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">4.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率120%</th><td class="style_td" style="text-align:right;">120%</td><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90.01%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72.01%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.41%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">5.66回</td></tr>
<tr><th class="style_th" style="text-align:right;">必ず連撃+連撃率130%</th><td class="style_td" style="text-align:right;">130%</td><td class="style_td" style="text-align:right;">120%</td><td class="style_td" style="text-align:right;">110%</td><td class="style_td" style="text-align:right;">100%</td><td class="style_td" style="text-align:right;">90%</td><td class="style_td" style="text-align:right;">80%</td><td class="style_td" style="text-align:right;">70%</td><td class="style_td" style="text-align:right;">60%</td><td class="style_td" style="text-align:right;">50%</td><td class="style_td" style="text-align:right;">40%</td><td class="style_td" style="text-align:right;">30%</td><td class="style_td" style="text-align:right;">20%</td><td class="style_td" style="text-align:right;">10%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;">0%</td><td class="style_td" style="text-align:right;"></td></tr>
<tr><td class="style_td" style="text-align:right;">←×↑</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">100%</td><td class="style_td" style="background-color:Cyan; text-align:right;">90%</td><td class="style_td" style="background-color:Cyan; text-align:right;">72%</td><td class="style_td" style="background-color:Cyan; text-align:right;">50.4%</td><td class="style_td" style="background-color:Cyan; text-align:right;">30.24%</td><td class="style_td" style="background-color:Cyan; text-align:right;">15.12%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.05%</td><td class="style_td" style="background-color:Cyan; text-align:right;">1.82%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.37%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0.04%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">0%</td><td class="style_td" style="background-color:Cyan; text-align:right;">6.66回</td></tr>
</tbody></table></div></div>
</div></div>
<ul class="list1 list-indent1"><li>連撃はメインクエストとレイドで価値が若干変わってくる。
<ul class="list2 list-indent1"><li>メインクエストにおいては一撃で倒せない相手を連撃で倒せることがあり、反撃封じたり敵の行動機会を奪ったりとメリットの方が大きい。
<ul class="list3 list-indent1"><li>全体必殺アタッカーは必殺で数を倒すのが仕事なので装備枠が空いていても[コンボの謎]]を持たせるのは避けよう。</li></ul></li>
<li>レイドにおいては敵が倒れないので上記のメリットがなく、連撃のせいでFEVER中に必殺が間に合わない状況ではデメリットになる。
<ul class="list3 list-indent1"><li>ただし大半のアタッカーは十分に育成すればFEVER中に撃てる必殺回数は同じ(2回)になる。必殺回数が同じならダメージ差は連撃で付くので最終的にはメリット効果になる。<br>
※低連撃率によってFEVER時間外の必殺が1回増えても、FEVER中の連撃3回と等価なのでほぼ意味がない。</li>
<li>ステータス以外に必殺を早める要因を持つ一部のキャラはFEVER中の必殺3回目が間に合うことがある。そういったキャラは連撃率は低い方が都合が良くゲーム内でも低めに設定されていることが多い。</li>
<li>極端に連撃に特化したキャラは20回以上の連撃も可能で必殺2回のキャラのダメージを超えてくる。</li></ul></li></ul></li>
<li>最終的に火力が出ればいいアタッカーと違い、サポート向きのキャラにとってはデメリットの方が大きい。</li></ul>
<h4 id="content_1_31">反撃   <span id="l4fbeaf9"></span> </h4>
<p>キャラクターが敵キャラクターから攻撃を受けたときに反撃することがある。<br>
確率はキャラクターごとに設定された反撃率を参照し、必中でダメージ量は通常攻撃の50%。<br>
敵キャラクターも反撃を行い、必中でダメージ量半減なのは同じ。<br>
味方の後列に配置されたキャラクターは敵によっては反撃を受けない場合がある。<br>
敵の後列に対しては味方の反撃はしっかり行うので心配はいらない。</p>
<h4 id="content_1_32">命中判定、回避判定   <span id="i371c4dd"></span> </h4>
<pre>Q.回避力が高いのに敵の攻撃に当たる。</pre>
<pre>A.通常攻撃は、まず攻撃側の命中力を元に命中判定を行います。
自軍が防御側の場合のみ、
攻撃側の命中力よりも回避力が高ければ、
攻撃側の命中力が２５％減少した状態で命中判定が行われます。
命中判定が成功すると回避判定は行わず、攻撃は命中します。
命中判定で失敗した場合、次に防御側の回避力を元に回避判定を
行います。
回避判定で失敗した場合、攻撃は命中します。
なお、通常攻撃が魔法であれば、
固有効果で「攻撃を全て回避」効果がある場合を除き、
必ず命中します。
必殺技は命中判定が行われず、必ず命中します。（公式Ｑ＆Ａより）</pre>
<p>※2025/9/3より味方回避力が敵命中力より高い場合、敵命中力を25%減らして(×0.75して)判定する仕様が追加された。</p>
<p>敵の命中判定が失敗しない限り、回避判定が行われない仕様のため味方キャラの回避力を100以上にしただけでは敵の物理通常攻撃をすべて回避することはできない。<br>
(100%-敵命中力[%])×味方回避力[%]が実際の回避確率となる。<br>
回避によって敵からのダメージを減らすためには回避アップ効果と命中ダウン効果の併用が重要。<br>
なお反撃は必中であるため、回避によって味方全員のダメージを0にし続けることはゲーム仕様上困難。</p>
<h4 id="content_1_33">クリティカル(レイドのみ)   <span id="sea9a3cb"></span> </h4>
<p>レイドでは命中バフを付与することで効果量％でクリティカル判定が発生するようになる。<br>
対象は通常攻撃及び必殺技ダメージで1.25倍のダメージとなる。連撃はクリティカルしない。<br>
ダメージ表示の色が通常の黄色から濃いオレンジ色に変わり大きくなるのが特徴。（レイド以外クエストでの属性一致ダメージと同演出）</p>
<h3 id="content_1_34">状態異常（状態変化）   <span id="p1f733ee"></span> </h3>
<p>状態異常には以下のものがあります。<br>
※各種状態変化のアイコンは、キャラクターアイコン内に表示されます。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">状態</th><th class="style_th">アイコン</th><th class="style_th">説明</th></tr>
</thead><tbody><tr><td class="style_td">毒</td><td class="style_td" style="text-align:center;"><img alt="毒アイコン.png" height="26" loading="lazy" src="/img/82e8bc00aca03970.png" title="毒アイコン.png" width="31"></td><td class="style_td">毒状態になると、一定時間(約10秒)スタミナの自然減少量が２倍になります。</td></tr>
<tr><td class="style_td">魅了</td><td class="style_td" style="text-align:center;"><img alt="魅了アイコン.png" height="21" loading="lazy" src="/img/11eb9bddf7d859ee.png" title="魅了アイコン.png" width="32"></td><td class="style_td">魅了状態になると、一定時間(約20秒)自軍に攻撃を行うようになり必殺技が使用不能になります。<br class="spacer">撤退は可能なので、危険と思えば撤退させるのも有効です。</td></tr>
<tr><td class="style_td">スタン</td><td class="style_td" style="text-align:center;"><img alt="スタンアイコン.png" height="21" loading="lazy" src="/img/ce0183c3c390f7cc.png" title="スタンアイコン.png" width="33"></td><td class="style_td">スタン状態になると、一定時間(約10秒)行動不能となり、必ず敵からの攻撃が命中するようになります。<br class="spacer">必殺技ゲージも溜まらなくなり、固有効果による自動回復なども発動しません。</td></tr>
<tr><td class="style_td">呪縛</td><td class="style_td" style="text-align:center;"><img alt="呪縛アイコン.png" height="25" loading="lazy" src="/img/1670fe5097a85d7d.png" title="呪縛アイコン.png" width="25"></td><td class="style_td">呪縛状態になると、一定時間(約15秒)必殺充填量が０となります。<br class="spacer">（必殺技ゲージの自然増加量は変化しません）</td></tr>
</tbody></table></div></div>
<ul class="list1 list-indent1"><li><span>超昂大戦においては<strong>「状態異常」と「デバフ効果」は別種の物として扱われる</strong>
</span><ul class="list2 list-indent1"><li>必殺技や固有効果の「状態異常解除」と「デバフ解除」の効果は分けて考える必要がある。</li></ul></li>
<li>スタンの発生判定がどうなっているかは不明だが、レイドボスの模擬戦で検証すると味方のスタン発動率がボスのスタン抵抗率以下の場合はスタンにならないことなどから<br>
「攻撃側スタン発動率 - 防御側スタン抵抗率＝スタン発生率」となっている可能性が高い。</li>
<li>毒・魅了・呪縛にいたっては発動率・抵抗率のステータスも無いため、やはり発生判定は不明だが、こちらもレイドボスの模擬戦で検証すると<br>
基本的に通常時の発動率および抵抗率は0%であり、単純に「その攻撃の発動率(必殺技など)＝発生率」となっている可能性が高い。</li>
<li>敵に毒状態を付与する行動は存在しない。<br>
敵にスタンと魅了をかけた時は味方と同様の効果が発生する。<br>
敵に呪縛をかけた時は、敵の必殺技ゲージの増加速度が7～8割程度減少する。</li></ul>
<h3 id="content_1_35">バフ（強化）／デバフ（弱化）   <span id="q5bef4f0"></span> </h3>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td" style="background-color:white;"><img alt="バフ・デバフ図.jpg" height="360" loading="lazy" src="/img/d034b10556b8639f.jpg" title="バフ・デバフ図.jpg" width="640"></td></tr>
</tbody></table></div></div>
<p>バフは対象にプラスの効果を<br>
デバフは対象にマイナスの効果を与えます。<br>
必殺技や固有効果の発動で付与されます。</p>
<ul class="list1 list-indent1"><li>例：味方に速度アップの効果がかかっている → 味方への速度バフ<br>
　　味方に速度ダウンの効果がかかっている → 味方への速度デバフ<br>
　　敵に速度アップの効果がかかっている → 敵への速度バフ<br>
　　敵に速度ダウンの効果がかかっている → 敵への速度デバフ</li></ul>
<p>また、超昂大戦においては<span style="color:red"><strong>デバフと状態異常を分けて考えます</strong></span>。</p>
<ul class="list1 list-indent1"><li>状態異常：スタンや毒などキャラクターに発生する特殊な症状</li>
<li>デバフ：攻撃ダウンや速度ダウンなどキャラクターのステータスに負の効果を与える効果</li></ul>
<p>状態異常はデバフの一種では無く、あくまでデバフとは別のカテゴリとして扱われるため、<br>
必殺技や固有効果の「状態異常解除」と「デバフ解除」の効果は分けて考える必要があります。</p>
<p>加えて、超昂大戦独自要素としてバフとデバフには<br>
「キャラクター対象」の物と「フィールド対象」の物の2種類があります。</p>
<h4 id="content_1_36">キャラクター対象「バフ／デバフ」   <span id="o6779dba"></span> </h4>
<p>各キャラクターを対象として各種効果（バフはプラス効果、デバフはマイナス効果）を及ぼします。<br>
効果は様々で、味方キャラクターや敵キャラクターの固有効果や必殺技などで付与されます。</p>
<h4 id="content_1_37">フィールド対象「バフ／デバフ」   <span id="d064ac47"></span> </h4>
<p>戦闘時、対象の味方および敵フィールドに対し行われるバフ／デバフです。<br>
キャラクター対象のバフ／デバフと違い、一定時間、敵や出撃キャラクターが入れ替わっても対象フィールドにいる全員に影響を及ぼすので効果は大きいです。</p>
<h4 id="content_1_38">効果の重複について   <span id="m52f05ab"></span> </h4>
<p><span style="color:red"><strong>(重要)「<span style="background-color:#ffff99">キャラクター対象</span>」のバフ・デバフと「<span style="background-color:#ffff99">フィールド対象</span>」のバフ・デバフは同じ効果の物の同士で数値が加算されます</strong></span>。<br>
反対に「キャラクター対象」の「バフ・デバフ」同士、「フィールド」対処の「バフ・デバフ」同士の場合は、同じ効果の物であっても<strong>効果は重複しません</strong>。最も効果量の大きい物のみが適用されます。</p>
<ul class="list1 list-indent1"><li>同一効果で効果量と効果時間の異なるキャラクター対象バフが重複した場合の例
</li></ul>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">経過時間</th><th class="style_th">0秒後</th><th class="style_th">10秒後</th><th class="style_th">20秒後</th><th class="style_th">30秒後</th><th class="style_th">40秒後</th></tr>
</thead><tbody><tr><th class="style_th">効果量40%<br class="spacer">効果時間20秒<br class="spacer">の場合</th><td class="style_td">40%</td><td class="style_td">40%</td><td class="style_td">40%</td><td class="style_td">0%</td><td class="style_td">0%</td></tr>
<tr><th class="style_th">効果量30%<br class="spacer">効果時間30秒<br class="spacer">の場合</th><td class="style_td"><del>30</del>%</td><td class="style_td"><del>30</del>%</td><td class="style_td"><del>30</del>%</td><td class="style_td">30%</td><td class="style_td">0%</td></tr>
<tr><th class="style_th">実際の効果量</th><td class="style_td">40%</td><td class="style_td">40%</td><td class="style_td">40%</td><td class="style_td">30%</td><td class="style_td">0%</td></tr>
</tbody></table></div></div>
<p>（例：効果が重複した場合、効果量の多い方しか効果は得られないが共存はしている。<br>
先に40%アップが切れた時点から残り時間分だけ30%アップの効果が得られる）</p>
<h4 id="content_1_39">効果の上書きについて   <span id="m487b5b7"></span> </h4>
<p>同一の対象に対して、効果が対になるバフ・デバフ（例：速度アップと速度ダウン）が付与された場合、<br>
<span style="color:red"><strong>(重要)後から付与された効果が先に付与されていた効果を一方的に上書きします</strong></span>。<br>
対になるバフとデバフの間で数値の相殺が行われることはありません。<br>
この処理は敵味方に関係ありません。つまり<span style="color:red">敵にかけられたデバフを味方のバフで上書きできます</span>。(逆も有り得ます)<br>
フィールド対象の場合であっても処理は同様です。</p>
<h4 id="content_1_40">バフ／デバフ一覧   <span id="e40e8eda"></span> </h4>
<ul class="list1 list-indent1"><li>▼バフ／デバフには以下のものがあります。(レイドでは違う効果を発揮するものがあります)
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">バフ／デバフ名</th><th class="style_th">アイコン</th><th class="style_th">説明</th></tr>
</thead><tbody><tr><td class="style_td">攻撃</td><td class="style_td" style="text-align:center;"><img alt="攻撃アイコン.png" height="23" loading="lazy" src="/img/54ad51d80a3caaf0.png" title="攻撃アイコン.png" width="44"></td><td class="style_td">攻撃力／魔法力が変化する</td></tr>
<tr><td class="style_td">防御</td><td class="style_td" style="text-align:center;"><img alt="防御アイコン.png" height="22" loading="lazy" src="/img/8699148caac19041.png" title="防御アイコン.png" width="44"></td><td class="style_td">防御力／魔法抵抗力が変化する</td></tr>
<tr><td class="style_td">命中</td><td class="style_td" style="text-align:center;"><img alt="命中アイコン.png" height="21" loading="lazy" src="/img/192443d7592f925f.png" title="命中アイコン.png" width="44"></td><td class="style_td">命中力が変化する</td></tr>
<tr><td class="style_td">回避</td><td class="style_td" style="text-align:center;"><img alt="回避アイコン.png" height="21" loading="lazy" src="/img/7cb067d9cbdc3d7b.png" title="回避アイコン.png" width="44"></td><td class="style_td">回避力が変化する</td></tr>
<tr><td class="style_td">速度</td><td class="style_td" style="text-align:center;"><img alt="速度アイコン.png" height="20" loading="lazy" src="/img/2720f7c6bf4ddc8b.png" title="速度アイコン.png" width="44"></td><td class="style_td">行動速度が変化する（フィールドが対象の場合、移動速度と出撃速度にも影響する）<br class="spacer">必殺技ゲージの自然増加量（通常は１秒ごとに１％ずつ）が変化する</td></tr>
<tr><td class="style_td">与ダメージ（与ダメ）</td><td class="style_td" style="text-align:center;"><img alt="最終ダメージアイコン.png" height="24" loading="lazy" src="/img/7b128cc4e2b4f080.png" title="最終ダメージアイコン.png" width="44"></td><td class="style_td">最終ダメージが変化する</td></tr>
<tr><td class="style_td">スタン抵抗率</td><td class="style_td" style="text-align:center;"><img alt="スタン抵抗率アイコン.png" height="21" loading="lazy" src="/img/752ebf1c5b2a4d31.png" title="スタン抵抗率アイコン.png" width="44"></td><td class="style_td">スタン抵抗率が変化する</td></tr>
<tr><td class="style_td">ヘイト</td><td class="style_td" style="text-align:center;"><img alt="ヘイトアイコン_2.png" height="21" loading="lazy" src="/img/be697ac4fb12df44.png" title="ヘイトアイコン_2.png" width="48"></td><td class="style_td">ヘイトが増減する（増加がターゲティング、減少が物陰に隠れる）<br class="spacer">状態変化中はヘイト値が最大、最小の数値に固定される</td></tr>
</tbody></table></div></div></li></ul>
<p>※各種アイコンはキャラクター対象のバフ／デバフはキャラクターアイコン内に、フィールドバフ／デバフは画面上側のFIELD部に表示されます。<br>
※ヘイトは公式ヘルプではバフ／デバフと特殊状態には数えられていません。</p>
<h4 id="content_1_41">特殊状態   <span id="rdca1cee"></span> </h4>
<p>戦闘時、対象に影響を及ぼす効果です。</p>
<ul class="list1 list-indent1"><li>▼以下のものは「特殊状態」と呼ばれます。(バフ消しやデバフ消しの効果には影響されません)
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">特殊状態名</th><th class="style_th">アイコン</th><th class="style_th">説明</th></tr>
</thead><tbody><tr><td class="style_td">回復</td><td class="style_td" style="text-align:center;"><img alt="回復アイコン.png" height="24" loading="lazy" src="/img/b85b092cd898c306.png" title="回復アイコン.png" width="23"></td><td class="style_td">毎秒ダメージが回復する</td></tr>
<tr><td class="style_td">継続ダメージ</td><td class="style_td" style="text-align:center;"><img alt="継続ダメージアイコン.png" height="21" loading="lazy" src="/img/f2b8ae8773c48d60.png" title="継続ダメージアイコン.png" width="30"></td><td class="style_td">毎秒ダメージが発生する</td></tr>
<tr><td class="style_td">時間停止(フィールド専用)</td><td class="style_td" style="text-align:center;"><img alt="時間停止アイコン.png" height="24" loading="lazy" src="/img/b4356a18eacb75ab.png" title="時間停止アイコン.png" width="25"></td><td class="style_td">対象フィールドの時間が停止する</td></tr>
</tbody></table></div></div></li></ul>
<h3 id="content_1_42">戦闘中における装備アイテムのアイコン表示   <span id="f2be69c3"></span> </h3>
<p>装備していると状態変化やバフ／デバフと同じくキャラクターアイコン内にアイコンが表示される装備アイテムが存在します。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">装備アイテム名</th><th class="style_th">アイコン</th><th class="style_th">説明</th></tr>
</thead><tbody><tr><td class="style_td"><a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%8F%E3%83%8B%E3%83%BC%E3%82%B8%E3%83%83%E3%83%9D" rel="noopener" target="_blank">ハニージッポ</a></td><td class="style_td" style="text-align:center;"><img alt="ハニージッポ_アイコン.png" height="23" loading="lazy" src="/img/9d4e94603c60dc97.png" title="ハニージッポ_アイコン.png" width="23"></td><td class="style_td">戦闘不能になると全快する</td></tr>
</tbody></table></div></div>
<h3 id="content_1_43">パラメータ強化の限界   <span id="v4c9ca4a"></span> </h3>
<p>キャラクターの各種パラメータは覚醒強化によって強化することが可能ですが、<br>
下記のパラメータは装備や覚醒での強化に限界があります。</p>
<p>・物理ダメージ軽減：最大８５％まで<br>
・魔法ダメージ軽減：最大８５％まで<br>
・行動速度：最小１．５secまで<br>
・必殺充填量：最大２０％まで</p>
<p>※戦闘中のバフやフィーバーによる速度上昇といった強化には、こちらの数値は適用外となります。</p>
<h3 id="content_1_44">所属勢力   <span id="i581bc26"></span> </h3>
<p>ゲーム内のプレイアブルキャラクターは全て以下の勢力のうちのどこか1つに所属します。</p>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><thead><tr><th class="style_th">区分</th><th class="style_th">勢力名</th><th class="style_th">紋章</th><th class="style_th">説明</th></tr>
</thead><tbody><tr><td class="style_td" rowspan="2" style="text-align:center;">戦士</td><td class="style_td" style="text-align:center;">戦士(異界)</td><td class="style_td" style="text-align:center;"><img alt="nolink" height="51" loading="lazy" src="/img/4002d2a4a2fc4dfb.png" title="nolink" width="100"></td><td class="style_td" style="text-align:left;">ダイビートにのみ所属する戦士のうち、異界から召喚された者たちの勢力。<br class="spacer">『超昂天使エスカレイヤー』が出典の勢力も含まれる。<br class="spacer">コラボキャラの大半が所属する。</td></tr>
<tr><td class="style_td" style="text-align:center;">戦士(現界)</td><td class="style_td" style="text-align:center;"><img alt="nolink" height="57" loading="lazy" src="/img/170ab31d64c3a008.png" title="nolink" width="100"></td><td class="style_td" style="text-align:left;">ダイビートにのみ所属する戦士のうち、異界から召喚されていない者たちの勢力。<br class="spacer">現地登用組という意味では神騎(地上)に近い。</td></tr>
<tr><td class="style_td" rowspan="2" style="text-align:center;">閃忍</td><td class="style_td" style="text-align:center;">閃忍(想破)</td><td class="style_td" style="text-align:center;"><img alt="nolink" height="100" loading="lazy" src="/img/f4e492bce015b394.png" title="nolink" width="100"></td><td class="style_td" style="text-align:left;">『超昂閃忍ハルカ』が出典の忍者(閃忍)の勢力。<br class="spacer">組織としての正式名称は「想破上弦衆」</td></tr>
<tr><td class="style_td" style="text-align:center;">閃忍(久世)</td><td class="style_td" style="text-align:center;"><img alt="nolink" height="100" loading="lazy" src="/img/7635d016b06f09f6.png" title="nolink" width="100"></td><td class="style_td" style="text-align:left;">超昂大戦オリジナルの閃忍の勢力。<br class="spacer">組織としての正式名称は「久世上弦衆」</td></tr>
<tr><td class="style_td" rowspan="2" style="text-align:center;">神騎</td><td class="style_td" style="text-align:center;">神騎(天界)</td><td class="style_td" rowspan="2" style="text-align:center;"><img alt="nolink" height="100" loading="lazy" src="/img/d20ee90cafe4a288.png" title="nolink" width="100"></td><td class="style_td" style="text-align:left;">『超昂神騎エクシール』が出典の天使(神騎)の勢力。</td></tr>
<tr><td class="style_td" style="text-align:center;">神騎(地上)</td><td class="style_td" style="text-align:left;">人間の神騎の勢力だが、天界由来と別組織という訳では無い。</td></tr>
<tr><td class="style_td" colspan="2" style="text-align:center;">魔女</td><td class="style_td" style="text-align:center;"><img alt="nolink" height="100" loading="lazy" src="/img/40e434e921b0efde.png" title="nolink" width="100"></td><td class="style_td" style="text-align:left;">超昂大戦オリジナルの魔女の勢力。</td></tr>
</tbody></table></div></div>
<p><span style="font-size:15px;display:inline-block;line-height:130%;text-indent:0px"><span style="color:black; background-color:#dfeefe"><strong>所属勢力のゲーム中の特徴</strong></span></span><br>
所属する勢力によってキャラクターの能力傾向が違ったり、特殊な能力があったりする事はありません。<br>
これら勢力分けは、主にイベントやレイド等バトルコンテンツにおける特効勢力の区分として使用されます。<br>
また、一部に特定の勢力を指定して効果を発動する、各種バフ効果を持つキャラクターが存在します。</p>
<ul class="list1 list-indent1"><li>例：エスカレイヤー・閃忍ハルカ・神騎エクシールの各キャラが持つ固有効果（レジェンドバフ）などが該当します</li></ul>
<p>イベント特効勢力や必殺技・固有効果の効果対象として指定される範囲は、<br>
大まか区分である「戦士」「閃忍」「神騎」「魔女」の4区分である場合と、<br>
各勢力をより細かく分けた7分類である場合の両方のケースがあります。</p>
<p>現在、味方側の勢力区分が戦闘処理時における相性判定に使用される事はありません。</p>
<ul class="list1 list-indent1"><li>例：閃忍勢力のみがダメージアップしたり、被ダメ増加が発生するようなタイプの敵は存在しない</li></ul>
<p>また、特定の勢力のみが出撃可能、もしくは出撃不可能なコンテンツも存在しません。<br>
出撃制限を受ける場合があるのは下記の属性要素となります。</p>
<h3 id="content_1_45">属性   <span id="mfefa30d"></span> </h3>
<p><img alt="属性.png" height="143" loading="lazy" src="/img/898bf3550d16a918.png" title="属性.png" width="426"><br>
ゲーム内には「太陽」「月」「星」3つの属性が存在する。<br>
全てのキャラクターは、必ずこの3つの属性のうちのどれか1つを持っている。<br>
キャラクターアイコンの背景色で属性を判別することが可能。<br>
ただし、一般のゲームに存在するような属性の相克による複雑なダメージ増減のシステムは存在しない。<br>
（3すくみ要素等は無い）</p>
<p>敵キャラクターは一部のみが属性を持っており、一般的な敵は全て属性を持たない「属性無し」キャラとなっている。<br>
属性持ちの敵キャラクターは、HPバー左に属性アイコンが付与されているため、視覚的に判別する事が可能である。<br>
（HPバーにアイコンのついてない一般的な敵は全て属性無しである）</p>
<p>属性の一致するキャラで攻撃を加えると、与ダメージが1.2倍に増加する（被ダメージも上がるかどうかは不明）<br>
ダメージ表示の色が通常の黄色から濃いオレンジ色に変わるため視覚的に確認できる（レイドバトルでのクリティカルと同演出）<br>
また、属性の一致しないキャラクターで攻撃しても、特にペナルティ等は発生しない。<br>
ゲーム内においては、属性制限ステージに遭遇しない限り、あまり意識される事の無い要素となっている。</p>
<p>キャラクターの属性は、アイテム「チェーイングガム」などによって、後から入れ替える事も可能である。<br>
「ビートスター・マリナ」など一部のキャラクターは、属性の変更によって必殺技の性能が変化する。<br>
「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E6%88%A6%E9%83%A8%E3%83%A6%E3%82%AD%E3%82%BF%E3%82%AB" rel="noopener" target="_blank">戦部ユキタカ</a>」等の一部サポーターは、特定の属性のキャラクターのみを性能アップする特性を持っている。<br>
プレイヤー装備の「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E5%A4%AA%E9%99%BD%E3%81%AE%E3%83%88%E3%82%A6" rel="noopener" target="_blank">太陽のトウ</a>」「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E6%9C%88%E3%81%AE%E3%82%A6%E3%82%B5%E3%82%AE" rel="noopener" target="_blank">月のウサギ</a>」「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E6%98%9F%E3%81%AE%E3%82%AB%E3%83%BC%E3%83%95%E3%82%A3%E3%83%BC" rel="noopener" target="_blank">星のカーフィー</a>」でそれぞれの属性キャラの与ダメージがアップする。</p>
<h4 id="content_1_46">弱点効果   <span id="c91c0faa"></span> </h4>
<p>上記の「太陽」「月」「星」とは異なり、一部敵キャラクターには<br>
装備「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%82%B4%E3%83%96%E3%82%B9%E3%83%AC%E3%83%BC" rel="noopener" target="_blank">ゴブスレー</a>」「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%95%E3%83%BC%E3%83%9E%E3%83%B3%E3%82%AD%E3%83%A9%E3%83%BC" rel="noopener" target="_blank">フーマンキラー</a>」「<a class="source-link" data-mtime="" href="https://escalationheroines.wikiru.jp/?%E3%83%8C%E3%83%B3%E3%82%B8%E3%83%A3%E3%82%B9%E3%83%97%E3%83%AC%E3%83%BC" rel="noopener" target="_blank">ヌンジャスプレー</a>」および「神騎ベラトリクス」等の一部キャラの固有効果によって、弱点効果と呼ばれる特徴が付与される。<br>
これら装備キャラ及び、固有効果持ちのキャラからの攻撃によって、対象となる敵に与えるダメージが1.2倍に増加する。<br>
ただし、上記の属性一致による与ダメージの上昇と効果は重複しない。</p>
<h3 id="content_1_47">特殊属性   <span id="h9d0d66f"></span> </h3>
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td"><img alt="特殊属性確認画面.jpg" height="235" loading="lazy" src="/img/710e36cdebb897bd.jpg" title="特殊属性確認画面.jpg" width="400"></td></tr>
</tbody></table></div></div>
<p>上記「太陽」「月」「星」とも「弱点特性」とも異なる、一部のキャラクターだけが持つ特殊な属性。<br>
特殊属性の付与は、主にそのキャラが排出される限定ガチャのシーズンイベントに起因する。<br>
例えば、バレンタインガチャから排出されたキャラには「バレンタイン属性」が、フェスガチャから排出されたキャラには「超昂属性」といったように、<br>
各イベントに応じた特殊属性が付与されているケースが多い。<br>
（ただしシーズンイベントに起因しないメガネ属性なども存在する）</p>
<p>ゲーム内に存在する特殊属性の一覧は下記ページより確認する事ができる。</p>
<ul class="list1 list-indent1"><li>関連ページ：特殊属性一覧</li></ul>
<div class="rgn-container" style=" position:relative; padding-left:35px; margin-bottom: 1em; "><div class="rgn-button" style=" display: flex; align-items: center; justify-content: center; cursor:pointer; height:26px; left:0; position:absolute; top:0; width:26px; "><svg class="plus-icon" style="display: block" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96l0 320c0 17.7 14.3 32 32 32l320 0c17.7 0 32-14.3 32-32l0-320c0-17.7-14.3-32-32-32L64 64zM0 96C0 60.7 28.7 32 64 32l320 0c35.3 0 64 28.7 64 64l0 320c0 35.3-28.7 64-64 64L64 480c-35.3 0-64-28.7-64-64L0 96zM208 352l0-80-80 0c-8.8 0-16-7.2-16-16s7.2-16 16-16l80 0 0-80c0-8.8 7.2-16 16-16s16 7.2 16 16l0 80 80 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-80 0 0 80c0 8.8-7.2 16-16 16s-16-7.2-16-16z" fill="currentColor"></path></svg><svg class="minus-icon" style="display: none" viewbox="0 0 448 512"><path d="M64 64C46.3 64 32 78.3 32 96V416c0 17.7 14.3 32 32 32H416c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32H64zM0 96C0 60.7 28.7 32 64 32H416c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM128 256c0-8.8 7.2-16 16-16H304c8.8 0 16 7.2 16 16s-7.2 16-16 16H144c-8.8 0-16-7.2-16-16z" fill="currentColor"></path></svg></div><div class="rgn-description" style="display: block"><p>特殊属性確認画面を開く</p>
</div><div class="rgn-content" style="display: none">
<div class="ie5"><div class="table-scroll"><table border="0" cellspacing="1" class="style_table"><tbody><tr><td class="style_td">特殊属性確認画面<br class="spacer"> <img alt="特殊属性表示画面.jpg" height="249" loading="lazy" src="/img/348282d52f8846a2.jpg" title="特殊属性表示画面.jpg" width="424"></td></tr>
</tbody></table></div></div>
</div></div>
<p>現在、特殊属性は、主にキャラのバフ能力の発動トリガーとなっている事が多い。<br>
例として「真夏のハルカ」は、同じ「真夏属性」を持つキャラからバフ効果を得る事が出来、<br>
また「ハロウィンニコール」は、同じ「ハロウィン属性」を持つキャラの火力をアップする事が可能である等、<br>
同一の「特殊属性」キャラを集中運用する事によって、プラス効果をもたらす必殺技や固有効果が複数存在する。<br>
特殊属性が、敵との攻防において相性判定に使用されるようなケースは存在していない。</p>
<h3 id="content_1_48">ダメージ補正   <span id="ldc7facd"></span> </h3>
<p>弱点効果(属性一致)：120%<br>
反撃：50%<br>
連撃：70%　(2021-03-24のアップデートで変更)</p>
<h2 id="content_1_49">クエストをクリアするための基本的な考え   <span id="u3f3655b"></span> </h2>
<h3 id="content_1_50">優先出撃キャラクターに精鋭を配置する   <span id="n46d2a8d"></span> </h3>
<p>制限時間内に一定数の敵を倒せないとボーダーとなり、戦闘に敗北となってしまう。<br>
よって、最初に精鋭を出撃させて敵の撃破数を稼いでおくこととなる。</p>
<h3 id="content_1_51">前列と後列を意識する   <span id="o78274b9"></span> </h3>
<p>近距離攻撃のキャラは前列に3名までしか出撃できないため、最大人数の5名が場にいられるように、後列に遠距離攻撃のキャラを2名以上は配置するようにする。<br>
画面右下の出撃準備中のキャラクターが近距離攻撃か遠距離攻撃か(キャラクターアイコン左上が<span style="background-color:yellow">黄色</span>なら近距離攻撃、<span style="color:blue">青色</span>なら遠距離攻撃)を見て、<br>
前列が詰まっている場合は撤退させることも必要になる。そうしないと後続が出てこられない。</p>
<p>↓前列が詰まっているので、スタミナが余っているもののビートバイカー・マッハを撤退させて後続を出すようにする。<br>
（※この場合はバフが乗っているので悩むところではある。）<br>
<img alt="前衛詰まり.jpg" height="427" loading="lazy" src="/img/bd41a7f23182d5b8.jpg" title="前衛詰まり.jpg" width="750"></p>
<h3 id="content_1_52">固有効果や必殺技を把握する   <span id="a5f915eb"></span> </h3>
<p>固有効果や必殺技によりキャラクターにバフ(強化)をかけたり、敵キャラにデバフ(弱化)をかけることが可能なキャラクターが存在する。<br>
固有効果を考えてキャラを優先出撃させたり、スタミナが少なくても残す場合がある。</p>
<h3 id="content_1_53">戦線を守る   <span id="j62e8295"></span> </h3>
<p><strong>重要な考え方</strong>。<br>
人数が少なくなると少ない人数で複数の敵の攻撃を受けることになる。</p>
<p>出撃は1人ずつしかできないため</p>
<p>フィールド上のキャラクターが敵から集中攻撃を受けて撤退<br>
↓<br>
新しく出撃したキャラクターが出撃時間(行動できない)に敵から攻撃を受ける<br>
↓<br>
行動可能になったときにはスタミナが少なく、また敵から攻撃を受けて撤退<br>
↓<br>
以下ループ</p>
<p>という負のスパイラルに陥ることになる。これを防ぐことが重要。</p>
<h2 id="content_1_54">基本戦術   <span id="ed5f3d74"></span> </h2>
<p>クエストをクリアするための基本戦術について</p>
<h3 id="content_1_55">一番体力の少ない敵をロックする   <span id="m991ab08"></span> </h3>
<p>RPGの基本でもあるが、敵の頭数を減らすことでダメージを減らすことができる。<br>
一番体力が低い敵から優先して撃破すること。<br>
<img alt="体力の低い敵をロックする.jpg" height="422" loading="lazy" src="/img/e4463f53f7b5dfe7.jpg" title="体力の低い敵をロックする.jpg" width="750"></p>
<h3 id="content_1_56">必殺ゲージを持つ敵から倒す   <span id="o69a9869"></span> </h3>
<p><a href="#e26a1ddf">必殺ゲージのランプ</a>がある雑魚敵は時間経過で必殺技を撃ってくる。<br>
普段は意識せずとも防げるが、固い相手や敵が逐次投入されるラッシュ時には食らいやすい。<br>
特にラッシュ時は敵前列が倒したそばから投入され後列の敵を放置しがちになるので、ロックを使って必殺技の前に撃破したい。<br>
<img alt="必殺ゲージを持つ敵から倒す.png" height="422" loading="lazy" src="/img/89f71b9f00c6870c.png" title="必殺ゲージを持つ敵から倒す.png" width="750"><br>
↑ゲージが赤くなったら必殺技を撃たれる寸前だ。こうなる前にさっさと倒してしまおう。</p>
<h3 id="content_1_57">状態異常を引き起こす敵を優先的に狙う   <span id="w5b89336"></span> </h3>
<p>雑魚敵の中で最も厄介なのが<a href="#p1f733ee">状態異常の魅了</a>を引き起こすパピヨン系（蛾）の敵。<br>
魅了は閃忍ニャンコなどの固有効果で無効に出来るメンバーを入れる以外には防御手段がない上に魅了されてしまったキャラは手動で撤退させるくらいしか対処法が無い。<br>
（一応、六の法杖セラフィールの固有効果や魔女レイヴンの必殺技などで解除することは可能）<br>
画面から目を離していたら攻撃力の高いキャラが魅了されて壊滅していた・・・という事態を引き起こすことがある。<br>
パピヨンが出現したら即ロックして優先的に攻撃するのが安全だ。</p>
<p><img alt="状態異常を引き起こす敵を優先的に狙う.png" height="422" loading="lazy" src="/img/4c31cb81b5f9d2c3.png" title="状態異常を引き起こす敵を優先的に狙う.png" width="750"><br>
↑魅了されたアキレスの強力な攻撃が味方のエスカレイヤーを襲う。こうなると悲劇である。</p>
<h3 id="content_1_58">スタミナを揃えない   <span id="p56eb2bf"></span> </h3>
<p>味方キャラクターのスタミナが全員同じくらいの場合、同じタイミングで複数のキャラクターが離脱してしまう可能性が高い。<br>
片方のキャラクターを優先して離脱させるなどして、味方のスタミナ（離脱タイミング）に差をつけること。<br>
<strong>同じくらいスタミナのキャラクターが3人以上いる場合は危険。</strong></p>
<p>左2人のスタミナが揃っているため、ほぼ同時に2人が撤退してしまう可能性がある。できれば回避したい。<br>
<img alt="スタミナが揃っている.jpg" height="419" loading="lazy" src="/img/b345fa8cf9c28248.jpg" title="スタミナが揃っている.jpg" width="750"></p>
<p>優先出撃でも体力が低いキャラと高いキャラを混ぜて出撃させること。</p>
<h3 id="content_1_59">バフを使う   <span id="p161abc7"></span> </h3>
<p>キャラクターにバフをつけられるキャラクターをうまく使うこと。<br>
エスカレイヤー、閃忍ハルカ、神騎エクシールはそれぞれ戦士、閃忍、神騎のキャラクターに対してバフを付与できる。<br>
優先出撃枠を使って固めて出撃させることで殲滅力の増加が期待できる。<br>
<img alt="バフを使う.png" height="421" loading="lazy" src="/img/8096fed3b0342556.png" title="バフを使う.png" width="750"><br>
↑エスカレイヤーの固有効果「レジェンド戦士＋」で、開始直後から味方の戦士3人に強力なバフをかけている。セオリーの一つだ。</p>
<h3 id="content_1_60">助っ人のゲージを見る   <span id="x93166fd"></span> </h3>
<p>助っ人はオート操作（＝必殺技が溜まったらすぐ使用する）である。<br>
全体必殺技を複数体に向けて使用してもらえるように敵の数を調整するとよい。</p>
<p>↓今いる敵を倒した次に敵が5匹出現する場合、助っ人ハルカの必殺技が溜まる前に今の敵を片付けると5体に対して必殺技を撃ってくれる。<br>
<img alt="助っ人のゲージを見る.jpg" height="420" loading="lazy" src="/img/d4a6ee885d1b4e4e.jpg" title="助っ人のゲージを見る.jpg" width="750"></p>


<ins class="adsbygoogle" data-ad-client="ca-pub-6756084042400545" data-ad-format="auto" data-ad-slot="9804070536" data-full-width-responsive="true" style="display:block"></ins>
<br><h2 id="content_1_61">発展的な戦術   <span id="af329b26"></span> </h2>
<p>基本的な戦術ができてきたらこちらにトライするとよい。</p>
<h3 id="content_1_62">戦線を崩壊させないための考え方   <span id="je99192d"></span> </h3>
<p>戦線が崩壊する代表的なケースは一度に複数キャラクターが撤退してしまい、新しいキャラクターが戦線に到着する前に残ったキャラクターも倒されてしまうようなケースである。<br>
なぜそのような状況になってしまうのか？</p>
<p>端的に言うと<strong>メンバーの交代がうまくいっていないから</strong>である。</p>
<p>キャラクターのスタミナは時間経過につれて減少するため、交代が必要になる。<br>
一時的に味方の人数が減ってしまうため、残った味方が集中攻撃を受けて倒されてしまうと戦線は崩壊する。<br>
そうならないような工夫をする必要があり、例として以下のような方法がある。</p>
<ul class="list1 list-indent1"><li>敵の数が少ない時に交代する<br>
敵の数が少ない時に交代すると残った味方が受ける攻撃も少なくなり、戦線は崩壊しづらい。<br>
数的有利かどうかを意識するとよい。</li></ul>
<p>↓敵が1体のときを狙って交代した図。瞬間的に攻撃は1回しか行われず、安全に交代できる。<br>
<img alt="敵が少ない時に交代.jpg" height="421" loading="lazy" src="/img/03b635673494a1e8.jpg" title="敵が少ない時に交代.jpg" width="750"></p>
<ul class="list1 list-indent1"><li>フィールド上の敵を一時的に全員倒して交代する<br>
敵にも復活の時間があるため、敵の復活の時間を利用して交代すると戦線は崩壊しづらい。<br>
（※理由は後述するが、個人的には推奨しない。）</li></ul>
<p>↓必殺技で敵を一時的に全滅させることを見越して交代を行った図。この瞬間は敵の攻撃が行われないため安全。<br>
<img alt="敵全滅.jpg" height="415" loading="lazy" src="/img/5613f4d628380135.jpg" title="敵全滅.jpg" width="750"></p>
<ul class="list1 list-indent1"><li>敵にデバフをかけて交代する<br>
スタンやデバフなどを与えて交代することで攻撃の数や威力を減らすことができるため、戦線は崩壊しづらい。</li></ul>
<p>↓閃忍ツルコの必殺技でスタンさせた後の交代を狙う図(既に崩壊気味で良くない。。。)<br>
<img alt="スタン.jpg" height="418" loading="lazy" src="/img/2acdf5fbac617750.jpg" title="スタン.jpg" width="750"></p>
<h3 id="content_1_63">敵の出現方法の種類   <span id="n968bd66"></span> </h3>
<p>敵の出現にはいくつか種類があり、それによりこちらのアクションを変えるとよい。<br>
状況によって<strong>必殺技ゲージの溜まっているキャラクターをわざと撤退させる</strong>こともある。<br>
敗北したステージがあった場合、なぜ敗北したかを考えるべき。（大抵はラッシュで崩れている）</p>
<ol class="list1 list-indent1"><li>小隊型<br>
敵が複数体出現する。出現した全員を倒すまでは新たな敵は追加されない。<br>
敵の数を減らすと数的優位が作れるため<strong>交代には適している。</strong><br>
味方の人数が少なかったり、スタミナの少ないキャラクターが多い場合はこのタイミングで交代をする。<br>
必殺技ゲージが溜まっているからといって焦ってうたないように。必殺技を抱え落ちさせても戦線を整えることが優先される場面もある。</li>
<li>逐次投入型<br>
敵が1～5体出現し、敵を撃破すると一定時間後に敵が追加される。<br>
敵の数が多い時に交代を行うと戦線が崩壊する危険性があるが、<strong>敵の数が少ない時に交代すると安全に交代可能。</strong><br>
敵が2～3匹くらいで落ち着いているときはスタミナの少ないキャラクターを交代しておくとよい。</li>
<li>ラッシュ型<br>
敵が5体出現し、敵を倒すと即時で追加される。<br>
変に交代して戦線が崩壊すると、キャラクターが出現するたびにタコ殴りにされるため基本的に立て直しできない。<br>
<strong>戦線が崩壊するときの原因は大体これ。ラッシュに対していかに凌ぐかがクエスト攻略の鍵となる。</strong><br>
敵を全滅させたときに交代を推奨しないのはラッシュ警戒である。<br>
敵を全滅させる→ラッシュなのでスタミナMAXの敵が5体揃う<br>
という状態で交代をすると人数不利となってしまい、戦線崩壊の原因となるからである。</li>
<li>その他<br>
ステージによっては敵が特殊な出現方法をすることがある。</li></ol>
<ul class="list1 list-indent1"><li>敵の数は少ないが、強めの敵が一度に1～3体くらい出てくるステージ<br>
中途半端な育成のキャラクターが必殺技が溜まる前に撤退しやすい。<br>
強いキャラ優先出撃＋SSRキャラのバフを使って押し切るとよい。<br>
スタミナが残っているように見えても一撃のダメージが大きいため、必殺技が溜まったら基本的には撃ってよい。</li>
<li>弱めの敵が大量に出てくるステージ<br>
敵は弱いもののラッシュが多く、交代のタイミングが難しい。<br>
また、テンポよく敵を倒せないと制限時間で敗北することもある。<br>
一撃で相手を倒せて、行動速度の速いキャラクターや全体攻撃持ちのキャラクターを優先的に出撃させること。</li>
<li>盾持ちのフーマンを含む小隊<br>
盾持ちフーマンが他の敵キャラクターを庇う。<br>
盾持ちフーマンを優先して落としたくなるが、他の敵キャラクターを残すと必殺技を撃たれることがある。<br>
また、盾持ちフーマンも1体扱いなので、撃破に時間をかけると制限時間で敗北になってしまいやすい。<br>
盾持ちフーマンは単体必殺技で倒すようにして、通常攻撃は他の敵キャラクターを優先するとよい。<br>
（盾持ちフーマンの体力が少なかったら通常攻撃で倒してもよい）</li></ul>
<h4 id="content_1_64">ラッシュへの対応   <span id="v59c8e38"></span> </h4>
<p>ラッシュ中は敵の攻撃が激しいため、どうしても交代が必要なケースがある。<br>
比較的安全に交代するための方法は<strong>相手にデバフをかける</strong>か、<strong>2人の必殺技で相手を2回全滅させる</strong>である。<br>
デバフをかけて味方キャラクターが受けるダメージを減らしたり、<br>
敵を必殺技で全滅→敵出現→必殺技で全滅→敵出現とやっている間の時間で交代を進めるとよい。</p>
<ul class="list1 list-indent1"><li>おすすめデバフもちキャラ<br>
鬼の斗羽大洋：一定時間、敵全体の攻防40%ダウン。交代中のダメージを抑え、敵の撃破率が上がることで一瞬攻撃されない状況を作れる。<br>
氷のシズカ：敵全体に物理ダメージ 一定時間、速度20%ダウン。相手の速度が下がるため、攻撃を受ける回数が減る。<br>
閃忍ツルコ：敵全体に物理ダメージ/スタン50%。スタン中の敵は攻撃をしてこないため交代しやすい。<br>
他</li></ul>
<h3 id="content_1_65">戦線の立て直し   <span id="a5f07262"></span> </h3>
<p>一度半壊した戦線の立て直しは難しい。<strong>基本的には戦線を壊さないことが重要。</strong></p>
<p>敗色濃厚でも足掻く場合にできることとしては以下の通り。</p>
<ul class="list1 list-indent1"><li>とにかく新しいキャラクターの出撃を妨げないようにして、スタミナの低いキャラは撤退させるようにする。</li>
<li>全員オートをつかって、撃てる必殺技は全て撃ってもらう</li>
<li>体力の少ない敵から狙い、スタンした敵は後回しにして敵の攻撃回数を減らす。（敗北する場合でも、1体でも多く敵を倒せると宝箱が落ちる可能性もある。）</li>
<li>後続がすぐに戦闘に参加できるように、出撃速度や移動速度が早いキャラクターを育てておく。</li></ul>
<h2 id="content_1_66">コメントフォーム   <span id="td3fc1c4"></span> </h2>

<ins class="adsbygoogle" data-ad-client="ca-pub-6756084042400545" data-ad-format="auto" data-ad-slot="2456832941" data-full-width-responsive="true" style="display:block"></ins>
<br>
<div class="pcomment">

<ul class="list1 list-indent1"><li class="pcmt" data-comment-id="comment_e6097b137378441cf4aac9cc743e2974">宝箱について書いた者です。途中まで書きましたが一時保存していた内容が消えたのでまたの機会に続きを書きます。。。 -- [4/Lgq7Owfa6] <span class="comment_date">2020-12-03 (木) 01:56:46</span></li>
<li class="pcmt" data-comment-id="comment_4b8f0792cb9d505456c3a07c8d7102d2">おーこういうページ助かります個人的には盾っぽいものを持ったフーマンが出た時にそいつから潰すべきか、他のやつから潰すべきかとかも悩むので皆の意見聞けたら嬉しいですねー。その他この敵はこういう攻撃をするとかも。 -- [uTyqMtcUQms] <span class="comment_date">2020-12-03 (木) 01:59:54</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_1d2360db29f84399bdab1a52e5b85484">と、思ったら敵の種類による対応って項目ありましたね。見落としてました（中身はまだっぽいですが -- [uTyqMtcUQms] <span class="comment_date">2020-12-03 (木) 02:01:02</span></li>
<li class="pcmt" data-comment-id="comment_6782b4046b02f93a541137d71371ba46"><span>盾持ちフーマン、かばうときはダメージ軽減されるし、出撃メンバーの火力によっては他は倒せるけど盾持ちフーマンだけ落とせない、ってことになるからマップによっては注意が必要だね。全力で盾持ちを狙うべき。<br class="spacer">何体も出てくるマップなんてそんなにないけど。 -- [fDCL3hAOt7M] </span><span class="comment_date">2021-01-10 (日) 15:03:20</span></li></ul></li>
<li class="pcmt" data-comment-id="comment_b289137064dac0ec1fc12a449143e4eb"><span>出撃数よりキャラ所持数が多い時<br class="spacer">戦闘するキャラはランダムに選ばれるのでしょうか -- [ULCANz9t.zY] </span><span class="comment_date">2020-12-04 (金) 01:47:59</span></li>
<li class="pcmt" data-comment-id="comment_45ad08700026fe552b3deaddbf8b5f1a">わかりやすい。乙。攻撃と必殺に関してだけど、必殺を使うと攻撃までのインターバルを表す星ってリセットされて最初からになるよね。攻撃を無駄にしないという観点だと星の位置を確認し、もうすぐ攻撃するなら攻撃を待ってから必殺を出す…ってのも大事かも -- [wJ4BHkUNliE] <span class="comment_date">2020-12-04 (金) 02:08:10</span></li>
<li class="pcmt" data-comment-id="comment_be41e0eae5c73c4079fa90d694ca369a">もしかして、敵も所属（種族）で、ダメージが入りやすい入りにくいがありますか？ときどき、雑魚なのにすごく撃破に時間がかかる時があったりするので。出撃メンバーとの相性なのかな？？？ -- [8chgAARUa7Y] <span class="comment_date">2020-12-13 (日) 10:41:05</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_79249896290a80fcd991f91246ea01fd">見た目同じでもステージによってステータスにはかなり差がある。50数体とか沢山出てくるとこなら個々のスペックが低く一撃で倒せるけど、10前後だと数が少ない分かなりタフだし一発が重くて結構苦戦する -- [Y2/5PhOhUwc] <span class="comment_date">2020-12-13 (日) 14:44:46</span>
<ul class="list3 list-indent1"><li>後ダメージが増減するステータスとして属性がある。マークの付いてる敵を同じ属性で殴るとダメージが上がって、表記もいつもの黄色からオレンジになる。被弾や別属性に対して増減があるかは把握してない -- [Y2/5PhOhUwc] <span class="comment_date">2020-12-13 (日) 14:48:00</span></li></ul></li></ul></li>
<li class="pcmt" data-comment-id="comment_bf1d846dc4882949bdbd58f33c9017a6">必殺技が発生してる時は、撤退とか次の必殺のONOFFが出来なくなるのは、バグですか？ -- [Bwv8AsZbkQg] <span class="comment_date">2021-01-12 (火) 14:53:27</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_43b13b3bb79b01ad5b84eab208ec9e1b"><span>必殺技中は全行動固まるため仕様だと思います。<br class="spacer">まあ必殺技だけ撃って撤退する人はいないと思いますが… -- [FY0B3mCGL2I] </span><span class="comment_date">2021-01-12 (火) 15:49:00</span></li>
<li class="pcmt" data-comment-id="comment_692b6154417545b41aae583740d65a29">わかる。ＳＴ管理してて、次の子を早出ししたくても、必殺がＡＵＴＯ発動して、撤退がタイミング良く出来ないときあるよね。 -- [XnlPQ02dLxQ] <span class="comment_date">2021-01-12 (火) 18:09:59</span></li></ul></li>
<li class="pcmt" data-comment-id="comment_3a0999a8b85470b5615347e78aa8a47e">出撃制限があるマップで出撃不可の属性を持ってる助っ人を選択した場合どうなりますか？ -- [hEyS/IEvutg] <span class="comment_date">2021-01-15 (金) 11:27:30</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_b66e24cb4456b537b7a45e480fdfb3ba">普通に出撃できます。これチュートリアルとか探してもどこにも書いてなくて、私も雑談版で教えてもらいました。上にも書き足しておこう。 -- [WNoo29HhD1M] <span class="comment_date">2021-01-15 (金) 12:03:24</span>
<ul class="list3 list-indent1"><li>制限無いんですね。ありがとうございます。 -- [hEyS/IEvutg] <span class="comment_date">2021-01-15 (金) 16:34:06</span></li></ul></li></ul></li>
<li class="pcmt" data-comment-id="comment_129e3f35623b63e506dd9068633a333e"><span>戦略的に狙ってできるかはともかく、連撃中に他のキャラの攻撃が当たって倒してしまえば、本来最初に攻撃したキャラに発動するはずの反撃を封じれそう。一桁になった連撃にも一応価値はある。<br class="spacer">終末環境（全員ロケット虎完全強化）になったら実用的な戦術になるかも。 -- [fDCL3hAOt7M] </span><span class="comment_date">2021-01-15 (金) 12:25:26</span></li>
<li class="pcmt" data-comment-id="comment_ae4d0bc1059775d49b30922ec01c6562">優先出動の組み合わせをあらかじめセットしておいて、ワンボタンで切り替えできるようにならないかな？忍者と神姫を切り替えるの、毎回選び直すのすごくめんどくさい。 -- [UVezykjxgQc] <span class="comment_date">2021-01-24 (日) 12:18:50</span></li>
<li class="pcmt" data-comment-id="comment_9989c8f3a9710b13b06ffb4c61d710f2"><span>このゲームで処理落ちする原因<br class="spacer">戦闘中に必殺技が発動するタイミングで<br class="spacer">撤退を無理に行うと発生しやすい<br class="spacer">特に△３の時に落ちやすい<br class="spacer">なので速度を落としてから撤退させるのも手 -- [labl4IiMpH2] </span><span class="comment_date">2021-01-27 (水) 00:10:24</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_a3c4cc3bd3ded4816b0f0d13667b2ca9">ステージセレクトしてローディング80％台ぐらいでブラウザのエラー出て止まった時、STロストしてたな。シナリオを連続して読むと割と止まりやすいけど、そのエラーメッセージと同じ（メモリ周り）。せめてステージスタート時点でST消費にならないものか…。 -- [BPo2uwI2DmA] <span class="comment_date">2021-07-09 (金) 21:37:57</span></li></ul></li>
<li class="pcmt" data-comment-id="comment_68f5e05e692764d901ed07837d069268">このゲーム属性相性あったような気がするけど、有利不利の確認方法が分からない。太陽には月有利？ -- [xY8nxuxE3Yk] <span class="comment_date">2021-02-01 (月) 18:55:43</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_e42c1bf27327d9d84fbb5be78a3ef1fa">三すくみではなく、同属性で1.2倍ダメージ。太陽には太陽で攻撃すると有利。 -- [EQiiTzDUrGE] <span class="comment_date">2021-02-01 (月) 19:01:09</span></li></ul></li>
<li class="pcmt" data-comment-id="comment_305f4f2a1e22515f164a1cb1cff3d7ef">命中回避の文章、命中50回避50だと攻撃が当たる確率は75%じゃないですか？ -- [UPNf51iTEk.] <span class="comment_date">2022-02-11 (金) 08:11:35</span></li>
<li class="pcmt" data-comment-id="comment_1f318eab8e8b91eca811b6b66b45140e">メインクエストで初めて呪縛受けた。錫杖滅忍とかの通常攻撃だろうか。優先2セラフィールで治した -- [Gxe7mYUxnNI] <span class="comment_date">2022-11-10 (木) 19:04:06</span></li>
<li class="pcmt" data-comment-id="comment_8df5e662b95f6afc7639a5a4a7e1cca4"><span>実際検証してない文章だけ見た感想だけど <br class="spacer">敵の命中より味方の回避が戦った時に敵の命中力の低下は25じゃなくて25%じゃない？ <br class="spacer">敵の命中力が75の時に命中ダウン50に回避の方が上補正かかった時に75-50+25 <br class="spacer">=0って計算してるけど <br class="spacer">多分(75-50)×0.75=18.75になるんじゃないかな -- [5KDYl20rwjM] </span><span class="comment_date">2025-09-07 (日) 18:58:53</span>
<ul class="list2 list-indent1"><li class="pcmt" data-comment-id="comment_4b6ed4f5f9e10449dd49896370ea846a">75-(50+25)=0あるいは75-50-25=0ね -- [5KDYl20rwjM] <span class="comment_date">2025-09-07 (日) 19:00:56</span></li>
<li class="pcmt" data-comment-id="comment_ff693708328d756f75c0d603749c8553"><span>検証してきた。 <br class="spacer">BユニVHディストバーンに命中ダウン80で回避力100のキャラが回避98/100 <br class="spacer">命中ダウン99で回避100/100 <br class="spacer">ので『攻撃側の命中力が２５％減少した』影響は命中ダウン19より小さい。記載の通り割合減少と思われる。 -- [kGPp72HFw0Q] </span><span class="comment_date">2025-09-07 (日) 23:05:05</span>
<ul class="list3 list-indent1"><li>ただこの結果は体感と差がある。ディストバーンの命中力85だとしたら、命中ダウン無しでは回避100キャラでも15%しか回避できないはずなんだけどそれ以上に避けてる気がする。 -- [kGPp72HFw0Q] <span class="comment_date">2025-09-07 (日) 23:15:48</span></li>
<li>命中85vs回避100だとして命中85に-25%補正で63.75になるので4割弱回避するようになるのではないでしょうか -- [xLysrBPsizs] <span class="comment_date">2025-09-07 (日) 23:57:58</span></li>
<li>ご指摘の通りです。なら合ってそうですね。 -- [kGPp72HFw0Q] <span class="comment_date">2025-09-08 (月) 01:41:53</span></li></ul></li></ul></li></ul>
</div>
`,r={html:c},_=JSON.parse('{"title":"戦闘","description":"","frontmatter":{"title":"戦闘","layout":"doc","meta":{"sourceUrl":"https://escalationheroines.wikiru.jp/?%E6%88%A6%E9%97%98","sourceUpdated":"2026-04-09 (木) 20:30:09","synced":"2026-07-22","reviewed":false,"translated":false}},"headers":[],"relativePath":"site/ja/battle.md","filePath":"site/ja/battle.md"}'),g={name:"site/ja/battle.md"},b=Object.assign(g,{setup(y){return(o,t)=>{const l=s("MirrorContent");return e(),a("div",null,[d(l,{html:n(r).html},null,8,["html"]),t[0]||(t[0]=i("div",{class:"search-index",style:{display:"none"},"aria-hidden":"true"},"最終更新日時:2026-04-09 (木) 20:30:09 戦闘 戦闘 戦闘について 戦闘速度の調整方法 戦闘の一時停止方法 特定の敵をロックオンする方法 特定のキャラのみを撤退させる方法 必殺技の自動設定方法 バトルをリトライしたい 助っ人について 助っ人の選択方法 助っ人の設定方法 戦闘の基礎知識 各種パラメータ 物理攻撃と魔法攻撃 スタミナとダメージ 出撃 出撃可能人数 優先出撃設定 出撃パーティーの固定方法 前列／後列と近距離攻撃／遠距離攻撃 撤退 必殺技と固有効果 必殺技 敵の必殺技 必殺技ゲージの計算式 必殺技発動までの主な時間 固有効果 対象ロック 攻撃、連撃、反撃、命中・回避判定、クリティカル 攻撃 連撃 反撃 命中判定、回避判定 クリティカル(レイドのみ) 状態異常（状態変化） バフ（強化）／デバフ（弱化） キャラクター対象「バフ／デバフ」 フィールド対象「バフ／デバフ」 効果の重複について 効果の上書きについて バフ／デバフ一覧 特殊状態 戦闘中における装備アイテムのアイコン表示 パラメータ強化の限界 所属勢力 属性 弱点効果 特殊属性 ダメージ補正 クエストをクリアするための基本的な考え 優先出撃キャラクターに精鋭を配置する 前列と後列を意識する 固有効果や必殺技を把握する 戦線を守る 基本戦術 一番体力の少ない敵をロックする 必殺ゲージを持つ敵から倒す 状態異常を引き起こす敵を優先的に狙う スタミナを揃えない バフを使う 助っ人のゲージを見る 発展的な戦術 戦線を崩壊させないための考え方 敵の出現方法の種類 ラッシュへの対応 戦線の立て直し コメントフォーム 戦闘について 手持ちのキャラクターを使用して戦闘を行います。 基本的に戦闘は自動で出撃、自動で接敵、自動で攻撃と、ほぼフルオートで行われます。 味方全員のスタミナが尽きるより前に全ての敵を倒せば勝利となります。 必殺技の発動も全てオートに設定すれば完全自動戦闘になります。 手動戦闘を行う場合は戦況を見て、適時必殺技を運用する形になりますが キャラ育成の進んでいない序盤の段階では、必殺技のチャージに相応の時間が必要になります。 （戦力の育成が進むにつれ、必殺技を撃ちまくれるようになります） 戦闘には制限時間(画面左上)があり、残り時間が無くなると戦闘敗北となります。 また戦闘中、戦果を判定するタイミングが何回か存在します。(途中判定の無い戦闘も存在します) 画面左端のバー(戦況ゲージ)がそれらを表しており、左の緑色ゲージは時間経過で上昇し、右の橙色ゲージは敵にダメージを与えると上昇します。 左ゲージが砂時計マークのラインまで上昇した時点で右ゲージが砂時計のラインを通過していない場合その時点で戦闘敗北となります。 あまり攻撃出来ていないと味方が全滅してなくても負けちゃうよ、ということです。⇒関連リンク：戦闘に勝てない時は？ なお、クエストに失敗(全滅、タイムアップ、撤退問わず)しても、その時点までドロップしていた資金、宝箱、到達度に応じたEXPを獲得できます。 戦闘速度の調整方法 画面左下の▶ボタンで戦闘速度を3段階(速度1～3)に切り替える事が可能です。 ▶ボタンが1か2段階の状態でCtrlを押すと、押し続けている間だけ速度3(3倍速)に加速できるのでレイド戦にて手動戦闘する場合などに便利。 また、Ctrl+Shiftの長押しで速度3+必殺アニメーション再生設定を「再生しない」状態にすることができます。 戦闘の一時停止方法 画面左下の「必殺設定」ボタンをクリックする事によって戦闘画面を一時停止状態にする事ができます。 特定の敵をロックオンする方法 対象の敵をワンクリックする事により、敵にロックマークが付き味方がその敵を集中して狙うようになります。 （クリックで大丈夫です。マウスボタンを押し続ける必要はありません） ⇒関連リンク：対象ロック 特定のキャラのみを撤退させる方法 対象キャラの顔アイコンを画面下方向に向けドラッグさせれば戦場から撤退し、後続のキャラと入れ替わります。 戦線の崩壊によるもぐら叩き状態を防いだり、一部固有効果の早期発動を狙う際に使用します。 ⇒関連リンク：撤退 必殺技の自動設定方法 画面下のキャラクター顔アイコンを1クリックする事で、キャラが自動で必殺技を撃つようになります。 （初期設定はクリックによる手動発動） 画面左下の「全員AUTO」ボタンをonにする事によって、全キャラクターの必殺技が完全自動発動されるようになります。 ⇒関連リンク：必殺技 必殺技の演出設定 画面左下の必殺設定ボタンで必殺技のアニメーションの再生方法を設定することが出来ます。 再生設定説明 全て再生全ての必殺技を通常再生します 1日1度再生当日に再生されたキャラクターの必殺技をスキップします。 初回のみ再生過去に再生されたキャラクターの必殺技をスキップします 再生しない味方の全ての必殺技をスキップします バトルをリトライしたい 操作ミスやアクシデントによって予定外の敗北を迎えそうな場合には、 戦闘の決着が着く前にブラウザのタブを閉じてゲームを開き直せば、その戦闘を無かった事にして再挑戦できます。 （アプリ版の場合はアプリの強制終了） 「再戦する」ボタンを選択します「キャンセル」ボタンを押した場合はST等を消費の上で敗北扱いとなります 助っ人について 助っ人（他のプレイヤーが助っ人に設定しているキャラクター）を使用することができる。 戦闘に行き詰まった際は気軽に利用して問題ない。 一日の助っ人利用回数には上限があり、初期値では5回までとなっている。 ⇒関連リンク：助っ人として呼ぶのに適切なキャラクターを教えて 使用回数について 助っ人の使用回数は午前4時にリセットされる。 1日に使用できる助っ人の回数は初期は5回だがVIPランクにより増やすことが出来る。 助っ人を使い切った場合でもアイテム「4回転エテ公」を消費することで追加して助っ人を使用することができる。 自軍戦力の整わないゲーム序盤のうちは、特に出し惜しみする事無く消費して問題ない。 （アイテムの消費を警戒して進行が滞るより、早期攻略を進めて戦力を整えたほうがトータルでの効率は良くなる） 助っ人の使用回数が「達成宝箱」のポイントを得る条件のひとつになっているので、無料分は毎日上限まで使っておくとよい。 助っ人の装備について 「ハニージッポ」など一部の装備は助っ人では効果を発揮せず、装備画面でロックされて表示される。 助っ人キャラの装備は助っ人プレイヤーが現在装備させているものがリアルタイムで反映される。 助っ人の性能について 自身のプレイヤーレベル以上のレベル150(☆1～☆5)までのキャラが出現する。(2023/11/29のアップデート) プレイヤーレベル100以上の場合、出現するキャラのレベルは100～150で固定される。 たとえ自身のレベルが低くても、プレイヤー人口の影響かレベル99以下の助っ人はほとんど表示されることがない。 その他 助っ人はキャラアイコンをクリックして必殺技を不使用にすることは出来ず、ゲージが溜まればオートで必殺技を撃つ。 助っ人の出すダメージはイベントの最大ダメージボーナスの対象にならない。 助っ人はステージに設定されている出撃属性の制限を受けない。 自身の助っ人キャラの設定や、助っ人被使用回数は「キャラクター」の「助っ人設定」から確認可能。 ログインしたり戦闘(時短含む)を行うことで自身の設定した助っ人は借りる側のリストの先頭に並ぶようになる。 時間帯により更新スピードが違い、夜や休日等のアクティブプレイヤーの多い時間帯はリストのキャラクターが流れやすい。 助っ人関連の旧仕様 助っ人関連の古い仕様 2021/12のアップデートで他のユーザーに自分の助っ人が使用された場合D2Pが獲得（上限月30ポイント）できるようになった。 自身の所持キャラクターの最大☆数までの助っ人キャラクターしか表示されない制限があった。(2022/12/21に撤廃) 助っ人リストに表示されるキャラは、自分のプレイヤーレベルの-2～+2の範囲のキャラクターレベルの助っ人キャラだった。(2023/11/29に仕様変更) 一度使用した助っ人キャラはしばらくの間は再度助っ人リストに出て来ないので、連続使用はできない。 2022/05のアップデートで時短戦闘をメインにするなどプレイスタイル次第では他のプレイヤーの助っ人リストに並びにくかった点を調整。 2023/01/11のアップデートで表示されるキャラの選出アルゴリズムが調整され、開くたびに違う助っ人が表示されることが多くなった。 2024/04/03のアップデートで使用した助っ人プレイヤーを同日には表示しない制限を撤廃。 助っ人の選択方法 助っ人を選択する際は、助っ人キャラの「名前の書かれた部分」をクリックする。 顔アイコンをクリックした場合、助っ人の持つ必殺技や性能が表示される（選択は行われない）。 レベルが高く、顔アイコンの上に並ぶ☆の数が多いほど性能は強化されている。 自軍戦力が整わない段階では、敵に対して直接的な打撃を与える必殺技を持つ助っ人が助けになる。 助っ人選択画面のサンプルを開く 助っ人アイコン右下に「助」の文字が入っているキャラは当該イベントの報酬ボーナスがUP 赤アイコン→15% オレンジアイコン→10% 緑アイコン→5% 助っ人の設定方法 自分の出した助っ人が他人に使用される事により、使用された回数に応じて翌月に一括でD2Pを獲得できる。 獲得量の上限は毎月30。毎月1日の4時に更新される。 自身の出す助っ人の設定は「ホーム画面」→「キャラクター」→「助っ人設定」から行う。 安定して助っ人に選ばれやすいキャラクターの傾向 開催中のイベントのピックアップ対象SSRキャラ（イベント出撃メンバーに組み込むと報酬にボーナスが付くため） Wドリル状態（ドリル系装備を2本装備）の閃忍ツカサ（必殺技が覚醒されているとさらに採用率が上がる） 限界突破され高レベルの超昂閃忍ナリカなど攻略で使いやすいキャラ 戦闘の基礎知識 各種パラメータ パラメータ画面例 画面左側：レベルアップ や 限界突破 等に応じて成長するステータス スタミナこれが無くなるとキャラは撤退する。ヒットポイント。敵からダメージを受ける以外にも、ステージ毎に設定された消耗量によって自動的に減っていく。 攻撃力/魔法力物理攻撃タイプは攻撃力が、魔法攻撃タイプは魔法力が設定されている。両方設定されているキャラもいる（通常攻撃は物理判定・必殺技は魔法判定等のパターン） 防御力/魔法抵抗力防御力は物理攻撃の、魔法抵抗力は魔法攻撃の受けるダメージを減らす。レイドでは無意味。 画面右側：ステータス固定：装備 と 覚醒強化 によってのみ上昇するステータス 命中力通常攻撃の命中しやすさの目安となる。１００なら必中。レイドでは無意味。 仕様により、例えば値が40だからといって、40%しか命中しないという意味にはならない。 回避力どれだけ回避力が高くても敵の命中力が高いと回避できない。レイドでは無意味。 連撃率通常攻撃時に連続攻撃を行う確率。火力は上昇するが連続攻撃時はゲージの充填が行われず、必殺技の発動が遅くなるなどデメリットも大きい。 反撃率通常攻撃を受けた時に敵に反撃を行う確率。レイドでは無意味(効果は発動しているがレイドの仕様上無視して問題ない) スタン発動率攻撃時に敵をスタン状態にするかどうかの目安となる。 スタン抵抗率攻撃を受けた時のスタン状態のなりやすさの目安となる。 装備で簡単に防げるため気にする必要は無い。 移動速度キャラクターが出撃可能になって画面端から戦場に到着するまでの時間。 出撃速度キャラクターがNEXTから出撃可能になるまでの時間。 行動速度通常攻撃を行う頻度のこと。最重要。 この値が遅いキャラほど戦闘で不利になる。最速のキャラで3秒。この値が6秒以上のキャラは非常に遅い。初期値では4秒となっているキャラが最も多い。3秒のキャラは、6秒のキャラが1回攻撃する間に2回弱攻撃できる事になる。 必殺充填量通常攻撃の度に増加する必殺技ゲージの量。重要。その仕組み上、行動速度との相乗効果が非常に大きい。未強化状態の場合、RとSRは7.5%、SSRは10%のキャラが最も多い。10%未満だと必殺技の発動は目に見えて遅くなり、6%を切ると味方や装備の補助無しで単独で必殺技を撃つのは難しくなる。 それぞれのステータスは「装備」「限界突破」「覚醒強化」「レベル上限UP」などで強化する事ができる。 物理攻撃と魔法攻撃 物理攻撃なら攻撃力を、魔法攻撃なら魔法力を参照してダメージを与える。 攻撃を受ける側も、防御力や物理耐性で物理ダメージを、魔法抵抗や魔法耐性で魔法ダメージを減らす。 通常攻撃と必殺技の物理／魔法が一致しているキャラが大半だが、たまに通常攻撃が物理で必殺技が魔法のキャラもいる。通常が魔法で必殺が物理のキャラは今のところいない。 魔法攻撃の通常攻撃は命中が99で基本的に必中であるメリットと、ダメージが0.8倍になるデメリットがある。魔法攻撃の必殺技には0.8倍は適応されない。 ハニー系と呼ばれるハニワのような敵は、魔法ダメージと魔法キャラが使用した自身へのデバフと状態異常を無効にする。 例外的にゴールデンハニーのみ、魔法ダメージを半減し、デバフと状態異常は無効にしない。 ハニ噛み王子という装備を持つと、この無効や半減を打ち消しつつ、更に魔法ダメージを1.1～2倍にすることができる。 スタミナとダメージ 黄色部分……残りHP赤色部分……被ダメージ部分（ヒーラースキルで回復可能分）黒色部分……時間経過によるスタミナ消費分（回復不可能・一部例外あり）外周部分……必殺技ゲージ キャラクターにはスタミナがあり、キャラクターアイコンの黄色いバーがスタミナゲージになっている。 スタミナは1秒経過するごとに減少していく。(減少量はステージごとに「スタミナ減少量 ○/sec」と表示されている) よって戦場に立つキャラクターは、たとえ敵からの攻撃がノーダメージであっても、最終的には時間経過により自動撤退する。 （ただし超昂閃忍ナリカなど一部には固有効果により自動撤退適用外の例外キャラも存在する） 時間経過により自然減少したスタミナは基本的に回復させる手段が無いのでスタミナ最大値が減るのとほぼ同義である。(※こちらも一部例外あり) 消費アイテムである「ハニージッポ」が効果を発揮した場合のみ、ゼロになったスタミナが1度だけ最大値まで回復する。 キャラクターが敵の攻撃を受けるとスタミナゲージに赤い部分が出来るが、これがダメージである。この赤い部分だけを各キャラの固有効果や必殺技により回復することができる。 自然減少＋ダメージによりスタミナゲージの黄色いバーが無くなってしまうと戦闘からキャラが離脱する。 上述のように、たとえダメージを一切受けず自然減少だけでスタミナが0になっても戦闘から離脱してしまう。 (スタミナが0になってもダメージを受けるまでは離脱しない固有効果を持ったキャラや超昂閃忍ナリカなどの例外を除き、全てのキャラは自然減少でいつか退場する運命にある) （※）……ビートプレジデント・シーラの必殺技や「お茶会セット」の効果など一部に例外があるが非常に稀。 出撃 画面右下に表示されているキャラクターは出撃準備中のキャラクターであり、 逆時計回りの赤色のタイマーが一周してキャラクターアイコンがモノクロからカラー(GO!表示)になると出撃準備が完了し、 フィールドに空きスペースがあれば自動で出撃を開始する。 出撃開始後、画面右端から前列／後列の「戦闘可能位置」にキャラクターが移動し終わって初めて行動可能になる。 この行動可能になった瞬間を固有効果などの説明文にある「出撃完了時」と呼ぶ。 出撃準備時間は「出撃速度」、その後の移動時間を「移動速度」として各キャラクターごとにパラメータが設定されている。 出撃開始から行動可能になるまでの移動時間は時間経過によるスタミナ減少は発生しないが、敵の攻撃は容赦なく襲ってくる。 自軍フィールドにキャラがいなくなり、出撃するキャラが移動中に敵から一方的に攻撃される状況のことを「モグラ叩き」と表現することがある。 出撃可能人数 メインクエスト各ステージにおける出撃可能人数は30人が標準となっている。 属性制限ステージなど、条件によっては変動するケースがある。 初期状態では、自軍の手持ちユニットの中からランダムで出撃が行われる為、戦力バランスに著しい偏りが発生する。 これを防ぐため下記の「優先設定」機能を利用し、自軍の出撃メンバーを指定する事が必須となる。 戦闘開始時における自軍ユニットの初期配置数は2～4人。 こちらも同様に、条件によって変動するケースがある。（最低人数は1人から） また、デイリークエストの場合は5人での出撃となる。 ステージ毎の出撃人数・初期配置等に関しては「メインクエスト」から確認する事ができる。 助っ人は開始時の配置人数の制限には含まれないため、一般的なメインクエストにおける最大初期配置人数は自軍4人+助っ人1人の5人となる。 また捕獲対象キャラは、初期出撃人数の制限に含まれる。 優先出撃設定 自軍メンバーの出撃順番を制御するための機能です。 「ホーム画面」→「キャラクター」→「優先出撃設定」 の順に画面を選択する事で設定画面が開きます。 自軍主力メンバーを優先出撃に指定する事により戦力の偏りを防ぎます。 所持するキャラが3人増える毎に、優先出撃キャラに設定できる人数が1人増えます。 優先1は5人、優先2は15人が上限で、最大20人を優先設定することが可能です。 またアイテム「ヘビースターメン」を装備したキャラは優先１よりも早く最優先で出撃対象となります。 プレイヤー装備の「超昂人ロック」があればロックしたキャラクターを完全出撃不可(最大50人まで)に設定できる。 出撃パーティーの固定方法 5麺方式 ①最初に出撃させたいメンバー5人に「ヘビースターメン」を装備させる ②「優先1」出撃メンバーとして5人を指定する ③「優先2」出撃メンバーとして5人を指定する 上記の方法で最大3パーティー15人までの出撃編成を確実に固定できる。 出撃順番は 麺メンバー → 優先1 → 優先2 「麺メンバー」や「優先2」を6人以上設定した場合は、指定された6人以上がランダムな順番で出撃する。 （このケースで優先1や優先2にDENAIを装備させても優先効果は無視されDENAIの効果で上書きされる 出撃順序は 麺→優先1→優先2→ランダムメンバー→DENAI となる） 35麺（多麺）方式 主にレイドバトルにおいて使用される、出撃メンバーの固定方法。 ①出撃人数50人のうちの35人に「ヘビースターメン」を装備させる ②「優先1」出撃メンバーとして5人を指定する ③「優先2」出撃メンバーとして10人を指定する ④ ③で指定した10人のうち後半で出撃させたい5人に「DENAI」を装備させる この方法によって出撃メンバー50人すべてを固定する事ができる。 出撃順番は、 最初に「ヘビースターメン」を装備した35人（麺メンバー）がランダムに出撃する。 麺メンバーの出撃後に「優先1」の5人が 優先1 の出撃後に「優先2」の5人が 優先2 の出撃後に「優先2 + DENAI」メンバー5人が出撃する。 ここでは例としてレイド（50人編成）を挙げたが、優先1+2 合計15人以外の余分な出撃枠を麺メンバーで埋めれば、あらゆる戦闘において出撃メンバーを固定する事ができる。 （麺を使用して出撃メンバーを人数上限にまで固定した場合にのみ限って出撃順序が 優先2 → 優先2+DENAI という形に固定される） 前列／後列と近距離攻撃／遠距離攻撃 注：ユーザー間では近距離攻撃キャラのことを前衛、遠距離攻撃キャラのことを後衛と表すことがあります。 戦闘中にキャラクターがフィールドに配置される枠は、前列3枠／後列3枠 の合計6枠。 ただし、フィールドの最大同時出撃数は５人までとなっており、 「前２ ＋ 後３」もしくは「前３＋後２」の組み合わせとなる。 前列配置キャラは、ヘイトの初期値が増加しており敵からの攻撃を受けやすくなる。 後列に配置したキャラは、敵によっては反撃を受けないメリットがある。 各キャラクターにはステータスとして「近距離攻撃／遠距離攻撃」が設定されており、近距離攻撃のキャラは前列にしか立つ事ができない。 遠距離攻撃のキャラは、前列と後列の両方に立つ事ができる。（遠距離攻撃キャラが前列に立つ事がありえる） ただし、遠距離攻撃キャラは傾向として撃たれ弱いタイプが多い。 ''キャラクターアイコンの左上の欠けた部分が黄色なら近距離攻撃、青色なら遠距離攻撃を表している。 戦闘中の表示は装備「縛り亀甲」の状況が反映する。（近距離攻撃キャラでも「縛り亀甲」装備中は青くなる） 近距離攻撃のキャラクターは前列にしか出撃することができない。 この制限により、近距離攻撃キャラは最大でも同時に3人までしかフィールドに出撃する事はできない。 例外的に「縛り亀甲」を装備した場合のみ、近距離攻撃キャラクターであっても後列への出撃が可能となる。 近距離攻撃キャラを後列に配置しても攻撃力低下などのペナルティは発生しない。 前列3人の枠が既に埋まっている状態で、更に追加で近距離攻撃キャラが出撃しようとすると、5人出撃していなくても 「配置スペースなし」となり出撃することができず出撃待機中の状態となる。少ない人数で戦闘をすることになり、不利。 近距離攻撃キャラに上述の「縛り亀甲」を装備させる事によって対策可能。 遠距離攻撃のキャラクターは、前列にも出撃することが可能。 遠距離攻撃キャラは後列から優先して配置され、後列が既に3枠埋まっている状態で新たに出撃する場合のみ前列に配置される。 5人遠距離攻撃キャラで順番に出撃する場合、前列0人/後列3人→前列1人/後列3人→前列2人/後列3人という順番で配置される。 後列に空きがなくて前列に配置されてしまった遠距離攻撃キャラは、後列に空きができれば自動で後列に移動する。 ただし、後列に空きができた際に「出撃準備完了状態の遠距離攻撃キャラ」がいる場合は、そのキャラが空いた後列に配置され前列のキャラはその場所から動かない。 前列に遠距離攻撃キャラが2人いる状態で後列に空きができた場合、後列に移動するキャラは出撃順ではない不明な法則で毎回決まっている。 なお、敵側にも前列／後列の概念はあり、味方の必殺技や固有効果で前列／後列を対象にしたものが存在する。 撤退 キャラクターのスタミナが0になる前にキャラクターのアイコンを下にスワイプすることで個別に撤退させることが出来る。 出撃準備中(アイコンがモノクロ)のときに撤退させることは出来ないが、出撃待機中(アイコンにGO!表示)のキャラクターに対しては可能。 2021年9月のアップデートにより必殺技演出中に「個別撤退」が可能となった。 ただし撤退は必殺技を撃った後に行われるため、必殺技中の撤退操作で必殺技のダメージに撤退時の固有効果を載せるといったことはできない。 画面右上の「全軍撤退」を押すと戦闘をその時点で終了し、敗北扱いとなる。 必殺技と固有効果 各キャラクターは、それぞれ1つづつ「必殺技」と「固有効果」を持っており、 その内容が各キャラクターの個性付となっている。 覚醒強化を行うことにより、性能を大幅に強化する事ができる。 関連リンク：キャラクターの役割分け 必殺技・固有効果 確認画面 必殺技 必殺技は、戦闘中にキャラクターアイコン外周ゲージがMAXになる事で任意に発動可能が可能となる。 発動方法は、アイコンのクリック。もしくはオート。（設定で切り替え可能） ゲージがMAX状態ではない時にキャラクターアイコンをクリックすると、キャラごとの必殺技のオート発動設定をON/OFF出来る。 画面左下の「全員AUTO」ボタンでキャラクター全員のAUTO使用のON/OFFも可能。 外周部分……必殺技ゲージ 赤いゲージに先行して黄色に点滅している部分はステータスの必殺充填量を表している。 通常攻撃を行うと必殺充填量分の必殺技ゲージが増加する。 必殺技の発動後に攻撃周期はリセットされる。 味方キャラクターがスタン中は必殺技ゲージは溜まらない。 攻撃をミスしても命中した時と同様にゲージは増える。反撃、連撃中の追加攻撃ではゲージは増えない。 攻撃タイプの必殺技は次の3タイプに分類され、例外もあるが概ねこのような特徴を持つ。 タイプ攻撃対象ダメージ倍率(覚醒強化時) 敵単体1体6倍(9倍) 敵横一列最大3体(前列1体+後列2体)4倍(6倍) 敵全体最大5体(敵の「かばう」無効)2倍(4倍) 敵の必殺技 2021/12/22のアップデートで敵キャラクターの必殺ゲージが可視化された。 長い体力バーの右横にランプがあり、黒(無点灯)→青→緑→橙→赤と進行していき、最後の赤ランプが点灯すると必殺技を撃たれる。 ただし、必ず黒から始まるわけではなく、出現時にいずれかの色のランプが点灯している敵も居り出現と同時に必殺技を撃たれるケースも存在する。 ランプが無い敵は必殺技を撃ってくることは無い。 敵の必殺技は撃ち放題というわけでは無いらしく、何度か撃つとゲージが消失するケースがある。 必殺技ゲージの計算式 必殺技ゲージの計算方法 ・キャラクターが通常攻撃を行うと必殺充填量％分増加する。(増加するタイミングは攻撃モーションが終わった瞬間) ・必殺技ゲージは1%/secで自然増加していく。 ・攻撃モーション中は攻撃周期は停止する。 必殺技ゲージがMAXまで溜まる時間 = 攻撃回数 × (行動速度 + 攻撃モーション時間) + α - 初期配置ボーナスα > 行動速度 の場合 = (攻撃回数 + 1) × (行動速度 + 攻撃モーション時間) - 初期配置ボーナス 攻撃回数 = (100 - 必殺ゲージ初期値) / (必殺充填量 + 行動速度 + 攻撃モーション時間) ※小数点以下四捨五入 α = 100 - 必殺ゲージ初期値 - 必殺充填量 × 攻撃回数 - (行動速度 + 攻撃モーション時間) × 攻撃回数 攻撃モーション時間：各キャラごとの攻撃モーションにかかる時間（ツカサ0.5秒、デュエル0.65秒程度など） 必殺ゲージ初期値：ドリル系、ノノノ固有、イザナエル固有などの合計値 アルゴルの必殺技(+30%)を途中で撃つと想定する場合も初期値として扱って計算してよい。(対象キャラのゲージが70%になる前に撃つものとする) α：最後の攻撃からゲージMAXまでにかかる自然増加の秒数 ただし、α ＞ 行動速度 の場合は攻撃回数を+1してMAXまでの時間を計算し、αは除く。(自然増加でMAXになる前に次の攻撃が先にくるため) 初期配置ボーナス(期待値) = 行動速度 × 0.5 ※初期配置の場合 初期配置キャラには初期配置人数によって枠ごとに決まる80%から20%の攻撃周期ゲージから始まる。 初期配置人数によらず1キャラあたり期待値50%になっている。 後から出てくる場合は0、助っ人は70～80%、助っ人を呼んだ場合のそれ以外のキャラの期待値は30～42%程度に下がる。 ▼例：行動速度6sec 必殺充填量3.5 のキャラクター(閃忍ツカサ)でスーパードリルLV5(初期値+40)を装備して途中出撃した場合 攻撃回数 = (100 - 必殺ゲージ初期値40) / (必殺充填量3.5 + 行動速度6 + 攻撃モーション時間0.5) ※小数点以下四捨五入 60 / 10 = 6 攻撃回数は6回。割り切れない場合は小数点以下は切り捨てる。 必殺技ゲージがMAXまで溜まる時間 = 攻撃回数6 × (行動速度6 + 攻撃モーション時間0.5) + α- 初期配置ボーナス0 6 × 6.5 + α - 0 = 39 + α 溜まる時間は39秒 + α。 α = 100 - 必殺ゲージ初期値40 - 必殺充填量3.5 × 攻撃回数6 - (行動速度6 + 攻撃モーション時間0.5) × 攻撃回数6 α ＝０ 計算上は6回目の攻撃と同時、39秒ジャストでゲージがMAXになるはずである。 実際の計測でも39秒過ぎ、6回目の攻撃が終わるとすぐにゲージがMAXになるので、概ね正しいと分かる。 ゲージがMAXになるまでの時間が計算と違うのは何故か？ 計算に使用した攻撃モーション時間が正確ではない 攻撃のタイミングで敵フィールドに攻撃対象が存在しない時は攻撃を行わずに攻撃周期が進んでしまいゲージが増加しない 魔女ユウガや狂の秋道姫路といった通常攻撃の代わりに固有効果が発動するタイプの場合はその分ゲージが増加しない 連撃が発生して攻撃モーション時間が延びた 敵の攻撃でスタンした 速度バフ/速度フィールドバフの影響 初期配置ボーナスの影響 敵に通常攻撃を高頻度で当て続けるとずっと食らいモーションのままで攻撃されないことがあり(エロコマンダーが再現しやすい)、 味方の場合そこまで攻撃が集中されるケースがまず無いがもし起こればその場合は必殺技ゲージも遅延すると想像できる。 etc. 必殺技発動までの主な時間 早見 あくまで目安として参考程度に 必殺充填量1010.51111.51212.51313.51414.515 行動速度1.518(9)16(8)16(8)16(8)16(8)14(7)14(7)14(7)14(7)14(7)12(6)※14.8から6回攻撃で技発動 ()の中は攻撃回数 ※攻撃モーション時間0.5。ゲージ配布、連撃、反撃は無視。 固有効果 パッシブスキル以外に出撃完了時、撤退時、一定量のスタミナ減少時など様々なタイミングで効果が発動する。 「ハニージッポ」を装備し発動条件を再度満たしても1回のみと限定されているものは発動できない。(必殺技も同様) なお、撤退時に発動するタイプの固有効果は出撃待機中(GO!表示)のキャラを手動で撤退させても効果を発揮する。 戦闘開始直後の味方キャラの固有効果は出撃順番通りに左側のキャラアイコンから右側に向かって発動する。 2023/4/26のアップデートにより、 戦闘において、同じ値に影響を及ぼす固有効果が敵と味方で同時に発生した場合、処理の順番が敵→味方、だったものを、味方→敵、に変更となった。 対象ロック 敵キャラクターのアイコンをクリックすることでその敵キャラクターを集中して攻撃させることができる。 もう1度クリックするとロックが解除される。 敵キャラクターの中には「かばう」能力を持っているキャラクターがおり、その場合は「かばう」が優先される。 攻撃、連撃、反撃、命中・回避判定、クリティカル 攻撃 キャラクターのアイコンの周りを回っている☆が一周するとキャラクターが攻撃する。(☆が一周してもそのタイミングで攻撃可能な敵がいないと攻撃せずに次の周回が始まる) 自分の必殺技を発動すると☆は初期位置に戻る。（☆がもう少しで一周しそうなタイミングでも攻撃せずに次の周回が始まる） 1回の攻撃ごとにかかる時間はキャラクターごとに設定された行動速度の値を参照し、速度UP・DOWNのバフ・デバフで変化する。 攻撃モーション中は攻撃周期の☆は停止するのでステータスの行動速度より実際の行動速度は遅くなる。(連撃発生中は攻撃モーションが長くなるので特に遅延する) 攻撃は物理と魔法の2タイプがあり、それぞれ攻撃力と防御力が設定されている。 魔法タイプの攻撃は必中だが与えるダメージが20%減衰(ただし必殺技は表記どおりの倍率で減衰しない)する。 初期出撃のキャラは左から順に☆の開始位置が先になっており(初期出撃人数が多いほど早い)、最初の一撃に限り早く攻撃出来る。 連撃 通常攻撃時、キャラクターごとに設定された連撃率を参照し、連続で攻撃することがある。 連撃するごとに与えるダメージが20%減衰するが、下限は30％になるので、40％からの減衰は20％ではなく10％となる。(80%⇒60%⇒40%⇒30%⇒30%⇒…) ダメージ減衰は70%まで。(2021-03-24のアップデートで変更) 必殺充填量による必殺ゲージの増加、命中判定、スタン発動率の判定、レイドバトルでのクリティカルは連撃では発生しない。 通常攻撃及び連撃中は行動ゲージが進まないので連撃が発生しすぎると行動周期が遅くなり結果、必殺技の発動が遅くなる。 キャラが攻撃中に敵味方問わず誰かが必殺技を発動すると、連撃含めた攻撃モーションが終わるまで戦闘そのものが一時停止しこのデメリットを踏み倒す。 この挙動は必殺が飛び交う戦闘では勝手に発生しているが、手動操作で狙って発生させることもできる。 この現象による硬直時間の短縮期待値は硬直時間の二乗に比例する。つまり連撃に特化したキャラほど連撃率を延ばす事による恩恵が大きい。 連撃は発生する度、連撃率を10%ずつ減らして再判定している。※ゲーム内に説明はなく高連撃率キャラの行動約500回分からの推定 この仕様は固有効果等で1回は必ず連撃する効果を持つキャラでも連撃1回目から適用される。（必ず連撃するキャラの連撃率が50%の場合、連撃1回目は確定、連撃2回目の発生率は40%) 連撃期待値計算表(10%刻み) 連撃期待値計算表(10%刻み) ・水色セルがその連撃数に到達できる確率。 ・2026/2時点での最大連撃率は連撃率70%キャラにコンボ+チョコットGPTを装備した150%。必ず6連撃する。 連撃数123456789101112131415連撃期待値 連撃率10%10%0%0%0%0%0%0%0%0%0%0%0%0%0%0% ←×↑10%0%0%0%0%0%0%0%0%0%0%0%0%0%0%0.1回 連撃率20%20%10%0%0%0%0%0%0%0%0%0%0%0%0%0% ←×↑20%2%0%0%0%0%0%0%0%0%0%0%0%0%0%0.22回 連撃率30%30%20%10%0%0%0%0%0%0%0%0%0%0%0%0% ←×↑30%6%0.6%0%0%0%0%0%0%0%0%0%0%0%0%0.36回 連撃率40%40%30%20%10%0%0%0%0%0%0%0%0%0%0%0% ←×↑40%12%2.4%0.24%0%0%0%0%0%0%0%0%0%0%0%0.54回 連撃率50%50%40%30%20%10%0%0%0%0%0%0%0%0%0%0% ←×↑50%20%6%1.2%0.12%0%0%0%0%0%0%0%0%0%0%0.77回 連撃率60%60%50%40%30%20%10%0%0%0%0%0%0%0%0%0% ←×↑60%30%12%3.6%0.72%0.08%0%0%0%0%0%0%0%0%0%1.06回 連撃率70%70%60%50%40%30%20%10%0%0%0%0%0%0%0%0% ←×↑70%42%21%8.4%2.52%0.51%0.06%0%0%0%0%0%0%0%0%1.44回 連撃率80%80%70%60%50%40%30%20%10%0%0%0%0%0%0%0% ←×↑80%56%33.6%16.8%6.72%2.02%0.41%0.05%0%0%0%0%0%0%0%1.95回 連撃率90%90%80%70%60%50%40%30%20%10%0%0%0%0%0%0% ←×↑90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%0%0%0%0%0%2.66回 連撃率100%100%90%80%70%60%50%40%30%20%10%0%0%0%0%0% ←×↑100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%0%0%0%0%3.66回 連撃率110%110%100%90%80%70%60%50%40%30%20%10%0%0%0%0% ←×↑100%100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%0%0%0%4.66回 連撃率120%120%110%100%90%80%70%60%50%40%30%20%10%0%0%0% ←×↑100%100%100%90%72.01%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%0%0%5.66回 連撃率130%130%120%110%100%90%80%70%60%50%40%30%20%10%0%0% ←×↑100%100%100%100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.61%0%0%6.66回 連撃率140%140%130%120%110%100%90%80%70%60%50%40%30%20%10%0% ←×↑100%100%100%100%100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%7.66回 連撃率150%150%140%130%120%110%100%90%80%70%60%50%40%30%20%10% ←×↑100%100%100%100%100%100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%8.66回 必ず連撃+連撃率30%100%20%10%0%0%0%0%0%0%0%0%0%0%0%0% ←×↑100%20%2%0%0%0%0%0%0%0%0%0%0%0%0%1.22回 必ず連撃+連撃率40%100%30%20%10%0%0%0%0%0%0%0%0%0%0%0% ←×↑100%30%6%0.6%0%0%0%0%0%0%0%0%0%0%0%1.36回 必ず連撃+連撃率50%100%40%30%20%10%0%0%0%0%0%0%0%0%0%0% ←×↑100%40%12%2.4%0.24%0%0%0%0%0%0%0%0%0%0%1.54回 必ず連撃+連撃率60%100%50%40%30%20%10%0%0%0%0%0%0%0%0%0% ←×↑100%50%20%6%1.2%0.12%0%0%0%0%0%0%0%0%0%1.77回 必ず連撃+連撃率70%100%60%50%40%30%20%10%0%0%0%0%0%0%0%0% ←×↑100%60%30%12%3.6%0.72%0.08%0%0%0%0%0%0%0%0%2.06回 必ず連撃+連撃率80%100%70%60%50%40%30%20%10%0%0%0%0%0%0%0% ←×↑100%70%42%21%8.4%2.52%0.51%0.06%0%0%0%0%0%0%0%2.44回 必ず連撃+連撃率90%100%80%70%60%50%40%30%20%10%0%0%0%0%0%0% ←×↑100%100%70%42%21%8.4%2.52%0.51%0.06%0%0%0%0%0%0%3.44回 必ず連撃+連撃率100%100%90%80%70%60%50%40%30%20%10%0%0%0%0%0% ←×↑100%100%80%56%33.6%16.8%6.72%2.02%0.41%0.05%0%0%0%0%0%3.95回 必ず連撃+連撃率110%110%100%90%80%70%60%50%40%30%20%10%0%0%0%0% ←×↑100%100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%0%0%0%4.66回 必ず連撃+連撃率120%120%110%100%90%80%70%60%50%40%30%20%10%0%0%0% ←×↑100%100%100%90.01%72.01%50.41%30.24%15.12%6.05%1.82%0.37%0.04%0%0%0%5.66回 必ず連撃+連撃率130%130%120%110%100%90%80%70%60%50%40%30%20%10%0%0% ←×↑100%100%100%100%90%72%50.4%30.24%15.12%6.05%1.82%0.37%0.04%0%0%6.66回 連撃はメインクエストとレイドで価値が若干変わってくる。 メインクエストにおいては一撃で倒せない相手を連撃で倒せることがあり、反撃封じたり敵の行動機会を奪ったりとメリットの方が大きい。 全体必殺アタッカーは必殺で数を倒すのが仕事なので装備枠が空いていても[コンボの謎]]を持たせるのは避けよう。 レイドにおいては敵が倒れないので上記のメリットがなく、連撃のせいでFEVER中に必殺が間に合わない状況ではデメリットになる。 ただし大半のアタッカーは十分に育成すればFEVER中に撃てる必殺回数は同じ(2回)になる。必殺回数が同じならダメージ差は連撃で付くので最終的にはメリット効果になる。 ※低連撃率によってFEVER時間外の必殺が1回増えても、FEVER中の連撃3回と等価なのでほぼ意味がない。 ステータス以外に必殺を早める要因を持つ一部のキャラはFEVER中の必殺3回目が間に合うことがある。そういったキャラは連撃率は低い方が都合が良くゲーム内でも低めに設定されていることが多い。 極端に連撃に特化したキャラは20回以上の連撃も可能で必殺2回のキャラのダメージを超えてくる。 最終的に火力が出ればいいアタッカーと違い、サポート向きのキャラにとってはデメリットの方が大きい。 反撃 キャラクターが敵キャラクターから攻撃を受けたときに反撃することがある。 確率はキャラクターごとに設定された反撃率を参照し、必中でダメージ量は通常攻撃の50%。 敵キャラクターも反撃を行い、必中でダメージ量半減なのは同じ。 味方の後列に配置されたキャラクターは敵によっては反撃を受けない場合がある。 敵の後列に対しては味方の反撃はしっかり行うので心配はいらない。 命中判定、回避判定 Q.回避力が高いのに敵の攻撃に当たる。 A.通常攻撃は、まず攻撃側の命中力を元に命中判定を行います。 自軍が防御側の場合のみ、 攻撃側の命中力よりも回避力が高ければ、 攻撃側の命中力が２５％減少した状態で命中判定が行われます。 命中判定が成功すると回避判定は行わず、攻撃は命中します。 命中判定で失敗した場合、次に防御側の回避力を元に回避判定を 行います。 回避判定で失敗した場合、攻撃は命中します。 なお、通常攻撃が魔法であれば、 固有効果で「攻撃を全て回避」効果がある場合を除き、 必ず命中します。 必殺技は命中判定が行われず、必ず命中します。（公式Ｑ＆Ａより） ※2025/9/3より味方回避力が敵命中力より高い場合、敵命中力を25%減らして(×0.75して)判定する仕様が追加された。 敵の命中判定が失敗しない限り、回避判定が行われない仕様のため味方キャラの回避力を100以上にしただけでは敵の物理通常攻撃をすべて回避することはできない。 (100%-敵命中力[%])×味方回避力[%]が実際の回避確率となる。 回避によって敵からのダメージを減らすためには回避アップ効果と命中ダウン効果の併用が重要。 なお反撃は必中であるため、回避によって味方全員のダメージを0にし続けることはゲーム仕様上困難。 クリティカル(レイドのみ) レイドでは命中バフを付与することで効果量％でクリティカル判定が発生するようになる。 対象は通常攻撃及び必殺技ダメージで1.25倍のダメージとなる。連撃はクリティカルしない。 ダメージ表示の色が通常の黄色から濃いオレンジ色に変わり大きくなるのが特徴。（レイド以外クエストでの属性一致ダメージと同演出） 状態異常（状態変化） 状態異常には以下のものがあります。 ※各種状態変化のアイコンは、キャラクターアイコン内に表示されます。 状態アイコン説明 毒毒状態になると、一定時間(約10秒)スタミナの自然減少量が２倍になります。 魅了魅了状態になると、一定時間(約20秒)自軍に攻撃を行うようになり必殺技が使用不能になります。撤退は可能なので、危険と思えば撤退させるのも有効です。 スタンスタン状態になると、一定時間(約10秒)行動不能となり、必ず敵からの攻撃が命中するようになります。必殺技ゲージも溜まらなくなり、固有効果による自動回復なども発動しません。 呪縛呪縛状態になると、一定時間(約15秒)必殺充填量が０となります。（必殺技ゲージの自然増加量は変化しません） 超昂大戦においては「状態異常」と「デバフ効果」は別種の物として扱われる 必殺技や固有効果の「状態異常解除」と「デバフ解除」の効果は分けて考える必要がある。 スタンの発生判定がどうなっているかは不明だが、レイドボスの模擬戦で検証すると味方のスタン発動率がボスのスタン抵抗率以下の場合はスタンにならないことなどから 「攻撃側スタン発動率 - 防御側スタン抵抗率＝スタン発生率」となっている可能性が高い。 毒・魅了・呪縛にいたっては発動率・抵抗率のステータスも無いため、やはり発生判定は不明だが、こちらもレイドボスの模擬戦で検証すると 基本的に通常時の発動率および抵抗率は0%であり、単純に「その攻撃の発動率(必殺技など)＝発生率」となっている可能性が高い。 敵に毒状態を付与する行動は存在しない。 敵にスタンと魅了をかけた時は味方と同様の効果が発生する。 敵に呪縛をかけた時は、敵の必殺技ゲージの増加速度が7～8割程度減少する。 バフ（強化）／デバフ（弱化） バフは対象にプラスの効果を デバフは対象にマイナスの効果を与えます。 必殺技や固有効果の発動で付与されます。 例：味方に速度アップの効果がかかっている → 味方への速度バフ 味方に速度ダウンの効果がかかっている → 味方への速度デバフ 敵に速度アップの効果がかかっている → 敵への速度バフ 敵に速度ダウンの効果がかかっている → 敵への速度デバフ また、超昂大戦においてはデバフと状態異常を分けて考えます。 状態異常：スタンや毒などキャラクターに発生する特殊な症状 デバフ：攻撃ダウンや速度ダウンなどキャラクターのステータスに負の効果を与える効果 状態異常はデバフの一種では無く、あくまでデバフとは別のカテゴリとして扱われるため、 必殺技や固有効果の「状態異常解除」と「デバフ解除」の効果は分けて考える必要があります。 加えて、超昂大戦独自要素としてバフとデバフには 「キャラクター対象」の物と「フィールド対象」の物の2種類があります。 キャラクター対象「バフ／デバフ」 各キャラクターを対象として各種効果（バフはプラス効果、デバフはマイナス効果）を及ぼします。 効果は様々で、味方キャラクターや敵キャラクターの固有効果や必殺技などで付与されます。 フィールド対象「バフ／デバフ」 戦闘時、対象の味方および敵フィールドに対し行われるバフ／デバフです。 キャラクター対象のバフ／デバフと違い、一定時間、敵や出撃キャラクターが入れ替わっても対象フィールドにいる全員に影響を及ぼすので効果は大きいです。 効果の重複について (重要)「キャラクター対象」のバフ・デバフと「フィールド対象」のバフ・デバフは同じ効果の物の同士で数値が加算されます。 反対に「キャラクター対象」の「バフ・デバフ」同士、「フィールド」対処の「バフ・デバフ」同士の場合は、同じ効果の物であっても効果は重複しません。最も効果量の大きい物のみが適用されます。 同一効果で効果量と効果時間の異なるキャラクター対象バフが重複した場合の例 経過時間0秒後10秒後20秒後30秒後40秒後 効果量40%効果時間20秒の場合40%40%40%0%0% 効果量30%効果時間30秒の場合30%30%30%30%0% 実際の効果量40%40%40%30%0% （例：効果が重複した場合、効果量の多い方しか効果は得られないが共存はしている。 先に40%アップが切れた時点から残り時間分だけ30%アップの効果が得られる） 効果の上書きについて 同一の対象に対して、効果が対になるバフ・デバフ（例：速度アップと速度ダウン）が付与された場合、 (重要)後から付与された効果が先に付与されていた効果を一方的に上書きします。 対になるバフとデバフの間で数値の相殺が行われることはありません。 この処理は敵味方に関係ありません。つまり敵にかけられたデバフを味方のバフで上書きできます。(逆も有り得ます) フィールド対象の場合であっても処理は同様です。 バフ／デバフ一覧 ▼バフ／デバフには以下のものがあります。(レイドでは違う効果を発揮するものがあります) バフ／デバフ名アイコン説明 攻撃攻撃力／魔法力が変化する 防御防御力／魔法抵抗力が変化する 命中命中力が変化する 回避回避力が変化する 速度行動速度が変化する（フィールドが対象の場合、移動速度と出撃速度にも影響する）必殺技ゲージの自然増加量（通常は１秒ごとに１％ずつ）が変化する 与ダメージ（与ダメ）最終ダメージが変化する スタン抵抗率スタン抵抗率が変化する ヘイトヘイトが増減する（増加がターゲティング、減少が物陰に隠れる）状態変化中はヘイト値が最大、最小の数値に固定される ※各種アイコンはキャラクター対象のバフ／デバフはキャラクターアイコン内に、フィールドバフ／デバフは画面上側のFIELD部に表示されます。 ※ヘイトは公式ヘルプではバフ／デバフと特殊状態には数えられていません。 特殊状態 戦闘時、対象に影響を及ぼす効果です。 ▼以下のものは「特殊状態」と呼ばれます。(バフ消しやデバフ消しの効果には影響されません) 特殊状態名アイコン説明 回復毎秒ダメージが回復する 継続ダメージ毎秒ダメージが発生する 時間停止(フィールド専用)対象フィールドの時間が停止する 戦闘中における装備アイテムのアイコン表示 装備していると状態変化やバフ／デバフと同じくキャラクターアイコン内にアイコンが表示される装備アイテムが存在します。 装備アイテム名アイコン説明 ハニージッポ戦闘不能になると全快する パラメータ強化の限界 キャラクターの各種パラメータは覚醒強化によって強化することが可能ですが、 下記のパラメータは装備や覚醒での強化に限界があります。 ・物理ダメージ軽減：最大８５％まで ・魔法ダメージ軽減：最大８５％まで ・行動速度：最小１．５secまで ・必殺充填量：最大２０％まで ※戦闘中のバフやフィーバーによる速度上昇といった強化には、こちらの数値は適用外となります。 所属勢力 ゲーム内のプレイアブルキャラクターは全て以下の勢力のうちのどこか1つに所属します。 区分勢力名紋章説明 戦士戦士(異界)ダイビートにのみ所属する戦士のうち、異界から召喚された者たちの勢力。『超昂天使エスカレイヤー』が出典の勢力も含まれる。コラボキャラの大半が所属する。 戦士(現界)ダイビートにのみ所属する戦士のうち、異界から召喚されていない者たちの勢力。現地登用組という意味では神騎(地上)に近い。 閃忍閃忍(想破)『超昂閃忍ハルカ』が出典の忍者(閃忍)の勢力。組織としての正式名称は「想破上弦衆」 閃忍(久世)超昂大戦オリジナルの閃忍の勢力。組織としての正式名称は「久世上弦衆」 神騎神騎(天界)『超昂神騎エクシール』が出典の天使(神騎)の勢力。 神騎(地上)人間の神騎の勢力だが、天界由来と別組織という訳では無い。 魔女超昂大戦オリジナルの魔女の勢力。 所属勢力のゲーム中の特徴 所属する勢力によってキャラクターの能力傾向が違ったり、特殊な能力があったりする事はありません。 これら勢力分けは、主にイベントやレイド等バトルコンテンツにおける特効勢力の区分として使用されます。 また、一部に特定の勢力を指定して効果を発動する、各種バフ効果を持つキャラクターが存在します。 例：エスカレイヤー・閃忍ハルカ・神騎エクシールの各キャラが持つ固有効果（レジェンドバフ）などが該当します イベント特効勢力や必殺技・固有効果の効果対象として指定される範囲は、 大まか区分である「戦士」「閃忍」「神騎」「魔女」の4区分である場合と、 各勢力をより細かく分けた7分類である場合の両方のケースがあります。 現在、味方側の勢力区分が戦闘処理時における相性判定に使用される事はありません。 例：閃忍勢力のみがダメージアップしたり、被ダメ増加が発生するようなタイプの敵は存在しない また、特定の勢力のみが出撃可能、もしくは出撃不可能なコンテンツも存在しません。 出撃制限を受ける場合があるのは下記の属性要素となります。 属性 ゲーム内には「太陽」「月」「星」3つの属性が存在する。 全てのキャラクターは、必ずこの3つの属性のうちのどれか1つを持っている。 キャラクターアイコンの背景色で属性を判別することが可能。 ただし、一般のゲームに存在するような属性の相克による複雑なダメージ増減のシステムは存在しない。 （3すくみ要素等は無い） 敵キャラクターは一部のみが属性を持っており、一般的な敵は全て属性を持たない「属性無し」キャラとなっている。 属性持ちの敵キャラクターは、HPバー左に属性アイコンが付与されているため、視覚的に判別する事が可能である。 （HPバーにアイコンのついてない一般的な敵は全て属性無しである） 属性の一致するキャラで攻撃を加えると、与ダメージが1.2倍に増加する（被ダメージも上がるかどうかは不明） ダメージ表示の色が通常の黄色から濃いオレンジ色に変わるため視覚的に確認できる（レイドバトルでのクリティカルと同演出） また、属性の一致しないキャラクターで攻撃しても、特にペナルティ等は発生しない。 ゲーム内においては、属性制限ステージに遭遇しない限り、あまり意識される事の無い要素となっている。 キャラクターの属性は、アイテム「チェーイングガム」などによって、後から入れ替える事も可能である。 「ビートスター・マリナ」など一部のキャラクターは、属性の変更によって必殺技の性能が変化する。 「戦部ユキタカ」等の一部サポーターは、特定の属性のキャラクターのみを性能アップする特性を持っている。 プレイヤー装備の「太陽のトウ」「月のウサギ」「星のカーフィー」でそれぞれの属性キャラの与ダメージがアップする。 弱点効果 上記の「太陽」「月」「星」とは異なり、一部敵キャラクターには 装備「ゴブスレー」「フーマンキラー」「ヌンジャスプレー」および「神騎ベラトリクス」等の一部キャラの固有効果によって、弱点効果と呼ばれる特徴が付与される。 これら装備キャラ及び、固有効果持ちのキャラからの攻撃によって、対象となる敵に与えるダメージが1.2倍に増加する。 ただし、上記の属性一致による与ダメージの上昇と効果は重複しない。 特殊属性 上記「太陽」「月」「星」とも「弱点特性」とも異なる、一部のキャラクターだけが持つ特殊な属性。 特殊属性の付与は、主にそのキャラが排出される限定ガチャのシーズンイベントに起因する。 例えば、バレンタインガチャから排出されたキャラには「バレンタイン属性」が、フェスガチャから排出されたキャラには「超昂属性」といったように、 各イベントに応じた特殊属性が付与されているケースが多い。 （ただしシーズンイベントに起因しないメガネ属性なども存在する） ゲーム内に存在する特殊属性の一覧は下記ページより確認する事ができる。 関連ページ：特殊属性一覧 特殊属性確認画面を開く 特殊属性確認画面 現在、特殊属性は、主にキャラのバフ能力の発動トリガーとなっている事が多い。 例として「真夏のハルカ」は、同じ「真夏属性」を持つキャラからバフ効果を得る事が出来、 また「ハロウィンニコール」は、同じ「ハロウィン属性」を持つキャラの火力をアップする事が可能である等、 同一の「特殊属性」キャラを集中運用する事によって、プラス効果をもたらす必殺技や固有効果が複数存在する。 特殊属性が、敵との攻防において相性判定に使用されるようなケースは存在していない。 ダメージ補正 弱点効果(属性一致)：120% 反撃：50% 連撃：70% (2021-03-24のアップデートで変更) クエストをクリアするための基本的な考え 優先出撃キャラクターに精鋭を配置する 制限時間内に一定数の敵を倒せないとボーダーとなり、戦闘に敗北となってしまう。 よって、最初に精鋭を出撃させて敵の撃破数を稼いでおくこととなる。 前列と後列を意識する 近距離攻撃のキャラは前列に3名までしか出撃できないため、最大人数の5名が場にいられるように、後列に遠距離攻撃のキャラを2名以上は配置するようにする。 画面右下の出撃準備中のキャラクターが近距離攻撃か遠距離攻撃か(キャラクターアイコン左上が黄色なら近距離攻撃、青色なら遠距離攻撃)を見て、 前列が詰まっている場合は撤退させることも必要になる。そうしないと後続が出てこられない。 ↓前列が詰まっているので、スタミナが余っているもののビートバイカー・マッハを撤退させて後続を出すようにする。 （※この場合はバフが乗っているので悩むところではある。） 固有効果や必殺技を把握する 固有効果や必殺技によりキャラクターにバフ(強化)をかけたり、敵キャラにデバフ(弱化)をかけることが可能なキャラクターが存在する。 固有効果を考えてキャラを優先出撃させたり、スタミナが少なくても残す場合がある。 戦線を守る 重要な考え方。 人数が少なくなると少ない人数で複数の敵の攻撃を受けることになる。 出撃は1人ずつしかできないため フィールド上のキャラクターが敵から集中攻撃を受けて撤退 ↓ 新しく出撃したキャラクターが出撃時間(行動できない)に敵から攻撃を受ける ↓ 行動可能になったときにはスタミナが少なく、また敵から攻撃を受けて撤退 ↓ 以下ループ という負のスパイラルに陥ることになる。これを防ぐことが重要。 基本戦術 クエストをクリアするための基本戦術について 一番体力の少ない敵をロックする RPGの基本でもあるが、敵の頭数を減らすことでダメージを減らすことができる。 一番体力が低い敵から優先して撃破すること。 必殺ゲージを持つ敵から倒す 必殺ゲージのランプがある雑魚敵は時間経過で必殺技を撃ってくる。 普段は意識せずとも防げるが、固い相手や敵が逐次投入されるラッシュ時には食らいやすい。 特にラッシュ時は敵前列が倒したそばから投入され後列の敵を放置しがちになるので、ロックを使って必殺技の前に撃破したい。 ↑ゲージが赤くなったら必殺技を撃たれる寸前だ。こうなる前にさっさと倒してしまおう。 状態異常を引き起こす敵を優先的に狙う 雑魚敵の中で最も厄介なのが状態異常の魅了を引き起こすパピヨン系（蛾）の敵。 魅了は閃忍ニャンコなどの固有効果で無効に出来るメンバーを入れる以外には防御手段がない上に魅了されてしまったキャラは手動で撤退させるくらいしか対処法が無い。 （一応、六の法杖セラフィールの固有効果や魔女レイヴンの必殺技などで解除することは可能） 画面から目を離していたら攻撃力の高いキャラが魅了されて壊滅していた・・・という事態を引き起こすことがある。 パピヨンが出現したら即ロックして優先的に攻撃するのが安全だ。 ↑魅了されたアキレスの強力な攻撃が味方のエスカレイヤーを襲う。こうなると悲劇である。 スタミナを揃えない 味方キャラクターのスタミナが全員同じくらいの場合、同じタイミングで複数のキャラクターが離脱してしまう可能性が高い。 片方のキャラクターを優先して離脱させるなどして、味方のスタミナ（離脱タイミング）に差をつけること。 同じくらいスタミナのキャラクターが3人以上いる場合は危険。 左2人のスタミナが揃っているため、ほぼ同時に2人が撤退してしまう可能性がある。できれば回避したい。 優先出撃でも体力が低いキャラと高いキャラを混ぜて出撃させること。 バフを使う キャラクターにバフをつけられるキャラクターをうまく使うこと。 エスカレイヤー、閃忍ハルカ、神騎エクシールはそれぞれ戦士、閃忍、神騎のキャラクターに対してバフを付与できる。 優先出撃枠を使って固めて出撃させることで殲滅力の増加が期待できる。 ↑エスカレイヤーの固有効果「レジェンド戦士＋」で、開始直後から味方の戦士3人に強力なバフをかけている。セオリーの一つだ。 助っ人のゲージを見る 助っ人はオート操作（＝必殺技が溜まったらすぐ使用する）である。 全体必殺技を複数体に向けて使用してもらえるように敵の数を調整するとよい。 ↓今いる敵を倒した次に敵が5匹出現する場合、助っ人ハルカの必殺技が溜まる前に今の敵を片付けると5体に対して必殺技を撃ってくれる。 発展的な戦術 基本的な戦術ができてきたらこちらにトライするとよい。 戦線を崩壊させないための考え方 戦線が崩壊する代表的なケースは一度に複数キャラクターが撤退してしまい、新しいキャラクターが戦線に到着する前に残ったキャラクターも倒されてしまうようなケースである。 なぜそのような状況になってしまうのか？ 端的に言うとメンバーの交代がうまくいっていないからである。 キャラクターのスタミナは時間経過につれて減少するため、交代が必要になる。 一時的に味方の人数が減ってしまうため、残った味方が集中攻撃を受けて倒されてしまうと戦線は崩壊する。 そうならないような工夫をする必要があり、例として以下のような方法がある。 敵の数が少ない時に交代する 敵の数が少ない時に交代すると残った味方が受ける攻撃も少なくなり、戦線は崩壊しづらい。 数的有利かどうかを意識するとよい。 ↓敵が1体のときを狙って交代した図。瞬間的に攻撃は1回しか行われず、安全に交代できる。 フィールド上の敵を一時的に全員倒して交代する 敵にも復活の時間があるため、敵の復活の時間を利用して交代すると戦線は崩壊しづらい。 （※理由は後述するが、個人的には推奨しない。） ↓必殺技で敵を一時的に全滅させることを見越して交代を行った図。この瞬間は敵の攻撃が行われないため安全。 敵にデバフをかけて交代する スタンやデバフなどを与えて交代することで攻撃の数や威力を減らすことができるため、戦線は崩壊しづらい。 ↓閃忍ツルコの必殺技でスタンさせた後の交代を狙う図(既に崩壊気味で良くない。。。) 敵の出現方法の種類 敵の出現にはいくつか種類があり、それによりこちらのアクションを変えるとよい。 状況によって必殺技ゲージの溜まっているキャラクターをわざと撤退させることもある。 敗北したステージがあった場合、なぜ敗北したかを考えるべき。（大抵はラッシュで崩れている） 小隊型 敵が複数体出現する。出現した全員を倒すまでは新たな敵は追加されない。 敵の数を減らすと数的優位が作れるため交代には適している。 味方の人数が少なかったり、スタミナの少ないキャラクターが多い場合はこのタイミングで交代をする。 必殺技ゲージが溜まっているからといって焦ってうたないように。必殺技を抱え落ちさせても戦線を整えることが優先される場面もある。 逐次投入型 敵が1～5体出現し、敵を撃破すると一定時間後に敵が追加される。 敵の数が多い時に交代を行うと戦線が崩壊する危険性があるが、敵の数が少ない時に交代すると安全に交代可能。 敵が2～3匹くらいで落ち着いているときはスタミナの少ないキャラクターを交代しておくとよい。 ラッシュ型 敵が5体出現し、敵を倒すと即時で追加される。 変に交代して戦線が崩壊すると、キャラクターが出現するたびにタコ殴りにされるため基本的に立て直しできない。 戦線が崩壊するときの原因は大体これ。ラッシュに対していかに凌ぐかがクエスト攻略の鍵となる。 敵を全滅させたときに交代を推奨しないのはラッシュ警戒である。 敵を全滅させる→ラッシュなのでスタミナMAXの敵が5体揃う という状態で交代をすると人数不利となってしまい、戦線崩壊の原因となるからである。 その他 ステージによっては敵が特殊な出現方法をすることがある。 敵の数は少ないが、強めの敵が一度に1～3体くらい出てくるステージ 中途半端な育成のキャラクターが必殺技が溜まる前に撤退しやすい。 強いキャラ優先出撃＋SSRキャラのバフを使って押し切るとよい。 スタミナが残っているように見えても一撃のダメージが大きいため、必殺技が溜まったら基本的には撃ってよい。 弱めの敵が大量に出てくるステージ 敵は弱いもののラッシュが多く、交代のタイミングが難しい。 また、テンポよく敵を倒せないと制限時間で敗北することもある。 一撃で相手を倒せて、行動速度の速いキャラクターや全体攻撃持ちのキャラクターを優先的に出撃させること。 盾持ちのフーマンを含む小隊 盾持ちフーマンが他の敵キャラクターを庇う。 盾持ちフーマンを優先して落としたくなるが、他の敵キャラクターを残すと必殺技を撃たれることがある。 また、盾持ちフーマンも1体扱いなので、撃破に時間をかけると制限時間で敗北になってしまいやすい。 盾持ちフーマンは単体必殺技で倒すようにして、通常攻撃は他の敵キャラクターを優先するとよい。 （盾持ちフーマンの体力が少なかったら通常攻撃で倒してもよい） ラッシュへの対応 ラッシュ中は敵の攻撃が激しいため、どうしても交代が必要なケースがある。 比較的安全に交代するための方法は相手にデバフをかけるか、2人の必殺技で相手を2回全滅させるである。 デバフをかけて味方キャラクターが受けるダメージを減らしたり、 敵を必殺技で全滅→敵出現→必殺技で全滅→敵出現とやっている間の時間で交代を進めるとよい。 おすすめデバフもちキャラ 鬼の斗羽大洋：一定時間、敵全体の攻防40%ダウン。交代中のダメージを抑え、敵の撃破率が上がることで一瞬攻撃されない状況を作れる。 氷のシズカ：敵全体に物理ダメージ 一定時間、速度20%ダウン。相手の速度が下がるため、攻撃を受ける回数が減る。 閃忍ツルコ：敵全体に物理ダメージ/スタン50%。スタン中の敵は攻撃をしてこないため交代しやすい。 他 戦線の立て直し 一度半壊した戦線の立て直しは難しい。基本的には戦線を壊さないことが重要。 敗色濃厚でも足掻く場合にできることとしては以下の通り。 とにかく新しいキャラクターの出撃を妨げないようにして、スタミナの低いキャラは撤退させるようにする。 全員オートをつかって、撃てる必殺技は全て撃ってもらう 体力の少ない敵から狙い、スタンした敵は後回しにして敵の攻撃回数を減らす。（敗北する場合でも、1体でも多く敵を倒せると宝箱が落ちる可能性もある。） 後続がすぐに戦闘に参加できるように、出撃速度や移動速度が早いキャラクターを育てておく。 コメントフォーム 宝箱について書いた者です。途中まで書きましたが一時保存していた内容が消えたのでまたの機会に続きを書きます。。。 -- [4/Lgq7Owfa6] 2020-12-03 (木) 01:56:46 おーこういうページ助かります個人的には盾っぽいものを持ったフーマンが出た時にそいつから潰すべきか、他のやつから潰すべきかとかも悩むので皆の意見聞けたら嬉しいですねー。その他この敵はこういう攻撃をするとかも。 -- [uTyqMtcUQms] 2020-12-03 (木) 01:59:54 と、思ったら敵の種類による対応って項目ありましたね。見落としてました（中身はまだっぽいですが -- [uTyqMtcUQms] 2020-12-03 (木) 02:01:02 盾持ちフーマン、かばうときはダメージ軽減されるし、出撃メンバーの火力によっては他は倒せるけど盾持ちフーマンだけ落とせない、ってことになるからマップによっては注意が必要だね。全力で盾持ちを狙うべき。何体も出てくるマップなんてそんなにないけど。 -- [fDCL3hAOt7M] 2021-01-10 (日) 15:03:20 出撃数よりキャラ所持数が多い時戦闘するキャラはランダムに選ばれるのでしょうか -- [ULCANz9t.zY] 2020-12-04 (金) 01:47:59 わかりやすい。乙。攻撃と必殺に関してだけど、必殺を使うと攻撃までのインターバルを表す星ってリセットされて最初からになるよね。攻撃を無駄にしないという観点だと星の位置を確認し、もうすぐ攻撃するなら攻撃を待ってから必殺を出す…ってのも大事かも -- [wJ4BHkUNliE] 2020-12-04 (金) 02:08:10 もしかして、敵も所属（種族）で、ダメージが入りやすい入りにくいがありますか？ときどき、雑魚なのにすごく撃破に時間がかかる時があったりするので。出撃メンバーとの相性なのかな？？？ -- [8chgAARUa7Y] 2020-12-13 (日) 10:41:05 見た目同じでもステージによってステータスにはかなり差がある。50数体とか沢山出てくるとこなら個々のスペックが低く一撃で倒せるけど、10前後だと数が少ない分かなりタフだし一発が重くて結構苦戦する -- [Y2/5PhOhUwc] 2020-12-13 (日) 14:44:46 後ダメージが増減するステータスとして属性がある。マークの付いてる敵を同じ属性で殴るとダメージが上がって、表記もいつもの黄色からオレンジになる。被弾や別属性に対して増減があるかは把握してない -- [Y2/5PhOhUwc] 2020-12-13 (日) 14:48:00 必殺技が発生してる時は、撤退とか次の必殺のONOFFが出来なくなるのは、バグですか？ -- [Bwv8AsZbkQg] 2021-01-12 (火) 14:53:27 必殺技中は全行動固まるため仕様だと思います。まあ必殺技だけ撃って撤退する人はいないと思いますが… -- [FY0B3mCGL2I] 2021-01-12 (火) 15:49:00 わかる。ＳＴ管理してて、次の子を早出ししたくても、必殺がＡＵＴＯ発動して、撤退がタイミング良く出来ないときあるよね。 -- [XnlPQ02dLxQ] 2021-01-12 (火) 18:09:59 出撃制限があるマップで出撃不可の属性を持ってる助っ人を選択した場合どうなりますか？ -- [hEyS/IEvutg] 2021-01-15 (金) 11:27:30 普通に出撃できます。これチュートリアルとか探してもどこにも書いてなくて、私も雑談版で教えてもらいました。上にも書き足しておこう。 -- [WNoo29HhD1M] 2021-01-15 (金) 12:03:24 制限無いんですね。ありがとうございます。 -- [hEyS/IEvutg] 2021-01-15 (金) 16:34:06 戦略的に狙ってできるかはともかく、連撃中に他のキャラの攻撃が当たって倒してしまえば、本来最初に攻撃したキャラに発動するはずの反撃を封じれそう。一桁になった連撃にも一応価値はある。終末環境（全員ロケット虎完全強化）になったら実用的な戦術になるかも。 -- [fDCL3hAOt7M] 2021-01-15 (金) 12:25:26 優先出動の組み合わせをあらかじめセットしておいて、ワンボタンで切り替えできるようにならないかな？忍者と神姫を切り替えるの、毎回選び直すのすごくめんどくさい。 -- [UVezykjxgQc] 2021-01-24 (日) 12:18:50 このゲームで処理落ちする原因戦闘中に必殺技が発動するタイミングで撤退を無理に行うと発生しやすい特に△３の時に落ちやすいなので速度を落としてから撤退させるのも手 -- [labl4IiMpH2] 2021-01-27 (水) 00:10:24 ステージセレクトしてローディング80％台ぐらいでブラウザのエラー出て止まった時、STロストしてたな。シナリオを連続して読むと割と止まりやすいけど、そのエラーメッセージと同じ（メモリ周り）。せめてステージスタート時点でST消費にならないものか…。 -- [BPo2uwI2DmA] 2021-07-09 (金) 21:37:57 このゲーム属性相性あったような気がするけど、有利不利の確認方法が分からない。太陽には月有利？ -- [xY8nxuxE3Yk] 2021-02-01 (月) 18:55:43 三すくみではなく、同属性で1.2倍ダメージ。太陽には太陽で攻撃すると有利。 -- [EQiiTzDUrGE] 2021-02-01 (月) 19:01:09 命中回避の文章、命中50回避50だと攻撃が当たる確率は75%じゃないですか？ -- [UPNf51iTEk.] 2022-02-11 (金) 08:11:35 メインクエストで初めて呪縛受けた。錫杖滅忍とかの通常攻撃だろうか。優先2セラフィールで治した -- [Gxe7mYUxnNI] 2022-11-10 (木) 19:04:06 実際検証してない文章だけ見た感想だけど 敵の命中より味方の回避が戦った時に敵の命中力の低下は25じゃなくて25%じゃない？ 敵の命中力が75の時に命中ダウン50に回避の方が上補正かかった時に75-50+25 =0って計算してるけど 多分(75-50)×0.75=18.75になるんじゃないかな -- [5KDYl20rwjM] 2025-09-07 (日) 18:58:53 75-(50+25)=0あるいは75-50-25=0ね -- [5KDYl20rwjM] 2025-09-07 (日) 19:00:56 検証してきた。 BユニVHディストバーンに命中ダウン80で回避力100のキャラが回避98/100 命中ダウン99で回避100/100 ので『攻撃側の命中力が２５％減少した』影響は命中ダウン19より小さい。記載の通り割合減少と思われる。 -- [kGPp72HFw0Q] 2025-09-07 (日) 23:05:05 ただこの結果は体感と差がある。ディストバーンの命中力85だとしたら、命中ダウン無しでは回避100キャラでも15%しか回避できないはずなんだけどそれ以上に避けてる気がする。 -- [kGPp72HFw0Q] 2025-09-07 (日) 23:15:48 命中85vs回避100だとして命中85に-25%補正で63.75になるので4割弱回避するようになるのではないでしょうか -- [xLysrBPsizs] 2025-09-07 (日) 23:57:58 ご指摘の通りです。なら合ってそうですね。 -- [kGPp72HFw0Q] 2025-09-08 (月) 01:41:53",-1))])}}});export{_ as __pageData,b as default};
