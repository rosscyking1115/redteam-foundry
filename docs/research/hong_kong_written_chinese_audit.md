# 香港書面中文來源審計：港式中文、粵字、HKSCS、教材同 OpenCC

**證據截點：2026 年 8 月 2 日**
**寫作口徑：香港書面中文；粵語例字全部附粵拼（Jyutping）同釋義。**
**來源原則：香港政府、香港院校、香港媒體及香港社群優先；技術標準用 Unicode、MySQL、OpenCC 原始檔。台灣資料只用作對照，內地資料不作香港慣例證據。**

## 摘要：先答最重要嗰幾點

1. **香港書面中文唔等於「台灣繁體字」。** 正式文本以現代標準書面中文為底，但有香港字形、香港詞彙、粵語及英語接觸痕跡；非正式文本可以直接寫粵語。香港學界確實將「港式中文」視為一種地域／社會／功能變體。
2. **「香港粵字有幾多個」冇一個官方封閉答案。** 《香港增補字符集》（HKSCS）亦明言，單字用途重疊，所以不逐字分類。本文列出一個可操作嘅日常核心表（55 個字／字組）；呢個係研究操作集合，唔係官方總數。
3. **HKSCS-2016 有 5,033 個字符：4,591 個中文字、442 個符號。** 按政府公開 JSON 逐碼位計算，3,317 個在 BMP、**1,716 個在增補平面**。全部 5,033 個都係原始 Big5 以外嘅香港補充項；其中 5,009 個承接 Big5-HKSCS 碼位，2016 新增 24 個只用 Unicode。
4. **「台灣讀者完全唔識讀」係合理假說，未係已量度事實。** 高風險例子包括 `嘅 ge3`、`咗 zo2`、`喺 hai2`、`哋 dei6`、`嗰 go2`、`啲 di1`、`㗎 gaa3`、`𡃁 leng1`、`𨋢 lip1`。要聲稱「幾多台灣人唔識」，必須做讀音／釋義實驗；字集或字典本身證明唔到讀者能力。
5. **OpenCC `s2hk` 唔會將書面普通話／國語句子變成書面粵語。** 原始設定只做簡繁復原及香港字形變體；現行 OpenCC 另有 `s2hkp` 加一個細小香港詞彙層。直接檢查 npm `opencc` 1.4.1：`HKVariants` 66 條、`HKVariantsPhrases` 272 條、`HKPhrases` 39 條；香港字典冇規則將 `的／了／在` 變成 `嘅／咗／喺`。
6. **「繁體中文網頁香港佔幾多」暫時答唔到。** `zh-hant` 係顯示變體，唔係作者來源；Common Crawl 同 zhTenTen 公開統計亦冇穩定分拆香港／台灣。聲稱香港或台灣「佔大多數」均屬 **未核實**。

## 1. 日常書面粵語核心字表

### 點樣理解「頻率」同「標準中文有冇呢個字」

- **極高／高／中／低**係跨香港論壇、社交媒體、字幕及日常訊息嘅定性分級，**唔係代表性語料計數**；目前未搵到可直接代表「全香港日常書面粵語」嘅抽樣頻率表。
- 「標準中文關係」分三類：`專屬語法／詞彙`（普通標準書面中文一般唔用）、`古字或另義`（字本身存在，但粵語讀音／意思屬香港用法）、`共用字、粵用`（字常見，但粵語搭配或讀音有地域性）。
- Big5 欄係以 Python `big5` codec 測試原始 Big5；HKSCS 欄以 `big5hkscs` 測試。`SIP` 指 Unicode Supplementary Ideographic Plane（Plane 2）。

| 字 | 粵拼 | 香港用法／意思 | 頻率 | 標準中文關係 | 編碼 |
|---|---|---|---|---|---|
| 嘅 | ge3；句末亦可 ge2 | 屬格、名詞化，約等於「的」 | 極高 | 粵語語法字 | Big5：否；HKSCS：是；BMP |
| 咗 | zo2 | 完成體，約等於「了」 | 極高 | 粵語語法字 | 否／是；BMP |
| 喺 | hai2 | 在、位於 | 極高 | 粵語語法字 | 否／是；BMP |
| 唔 | m4 | 不、不是 | 極高 | 粵語詞 | 是／是；BMP |
| 冇 | mou5 | 沒有 | 極高 | 粵語詞；字形在其他傳統亦有 | 是／是；BMP |
| 佢 | keoi5 | 他／她／它 | 極高 | 粵語代詞 | 是／是；BMP |
| 哋 | dei6 | 人稱代詞複數後綴：我哋、佢哋 | 極高 | 粵語語法字 | 否／是；BMP |
| 嘢 | je5 | 東西、事情 | 極高 | 粵語詞 | 否／是；BMP |
| 睇 | tai2 | 看、觀看 | 極高 | 字存在；粵語詞義／讀音 | 是／是；BMP |
| 諗 | nam2 | 想、思考 | 極高 | 字存在；粵語詞義／讀音 | 是／是；BMP |
| 乜 | mat1 | 甚麼、哪一個 | 極高 | 古字／方言用法 | 是／是；BMP |
| 嗰 | go2 | 那、那個 | 極高 | 粵語指示詞 | 否／是；BMP |
| 啲 | di1 | 一些；複數／程度標記 | 極高 | 粵語語法字 | 否／是；BMP |
| 咁 | gam2／gam3 | 這樣、那麼；語調相關 | 極高 | 字存在；粵語語法／詞義 | 是／是；BMP |
| 嚟 | lai4；口音亦可 lei4 | 來；用於「用嚟」等 | 極高 | 粵語詞 | 否／是；BMP |
| 畀 | bei2 | 給；被動標記 | 極高 | 古字／粵語語法 | 是／是；BMP |
| 係 | hai6 | 是 | 極高 | 字存在；粵語繫詞 | 是／是；BMP |
| 咩 | me1 | 甚麼；疑問／驚訝語氣 | 極高 | 粵語詞／語氣字 | 是／是；BMP |
| 呢 | ni1；句末 ne1 | 這；話題／疑問語氣 | 極高 | 共用字；粵語讀法／語法 | 是／是；BMP |
| 咪 | mai5／mai6 | 不要；就是／那就 | 高 | 共用字；粵語語法 | 是／是；BMP |
| 吓 | haa5 | 一下；弱化語氣 | 高 | 粵語語法／量化用法 | 否／是；BMP |
| 喎 | wo3 | 新知、提醒、反預期語氣 | 高 | 粵語句末助詞 | 是／是；BMP |
| 囉 | lo1 | 顯然、結論、無奈語氣 | 高 | 粵語句末助詞 | 是／是；BMP |
| 啦 | laa1 | 指令、結論、狀態改變等語氣 | 極高 | 粵語句末助詞；他區亦見 | 是／是；BMP |
| 㗎 | gaa3 | `嘅呀` 合音；陳述／判定句末助詞 | 高 | 粵語語法字 | 否／是；BMP |
| 啩 | gwaa3 | 推測：「大概／吧」 | 中至高 | 粵語句末助詞 | 否／是；BMP |
| 噃 | bo3 | 提醒、反預期語氣 | 中 | 粵語句末助詞 | 否／是；BMP |
| 噉 | gam2 | 如此、這樣；常同「咁」競爭 | 中 | 粵語詞；拼寫有變體 | 是／是；BMP |
| 攞 | lo2 | 拿、取得 | 高 | 字存在；粵語常用詞 | 否／是；BMP |
| 揸 | zaa1 | 握、拿；駕駛 | 高 | 字存在；粵語常用義 | 否／是；BMP |
| 掂 | dim6 | 搞得定、成功；碰到 | 高 | 字存在；粵語常用義 | 是／是；BMP |
| 冚 | kam2；`冚家` ham6 | 蓋住；`冚家` 表全家（可成粗語） | 中 | 粵語詞／古字 | 否／是；BMP |
| 氹 | tam5 | 哄；水氹＝水坑 | 中 | 字存在；粵語常用義 | 否／是；BMP |
| 孭 | me1 | 背負、揹在背上 | 中 | 方言字 | 否／是；BMP |
| 攰 | gui6 | 累、疲倦 | 高 | 古字／方言常用 | 否／是；BMP |
| 嘥 | saai1 | 浪費 | 高 | 粵語詞 | 否／是；BMP |
| 冧 | lam3 | 倒塌；迷戀／冧女 | 中 | 字存在；粵語義 | 否／是；BMP |
| 揼 | dam2 | 擲、搥；拖延／花費（視搭配） | 中 | 方言字，多義 | 否／是；BMP |
| 嗌 | aai3 | 叫喊；叫餸／點餐 | 高 | 字存在；粵語常用義 | 是／是；BMP |
| 嬲 | nau1 | 生氣 | 高 | 方言／古字；他區亦見但讀法異 | 是／是；BMP |
| 瞓 | fan3 | 睡覺 | 高 | 粵語詞 | 否／是；BMP |
| 搵 | wan2 | 找；賺（搵錢） | 高 | 字存在；粵語常用義 | 是／是；BMP |
| 靚 | leng3 | 漂亮、品質好 | 高 | 字存在；粵語詞義／讀音 | 是／是；BMP |
| 叻 | lek1 | 聰明、能幹 | 中至高 | 方言詞 | 是／是；BMP |
| 黐 | ci1 | 黏；黐線＝瘋／不合理 | 中至高 | 字存在；粵語常用義 | 是／是；BMP |
| 啱 | ngaam1 | 正確、合適；剛才／剛剛 | 極高 | 粵語詞 | 否／是；BMP |
| 慳 | haan1 | 節省、儉省 | 中至高 | 字存在；粵語常用義 | 是／是；BMP |
| 嚡 | haai4 | 粗糙、不順滑；口感澀 | 低至中 | 方言字 | 否／是；BMP |
| 曱甴 | gaat6 zaat2 | 蟑螂（兩字合成一詞） | 中 | 方言詞 | 兩字均否／是；BMP |
| 𡃁 | leng1 | 年輕人、小子（後生仔語感） | 低至中 | 粵語方言字 | 否／是；**SIP U+210C1** |
| 𨋢 | lip1 | 升降機、電梯（英語 *lift*） | 中 | 香港粵語借詞字 | 否／是；**SIP U+282E2** |
| 𨳒 | diu2 | 粗口性動詞／咒罵語 | 低至中，論壇可高 | 粵語粗口字 | 否／是；**SIP U+28CD2** |
| 閪 | hai1 | 粗口：女性生殖器／咒罵成分 | 低至中，論壇可高 | 粵語粗口用法 | 否／是；BMP |
| 撚 | nan2 | 粗口名詞／強調成分 | 低至中，論壇可高 | 字存在；粵語粗口義 | 是／是；BMP |
| 鳩 | gau1 | 粗口名詞／貶義強調成分 | 低至中，論壇可高 | 字存在；粵語粗口義 | 是／是；BMP |

另外一批字本身對台灣讀者並不陌生，但**粵語讀音、搭配或語義**仍然係來源訊號：`企 kei5`（站）、`返 faan1`（回去）、`食 sik6`（吃）、`行 haang4`（走路）、`正 zeng3`（很棒）、`煲 bou1`（煮；煲劇）、`梗 gang2`（當然）、`而家 ji4 gaa1`（現在）。呢類唔應該計成「台灣冇見過嘅字」，但模型仍要學識其香港語義。

### 台灣讀者最可能卡住邊一類？

以下只係**待驗證分層假說**，唔係台灣讀者實驗結果：

- **最難由字形猜讀音兼意思：** `嘅 ge3、咗 zo2、喺 hai2、哋 dei6、嗰 go2、啲 di1、孭 me1、攰 gui6、嘥 saai1、冧 lam3、揼 dam2、㗎 gaa3、啩 gwaa3、𡃁 leng1、𨋢 lip1、𨳒 diu2`。
- **上下文可能猜到意思，但讀音未必猜到：** `睇 tai2、諗 nam2、攞 lo2、揸 zaa1、掂 dim6、畀 bei2、嬲 nau1、瞓 fan3、搵 wan2、靚 leng3、叻 lek1、黐 ci1、啱 ngaam1`。
- **字熟悉、但粵語語法／讀法陌生：** `係 hai6、咪 mai5/mai6、企 kei5、返 faan1、食 sik6、行 haang4、正 zeng3`。

要量度「真係唔識」，最小研究應該將**讀音、意思、信心、上下文前後**分開測；唔可以由 Unicode 碼位或台灣字典有冇收字倒推出讀者識唔識。

主要字音來源：[香港中文大學《粵語審音配詞字庫》](https://humanum.arts.cuhk.edu.hk/Lexis/lexi-can/)（學術）、[粵典 words.hk](https://words.hk/)（香港社群辭典；例：[嘅](https://words.hk/zidin/%E5%98%85)、[嘢](https://words.hk/zidin/%E5%98%A2)、[嚟](https://words.hk/zidin/%E5%9A%9F)、[喎](https://words.hk/zidin/%E5%96%8E)）。粵典並非政府規範，但對當代口語、例句同異寫處理最實用。

## 2. HKSCS：香港需要額外字符嘅編碼證據

### 點解要有 HKSCS

香港政府 1995 年先制定「政府通用字庫」，處理政府部門之間交換香港人名、地名及本地用字嘅實際需要；1999 年擴充成 HKSCS。版本沿革係：

- HKSCS-1999：建立香港補充集；
- HKSCS-2001：增 116；
- HKSCS-2004：增 123；
- HKSCS-2008：增 68；
- HKSCS-2016：增 24，總數 5,033；
- 2016 後再通過 4 個增收／修訂項目，包括 `岃 U+5C83`、`𭉝 U+2D25D`、`𫬷 U+2BB37`、`㗩 U+35E9`。

政府將 4,591 個中文字概括為：

1. 人名、地名、公司名等專有名詞用字；
2. 粵方言用字；
3. 科學名詞用字；
4. 部首或部件。

政府特別話明：一個字可以有多個用途，所以 **HKSCS-2016 冇逐字詳細分類**。因此，唔可以用 4,591 或 5,033 當成「粵語專用字數」。[政府：HKSCS 說明](https://www.ccli.gov.hk/tc/hkscs/what_is_hkscs.html)、[政府：HKSCS FAQ](https://www.ccli.gov.hk/tc/faq/hkscs.html)、[政府：HKSCS-2016 全文](https://www.digitalpolicy.gov.hk/open_data/ccli/c_hkscs_2016.pdf)。

### 數字要用邊個口徑

| 問法 | 答案 | 點解 |
|---|---:|---|
| HKSCS-2016 一共收幾多？ | **5,033** | 4,591 中文字符 + 442 符號 |
| 原始 Big5 冇、HKSCS 補入幾多？ | **5,033** | HKSCS 本身就係 Big5 補充集 |
| Big5-HKSCS 有位、2016 新增只用 Unicode？ | **5,009／24** | HKSCS-2008 起停止分配新 Big5 碼位；2016 新增 24 個只用 Unicode |
| BMP 內／外？ | **3,317／1,716** | 本報按政府 HKSCS-2016 JSON 嘅 Unicode code point 逐項計算 |
| 當中「粵語字」有幾多？ | **未有官方數字** | 政府明言不逐字分類；人名、粵字、科學字用途可重疊 |

非 BMP 計數方法：讀取[政府 HKSCS-2016 JSON](https://www.digitalpolicy.gov.hk/open_data/ccli/HKSCS2016.json)全部 5,033 條記錄，以 `codepoint > U+FFFF` 為條件；結果 1,716。呢個係可重現計算，不是政府頁面直接印出嘅統計。

### 增補平面實際會壞啲乜？

| 系統層 | 典型問題 | 正確描述 |
|---|---|---|
| UTF-16 字串 | JavaScript／Java 舊 API 以 code unit 計長度，SIP 字成兩個 surrogate；切片可斬開 | 用 code-point iterator、JS `/u` regex、Unicode-aware API；唔係「所有 regex 都壞」 |
| Tokenizer | 逐 UTF-16 單元或 BMP 假設嘅 char tokenizer 會拆錯；byte/BPE 通常可處理但可能碎成多 token | 要實測指定 tokenizer；唔可以話所有 LLM tokenizer 都唔支援 |
| MySQL | `utf8mb3` 只容納最多 3-byte UTF-8，存唔到 SIP | 用 `utf8mb4`；見 [MySQL 官方 Unicode 字符集文件](https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html) |
| 字體 fallback | 字碼存在但 font 冇 glyph，顯示豆腐框或換字體 | HKSCS 解決編碼唔等於每個平台都有合適字款 |
| Collation／排序 | 舊 collation 冇擴展字排序權重，可能按碼位排或當 unknown | 要指定 Unicode 版本同 collation；「可存」唔等於「按粵語／筆畫正確排」 |
| 長度／截斷／驗證 | 以 `length`、固定欄位或正則白名單估「一字一單元」會出錯 | 用 grapheme/code-point aware 驗證，並測試 `𡃁、𨋢、𨳒` |

Unicode 對 surrogate pair 嘅技術說明見 [Unicode UTF FAQ](https://www.unicode.org/faq/utf_bom.html)。

## 3. 港式中文係咪一個獲承認嘅變體？

**係。** 香港學術文獻通常將港式中文界定為：以現代通用／標準書面中文為主體，受粵語、英語同部分文言傳統影響，流通於香港社會嘅地域性書面變體。香港理工大學相關研究將佢稱為社會、地域同功能變體；中文大學研究亦直接講「具有香港地區特色的漢語書面語」。[理大學術庫](https://ira.lib.polyu.edu.hk/handle/10397/5210)、[中大：港式中文詞彙隱性差異](https://www.cuhk.edu.hk/ics/clrc/crcl_101_2/xuht.pdf)、[公務員事務局《港式中文》文章](https://www.csb.gov.hk/hkgcsb/ol/news/no29/p05_8.pdf)。

### 書面語、口語寫低，同三及第

- **書面語**：學校、政府、新聞直稿、學術文本用嘅現代標準書面中文；會有香港詞彙同字形，但通常唔寫 `嘅、咗、喺`。
- **書面粵語／口語寫低**：直接把粵語語法、詞彙、句末助詞寫出，例如：`佢哋尋日喺連登講咗啲乜嘢？`（keoi5 dei6 cam4 jat6 hai2 lin4 dang1 gong2 zo2 di1 mat1 je5，意思：他們昨天在 LIHKG 說了甚麼？）。
- **三及第**：歷史上以白話／通用中文為底，混入文言同粵語。現代文言成分式微，田小琳稱港式中文為「新三及第」：通用中文夾粵語、英語，或用受英語影響嘅句法。[中大：田小琳〈三論香港地區的語言文字規範問題〉](https://www.cuhk.edu.hk/ics/clrc/crcl_100_1/tin.pdf)。

三及第仍然有分析價值，但唔係今日所有香港文本嘅單一文體名稱。今日最準確係語域連續體：同一個人可以按場合喺正式書面語、混合港式中文、全書面粵語之間切換。

### 語域階梯

| 級別 | 典型場合 | 實際語言形態 | 粵字密度 |
|---|---|---|---|
| 1. 最正式 | 法例、政府公文、政策報告、正式學術論文 | 標準書面中文 + 香港制度詞／字形；引語外幾乎無口語助詞 | 近零 |
| 2. 教育／編輯正式 | 中小學課本、考卷、大學教材、明報／星島／港台新聞直稿 | 標準書面中文；口語材料可先轉述成書面語，或在對話／語言教學中保留粵語 | 很低 |
| 3. 大眾媒體混合 | HK01 特寫、專欄、娛樂報道、標題 | 書面語主體 + 香港詞彙、粵語引句、英語碼混 | 低至中 |
| 4. 商業／社交混合 | 廣告、品牌 Facebook／Instagram、YouTube 標題及留言 | 港式中文；書面語句架混粵語詞、句末助詞及英文 | 中至高 |
| 5. 全書面粵語 | LIHKG、香港高登、即時通訊、部分留言區 | 粵語語法、代詞、體貌、句末助詞、粗口及英文全面出現 | 高 |

呢個係**語域模型，唔係平台永久標籤**：一篇 LIHKG 轉貼新聞可以係正式書面語；一份報章副刊亦可以非常口語。90 年代報章副刊研究正係將粵語滲入視為可量化現象，而非「一份報紙只得一種語體」。[中大粵語研究會議摘要](https://www.cuhk.edu.hk/chi/yue20/abstract_book_web_1.pdf)。

## 4. 香港課本實際印乜？

### 教育局嘅規範極

- 《常用字字形表》（2000）收 **4,759 字**，係香港學校常用字形嘅核心參考。
- 《香港小學學習字詞表》（2007）收 **3,171 字**：第一學習階段 2,169、第二階段再加 1,002，提供粵語、普通話讀音及配詞；佢係學習字詞表，唔係全體香港成人詞頻表。[教育局資源頁](https://www.edb.gov.hk/tc/curriculum-development/kla/chi-edu/resources/primary/lang/curriculum-materials.html)、[教育局《香港小學學習字詞表》](https://www.edb.gov.hk/attachment/tc/curriculum-development/major-level-of-edu/special-educational-needs/pri1-to-sec3-curriculum/hk%20chinese%20lexical%20list%20for%20primary%20learning_%28sen%29_2009.pdf)。
- 教育局非華語課程支援明確指出：香港人一般講粵語，但讀寫標準書面中文；學生要識分 `有啲／嗰度／搭車` 等口語同 `有些／那裡／乘車` 等書面形式。[教育局語文學習架構](https://www.edb.gov.hk/attachment/tc/curriculum-development/major-level-of-edu/special-educational-needs/cl-curriculum-second-lang-alf/Four%20strands%20of%20the%20ALF/CL_Alf_Framework_Introduction_final_20180824.pdf)。另一套教材甚至以 `馬騮 maa5 lau1`（猴子）對 `猴子`，將口語—書面語對照當成教學目標。[教育局學習資源套](https://www.edb.gov.hk/attachment/tc/curriculum-development/major-level-of-edu/special-educational-needs/cl-curriculum-second-lang-alf/NCS_CLRP/NCS%20Chi%20Learning%20Resource%20Package_full.pdf)。

### 小學、中學、大學嘅實際輪廓

| 層級 | 公開可核實結果 | 書面粵語地位 |
|---|---|---|
| 小學 | 教育局課程、字形表、學習字詞表同獲推薦課本以規範書面語、香港常用字形為主 | 可作口語／書面語對比、對話、聆聽口語材料；唔係一般說明文嘅預設文體 |
| 中學 | 正式閱讀、寫作、考核仍以現代書面語及文言篇章為核心；公開出版社樣本用 `着重` 等香港寫法 | 可在引語、語言現象、創意文本出現；正式作文一般要求書面表達 |
| 大學 | 冇全港統一「大學課本字形法規」；院校語文課仍明教書面／口語差別、規範漢字及實用文 | 粵語研究、語言學、文化研究會直接印書面粵語；一般學科教材仍以正式書面語為主 |

出版社方面，教育局現行推薦書目可見[現代教育研究社](https://www.modernedu.hk/zh-hant/)、教育出版社、啟思同牛津香港教材；[教育局推薦課本清單](https://www.edb.gov.hk/attachment/tc/curriculum-development/resource-support/textbook-info/RecommendedTextbookList/UPC_CHI.pdf)可核對系列。公開樣本（例如[啟思中文資料](https://www.keyschinese.com.hk/home)、[牛津香港樣卷](https://www.oupchina.com.hk/pclt-newbk-2025/sample/tsa-mock-paper_p1-31.pdf)）顯示主體係標準書面中文。

**限制：** 四間出版社完整電子課本多數要帳戶／訂閱；未能公開逐頁審計所有年級、版本、修訂年。出版社內部最新編輯手冊亦未搵到可公開核實版本。因此，「每一本都從不印書面粵語」或「某出版社全面採用某組異體」均屬 **未核實**。

**成人寫作同教科書標準一致幾多？** 正式成人寫作大致承接同一書面標準；但在訊息、論壇、廣告同社交媒體，受教育港人會轉用書面粵語或混合語體。呢個係語域轉換，唔應解作「學校冇教識」。

## 5. 香港同台灣標準字形差異

先分兩種：

1. **不同 Unicode 字符／不同用字選擇**，例如 `裏／裡`、`着／著`；純文本可偵測。
2. **同一 Unicode 碼位嘅字形差**，例如骨架、點畫位置、部件比例；要睇字體 glyph，copy/paste 後未必保留差異。

香港 2017 年公布嘅《香港電腦漢字參考字形》係官方比較基準，並非「2016 文件」；`2016` 指佢覆蓋 HKSCS-2016。文件直接比較香港參考字形、Big5 傳統字形同台灣教育部宋體，確認香港自有慣用字形原則。[政府：參考字形文件](https://www.ccli.gov.hk/doc/cliac2017_01b.pdf)、[政府：參考字形下載及比較表](https://www.ccli.gov.hk/tc/download/reference_glyphs.html)。

| 香港偏好／功能分工 | 台灣常見標準 | 類型 | 香港側理由／證據狀態 |
|---|---|---|---|
| 裏（裏面） | 裡 | 不同字符 | 《常用字字形表》承接香港慣用／傳統結構，`衣` 包 `里`；官方比較證實兩地慣例不同 |
| 着（着衫、看着、睡着）／著（著作、著名） | 多用著 | 不同字符兼語義分工 | 香港保留 `着` 作穿、附着、體貌等，`著` 作著作／顯著；係功能分化，唔係任意換字 |
| 綫（東鐵綫等專名、傳統用法）／線（亦普遍） | 線 | 字符／專名 | 香港交通專名長期保留 `綫`；一般輸入 `線` 同樣常見，不能當全民唯一標準 |
| 羣 | 群 | 不同字符 | 香港字形傳統可見 `羣`；結構／篆隸傳承解釋見香港字形研究，但當代一般輸入 `群` 很普遍 |
| 峯 | 峰 | 不同字符 | 香港傳統字形將 `山` 置頂；一般文本 `峰` 亦極常見 |
| 麪 | 麵 | 不同字符 | 香港舊標準／Big5 傳統異寫；現代輸入受字體、輸入法同跨地區平台影響，`麵` 常見 |
| 牀 | 床 | 不同字符 | 香港舊字形傳統保留 `牀`；今日 `床` 亦常見 |
| 糉 | 粽 | 不同字符 | 香港常見傳統異寫；精確官方逐對理由 **未核實** |
| 啓 | 啟 | 不同字符 | 香港歷史／機構名常保留 `啓`；一般文本有競爭 |
| 衞（衞生署舊式／專名） | 衛 | 不同字符 | 專名、機構歷史字形唔等於所有普通詞必用 `衞` |
| 滙（滙豐等專名） | 匯 | 不同字符 | 專名保留；不能推成一般 `匯` 字規則 |
| 黃、骨、令等 | 同一碼位但台灣字體筆形不同 | glyph-only | 官方參考字形以部件分析香港慣用點畫；純 Unicode 字串不能可靠判別 |

**重要限制：** 上表唔係「所有差異」。官方參考字形文件嘅附表以圖形逐部件比較，規模遠大過少數可用兩個 Unicode 字表達嘅異寫。將 glyph 差異扁平化成字符替換表會失真。`羣／群、峯／峰` 等歷史結構解說可參考香港社群整理，但唔應冒充政府逐對理由；[香港粵語維基：常用字字形表](https://zh-yue.wikipedia.org/wiki/%E5%B8%B8%E7%94%A8%E5%AD%97%E5%AD%97%E5%BD%A2%E8%A1%A8)屬社群二手資料。

## 6. Big5、台灣字體同「學裏打裡」

**廣義講法已獲香港官方證實。** 2002 年政府新聞稿指出，當時香港大部分電腦中文字體由內地或台灣廠商製作，未必反映香港慣用字形；電腦字同課本字形差異已影響教學，所以政府推動香港字形字體。[香港政府新聞公報，2002-02-27](https://www.info.gov.hk/gia/general/200202/27/0227167.htm)。2017 官方參考字形前言亦交代，香港 1990 年代採用台灣平台及 Big5，但香港慣用字形自有規則，與 Big5／台灣字形不盡相同。

**精確講法要收窄：**「所有學生都學 `裏`、但因 Big5 冇 `裏` 所以一律打 `裡`」目前只搵到香港社群敘述，未搵到代表性學生輸入調查。[粵典社群帖文](https://www.facebook.com/www.words.hk/posts/1406168844875391/)可作歷史見證，唔足以估比例。

Unicode 同 HKSCS 普及後：

- 字碼層面大幅改善，`裏／裡` 同增補平面粵字可分開儲存；
- 但用戶揀咩字仍由輸入法候選、字庫、平台 autocorrect、字體 fallback 同跨區內容影響；
- 同碼位 glyph 差異仍然取決於字體，Unicode 本身唔會指定「香港筆形」；
- 因此趨勢係**技術阻礙減少**，唔係所有打字自動回復教育局字形。

「打字香港文本偏離學校標準幾多」目前冇代表性量化研究，結論係 **未核實**。

## 7. 香港詞彙同英語借詞層

| 概念 | 香港常用 | 台灣常用（對照） | 內地常用（只作對照） |
|---|---|---|---|
| software | 軟件 | 軟體 | 软件 |
| network | 網絡 | 網路 | 网络 |
| hard disk | 硬盤、硬碟皆見 | 硬碟 | 硬盘 |
| screen | 熒幕、屏幕；電腦介面亦見螢幕 | 螢幕 | 屏幕 |
| computer | 電腦 | 電腦 | 电脑 |
| convenience／grocery shop | 士多 si6 do1、便利店 | 雜貨店、便利商店 | 小卖部、便利店 |
| taxi | 的士 dik1 si6 | 計程車 | 出租车 |
| bus | 巴士 baa1 si6 | 公車、巴士 | 公交车、公共汽车 |
| parking | 泊車 paak3 ce1 | 停車 | 停车 |
| air-conditioning | 冷氣 laang5 hei3 | 冷氣、空調 | 空调 |
| mobile phone | 手提電話、手機 | 手機 | 手机 |
| document/file | 文件；電腦語境亦見檔案 | 檔案 | 文件 |
| privacy | 私隱 | 隱私 | 隐私 |

呢啲係**概率分布**，唔係硬邊界：`電腦、冷氣、硬碟、手機` 可以跨地區共用；香港軟件介面亦受台灣、內地翻譯影響。最可靠係多個互相一致嘅詞彙聚類，而唔係單字分類。

### 音譯英語有幾深？

香港粵語大量以粵音吸收英語：`巴士 baa1 si6`（bus）、`的士 dik1 si6`（taxi）、`士多 si6 do1`（store）、`士多啤梨 si6 do1 be1 lei2`（strawberry）、`啫喱 ze1 lei2`（jelly）、`梳打 so1 daa2`（soda）、`多士 do1 si2`（toast）、`菲林 fei1 lam4`（film）、`雪糕 syut3 gou1`（ice cream）。部分已成日常基本詞，唔再有「夾英文」感覺。

香港理工大學英語借詞研究建立約 **700 詞**資料庫，覆蓋約 180 年；呢個數係研究資料庫規模，唔係「現代香港全部借詞總數」或當代詞頻。[理大學術庫：香港粵語英語借詞](https://ira.lib.polyu.edu.hk/handle/10397/5824)、[English Loanwords in Hong Kong Cantonese 資料庫](https://chaaklau.github.io/elw/)。

## 8. 繁體中文網絡語料，香港佔幾多？

**冇可靠公開比例。** 原因唔只係「未有人數」：

- 中文維基 `zh-hant` 係同一內容庫按變體轉換顯示，唔係「香港作者子集」；
- Common Crawl 公開語言統計通常到 language code，唔穩定提供香港／台灣來源標籤；
- zhTenTen 等 web corpus 主要分簡體／繁體，唔等於港／台；
- `.hk`／`.tw` domain 有高 precision 但低 recall；香港網站可用 `.com`，台灣作者亦可在全球平台出文；
- 新聞轉載、OpenCC 轉換、跨地區字體令字形訊號污染。

來源：[Common Crawl 語言統計](https://commoncrawl.github.io/cc-crawl-statistics/plots/languages)、[Sketch Engine zhTenTen](https://www.sketchengine.eu/zhtenten-chinese-corpus/)。早期香港／台灣詞彙分類研究證明兩者可區分，但冇提供今日訓練網絡嘅全球佔比：[ACL 1997 regional corpus study](https://aclanthology.org/O97-3004.pdf)、[ACL 2008 Chinese regional variants](https://aclanthology.org/O08-1009.pdf)。

所以「香港繁體文本壓過台灣」同相反講法目前都係 **未核實**。要答，應抽一個凍結 Common Crawl snapshot，以 URL/domain、頁面 metadata、香港／台灣詞彙、HKSCS 字、地址／電話格式、人工抽查做弱監督估計，並對機械轉換頁另設類別。

## 9. 粵語／香港中文 NLP 同安全資源

| 資源 | 規模／內容 | 香港來源性 | 可否當安全 benchmark？ |
|---|---|---|---|
| HKCanCor | 58 檔、153,656 個已切分詞；粵拼、詞性；CC BY | 香港自然口語轉寫，年代較舊 | 否；語料／標註資源 |
| CantoMap | 99 檔、118,572 詞；GPL-3.0 | 香港粵語地圖任務口語 | 否 |
| HKCanto-Eval | 粵語理解、文化常識；設書面中文／英文對照，部分題源自翻譯 | 2025 香港粵語 benchmark | 否；通用能力／文化 |
| Yue-Benchmark | 事實生成、數理、邏輯、推理、常識 | 廣東話／粵語取向，唔只香港 | 否；通用能力 |
| HKMMLU | 26,698 選擇題、66 科；另 90,550 普通話—粵語翻譯任務 | 香港知識／語言取向 | 否；最接近香港大型知識 benchmark |
| Beaver-zh-hk | 2,508 樣本、29 風險情景（14 一般 + 15 香港特定） | 香港社會文化安全情景 | **是；現時最接近香港安全 benchmark** |

來源：

- [PyCantonese datasets：HKCanCor、CantoMap](https://docs.pycantonese.org/stable/data.html)；[HKCanCor Hugging Face](https://huggingface.co/datasets/nanyang-technological-university-singapore/hkcancor)。
- [HKCanto-Eval 論文](https://aclanthology.org/2025.conll-1.1/)、[程式庫](https://github.com/hon9kon9ize/hkeval2025)。
- [Yue-Benchmark 論文](https://arxiv.org/html/2408.16756v3)、[程式庫](https://github.com/jiangjyjy/Yue-Benchmark)。
- [HKMMLU 論文](https://arxiv.org/abs/2505.02177)、[數據](https://huggingface.co/datasets/chuxuecao/HKMMLU)。
- [Beaver-zh-hk 程式庫](https://github.com/PKU-Alignment/Beaver-zh-hk)、[HKGAI-V1／安全研究論文](https://arxiv.org/abs/2507.11502)。
- 綜述：[Cantonese NLP resources review, SIGHAN 2024](https://aclanthology.org/2024.sighan-1.8.pdf)。

### 有冇香港版 TMMLU+ 或 TS-Bench？

- **TMMLU+ 對應物：** HKMMLU 係最接近嘅大規模知識／考試式基準，但來源結構、人工核實程度同台灣 TMMLU+ 唔應假設完全同構。
- **TS-Bench 安全對應物：** Beaver-zh-hk 係最接近；但佢唔等於「香港書面粵語安全測試」全部問題已解決。應另外審核題目係正式港式中文、書面粵語、翻譯文定機械轉換文；亦要獨立驗證 judge 同分類器。
- HKCanto-Eval、Yue-Benchmark、HKMMLU 均顯示現代模型處理粵語／香港知識仍有明顯差距，但佢哋**唔直接證明**「因為模型只用簡體或台灣文本訓練」。因果訓練來源通常不可見。

## 10. OpenCC `s2hk` 究竟產生乜

### 直接讀設定檔

現行 [`s2hk.json`](https://github.com/BYVoid/OpenCC/blob/master/data/config/s2hk.json)實際鏈：

1. 兼容字正規化；
2. `STPhrases` + 由地區字典生成嘅簡繁詞組，先做詞組級簡→繁復原；
3. `STCharacters` 做單字後備；
4. `HKVariantsPhrases`；
5. `HKVariants`。

即係：`s2hk` 先將簡體變成通用繁體，再套香港字形／詞組例外。佢**冇載入香港詞彙字典 `HKPhrases`**。

OpenCC 現行源碼另外提供 `s2hkp`（Simplified to Hong Kong Traditional Chinese with Hong Kong phrases），會加入 `HKPhrases`；見 [OpenCC CONTRIBUTING／設定清單](https://github.com/BYVoid/OpenCC/blob/master/CONTRIBUTING.md)。

### 直接讀字典：npm `opencc` 1.4.1

| 字典 | 非空、非註解條目 | 功能 |
|---|---:|---|
| `HKVariants` | 66 | 香港偏好字形／異體 |
| `HKVariantsPhrases` | 272 | 避免逐字轉錯、專名及詞組例外 |
| `HKPhrases` | 39 | 香港詞彙本地化；只供 `s2hkp`，唔係 `s2hk` |

`HKPhrases` 例子包括 `服務器→伺服器、硬盤→硬碟、鼠標→滑鼠、文件夾→資料夾、搜索→搜尋、隱私權→私隱權、密歇根→密芝根`。39 條係工程字典規模，遠遠唔係香港詞彙全貌；部分輸出亦同台灣用語重疊。

直接搜尋 `HKPhrases`、`HKVariants`、`HKVariantsPhrases`，冇規則以 `嘅、咗、喺、唔、冇、佢、哋、嘢、嗰、啲、㗎` 為輸出。故此：

- **確認：** `s2hk` 唔會將 `他的東西在這裡` 改寫成 `佢嘅嘢喺呢度`（keoi5 ge3 je5 hai2 ni1 dou6，意思：他的東西在這裡）。
- **確認：** `s2hkp` 有少量香港詞彙，但仍然唔係粵語語法生成器。
- **精確講法：** 如果輸入本身已有 `嘅／咗／喺`，OpenCC 通常會保留；「唔會產生」係指香港 locale 字典冇規則由標準中文成分**引入**呢啲助詞，而唔係會刪除佢哋。

所以 `s2hk` 輸出係：**香港字形慣例下嘅機械繁體標準中文**。佢唔係台灣文本，亦唔等於香港人非正式寫嘅書面粵語。`s2hkp` 進一步係：**少量香港詞彙本地化嘅標準中文**，仍唔係自然粵語轉寫。

## 結論

### (a) 香港書面中文同台灣中文有幾唔同？

**答案取決於語域。**

- 正式政府、教材、新聞直稿：兩者共享現代標準書面中文核心，互通度高；差異集中喺字形、制度詞、區域詞、翻譯慣例同英語接觸。稱為「同一書面標準嘅地域變體」有相當道理。
- 混合港式中文：已經係可識別地域書面變體，句法、詞義、搭配及碼混唔止係換字。
- 全書面粵語：語法、代詞、體貌、否定、句末助詞同大量詞彙都唔同；對只受台灣國語書寫教育嘅讀者，實際上係另一套書面語碼。稱佢只係「繁體字口音」會嚴重低估差異。

最準確總結：**港式中文係以共享標準書面中文為底、具有自己規範同接觸層嘅地域書面變體；書面粵語則係同佢相連但結構更獨立嘅書寫實踐。**

### (b) 只用台灣文本訓練嘅分類器可唔可以處理香港文本？

- 對正式新聞／政府文本：可能有不錯零樣本表現，但會受 `裏／裡、着／著、網絡／網路、軟件／軟體、私隱／隱私` 同機構名影響。
- 對混合港式中文：需要香港詞彙、英語碼混、香港制度同語義資料。
- 對全書面粵語：**唔應合理預期可靠**。`嘅、咗、喺、哋` 係高頻語法骨架；完全冇香港／粵語訓練，唔係單純 OOV 幾個名詞，而係句法同語用分布改變。

要研究嘅唔係「handle at all」二分，而係按語域報告：準確率、校準、拒答／誤判、token fragmentation、非 BMP 字處理，同香港母語者評分。

### (c) 可唔可以單靠字形分辨香港原生文本同機械簡轉繁？

- **對 `s2t`：** 中等至高可分，因為會殘留內地詞彙、翻譯名同非香港異體；但正式香港文本本來都可能同通用繁體接近。
- **對 `s2hk`：** 單靠「字符正寫」只得有限把握。佢已套香港異體，正式港式中文可以同輸出非常接近。
- **對非正式香港文本：** 很易分，因為自然書面粵語有 `嘅、咗、喺、哋、句末助詞、英語碼混、香港俚語`，而 `s2hk` 唔會創造。
- **可靠性結論：** 一個高 precision 規則可以話「出現多個粵語語法字 ⇒ 極可能唔係純機械標準中文」；反方向唔成立——冇粵字嘅文本可能係香港正式文、機械轉換文、台灣文或其他繁體文。正確做法係多類別來源分類，唔係單一 `zh-Hant` 標籤。

## 對研究設計嘅建議操作定義

將香港文本至少分四類，否則結果會畀語域混淆：

1. `HK-formal-native`：政府／教材／新聞正式書面語；
2. `HK-mixed-native`：港式中文混粵語／英文；
3. `Yue-written-native`：全書面粵語；
4. `SC-converted-s2hk` 與 `SC-converted-s2hkp`：凍結 OpenCC 版本同字典 hash。

每段記錄：HKSCS 字、非 BMP 字、粵語語法字、香港詞彙、英語碼混、香港制度實體、OpenCC 差異、字體／glyph 是否可觀察、來源 URL 同年份。聲稱台灣讀者「唔識」之前，加一個台灣讀者小型讀音／釋義實驗。

## 來源清單（按類型）

### 香港政府／教育

- [共通中文界面諮詢委員會：甚麼是 HKSCS](https://www.ccli.gov.hk/tc/hkscs/what_is_hkscs.html)
- [HKSCS-2016 正文](https://www.digitalpolicy.gov.hk/open_data/ccli/c_hkscs_2016.pdf)；[HKSCS-2016 JSON](https://www.digitalpolicy.gov.hk/open_data/ccli/HKSCS2016.json)
- [香港電腦漢字參考字形](https://www.ccli.gov.hk/doc/cliac2017_01b.pdf)；[官方下載／比較表](https://www.ccli.gov.hk/tc/download/reference_glyphs.html)
- [香港政府 2002：電腦字體與香港慣用字形](https://www.info.gov.hk/gia/general/200202/27/0227167.htm)
- [教育局：小學中國語文課程資源](https://www.edb.gov.hk/tc/curriculum-development/kla/chi-edu/resources/primary/lang/curriculum-materials.html)
- [教育局：《香港小學學習字詞表》](https://www.edb.gov.hk/attachment/tc/curriculum-development/major-level-of-edu/special-educational-needs/pri1-to-sec3-curriculum/hk%20chinese%20lexical%20list%20for%20primary%20learning_%28sen%29_2009.pdf)
- [教育局：口語／書面語學習架構](https://www.edb.gov.hk/attachment/tc/curriculum-development/major-level-of-edu/special-educational-needs/cl-curriculum-second-lang-alf/Four%20strands%20of%20the%20ALF/CL_Alf_Framework_Introduction_final_20180824.pdf)
- [教育局推薦課本清單](https://www.edb.gov.hk/attachment/tc/curriculum-development/resource-support/textbook-info/RecommendedTextbookList/UPC_CHI.pdf)

### 香港學術／院校

- [香港中文大學《粵語審音配詞字庫》](https://humanum.arts.cuhk.edu.hk/Lexis/lexi-can/)
- [中大：粵語與香港中文](https://cloud.itsc.cuhk.edu.hk/enewsasp/app/article-details.aspx/F1FF684626A68E84EE9E3CE710FA50F0/)
- [田小琳：港式中文與新三及第](https://www.cuhk.edu.hk/ics/clrc/crcl_100_1/tin.pdf)
- [中大：港式中文詞彙與通用中文的隱性差異](https://www.cuhk.edu.hk/ics/clrc/crcl_101_2/xuht.pdf)
- [理大：Hong Kong Chinese as a regional written variety](https://ira.lib.polyu.edu.hk/handle/10397/5210)
- [香港粵語英語借詞研究](https://ira.lib.polyu.edu.hk/handle/10397/5824)
- [HKCanto-Eval](https://aclanthology.org/2025.conll-1.1/)、[HKMMLU](https://arxiv.org/abs/2505.02177)、[Beaver-zh-hk](https://github.com/PKU-Alignment/Beaver-zh-hk)

### 香港媒體／現實語域入口

- [香港電台新聞](https://news.rthk.hk/)、[明報](https://news.mingpao.com/)、[星島日報](https://std.stheadline.com/)、[HK01](https://www.hk01.com/)
- [LIHKG](https://lihkg.com/)、[香港高登](https://forum.hkgolden.com/)

媒體同論壇連結用作語域入口，唔代表首頁每篇文章都屬同一語體；本報冇將平台名稱當作人工標註。

### 香港社群／辭書

- [粵典 words.hk](https://words.hk/)；[粵語 FAQ](https://words.hk/faiman/view/202/%E7%B2%B5%E5%85%B8%20%E7%B2%B5%E8%AA%9E%20FAQ)
- [粵語維基：常用字字形表](https://zh-yue.wikipedia.org/wiki/%E5%B8%B8%E7%94%A8%E5%AD%97%E5%AD%97%E5%BD%A2%E8%A1%A8)（二手社群整理）

### 技術原始資料

- [OpenCC `s2hk.json`](https://github.com/BYVoid/OpenCC/blob/master/data/config/s2hk.json)、[`HKVariants.txt`](https://github.com/BYVoid/OpenCC/blob/master/data/dictionary/HKVariants.txt)、[OpenCC CONTRIBUTING／設定清單](https://github.com/BYVoid/OpenCC/blob/master/CONTRIBUTING.md)
- [Unicode UTF FAQ](https://www.unicode.org/faq/utf_bom.html)、[MySQL utf8mb4](https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html)
- [Common Crawl language statistics](https://commoncrawl.github.io/cc-crawl-statistics/plots/languages)

## 證據限制

- 冇代表性研究直接量度台灣讀者對各粵字嘅讀音／釋義成功率；讀者困難分層係待測假說。
- 冇公開、代表性「全香港書面粵語」頻率語料；字表頻率係定性語域估計。
- HKSCS 嘅 5,033／4,591 唔係粵字總數；政府明言用途重疊、不逐字分類。
- 完整商業課本需登入，未能逐頁審核四間出版社所有版本；公開樣本只支持總體語域結論。
- 字形表包含字符差異同 glyph 差異；純文字分析見唔到後者。
- OpenCC 條目數係 1.4.1 版本嘅非空、非註解原始行數；字典會更新，研究必須凍結版本及 hash。
- 「未搵到」唔等於永遠不存在；網絡比例、輸入字形偏差同台灣讀者識字率均應標成 **未核實**，直至有抽樣研究。
