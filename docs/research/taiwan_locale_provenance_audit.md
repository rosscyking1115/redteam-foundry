# Taiwan Mandarin locale provenance: native text, OpenCC conversion, and what the contrast can support

**Evidence cut-off:** 2 August 2026.
**Scope:** informal written Taiwan Mandarin, especially short safety prompts. Hong Kong and Mainland China are treated as separate standards.
**Frequency labels:** qualitative expectations for a 20–50-character informal Taiwan prompt (`high`, `medium`, `low`, `conditional`), not corpus-estimated rates. Where no suitable informal corpus count was found, the report says **UNVERIFIED**.

## Executive summary

There is no single “native Taiwan” feature. The observable difference between native Taiwan Mandarin and mechanically traditionalised Mainland text is layered:

1. **character restoration** from Simplified to Traditional, including context-sensitive one-to-many merges;
2. **Taiwan standard-form normalisation** (字形/異體), which often makes converted text *more* prescriptively regular than casual native writing;
3. **regional lexical localisation**;
4. **proper-name conventions**;
5. **grammar, discourse particles, Hokkien contact features, Bopomofo and platform slang**;
6. **local civic references, dates and typography**.

OpenCC `s2t` handles layer 1 and deliberately targets an internal traditional lexical form, not a real locale. `s2tw` adds Taiwan character variants but **does not load `TWPhrases`**. It therefore does not collapse to `s2t`, yet it does not do Taiwan vocabulary localisation. `s2twp` adds `TWPhrases` and then Taiwan variants. In the current source tree, `TWPhrases` has only 817 non-comment entries, compared with more than 4,800 groups in the official cross-strait difference list. Those counts are not directly comparable, but they preclude calling `s2twp` comprehensive.

The strongest high-precision Taiwan-native clues are inline Bopomofo, Taiwan-only civic terms, Hokkien loans/phonetic spellings, uncovered Taiwan proper-name conventions, and *clusters* of Taiwan vocabulary plus particles/grammar. Each has low recall or content/register confounds. `臺灣`, `「」`, a Republic-of-China date, or one meme token alone is weak evidence of authorship.

The broad classification problem already exists. The VarDial 2019 DMT shared task classified Mainland versus Taiwan news after OpenCC conversion removed script cues; the best Traditional-track macro-F1 was 0.9084. Your exact counterfactual—same safety intent, `s2t` versus `s2twp` versus native Taiwan rendering, with safety-verdict stability as the outcome—was **not found** in the searched literature. The defensible novelty is locale-level safety-measurement validity, not first identification of Taiwan-native text.

## Feature map

| Phenomenon / 中文名 | Taiwan-native example | Glyph-converted example | Mainland source | Expected frequency | Machine detection | `s2t` | `s2twp` | Type |
|---|---|---|---|---|---|---|---|---|
| Taiwan standard character / 臺灣標準字、異體 | 裡、麵、為 | 裏、麪、爲 can survive some Traditional sources; `s2tw` normalises them | 里、面、为 | high at character opportunities; low per short prompt | deterministic character list, but not authorship | partly through phrase restoration; no Taiwan-variant stage | yes, `TWVariants*` | STANDARD, meaning normally preserved |
| Prescriptive–colloquial gap / 正字與俗用 | 台灣、講台 in casual text; 臺灣、講臺 in official/textbook prose | 臺灣、講臺 | 台湾、讲台 | `台` forms high in casual text; **UNVERIFIED rate** | deterministic surface cue; very weak provenance | often normalises to 臺 | same | REGISTER/STANDARD |
| One-to-many restoration / 簡繁一對多 | 麵、乾、幹、髮、後、隻、誌 | converter-selected traditional word | 面、干、发、后、只、志 | high opportunity across normal prose; actual errors low-to-conditional | deterministic candidate flag; correct sense needs context/model/human | yes, phrase-first then character fallback | same first stage | SEMANTIC when wrong |
| Taiwan regional vocabulary / 兩岸詞彙差異 | 軟體、網路、滑鼠、印表機、程式、資訊、影片、伺服器、硬碟、記憶體 | 軟件、網絡、鼠標、打印機、程序、信息、視頻、服務器、硬盤、內存 | 软件、网络、鼠标、打印机、程序、信息、视频、服务器、硬盘、内存 | medium; domain-dependent | deterministic lexicon + contextual heuristic | no | partly, phrase dictionary | mostly REGISTER/LOCALE; sometimes semantic |
| Same word, different regional sense / 同名異實 | 土豆 may mean peanut in Taiwan; 水準 preferred for “standard/level” | context may retain a Mainland sense | 土豆 often potato; 水平 often level | low-to-medium, topic-dependent | contextual classifier/native judgement | no | generally no | SEMANTIC/PRAGMATIC |
| Proper-name transliteration / 專名譯名 | 歐巴馬、紐西蘭、寮國、雪梨 | 奧巴馬→歐巴馬; 新西蘭→紐西蘭; 老撾→寮國, but 布什、悉尼 remain | 奥巴马、新西兰、老挝、悉尼 | low in generic prompts; conditional/high in news | deterministic named-entity lexicon; entities change over time | glyphs only | sparse/partial | REGISTER/REFERENCE; referent usually preserved |
| Taiwan syntax / 臺灣華語句法 | 你有去過嗎？我有跟他說；給 usage; 會 as epistemic/ability | converter cannot add these | 你去过吗？我跟他说过 | low per short prompt; medium in dialogue | heuristic/parser; not deterministic | no | no | GRAMMAR/REGISTER; proposition usually preserved, nuance may change |
| Sentence-final particles / 句末語氣詞 | 啦、喔、耶、欸、齁、囉 | absent unless present in source | 啊、呀、吧 and overlapping particles | medium in chat; low in formal prose | regex + positional/contextual heuristic | no | no | PRAGMATIC/REGISTER |
| Hokkien loans/contact writing / 臺語借詞、語碼混用 | 歹勢、好康、母湯、凍蒜、趴趴走 | absent unless source already contains them | usually paraphrased in Mandarin | low overall, conditional/high in performative local chat; individual rates **UNVERIFIED** | lexicon; spelling variation requires fuzzy match/native review | no | no for tested examples | REGISTER/IDENTITY; sometimes semantic |
| Inline Bopomofo / 注音文 | ㄏㄏ、好ㄛ、不ㄟ賽 | cannot be generated | Pinyin/Latin or characters | low overall, conditional in chat | deterministic Unicode range with exclusions | no | no | REGISTER/ORTHOGRAPHY |
| Taiwan internet/PTT slang / 網路語、批踢踢語彙 | 鄉民、婉君、森77、484、是在哈囉、咩噗 | absent unless source already contains it | platform-specific Mainland slang differs | individual tokens low and time-sensitive; **UNVERIFIED** | lexicon/regex; high platform and era confound | no | no | REGISTER/PLATFORM |
| Local institutions / 臺灣制度詞 | 健保卡、統一發票、超商、捷運、里長 | may appear only if source content was localised | 社保卡、发票、便利店、地铁、居委会/村委会 | conditional; high in local scenarios | deterministic lexicon/NER; topic leakage | character conversion only | partial and inconsistent | SEMANTIC/LOCALE CONTENT |
| ROC calendar / 民國紀年 | 民國115年 | 2026年 normally remains 2026年 | 2026年 | low overall; high official/civic | deterministic date parser | no | no | REFERENCE FORMAT, meaning preserved if converted correctly |
| Taiwan punctuation / 標點符號 | 「…」、『…』、全形中文標點 | “…” often survives | “…” under PRC norm | medium in edited prose; mixed online | deterministic typography rule, weak provenance | no | no | TYPOGRAPHY/REGISTER |
| Full-/half-width mixture / 全形半形 | 中文標點全形；ASCII letters/digits half-width in official style | source formatting normally survives | similar digital conventions | medium in edited text; highly mixed in chat | deterministic | no | no | TYPOGRAPHY, weak signal |
| Unicode glyph/compatibility artefacts / 字碼與字形 | font-dependent Taiwanese standard glyphs | converter may output canonical code points but renderer controls glyph | font-dependent | low as text-code signal | deterministic code-point audit; glyph needs font/render inspection | compatibility normalisation stage | same | ENCODING, not authorship |
| Topic and named-entity leakage / 主題洩漏 | 健保、立法院、台積電 | localised content may insert same cues | 人大、医保、微信 | conditional and often dominant | easy classifier feature; methodologically dangerous | no | partial at most | CONTENT, not linguistic provenance |

### Interpretation of frequency

No published corpus provides reliable per-feature rates for *informal Taiwan safety prompts*. The labels above are priors to be estimated, not measurements. The right empirical unit is “percentage of base intents with at least one opportunity for the feature” plus token-level incidence in a frozen Taiwan-native prompt corpus. PTT is not a population sample; textbook and news corpora undercount chat features.

## 1. 正字、俗字、異體字: what the standard is

### Prescriptive findings

The Ministry of Education’s standard is a **character-form system**, not a general ban on every alternate spelling.

- The Ministry’s *常用國字標準字體表* contains 4,808 common characters; separate tables cover secondary-common and rare forms. The table is the core school standard.
- The *異體字字典* defines a 正字/標準字 as a standard form present in the Ministry’s common, secondary-common or rare standard-form tables. An 異體字 is another form corresponding to the same 正字 in some or all readings/senses. Its current edition contains 29,920 正字, 74,381 異體字 and 2,002 unresolved appendix forms—106,303 entries in all. That is a historical/reference inventory, **not** the practical number of everyday competing spellings.
- A shape can be a 正字 in one sense and an 異體 in another. This is the crucial `台` caveat: `台` cannot be globally labelled a nonstandard replacement for `臺`; the relation is lexical/sense-specific.
- The *國語辭典簡編本* (about 45,000 entries) is oriented toward K–12 learners and generally uses standard forms. The much larger *重編國語辭典修訂本* (about 167,000 entries) is a historical/research dictionary. Neither should be described as the legal instrument that “binds” all editors.
- The National Academy’s 2024 trial *異形詞辨析手冊* is closer to the practical editorial problem: it considers current media/books, defines 異形詞 as same pronunciation/current meaning with different characters, requires headword characters to be Ministry standard forms or dictionary 正字, and recommends a preferred form for K–12 use.

### Main everyday standard/alternate patterns

There is no official “top N vulgar forms” frequency table. The practical set is in the dozens, not the 74,381-form historical inventory. High-visibility families include:

| Prescriptive/current Taiwan preference | Common alternate | Notes |
|---|---|---|
| 臺灣、講臺、舞臺、月臺、颱風 | 台灣、講台、舞台、月台、台風 | `台` casual forms are common; context decides whether it is an alternate of 臺/檯/颱 |
| 裡面、這裡 | 裏面、這裏 | Taiwan standard variant preference; OpenCC Taiwan variant stage handles it |
| 麵條、麵包 | 麪條、麪包 | Taiwan standard variant preference; `面` versus `麵` is separately a semantic restoration issue |
| 為、偽、啟、峰、群、才 | 爲、僞、啓、峯、羣、纔 | many are literary/other-region Traditional variants rather than living Taiwan “俗字” |
| 吃 | 喫 | variant; `喫` survives in some names/phrases |
| 週末、週年 | 周末、周年 | both `周` and `週` are standard characters; lexical preference is not a simple 正/俗 relation |
| 菸 | 煙 (tobacco contexts) | usage and dictionary treatment are lexical; do not reduce to glyph substitution |

**How large in practice?** **UNVERIFIED quantitatively.** OpenCC’s current `TWVariants.txt` has 40 source entries and `TWVariantsPhrases.txt` 12, but that is OpenCC’s engineering scope, not the Ministry’s or Taiwan usage’s complete inventory. A study should not infer linguistic prevalence from dictionary size.

## 2. Textbooks: elementary through university

### K–12 prescriptive pole

Taiwan’s K–12 books are subject to review. Review rules require compliance with Ministry printing/specification rules, announced terminology and pronunciation standards. National Academy documentation explicitly identifies the *國字標準字體* and *一字多音審訂表* as the standards for reviewed textbooks. Early elementary books add pedagogical constraints: larger type, specified Kai/Song forms, and extensive Bopomofo annotation.

康軒、南一 and 翰林 therefore publish against the same review framework; they do not define three competing public orthographic standards. I found **no public, current internal house style manual** from those publishers that can be independently audited; their internal documents are **UNVERIFIED**.

No evidence was found of a different orthographic standard by grade. What changes by grade is character load, font size, Bopomofo coverage and instructional complexity—not the identity of the Ministry standard forms.

### University pole

I found no national university-textbook review system that makes the K–12 character standard legally binding on every university press. University publishers use house styles. For example, National Tsing Hua University Press requires Ministry punctuation/full-width Chinese punctuation and recommends ROC dates for Taiwan contexts, Gregorian dates elsewhere. That is one publisher’s style, not a nationwide university rule.

### Descriptive pole

Textbooks establish the cleanest prescriptive endpoint; informal prompts are a different register. Casual Taiwan writers often use `台灣/講台/舞台`, mix punctuation, omit Bopomofo only when context does not invite it, and use local particles or vocabulary that a textbook would avoid. No suitable study was found that directly estimates the distance between K–12 standard spellings and a representative sample of current informal safety prompts. This gap must be measured in the study rather than asserted.

## 3. 一對多轉換: semantic collapses, not 正字/俗字

Simplification merged historically distinct characters. Restoration is a word-sense disambiguation task. OpenCC applies phrase dictionaries before character fallback, so an entry such as `面条→麪條` can be correct even though the character-level mapping for `面` has multiple targets. Short, novel or adversarial strings reduce context and make fallback errors more likely.

### Operational inventory for contemporary benchmark text

The following is the broad practical set found in OpenCC’s multi-target character inventory and common modern use. “Ambiguity” means the wrong traditional character can change meaning in plausible running text; it does not mean OpenCC necessarily fails on the listed example.

| Simplified source | Traditional distinctions and meanings | Running-text ambiguity |
|---|---|---|
| 面 | 面 face/surface; 麵 flour/noodles | high |
| 干 | 乾 dry/do; 幹 do/trunk/cadre; 干 shield/interfere | very high |
| 发 | 發 emit/develop; 髮 hair | high |
| 后 | 後 behind/after; 后 empress | high |
| 只 | 只 only; 隻 classifier/one of pair; 祇 deity/only in learned use | high |
| 系 | 系 system/department; 係 relation/is; 繫 tie/connect | high |
| 折 | 折 break/discount; 摺 fold | medium-high |
| 志 | 志 will/aspiration; 誌 record/journal | high |
| 松 | 松 pine/surname; 鬆 loose/relax | high |
| 里 | 里 village/distance; 裡 inside; 哩 particle/unit | high |
| 制 | 制 system/control; 製 manufacture | high |
| 表 | 表 surface/show/table; 錶 watch/meter | high |
| 谷 | 谷 valley; 穀 grain | high |
| 台 | 臺 platform/Taiwan; 檯 counter/desk; 颱 typhoon; 台 independent historical/special senses | very high |
| 余 | 余 surname/I (literary); 餘 remainder | medium |
| 冲 | 沖 rinse/rush; 衝 charge/collision | high |
| 准 | 準 standard/allow; 准 old/technical form | medium |
| 划 | 劃 divide/plan/stroke; 划 row/transfer (lexical) | high |
| 升 | 升 litre/rise; 昇 ascend | medium; often variant preference |
| 卷 | 卷 volume/paper; 捲 roll/curl | high |
| 历 | 歷 experience/history; 曆 calendar | high |
| 周 | 周 cycle/surname; 週 week | medium; regional standard intersects |
| 团 | 團 group; 糰 dumpling/ball of food | high |
| 复 | 復 return/recover; 複 complex/repeat; 覆 overturn/cover/reply | very high |
| 尽 | 盡 exhaust/all; 儘 as far as/let | medium-high |
| 并 | 並 and/side-by-side; 併 combine | high |
| 征 | 征 campaign/journey; 徵 levy/sign/solicit | high |
| 斗 | 斗 measure/constellation; 鬥 fight | high |
| 曲 | 曲 bend/song; 麴 fermentation starter | medium |
| 板 | 板 board; 闆 proprietor in 老闆 | high in one lexical family |
| 汇 | 匯 remit/flow together; 彙 collect/category | high |
| 沈 | 沈 surname/sink; 瀋 place name/juice in learned use | medium |
| 注 | 注 pour/focus; 註 annotate | high |
| 游 | 游 swim/surname; 遊 travel/wander | medium-high |
| 炼 | 煉 refine; 鍊 chain/forge | high |
| 烟 | 煙 smoke; 菸 tobacco | medium; Taiwan lexical convention |
| 签 | 簽 sign; 籤 lot/bamboo slip | high |
| 纤 | 纖 fine/fibre; 縴 towrope | low-medium |
| 胡 | 胡 surname/reckless; 鬍 beard; 衚 alley in 衚衕 | high in short phrases |
| 脏 | 臟 organ; 髒 dirty | high |
| 腊 | 臘 twelfth lunar month/cured; 腊 dried meat/rare form | medium |
| 范 | 范 surname; 範 model/scope | high |
| 获 | 獲 obtain; 穫 harvest | high |
| 蒙 | 蒙 cover/receive; 矇 deceive/blind; 濛 mist; 懞 muddled | high |
| 闲 | 閒 leisure/gap; 閑 barrier/idle (learned/variant distribution) | medium |
| 钟 | 鐘 clock/bell; 鍾 concentrate/surname | high |
| 须 | 須 must; 鬚 beard/tendril | high |
| 饥 | 飢 hungry; 饑 famine/crop failure | medium; modern usage can merge |
| 丑 | 丑 earthly branch/clown role; 醜 ugly | high |
| 仆 | 僕 servant; 仆 fall forward | medium |
| 几 | 幾 how many/almost; 几 small table (learned) | high |
| 云 | 雲 cloud; 云 say | high |
| 于 | 於 preposition; 于 surname/ancient form | medium |
| 了 | 了 aspect/completion; 瞭 understand/look from height | high in compounds |
| 卜 | 卜 divine; 蔔 radish element | high in compounds |
| 伙 | 伙 meals/group; 夥 numerous/partner | medium; overlap/variation |
| 咸 | 咸 all; 鹹 salty | high |

OpenCC 1.4.1’s `STCharacters.txt` contains **275 multi-target source entries**, but that is not a list of 275 independent modern semantic collapses: it mixes productive mergers, archaic distinctions, personal/place names, regional variants and target preferences. The reproducible “full list” for the experiment is therefore the frozen OpenCC file itself; the table above is the contemporary semantic subset that should be manually annotated for benchmark opportunities.

### Converter error rate

**OpenCC-specific error rate: UNVERIFIED.** I found no public current gold test with an error rate for the exact `s2t`, `s2tw` or `s2twp` configurations. Papers reporting roughly 98–98.5% disambiguation evaluate other systems/models and must not be attributed to OpenCC. A PRC Ministry claim of 99.994% concerns a PRC system and PRC standards, not OpenCC or Taiwan output.

The study should create its own gold audit: mark every source span with a multi-target opportunity, compare outputs to context-appropriate Taiwan characters, and report errors per opportunity with Wilson intervals. Phrase-covered easy cases and fallback cases must be separated.

## 4. Vocabulary differences

The strongest Taiwanese official resource is the *中華語文知識庫* / *中華語文大辭典* cross-strait difference list. It contains more than 4,800 groups in four useful relations: 同實異名, 同名異實, 臺灣特有 and 大陸特有; Taiwan entries use Taiwan standard forms and Mainland entries PRC normative forms. The Ministry’s concise dictionary republishes a cross-strait common-word table from this source.

This is an authoritative comparison resource, not a statutory list and not a frequency lexicon. Its own presentation warns against directional overreading: a paired preference such as Taiwan `水準` versus Mainland `水平` does not mean Taiwan never uses `水平`.

OpenCC 1.4.1 `s2twp` correctly localised many classic computing terms in the direct test: `軟件→軟體`, `網絡→網路`, `鼠標→滑鼠`, `打印機→印表機`, `程序→程式`, `信息→資訊`, `視頻→影片`, `服務器→伺服器`, `硬盤→硬碟`, `內存→記憶體`. It left `質量` as `質量`, demonstrating that not every contextual preference is converted. Coverage must be measured against a chosen official subset, not inferred from examples.

## 5. Proper-noun transliteration

Taiwan has institutional translation resources. The National Academy’s reviewed foreign-scholar name list reports 8,912 names across nine language groups, reviewed through 302 subgroup and 35 plenary meetings, with original-language forms as the basis. The Ministry of Foreign Affairs uses `紐西蘭` and `寮國` in official country pages.

The hypothesis that converters handle no proper names is **refuted**. In OpenCC 1.4.1, `TWPhrases` includes `奧巴馬→歐巴馬`, `新西蘭→紐西蘭` and `老撾→寮國`. It did not contain tested mappings for `布什→布希`, `悉尼→雪梨`, `克林頓/柯林頓`, or `里根→雷根`. Thus proper-name coverage is sparse and uneven, not absent.

Uncovered names can be strong native-locale signals, but they are entity- and era-dependent and can trivially leak topic/source. Evaluate them in a separate named-entity stratum.

## 6. Grammar and syntax

Taiwan Mandarin syntax is documented. A National Taiwan Normal University thesis derived ten feature families from Taiwan data: constructions involving `有、說、給、在、會、不行、用V的、V看看、不錯V、來/去＋地方`. It treats them as a continuum influenced by language background and education, not a categorical grammar.

Research on `有＋VP` ties the construction to language contact and grammaticalisation. Acceptability is construction-specific: in one 94-participant study, `有看到他嗎` and `有在聽` were rated much more acceptable than bare declarative variants such as some `有去過` statements. These are acceptability/usage studies, not prevalence estimates for written prompts.

OpenCC cannot add or repair syntax. A machine can flag candidate patterns, but deciding whether `給`, `會`, a final particle or word order is pragmatically natural requires context. Claims about written informal frequency remain **UNVERIFIED** unless measured in a current chat/PTT-like corpus.

## 7. Taiwanese Hokkien loans in written Mandarin

Taiwan scholarship documents Hokkien borrowing into Mandarin and discusses forms such as `走透透`; Academia Sinica public scholarship explains modern items including `奧步、撇步、毋湯`. This establishes the mechanism. It does not establish that every internet spelling in the prompt is common.

For the examples `甲意、好康、阿沙力、凍蒜、趴趴走、歹勢、系金ㄟ、母湯`, individual current frequencies in informal Taiwan Chinese are **UNVERIFIED**. Spellings mix loans, phonetic characters, Japanese-mediated vocabulary, election slogans and memes. `系金ㄟ` is a playful phonetic rendering, not a stable standard form.

A direct search of OpenCC 1.4.1 dictionaries found none of those eight strings as Taiwan localisation entries. The converter will not invent them. They are high-precision, low-recall register cues, best modelled as a spelling-variant lexicon with native adjudication.

## 8. Internet and PTT register

PTT is a Taiwan-specific BBS and has been used to build a dynamic corpus because older balanced corpora do not track new usage well. It is valuable for describing a register, not representative of every Taiwanese writer.

`鄉民、婉君、87、森77、484、是在哈囉、咩噗` are time-, community- and platform-sensitive. A token lexicon is deterministic but brittle. Numbers such as `87` and `484` have many ordinary uses; they require local context. OpenCC does not generate them.

Inline Bopomofo is the cleanest deterministic cue. Unicode `U+3105–U+312F` can be detected exactly. False positives include quoted teaching material, phonetic annotation and text copied from Taiwan by a non-Taiwan author. It is evidence of Taiwan-oriented production, not proof of author nationality.

## 9. Dates, numerals, punctuation and typography

Taiwan’s Ministry punctuation handbook prescribes 15 marks and uses horizontal `「」『』`; Executive Yuan public-document guidance requires full-width Chinese punctuation and half-width Arabic numerals/Latin letters in official documents. Government dates often use ROC years, so `民國115年` means 2026.

These are weak authorship cues:

- `「」` is not Taiwan-exclusive; it appears in Hong Kong, Japanese-influenced publishing and other Traditional contexts.
- Informal Taiwan users also type ASCII or curly quotes.
- ROC dates are strong evidence of Taiwan civic context, not of native authorship.
- OpenCC preserves punctuation and numerals; any difference comes from the source or a separate normaliser.

Hong Kong must remain separate: its standard vocabulary (`網絡、軟件`) and character preferences are not Taiwan errors. A “Traditional = Taiwan” label would contaminate this study.

## 10. Existing scholarship and corpora

### Taiwan corpora

- **Academia Sinica Balanced Corpus 4.0:** more than 10 million segmented/tagged words; useful for edited Taiwan Mandarin, but its texts span 1981–2007 and underrepresent current internet language.
- **Corpus of Contemporary Taiwanese Mandarin (COCT/國教院):** the 2020 technical report gives about 435.41 million written characters excluding the expanded news total, 3.43177 billion including news, 46.35 million spoken characters, 11.6 million bilingual and 1.564 million learner data. The dominance of news must be controlled.
- **PTT Corpus / LOPEN:** designed to update emerging Taiwan internet usage, but platform demographics and topic distributions make it a register corpus rather than a population baseline.

### Existing regional classifiers

VarDial 2019’s “Discriminating between Mainland and Taiwan Variation of Mandarin Chinese” task used roughly 10,000 news sentences per variety from the Sinica Corpus and the Lancaster Corpus of Mandarin Chinese. Organisers removed punctuation and Latin named entities and created both Traditional and Simplified tracks with OpenCC. This intentionally suppressed script as the main cue.

Seven teams participated. Best Traditional-track macro-F1 was **0.9084** (character n-grams); the best Simplified result was **0.8929**. The report notes that many errors involved generic topics and that topical vocabulary, more than grammar, appeared decisive. This is a direct precedent for machine-operationalised regional provenance, with serious topic leakage.

SC-TC-Bench (FAccT 2025) separately operationalises 110 Mainland/Taiwan regional-term pairs and 352 names to test model preference/bias. It is not an authorship classifier and not a paired safety-verdict audit.

**No exact prior study found:** I found no public study pairing the same Taiwan-native harmful/benign intent as `s2t`, `s2twp` and native text and then testing safety classifier or response-level verdict stability. This is a bounded literature-search result, not proof of nonexistence.

## 11. What OpenCC actually does

### Exact pipelines in current source

Inspection used OpenCC master commit `6b1538b5a1ad15c9025be0306a17b95ac897fa5e` (1 August 2026) and the released npm package `opencc` 1.4.1 (published 12 July 2026).

| Config | Pipeline after compatibility normalisation | Locale interpretation |
|---|---|---|
| `s2t` | union of `STPhrases` + `STPhrases_GeneratedFromRegionalPhrases`, then `STCharacters` | generic/internal Traditional restoration, not a real locale |
| `s2tw` | `s2t` stage, then `TWVariantsPhrases`, then `TWVariants` | Taiwan character-form normalisation; **no `TWPhrases`** |
| `s2twp` | `s2t` stage, then `TWPhrases`, `TWVariantsPhrases`, `TWVariants` | phrase localisation plus Taiwan variants |
| `t2s` | `TSPhrases`, `TSCharactersExt`, `TSCharacters` | Traditional to Simplified; also context-sensitive |

Therefore:

- “`s2tw` carries no vocabulary dictionary” is **confirmed** if “vocabulary dictionary” means `TWPhrases`.
- “`s2tw` collapses into `s2t`” is **refuted**: it performs a second Taiwan-variant stage (`麪→麵`, `裏→裡`, `爲→為`, etc.).
- `s2twp` is not “native transcreation”; it is deterministic phrase replacement plus character normalisation.

### Dictionary counts and version drift

| Dictionary | npm 1.4.1 non-comment entries | master, 1 Aug 2026 | Primary role |
|---|---:|---:|---|
| `STCharacters` | 4,012 | 4,012 | character restoration candidates |
| `STPhrases` | 49,139 | 49,174 | context-sensitive phrase restoration |
| `TWPhrases` | 775 | 817 | Taiwan phrase localisation |
| `TWVariants` | 38 | 40 | Taiwan preferred character variants |
| `TWVariantsPhrases` | 4 | 12 | phrase exceptions for variant conversion |
| `TSPhrases` | 476 | 477 | reverse phrase conversion |
| `TSCharacters` | 4,148 | 4,148 | reverse character conversion |

The master branch changed again after the npm release, including an August 2026 fix for greedy `s2twp` matching. Reproducibility requires freezing the package version **and** recording dictionary hashes; “OpenCC” alone is not a treatment definition.

### Direct conversion check (OpenCC 1.4.1)

For the controlled string of computing terms and names:

- `s2t` produced `軟件、網絡、鼠標、打印機、程序、信息、視頻、服務器、硬盤、內存` and `布什、奧巴馬、悉尼、新西蘭、老撾`.
- `s2tw` was the same at the vocabulary level, while changing Taiwan character variants such as `麪條→麵條`.
- `s2twp` produced `軟體、網路、滑鼠、印表機、程式、資訊、影片、伺服器、硬碟、記憶體` and localised `奧巴馬→歐巴馬、新西蘭→紐西蘭、老撾→寮國`; it retained `質量、布什、悉尼`.

This demonstrates classes, not accuracy. A converter can be correct on dictionary examples and fail on novel/adversarial context.

## Verdict

### (a) Strongest signals versus noise

**Strong, high-precision but low-recall:**

- inline Bopomofo after excluding educational quotation;
- Taiwan-only institutional/civic terms in genuinely local scenarios;
- Hokkien loans and Taiwan phonetic spellings;
- Taiwan proper-name forms missing from `TWPhrases`;
- multiple Taiwan lexical choices plus compatible particles/grammar in the same short text.

**Best broad machine signal:** character and word n-grams after script normalisation, with explicit controls for topic and named entities. VarDial demonstrates that this works on news, but also that it can be mostly topical.

**Mostly noise as single features:** `臺灣` rather than `台灣`; `「」`; one ROC date; one meme number; one `有＋VP`; or one standard variant. Both native official prose and mechanical output can contain the prescriptive form. In particular, OpenCC’s tendency to produce `臺灣/講臺/舞臺` can make mechanical text *less colloquial*, but it is not a stable native/non-native separator.

### (b) Has “native versus converted” already been operationalised?

**Partly yes.** VarDial 2019 deliberately used OpenCC to create parallel script tracks and classified Mainland versus Taiwan regional provenance. SC-TC-Bench formalises regional vocabulary/name pairs. Your study is not first to operationalise regional Chinese variation.

**Exact safety claim remains open in the searched record:** whether three semantically matched provenance renderings change guard/classifier verdicts, unsafe compliance, over-refusal or model ranking. That is the claim to make—only if the effect survives the controls below.

### (c) What a solo researcher can and cannot classify

| Claim | Solo-machine feasible? | Native review needed? |
|---|---|---|
| Unicode Bopomofo, ROC dates, punctuation, known lexicon hits | yes, deterministic | only for false-positive policy |
| OpenCC dictionary coverage and exact A→B diffs | yes, fully reproducible | no |
| Candidate one-to-many ambiguity opportunities | yes | yes for gold sense/output correctness |
| Regional classifier using n-grams/syntax | yes | yes to interpret topic leakage and error cases |
| Semantic equivalence of A/B/C prompts | not reliably | **at least two independent native Taiwan annotators** |
| Naturalness/localness and particle pragmatics | no | **native judgement and adjudication** |
| Current slang currency and social meaning | only heuristic | native, ideally demographically varied reviewers |
| “Author is Taiwanese” | no; features show text provenance/register, not identity | cannot be guaranteed even by readers |

The scientifically safe target is **locale provenance of the text**, not nationality or identity of the author.

## Kill criteria

The three-rendering design rests on an accidental tool contrast rather than a principled locale contrast if any of the following occurs:

1. After masking named entities, local institutions and Bopomofo, independent native annotators cannot order localness as `C > B > A` above chance.
2. `B` differs from `A` almost entirely through a handful of `TWPhrases` lookups, while `C` contains no independently specified grammar/register features.
3. The source prompts contain too few locale-bearing opportunities; most A/B/C triplets are byte-identical or differ only in `台/臺`.
4. Meaning-preservation agreement is poor, especially because `s2t` or `s2twp` selects the wrong member of a one-to-many set.
5. Safety effects disappear after controlling for token count, tokenisation, named entities, harmfulness/severity ratings and lexical edit count.
6. Within-condition decoding or classifier-version variance is larger than the A/B/C effect.
7. Results are driven by one OpenCC release, one dictionary update, one model, one classifier or fewer than five recurring phrases.
8. The result vanishes with another competent converter or with a human lexical-localisation baseline.
9. The native condition is one researcher’s idiolect and a second native annotator rejects its localness or semantic equivalence.
10. A classifier succeeds only through topic leakage (健保、立法院, place names) and fails on topic-matched or entity-masked prompts.
11. `s2tw` is treated as identical to `s2t`, or `s2twp` is represented as comprehensive Taiwan localisation; the actual configs refute both.
12. The only stable finding is that `s2twp` sounds nicer or `s2t` looks overly formal, with no change in the safety conclusion.
13. Effects do not replicate on both harmful prompts and matched benign hard negatives.
14. OpenCC version/dictionary hashes are not frozen, so the treatment cannot be reproduced.
15. The paper’s novelty collapses to “Mainland and Taiwan text can be classified”; VarDial 2019 already established that on news.

## Recommended operationalisation

Treat each triplet as a bundle of measured edits rather than three opaque labels. For every prompt record:

- frozen OpenCC package, commit and dictionary hashes;
- character-restoration edits, Taiwan-variant edits and `TWPhrases` edits separately;
- one-to-many ambiguity opportunities and gold correctness;
- Taiwan vocabulary/name hits;
- grammar/particle/Hokkien/Bopomofo/slang features;
- local-entity/topic features, separately maskable;
- length and model-token counts;
- two native ratings for semantic equivalence and Taiwan localness.

Pre-register the primary contrast `A vs C`; treat `B` as a mechanism probe. Test whether localness mediates safety-verdict changes and whether the effect remains after excluding the deterministic, potentially trivial cues.

## Sources

### Taiwan official and institutional

- Ministry of Education, [常用國字標準字體表](https://language.moe.gov.tw/material/info?m=9fe3ff5a-5a8c-4817-9e60-6337dd55a509).
- Ministry of Education, [異體字字典 FAQ: definitions of 正字 and 異體字](https://dict.variants.moe.edu.tw/page.jsp?ID=6) and [編輯略例/current entry counts](https://dict.variants.moe.edu.tw/page.jsp?ID=9&la=0).
- Ministry of Education, [異體字研訂說明處理原則](https://dict.variants.moe.edu.tw/page.jsp?ID=87).
- National Academy for Educational Research, [異形詞辨析手冊（試用版, 2024）](https://www.naer.edu.tw/upload/1/14/doc/4519/%E7%95%B0%E5%BD%A2%E8%A9%9E%E8%BE%A8%E6%9E%90%E6%89%8B%E5%86%8A_%E8%A9%A6%E7%94%A8%E7%89%88_V4_1130402_1.pdf).
- Ministry/National Academy, [國民中小學教科用書審查規範](https://edu.law.moe.gov.tw/LawContent.aspx?id=FL008948), [教科用書印製規格](https://edu.law.moe.gov.tw/LawContent.aspx?id=FL033134), and [review history identifying standard forms](https://naeraj.naer.edu.tw/wSite/PDFReader?fileName=1400772860303&format=pdf&xmlId=1663487).
- Ministry of Education, [國語辭典簡編本 FAQ](https://www.naer.edu.tw/PageFaq/go_page?page=2).
- Chinese Linguipedia, [兩岸差異用詞/about and 4,800+ groups](https://www.chinese-linguipedia.org/about.html) and Ministry concise dictionary [兩岸常用詞語對照表](https://dict.concised.moe.edu.tw/appendix.jsp?ID=54&la=0&powerMode=0).
- National Academy, [外國學者人名譯名審譯成果](https://epaper.naer.edu.tw/edm?content_no=3579&edm_no=203).
- Ministry of Foreign Affairs, [紐西蘭](https://www.mofa.gov.tw/CountryInfo.aspx?CASN=5&n=5&s=77&sms=33) and [寮國](https://www.mofa.gov.tw/CountryInfo.aspx?CASN=5&n=5&s=157&sms=33).
- Ministry of Education, [重訂標點符號手冊](https://language.moe.gov.tw/001/Upload/FILES/SITE_CONTENT/M0001/HAU/haushou.htm); Executive Yuan, [公文書橫式書寫數字使用原則](https://www.ey.gov.tw/File/E64C5F6D27B78A72?A=C) and [文書處理手冊](https://www.ey.gov.tw/File/955BDB8CECCB1C44?A=C).
- National Tsing Hua University Press, [撰稿體例](https://thup.site.nthu.edu.tw/p/412-1210-9517.php?Lang=zh-tw).

### Scholarship and corpora

- NTNU, [當代台灣國語的句法結構](https://www.airitilibrary.com/Publication/alDetailPrint?DocID=U0021-2603200719130652).
- NTNU, [台、華語語言接觸下的「有」字句](https://www.tcll.ntnu.edu.tw/twnica/downloadfile.php?issue_id=19&paper_id=119&periodicalsPage=2).
- [國語中的台語借詞：台灣的方言借入機制](https://www.airitilibrary.com/Article/Detail/18156576-200906-200907230049-200907230049-99-133); Academia Sinica, [奧步、撇步、毋湯與南方方言影響](https://research.sinica.edu.tw/linguistics-southern-min-modern-mandarin/).
- [Academia Sinica Balanced Corpus 4.0](https://asbc.iis.sinica.edu.tw/).
- National Academy, [臺灣華語文語料庫 technical report](https://coct.naer.edu.tw/file/files/%E6%8A%80%E8%A1%93%E5%A0%B1%E5%91%8A%EF%BC%9A%E3%80%8A%E8%87%BA%E7%81%A3%E8%8F%AF%E8%AA%9E%E6%96%87%E8%AA%9E%E6%96%99%E5%BA%AB-%E8%8F%AF%E8%AA%9E%E6%96%87%E6%95%99%E8%88%87%E5%AD%B8%E7%9A%84%E5%BF%85%E5%82%99%E5%B7%A5%E5%85%B7%E3%80%8B.pdf) and [COCT portal](https://coct.naer.edu.tw/).
- [PTT Corpus thesis](https://www.airitilibrary.com/Article/Detail?DocID=U0001-2110201409484500) and [LOPEN](https://lopen.linguistics.ntu.edu.tw/).
- Marcos Zampieri et al., [VarDial 2019 Evaluation Campaign](https://aclanthology.org/W19-1401/) and [campaign page](https://sites.google.com/view/vardial2019/campaign).
- [SC-TC-Bench repository](https://github.com/brucelyu17/SC-TC-Bench) and [FAccT 2025 paper](https://dl.acm.org/doi/full/10.1145/3715275.3732182).

### OpenCC primary files

- [Design principles](https://github.com/BYVoid/OpenCC/blob/master/DESIGN_PRINCIPLES.md).
- Configs: [`s2t.json`](https://github.com/BYVoid/OpenCC/blob/master/data/config/s2t.json), [`s2tw.json`](https://github.com/BYVoid/OpenCC/blob/master/data/config/s2tw.json), [`s2twp.json`](https://github.com/BYVoid/OpenCC/blob/master/data/config/s2twp.json), [`t2s.json`](https://github.com/BYVoid/OpenCC/blob/master/data/config/t2s.json).
- Dictionaries: [`STCharacters.txt`](https://github.com/BYVoid/OpenCC/blob/master/data/dictionary/STCharacters.txt), [`STPhrases.txt`](https://github.com/BYVoid/OpenCC/blob/master/data/dictionary/STPhrases.txt), [`TWPhrases.txt`](https://github.com/BYVoid/OpenCC/blob/master/data/dictionary/TWPhrases.txt), [`TWVariants.txt`](https://github.com/BYVoid/OpenCC/blob/master/data/dictionary/TWVariants.txt), [`TWVariantsPhrases.txt`](https://github.com/BYVoid/OpenCC/blob/master/data/dictionary/TWVariantsPhrases.txt).

## Evidence limitations

- The research distinguishes Taiwan from Mainland China and Hong Kong throughout. PRC conversion-performance claims were not imported as Taiwan evidence.
- No representative frequency study of current informal Taiwan safety prompts was found; qualitative labels are explicitly hypotheses.
- OpenCC counts were computed from nonblank, non-comment source lines. Dictionary entries vary in granularity and are not directly comparable with official lexical groups.
- Proper-name, slang and platform vocabularies change. The examples were checked against OpenCC 1.4.1, not claimed exhaustive for all releases.
- “Not found” is not “does not exist.” The literature search was broad but not a systematic review with database-exported inclusion logs.
