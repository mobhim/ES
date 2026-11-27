# جرد الحركة في `index.html` وقائمة «ممنوع اللمس»

- الملف المرجعي: `brand/index.before.html` (نسخة طبق الأصل من `index.html` قبل أي تعديل، SHA-256 يبدأ بـ `aa92c024bfa7d657`). كل أرقام الأسطر في هذا المستند تشير إليه.
- خط الأساس الآلي: `brand/motion-baseline.json` (قيمة `strict_sha256` = `8536ff97a9f23d960d18ea48a48ff9b818aa69e8e31219b379fc4715c9fcf576`).
- القاعدة: كل حركة تبقى كما هي في التوقيت والتسهيل والترتيب والمكتبات وأسماء الأصناف والمعرّفات والعناصر التي تعتمد عليها. إعادة التلوين تغيّر القيم اللونية فقط.

## أرقام إجمالية (من السكربت)

| البند | العدد |
|---|---|
| حركات مجرودة في هذا المستند | 69 (`M01` إلى `M69`) |
| كتل `@keyframes` | 20 كتلة، 18 اسماً فريداً (`up` و`pop` معرّفان مرتين، والتعريف الأخير هو النافذ) |
| تصريحات `transition*` | 28 خارج كتلة تقليل الحركة (+1 داخلها) |
| تصريحات `animation*` | 101 خارج كتلة تقليل الحركة (+1 داخلها) |
| قواعد CSS تحمل تصريحاً حركياً | 143 |
| استدعاءات `.animate(` | 3 (واحد داخل `anim()`، واحد في `route()`، واحد لتبديل السمة) |
| استدعاءات `anim(` / `openAnim(` / `tween(` | 3 / 2 / 4 |
| `setTimeout` / `clearTimeout` | 6 / 3 |
| `requestAnimationFrame` | 3 |
| `IntersectionObserver` | 2 |
| `document.startViewTransition` | 1 |
| دوال JS مصنّفة حركية | 21 من 29 |

ثوابت التسهيل المستخدمة في كل الملف:

- `--ease` = `cubic-bezier(.16,1,.3,1)` (سطر 29، مستخدم 55 مرة). نسخة مطابقة في JS: الثابت `EASE` (سطر 759).
- `--spring` = `cubic-bezier(.34,1.56,.64,1)` (سطر 29، مستخدم 14 مرة).
- تسهيل العدّادات في `tween()`: `1-(1-p)^4` محسوب يدوياً.

---

## 1. الجرد الكامل

اصطلاح: «نافذ» يعني القيمة التي تفوز في التتالي (cascade). كثير من القواعد معرّفة مرتين: مرة في القسم الأول (أسطر 105 إلى 162) ومرة في قسم `bolder motion` (أسطر 384 إلى 402) أو قسم `theme` (أسطر 328 إلى 382). القيمة المذكورة هنا هي النافذة، والتعريف المغلوب مذكور في العمود الأخير.

### أ. التحميل الأول (الشعار والقائمة)

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M01 | قوس الشعار يرسم نفسه | `.brand svg` المسار الأول، عند التحميل | CSS `@keyframes draw` + stroke-dash | 1.1s، تأخير .15s، `var(--ease)`، `forwards` | `stroke-dashoffset` من 1 إلى 0 | `.brand path` (سطر 106)، `stroke-dasharray:1`، السمة `pathLength="1"` على `<path>` (سطر 474)، المسار يجب أن يكون مرسوماً بـ `stroke` |
| M02 | خط المؤشر داخل الشعار يُرسم بعد القوس | `.brand svg` المسار الثاني، عند التحميل | نفس M01 | المدة .8s، التأخير .75s (سطر 107 يغيّر `animation-delay` و`animation-duration` فقط) | `stroke-dashoffset` | `.brand path+path`، ترتيب المسارين داخل الـ SVG |
| M03 | نقطة الشعار تظهر بتكبير | `.brand circle`، عند التحميل | CSS `@keyframes pop` (النافذ سطر 387: من `opacity:0; scale(0)`) | .5s، تأخير 1.4s، `var(--ease)`، `both` | `opacity`، `transform` | `.brand circle`، `transform-box:fill-box`، `transform-origin:center` (سطر 108). تعريف `pop` الأول (سطر 95، `scale(.35)`) مغلوب |
| M04 | اسم المنصة ووصفها يظهران تدريجياً | `.brand div`، عند التحميل | CSS `@keyframes fade` | .8s، تأخير .3s، تسهيل افتراضي `ease`، `both` | `opacity` | `.brand div` (سطر 109): أي `div` داخل `.brand` يأخذ الحركة |
| M05 | روابط القائمة تدخل واحداً تلو الآخر | `#nav a`، عند التحميل (عند بناء القائمة في `nav()`) | CSS `@keyframes navin` | .6s، تأخير `calc(var(--i)*55ms + .2s)`، `var(--ease)`، `both` | `opacity`، `transform: translateX(14px)` إلى 0 | `.nav a` (سطر 110)، `--i` يُكتب من `nav()` في `style="--i:${i}"` (سطر 771)، ترتيب `VIEWS` (سطر 678) |
| M06 | الحبة البيضاء خلف الرابط الحالي تظهر | `.pill`، عند التحميل | CSS `fade` | .5s، تأخير .55s، `ease`، `both` | `opacity` | `.pill` (سطر 111)، العنصر `<i class="pill">` يُنشأ في `nav()` كأول ابن لـ `#nav` |

### ب. القائمة الجانبية

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M07 | الحبة تنزلق إلى الرابط الجديد وتأخذ مقاسه | `.pill`، عند تغيير المسار، `resize`، واكتمال تحميل الخطوط | CSS transition، والقيم تُكتب inline من `pill()` | النافذ (سطر 388): `transform .7s var(--spring)`، `width .6s var(--ease)`، `height .3s var(--ease)` | `transform: translate(Xpx,Ypx)`، `width`، `height` | `pill()` (سطر 778) تقرأ `offsetWidth/offsetHeight/offsetLeft/offsetTop` للرابط `#nav a[aria-current]`؛ `.nav{position:relative}`؛ `.pill{position:absolute;top:0;left:0;z-index:0}`؛ `.nav a{position:relative;z-index:1}`؛ `addEventListener('resize',pill)` (سطر 813)؛ `document.fonts.ready.then(pill)` (سطر 1077). تعريف سطر 111 (`.6s var(--ease)` للتحويل) مغلوب |
| M08 | لون نص الرابط وخلفيته يتبدلان | `.nav a`، عند المرور وعند تغيّر `aria-current` | CSS transition | `background .2s var(--ease)`، `color .35s var(--ease)` (سطر 67) | `background`، `color` | `.nav a:hover` (النافذ سطر 333)، `.nav a[aria-current=page]{color:#0b4a44}` (سطر 69)، `aria-current` يُضبط في `route()` |
| M09 | أيقونة الرابط تكبر عند المرور | `.nav a svg`، hover | CSS transition | `transform .4s var(--ease)` (سطر 161) | `transform: scale(1.12)` (سطر 162) | الأيقونة يجب أن تبقى `<svg>` ابناً لـ `<a>`؛ `ic()` و`IC` |
| M10 | شارة عدد التنبيهات تنبض عند إصدار أمر عمل | `#badge` (`.nav .n`)، عند الضغط على زر `[data-go]` | CSS `@keyframes bump`، يعاد تشغيلها بإزالة الصنف ثم `void b.offsetWidth` ثم إضافته | .5s، بلا تأخير، `var(--ease)` | `transform: scale(1.35)` عند 40% | `badge(bump)` (سطر 774)، الصنف `bump`، `.nav .n.bump` (سطر 112)، `#badge` |

### ج. تغيير المسار (route)

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M11 | الشاشة الحالية تخفت وترتفع قليلاً قبل التبديل | `.view.on`، عند `hashchange` (ليس عند التحميل الأول) | WAAPI `cur.animate` (سطر 807) ثم `setTimeout` 180 ينفذ `an.cancel(); go()` | 180ms، `ease-in`، `fill:'forwards'` | `opacity` 1 إلى 0، `transform` إلى `translateY(-12px)` | `route()` (سطر 794)، المتغير `rt`، `clearTimeout(rt)`، الشرط `scroll&&!RM&&cur&&cur.id!=='v-'+v`، الأصناف `view` و`on`، المعرّفات `v-<اسم>` |
| M12 | عنوان الصفحة يدخل من الأسفل | `#title`، مع M11 | `anim()` (WAAPI) | 500ms، تأخير 180ms، `EASE`، `fill:'backwards'` | `opacity` 0 إلى 1، `transform` من `translateY(8px)` | `#title`، `anim()` (سطر 761)، `EASE` |
| M13 | الصفحة تعود للأعلى والرابط الحالي يُمرَّر إلى مجال الرؤية فوراً | عند تغيير المسار | `scrollTo(0,0)` و`scrollIntoView({block:'nearest',inline:'nearest'})` | فوري (لا يوجد `scroll-behavior` في الملف) | موضع التمرير | سطرا 800 و801. إضافة `scroll-behavior:smooth` تغيّر هذه الحركة |

### د. نظام الكشف `.pre` / `.play`

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M14 | أبناء الشاشة المباشرون يُخفَون ثم يُكشفون عند دخولهم مجال الرؤية، بفاصل بينهم | كل ابن مباشر لـ `section.view` عند دخول الشاشة | `enter()` يضيف `pre` ويراقب بـ `IntersectionObserver` اسمه `io`؛ عند التقاطع `setTimeout(()=>play(el), i++*120)` | عتبة `threshold:.06`؛ فاصل 120ms بين العناصر المتقاطعة في الدفعة نفسها (العدّاد `i` يبدأ من 0 لكل دفعة) | `opacity:0` عبر `.js .pre` (سطر 115) | `enter()` (سطر 789)، `io` (سطر 783)، `play()` (سطر 784)، الصنف `js` على `<html>` (سطر 760)، الصنفان `pre` و`play`، ترتيب وعدد الأبناء المباشرين لكل `.view` (يشمل `.srcline` التي يضيفها `fourTypes()` بـ `prepend`) |
| M15 | العنصر المكشوف يصعد ويتضح | كل عنصر يحمل `.play` | CSS `@keyframes up` (النافذ سطر 385: من `opacity:0; translateY(46px) scale(.97); filter:blur(8px)`) | .95s، بلا تأخير، `var(--ease)`، `both` (سطر 116) | `opacity`، `transform`، `filter` | `.play`. تعريف `up` الأول (سطر 90، `translateY(18px)`) مغلوب |
| M16 | الصنف `play` يُزال بعد انتهاء المشهد، أو فور تفاعل المستخدم | بعد الكشف | `setTimeout(...,3400)` في `play()`، ومستمع `pointerdown` على المستند (سطر 793) | 3400ms بعد الكشف؛ أو فوراً عند `pointerdown` على `button,tr,g,input,select` داخل `.play` | إزالة الصنف (توقف كل حركات `.play …` وتعود العناصر لوضعها الطبيعي) | `el._pt`، `clearTimeout(el._pt)`، المحدِّد `'button,tr,g,input,select'` |
| M17 | العمود الثاني في الصف يتأخر قليلاً | `.cols.play>:nth-child(2)` | CSS `up` | .95s، تأخير .16s، `var(--ease)`، `both` (سطر 117) | مثل M15 | `.cols` وترتيب ابنَيها |
| M18 | الأرقام تعدّ من 0 إلى قيمتها | كل `[data-to]` داخل العنصر المكشوف (أرقام `#figs` الأربعة) | `tween()` بـ rAF، مع `setTimeout` احتياطي | 1500ms؛ تسهيل `1-(1-p)^4`؛ الاحتياطي عند `dur+80` يكتب القيمة النهائية | `textContent` | `tween()` (سطر 762)، الدالة الداخلية `step`، `el._v`، `el._t`، `data-to`، `data-suf`، `N()`، `.fig dd span{display:inline-block}` (سطر 345)، `font-variant-numeric:tabular-nums` على `body` (سطر 50) |

### هـ. النظرة العامة (الأرقام، الأقواس، القوائم، الأشرطة)

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M19 | أرقام المؤشرات تصعد بالتتابع | `.play .fig dd` | CSS `up` | .9s، `var(--ease)`، `both`؛ التأخير: 0، .12s، .24s، .36s للبطاقات 1 إلى 4 (أسطر 392 و393) | مثل M15 | `.fig`، `dd`، ترتيب البطاقات |
| M20 | أعمدة المدرّج الصغير تنمو من الأسفل | `.play .hist i` | CSS `@keyframes growY` | النافذ (سطر 394): .9s، `var(--spring)`، `both`؛ التأخير للأعمدة 1 إلى 8: .30s إلى .58s بخطوة .04s (سطر 124) | `transform: scaleY(0)` إلى 1 | `.hist i{transform-origin:bottom}` (سطر 122)، ارتفاع كل عمود inline من `figs()` بمعادلة `x/m*34` بكسل (سطر 827) مع `.hist{height:34px}` |
| M21 | الأقواس (الأسابيع) تصعد بالتتابع | `.play .bay` في `#arc1` و`#arc2` | CSS `@keyframes rise` | النافذ (سطر 389): .85s، `var(--spring)`، `both`، تأخير `calc(var(--i)*60ms + 150ms)` | `opacity`، `transform` من `translateY(80px)` | `--i` من `arcade()` (سطر 835)، الصنف `bay`. سطر 118 مغلوب |
| M22 | امتلاء القوس ينمو من الأسفل | `.play .arch i` | CSS `growY` | النافذ (سطر 390): 1.2s، `var(--spring)`، `both`، تأخير `calc(var(--i)*60ms + 500ms)` | `transform: scaleY` | `.arch i{transform-origin:bottom}` (سطر 119)، `height:var(--h)` و`background:var(--c)` (سطر 190)، `--h` و`--c` من `arcade()`؛ `.arch{overflow:hidden;height:132px;border-radius:999px 999px 0 0}`. سطر 120 مغلوب |
| M23 | رقم القوس يظهر بعد الامتلاء | `.play .arch b` | CSS `fade` | النافذ (سطر 391): .5s، `ease`، `both`، تأخير `calc(var(--i)*60ms + 1000ms)` | `opacity` | `.arch b`. سطر 121 مغلوب |
| M24 | لمعة تمر على امتلاء القوس بلا توقف | `.arch i::after`، دائماً | CSS `@keyframes sheen` | 3.6s، `ease-in-out`، `infinite`، تأخير `calc(var(--i)*130ms)` (سطر 356) | `background-position` من `0 150%` إلى `0 -150%` (ثابتة حتى 35%) | الخلفية الأساسية `linear-gradient(...) 0 150%/100% 300% no-repeat` في القاعدة نفسها، `--i` |
| M25 | القوس يرتفع عند المرور ويبقى مرتفعاً عند الاختيار | `.bay:hover .arch`، `.bay[aria-pressed=true] .arch` | CSS transition | النافذ (سطر 351): `box-shadow .3s var(--ease)`، `transform .45s var(--spring)` | `transform: translateY(-8px)`، `box-shadow` | `aria-pressed` من `arcade()`، أسطر 353 و355. سطرا 189 و193 مغلوبان |
| M26 | رقم القوس يكبر عند المرور | `.bay:hover .arch b` | CSS transition | `transform .45s var(--spring)` (سطر 352) | `transform: translateX(-50%) scale(1.15)` (سطر 354) | التوسيط نفسه يعتمد على `left:50%;transform:translateX(-50%)` في سطر 352، فلا يُغيَّر أسلوب التوسيط |
| M27 | انتقال ارتفاع الامتلاء (معرَّف لكنه خامل عملياً لأن `arcade()` يعيد بناء العناصر) | `.arch i` | CSS transition | `height .7s var(--ease)` (سطر 190) | `height` | `--h`. يبقى كما هو |
| M28 | صفوف قائمة التنبيهات تصعد بالتتابع | `.play .rows li` (`#topAlerts` وقائمة لوحة المنطقة) | CSS `up` | .55s، `var(--ease)`، `both`؛ التأخير للصفوف 1 إلى 5: .30، .36، .42، .48، .54s (أسطر 127 و128) | مثل M15 | `.rows`، `li` |
| M29 | صف القائمة ينزاح قليلاً عند المرور | `.rows li:hover` | CSS transition | `padding .35s var(--ease)` (سطر 360) | `padding-inline-start` إلى 8px (سطر 361) | الحشو الأساسي `padding:11px 0` (سطر 207) |
| M30 | أشرطة النِّسب تمتد من اليمين | `.play .pbar i::after` و`.fb i::after` داخل `#topDist`، `#mLift`، `#mImp`، `#pciBars`، `#matMix`، `#matBase` | CSS `@keyframes growX` | النافذ (سطر 395): 1.3s، تأخير .4s، `var(--ease)`، `both` | `transform: scaleX(0)` إلى 1 | `transform-origin:100% 50%` (سطر 125)، `width:var(--w)`، `background:var(--c)`، `inset-inline-start:0`، `overflow:hidden` على المسار، اتجاه الصفحة `dir="rtl"`؛ `--w` و`--c` inline من JS. سطر 126 مغلوب. `#cBars` غير مشمول عمداً (انظر M46) |
| M31 | رقم «الوفر» يعدّ من قيمته السابقة إلى الجديدة | الخانة الرابعة في `#figs`، بعد إصدار أمر عمل | `tween()` | 1000ms (القيمة الافتراضية)، `1-(1-p)^4` | `textContent` | `figs()` (سطر 828): `sp._v=figSaved; tween(sp,saved)`، المتغير `figSaved` |

### و. الجداول والشرائح

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M32 | صفوف الجدول تظهر بالتتابع | `.play tbody tr.r` (`#aBody`، `#kBody`) | CSS `fade` | .6s، `ease`، `both`؛ التأخير للصفوف 1 إلى 6: .25 إلى .50s بخطوة .05s، ومن السابع فما بعد .55s (أسطر 129 و130) | `opacity` | الصنف `r` على `<tr>` |
| M33 | الصف يتلوّن عند المرور واسم المقطع ينزاح | `tbody tr.r:hover` | CSS transition | `background .15s` (سطر 222، تسهيل `ease`)؛ `transform .4s var(--ease)` على `td:first-child b` (سطر 358) | `background`، `transform: translateX(-6px)` | `tbody tr.r td:first-child b{display:inline-block}`، وجود `<b>` أول الخلية الأولى (يُبنى في `alerts()` و`contractors()`) |
| M34 | تفاصيل الصف المفتوح تنزل بالتتابع | أبناء `tr.x td` بعد الضغط على صف في `#aBody` أو `#kBody` | `openAnim()` ثم `anim()` (WAAPI) | 500ms، تأخير `i*90`ms، `EASE`، `fill:'backwards'` | `opacity` 0 إلى 1، `transform` من `translateY(-12px)` | `openAnim()` (سطر 769)، الصنف `x`، استدعاءان في السطرين 938 و965 (بالفأرة فقط، لوحة المفاتيح لا تستدعيها) |
| M35 | شرائح التصفية تصعد | `.filters.play .chip` (`#mapChips`، `#cChips`) | CSS `up` | النافذ (سطر 382): .6s، بلا تأخير، `var(--ease)`، `both` | مثل M15 | سطر 382 يساوي في الخصوصية قواعد التأخير في سطر 132 ويأتي بعدها، فيلغي تتابع .06/.12/.18s. هذا هو السلوك الحالي ويجب أن يبقى. أي إعادة ترتيب للقواعد تعيد التتابع وتغيّر الحركة |
| M36 | الشريحة تتلوّن عند المرور وتنضغط عند النقر | `.chip` | CSS transition | النافذ (سطر 349): `background .25s`، `color .25s`، `transform .35s var(--spring)` | `background`، `color`، `transform: scale(.94)` عند `:active` (سطر 350) | `aria-pressed` من `chips()`. سطر 239 مغلوب |

### ز. الخريطة

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M37 | طرق المخطط البديل تُرسم (فقط إذا لم تُحمَّل Leaflet) | `.play .map .road` | CSS `draw` + stroke-dash | 1.4s (سطر 397 يعدّل المدة فقط)، تأخير .15s، `var(--ease)`، `forwards` (سطر 135) | `stroke-dashoffset` | `pathLength="1"` يُكتب في `map()` (سطر 865)، الصنف `road` |
| M38 | الخط المتقطع فوق الطرق يظهر ثم يجري بلا توقف | `.map .road2` | أثناء `.play`: CSS `fade` (سطر 136)؛ بعدها: `@keyframes flow` (سطر 363) | `fade`: .6s تأخير .9s `both`؛ `flow`: 1.4s `linear` `infinite` | `opacity`؛ `stroke-dashoffset` إلى -14 | `stroke-dasharray:3 4` (سطر 253): القيمة -14 تساوي دورتين كاملتين من النمط |
| M39 | دوائر المناطق تنبثق بالتتابع | `.play .map g.d` | CSS `pop` | النافذ (سطر 396): .85s، `var(--spring)`، `both`، تأخير `calc(var(--i)*75ms + .4s)` | `opacity`، `transform: scale(0)` إلى 1 | `--i` من `map()` (سطر 868)، `transform-box:fill-box;transform-origin:center` (سطر 137). سطر 138 مغلوب |
| M40 | حلقة تتسع وتخفت حول المنطقة المختارة أو الحرجة | `.map .ring` (المخطط البديل) و`.pin.pulse::after` (خريطة Leaflet) | CSS `@keyframes ring` | 2.4s، `ease-out`، `infinite` (سطرا 139 و411) | `transform: scale(1)` إلى `scale(1.6)`، `opacity` .75 إلى 0 | الصنف `pulse` يضاف في `leaf()` عند `risk>=75`؛ `.pin.pulse::after{inset:-3px;border-radius:50%;border:2.5px solid var(--crit-f)}`؛ `.map .ring{stroke:currentColor}` واللون يُكتب inline |
| M41 | دائرة المنطقة تكبر عند المرور ويتغير إطارها | `.map g.d:hover` (المخطط البديل) | CSS transition | `transform .45s var(--spring)` (سطر 365)؛ `r .35s var(--ease)`، `stroke-width .2s` على `circle.b` (سطر 255) | `transform: scale(1.1)`، `stroke-width` 2 ثم 2.5 ثم 4 مع `.sel` | الأصناف `d`، `b`، `sel`، `data-d` |
| M42 | دبوس المنطقة يكبر عند المرور | `.pin:hover` (Leaflet) | CSS transition | `transform .45s var(--spring)` (سطر 406) | `transform: scale(1.12)` (سطر 407) | `.pin` داخل `L.divIcon` بـ `className:''`؛ Leaflet تحرّك العنصر الحاوي بـ `transform`، فلا يُنقل `.pin` إلى الحاوي |
| M43 | محتوى لوحة المنطقة يدخل بالتتابع عند تبديل المنطقة أو النوع | أبناء `#dp` | `anim()` (WAAPI) | 480ms، تأخير `i*60`ms، `EASE`، `fill:'backwards'` | `opacity` 0 إلى 1، `transform` من `translateY(10px)` | `map()` (سطر 880)، المتغير `dpLast` (لا تعمل في أول رسم) |
| M44 | الخريطة تعيد قياس نفسها وتضبط حدودها عند فتح شاشتها | `#map`، عند الانتقال إلى `#map` | `setTimeout(leafFit,60)` | تأخير 60ms؛ `fitBounds` مرة واحدة فقط (`LFit`) بحشو `[46,46]` | حجم الخريطة وإطارها | `leafFit()` (سطر 889)، `.map.geo{height:540px}` (400px تحت 820px) |
| M45 | حركات Leaflet الداخلية: تكبير، سحب بالقصور، ظهور البلاطات، ظهور النوافذ المنبثقة | خريطة `#map` | مكتبة Leaflet 1.9.4 من unpkg (CSS + JS)، غير معرّفة في الملف | قيم المكتبة الافتراضية (لم تُراجَع من مصدرها ضمن هذا الجرد) | `transform`، `opacity` | رابطا المكتبة (سطرا 11 و661) بالإصدار نفسه؛ خيارات `L.map(el,{zoomControl:true})` بلا تعطيل للحركة؛ عدم إضافة `transition` أو `transform` على أصناف `.leaflet-*`؛ `.map.geo{isolation:isolate;overflow:hidden}` |

### ح. الأسباب الجذرية والمنحنيات

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M46 | أشرطة العوامل تمتد من الصفر إلى قيمتها | `#cBars .fb i::after`، عند كل استدعاء لـ `causes()` (التحميل وتبديل الشريحة) | CSS transition يُشغَّل من JS: تُبنى الأشرطة بـ `--w:0%` ثم `requestAnimationFrame` مزدوج يكتب `--w` من `data-w` | `width .7s var(--ease)` (سطر 271) | `width` (عبر `var(--w)`) | `causes()` (أسطر 947 و948)، `data-w`، `setProperty('--w',…)`، المحدِّد `'#cBars .fb'` |
| M47 | منحنيات الصمود تُرسم | `.play .curve path` (`#survType`، `#survK`، `#matSurv`) | CSS `draw` + stroke-dash | 1.6s، تأخير .3s، `var(--ease)`، `forwards` (سطر 430) | `stroke-dashoffset` | `curves()` (سطر 1025) يكتب `pathLength="1"` ويضع `className='curve'` |

### ط. التوصيات (الميزانية)

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M48 | رقما «أعطال تُمنع» و«الوفر» يعدّان إلى القيمة الجديدة | `#sF`، `#sS`، عند تحريك `#bud` | `tween()` | 500ms، `1-(1-p)^4` | `textContent` | `recs()` (سطر 976)، `data-suf=" ر.س"` على `#sS` (سطر 583) |
| M49 | صفوف الإجراءات تبهت أو تعود حسب التمويل | `#rBody td`، `.fund`، عند تحريك `#bud` | CSS transition | `color .45s var(--ease)` (سطر 142)؛ `background .45s var(--ease)`، `color .45s var(--ease)` (سطر 143) | `color`، `background` | الصنف `off` يُبدَّل في `recs()`؛ `tr.off td`، `tr.off .roi`، `tr.off .fund` (أسطر 289 إلى 292)؛ الرموز `--off`، `--sunk`، `--low-soft`، `--low`، `--ink-2` |

### ي. شاشة «عن المنظومة»

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M50 | العنوان الكبير ينكشف من الأعلى إلى الأسفل | `.pitch.play h2` | CSS `@keyframes wipe` | النافذ (سطر 398): 1.1s، تأخير .15s، `var(--ease)`، `both` | `clip-path` من `inset(0 0 100% 0)` إلى `inset(0 0 -12% 0)`، `transform` من `translateY(26px)` | سطر 146 مغلوب. القيمة `-12%` تترك مجالاً لذيول الحروف العربية، وتعتمد على ارتفاع السطر `line-height:1.4` |
| M51 | الفقرة والزر يصعدان بعد العنوان | `.pitch.play p`، `.pitch.play .btn` | CSS `up` | .7s، `var(--ease)`، `both`؛ التأخير .35s للفقرة و.5s للزر (سطرا 147 و148) | مثل M15 | ترتيب `h2`، `p`، `a.btn` |
| M52 | صفوف التحوّل تظهر واحداً تلو الآخر | `.play .shift div` | CSS `fade` | .5s، `ease`، `both`، تأخير `calc(var(--i)*170ms + .4s)` (سطر 400 يغلب سطر 149) | `opacity` | `--i` يُكتب من JS (سطر 1074) لكل `.shift div` |
| M53 | خط الشطب يمتد على العبارة القديمة | `.play .shift s` | CSS `@keyframes strike` | .5s، `var(--ease)`، `both`، تأخير `calc(var(--i)*170ms + .8s)` (سطر 401) | `background-size` من `0 1px` إلى `100% 1px` | الخلفية الأساسية `linear-gradient(currentColor,currentColor) no-repeat 100% 58%/100% 1px` (سطر 302): الموضع `58%` مضبوط على مقاييس الخط الحالي |
| M54 | السهم ينزلق إلى مكانه | `.play .shift svg` | CSS `@keyframes nudge` | .6s، `var(--ease)`، `both`، تأخير `calc(var(--i)*170ms + .95s)` (سطر 402) | `opacity`، `transform` من `translateX(16px)` | السهم `<svg>` ابن مباشر لـ `.shift div` |
| M55 | العبارة الجديدة تهبط في مكانها | `.play .shift b` | CSS `@keyframes land` | النافذ (سطر 399): .8s، `var(--spring)`، `both`، تأخير `calc(var(--i)*170ms + 1.05s)` | `opacity`، `transform` من `translateX(20px) scale(.95)` | سطر 152 مغلوب |
| M56 | العبارة الجديدة تنزاح وتتلوّن عند المرور على الصف | `.shift div:hover b` | CSS transition | `transform .45s var(--spring)`، `background .3s` (سطر 374) | `transform: translateX(-6px)`، `background` | سطر 375 |
| M57 | زر «ادخل المنصة» يرتفع ويكبر عند المرور | `.pitch .btn:hover` | CSS transition | `transform .45s var(--spring)`، `background .2s` (سطر 372) | `transform: translateY(-3px) scale(1.04)`، `background` | سطرا 373 و299 |
| M58 | وهج ذهبي يتبع المؤشر داخل البطاقة | `.pitch`، عند `pointermove` | مستمع JS يكتب `--mx` و`--my` كنسب مئوية؛ بلا transition (تتبّع فوري) | فوري | مركز `radial-gradient` في خلفية `.pitch` | سطر 1093، `var(--mx,18%)` و`var(--my,12%)` في سطر 369، المحدِّد `$('.pitch')` (عنصر واحد) |
| M59 | مخطط «كيف تعمل المنظومة» ينكشف عند ظهور 30% منه | `.flow`، عند دخوله مجال الرؤية (مرة واحدة) | `IntersectionObserver` ثانٍ (سطر 1076) يضيف الصنف `in`؛ ثم CSS | عتبة `.3`؛ الأبناء: `up .7s var(--ease) both`؛ الثاني `nudge .5s` تأخير .3s؛ الثالث `midin .7s` تأخير .45s؛ الرابع `nudge .5s` تأخير .8s؛ الخامس `up` بتأخير .95s (أسطر 154 و155) | `opacity`، `transform`، `filter` | `.js .flow:not(.in)>*{opacity:0}` (سطر 153)، الصنف `in`، خمسة أبناء بالترتيب: عمود، سهم، عمود وسط، سهم، عمود |
| M60 | بنود الأعمدة تظهر بالتتابع | `.flow.in li` | CSS `fade` | .5s، `ease`، `both`؛ العمود الأول: البنود 2 إلى 4 بتأخير .12، .2، .28s؛ العمود الثالث .7s؛ الخامس 1.15s (أسطر 156 إلى 158) | `opacity` | بنية `ul > li` داخل كل عمود |
| M61 | بطاقة الميزة تتفاعل عند المرور: الأيقونة ترتفع، السطر ينزاح، سهم صغير يظهر | `.caps a:hover` | CSS transition | `transform .4s var(--ease)` على `svg` (سطر 159)؛ `padding .4s var(--ease)` (سطر 379)؛ `opacity .2s` على `b::after` (سطر 318) | `transform: translateY(-3px) scale(1.12)`، `padding-inline-start` إلى 10px، `opacity` 0 إلى 1 | بنية `<a>` من سطر 1072: `svg` ثم `b` ثم `span`؛ المحتوى `" ←"` في `b::after` |

### ك. عناصر عامة

| ID | ماذا يحدث | أين / المشغِّل | الآلية | المدة، التأخير، التسهيل | الخصائص المتحركة | التبعيات |
|---|---|---|---|---|---|---|
| M62 | الأزرار تتلوّن عند المرور وتنضغط عند النقر | `.btn` | CSS transition | `background .2s`، `border-color .2s`، `transform .2s`، كلها `var(--ease)` (سطر 79) | `background`، `border-color`، `transform: translateY(1px)` عند `:active`، و`translateY(-1px)` عند `.btn.pri:hover` (سطر 347) | أسطر 80 إلى 84 و346 و347 |
| M63 | ظل البطاقة يتعمق عند المرور | `.sec:hover` (و`.figs` تحمل الانتقال بلا حالة hover) | CSS transition | `box-shadow .5s var(--ease)` (سطر 336) | `box-shadow` من `var(--shadow)` إلى `0 24px 44px -26px rgba(11,74,68,.6)` | الرمز `--shadow` نفسه طرف في الانتقال |
| M64 | نقطة «بيانات تجريبية» تنبض بلا توقف | `.demo::before` | CSS `@keyframes beat` | 1.8s، `ease-in-out`، `infinite` (سطرا 341 و342) | `transform: scale(1.7)` و`opacity:.45` عند 50% | `.demo`، `--gold`. ملاحظة: تبقى تعمل مع تقليل الحركة لأن كتلة تقليل الحركة لا تشمل `::before` (سلوك قائم لا يُغيَّر) |
| M65 | رسالة التأكيد تصعد من أسفل الشاشة ثم تختفي | `#toast`، عند إصدار أمر عمل | CSS transition + `setTimeout` | النافذ (سطر 381): `transform .6s var(--spring)`؛ تبقى 3200ms ثم يُزال الصنف `on` | `transform` من `translateY(140%)` إلى `none` | `toast()` (سطر 814)، المتغير `tt`، الصنف `on`، `inset-block-end:24px`. سطر 324 (`.45s var(--ease)`) مغلوب |
| M66 | تبديل السمة بدائرة تتسع من مركز الزر | `#themeBtn`، عند النقر | View Transitions: `document.startViewTransition` ثم WAAPI على `::view-transition-new(root)` | 750ms، `EASE` | `clip-path` من `circle(0px at x y)` إلى `circle(Rpx at x y)` حيث `R` أبعد زاوية | أسطر 1085 إلى 1092؛ `setTheme()` (سطر 1079)؛ القاعدتان في السطرين 46 و47 (`animation:none;mix-blend-mode:normal` و`z-index:2`)؛ `data-theme` على `<html>`؛ `[data-theme=dark]`؛ بنية الزر `svg > path` واحد ثم `span`؛ `SUN` و`MOON`. بلا دعم للمتصفح أو مع تقليل الحركة: تبديل فوري |
| M67 | السمة تُضبط قبل أول رسم (لا وميض) | `<head>`، عند التحميل | سكربت inline (سطر 10) | فوري | السمة `data-theme` | مفتاح التخزين `istibaq-theme`، `prefers-color-scheme` |
| M68 | تقليل الحركة | كل الصفحة، عند `prefers-reduced-motion:reduce` | CSS (سطر 466) + الثابت `RM` في JS (سطر 759، يُقرأ مرة واحدة عند التحميل) | CSS: `*,*::after{animation:none!important;transition:none!important}`، و`stroke-dashoffset:0!important` على `.brand path,.map .road,.curve path`، و`opacity:1` على `.js .flow:not(.in)>*,.js .pre`. JS: `anim()` لا تفعل شيئاً، `tween()` تكتب القيمة النهائية، `enter()` تخرج فوراً، `route()` بلا خفوت، تبديل السمة فوري | كل ما سبق | الكتلة كاملة بنصها، `RM` في خمسة مواضع (أسطر 761، 764، 790، 806، 1087) |
| M69 | الطباعة تُظهر كل المحتوى المخفي بانتظار الكشف | `@media print` (سطر 467) | CSS | فوري | `opacity:1` على `.js .flow:not(.in)>*,.js .pre` | زر «تصدير التقرير» بـ `onclick="print()"` |

### ترتيب التنفيذ عند التحميل (لا يُغيَّر)

1. سكربت `<head>` يضبط `data-theme` (M67).
2. تحميل `leaflet.js` ثم `data/model_output.js` ثم `data/segments.js` ثم السكربت الرئيسي.
3. `document.documentElement.classList.add('js')` (سطر 760).
4. بناء `#rBody` و`#caps`، ثم كتابة `--i` على `.shift div` (سطر 1074).
5. السطر 1075 بهذا الترتيب: `overview(); map(); alerts(); causes(); contractors(); recs(); modelView(); roadsExtras(); materialsView(); fourTypes(); nav();`
6. `nav()` تبني القائمة ثم `badge()` ثم `route(false)`، ومنها `pill()` و`enter()`.
7. مراقب `.flow` (سطر 1076)، ثم `document.fonts.ready.then(pill)` (سطر 1077)، ثم `setTheme(...)` (سطر 1084).

---

## 2. ممنوع اللمس

كل ما في هذا القسم يبقى حرفياً. السكربت `motion_signature.py` يفحصه كله ضمن القسم `strict`.

### (أ) أسماء الأصناف

أصناف حالة تُضاف وتُزال من JS:
`js`، `pre`، `play`، `in`، `on`، `off`، `bump`، `geo`، `sel`، `pulse`، `dk`، `up` (على `.delta`)، `crit` / `high` / `med` / `low` (على `.pin`)، `s-crit` / `s-high` / `s-med` / `s-low`، `real` / `wait` / `fake`.

أصناف بنيوية ترتكز عليها محدِّدات الحركة أو JS:
`app`، `rail`، `brand`، `nav`، `pill`، `n`، `main`، `top`، `demo`، `btn`، `pri`، `view`، `sec`، `cols`، `figs`، `fig`، `hist`، `delta`، `arcade`، `bay`، `arch`، `rows`، `fbars`، `fb`، `pbar`، `filters`، `chip`، `tag`، `map`، `road`، `road2`، `d`، `b`، `ring`، `num`، `note`، `pin`، `dp`، `kv`، `r`، `x`، `xg`، `xact`، `save`، `fund`، `roi`، `pitch`، `shift`، `flow`، `col`، `mid`، `arr`، `caps`، `curve`، `grid`، `clegend`، `srcline`، `s`، `stackbar`، `toast`، `ic`، `sev`، `empty`، `more`، `head-row`، `id`، `ok`، `t`، `m`، `v`.

أصناف Leaflet لا تُضاف عليها حركة ولا تُعاد تسميتها: كل ما يبدأ بـ `leaflet-`.

### (ب) المعرّفات

`nav`، `badge` (يُنشأ من JS)، `title`، `themeBtn`، `toast`،
`v-overview`، `v-map`، `v-alerts`، `v-causes`، `v-contractors`، `v-materials`، `v-recs`، `v-model`، `v-about` (تُركَّب في JS من `'v-'+v` و`'#v-'+v`)،
`figs`، `arc1`، `arc2`، `topAlerts`، `topDist`، `topDistH`، `topDistS`، `pciSec`، `pciSub`، `pciBars`،
`mapChips`، `map`، `mapNote`، `dp`،
`q`، `fType`، `fSev` (تُركَّب من `'#'+i`)، `wkTag`، `wkX` (يُنشأ من JS)، `aCnt`، `aBody`،
`cChips`، `cTitle`، `cBars`، `cPat`،
`kHead`، `kBody`، `survSec`، `survType`، `survK`،
`matSurv`، `matMix`، `matBase`، `matK`، `matS`،
`bud`، `budOut`، `sN`، `sF`، `sS`، `optNote`، `rBody`،
`mFigs`، `mSub`، `mCmp`، `mLift`، `mImp`، `mCm`، `mSup`، `mFour`، `mSrc`،
`caps`.

المعرّفات الواردة داخل محدِّدات حركية في CSS: `#rBody` (سطر 142)، `#topDist`، `#mLift`، `#mImp`، `#pciBars`، `#matMix`، `#matBase` (سطر 395).

### (ج) السمات

- سمات البيانات: `data-theme` (على `<html>`)، `data-v`، `data-to`، `data-suf`، `data-w`، `data-d`، `data-id`، `data-n`، `data-k`، `data-go`.
- سمات الحالة المستخدمة في المحدِّدات: `aria-current`، `aria-pressed`، `aria-expanded`، `aria-sort`، `hidden`، `disabled`.
- `pathLength="1"`: مرتان في HTML (مسارا الشعار، سطر 474) ومرتان في قوالب JS (سطرا 865 و1032). بدونها ينكسر الرسم التدريجي.
- `dir="rtl"` و`lang="ar"` على `<html>`: اتجاهات `translateX` و`transform-origin:100% 50%` و`inset-inline-start` مبنية عليها.
- `onclick="print()"` على زر التصدير.

### (د) خصائص CSS المخصصة التي تُكتب من JS أو تدخل في حركة

| الخاصية | من يكتبها | أين تُستهلك |
|---|---|---|
| `--ease` | `:root` (سطر 29) | 55 موضعاً في `transition` و`animation` |
| `--spring` | `:root` (سطر 29) | 14 موضعاً |
| `--i` | `nav()` سطر 771، `arcade()` سطر 835، `map()` سطر 868، السطر 1074 | `animation-delay` في `.nav a`، `.play .bay`، `.play .arch i`، `.play .arch b`، `.arch i::after`، `.play .map g.d`، `.play .shift div / s / svg / b` |
| `--w` | قوالب الأشرطة (أسطر 842، 843، 927، 947، 959، 991، 993، 1041، 1051، 1055) و`setProperty` في سطر 948 | `width` في `.pbar i::after` و`.fb i::after` |
| `--h` | `arcade()` سطر 835 | `height` في `.arch i` |
| `--c` | القوالب نفسها مع `--w` و`--h` | `background` في `.arch i`، `.pbar i::after`، `.fb i::after` (مع بديل `var(--teal)`) |
| `--hc` | `figs()` سطر 827 | `background` في `.hist i` و`.hist i:last-child` (سطرا 343 و344) |
| `--s` | `leaf()` سطر 915 | `width` و`height` في `.pin` |
| `--mx`، `--my` | مستمع `pointermove` سطر 1093 | مركز `radial-gradient` في `.pitch` (سطر 369) |

لا تُعاد تسمية أيٍّ منها، ولا تُحذف صيغة `var(--…)` من القواعد المستهلِكة.

### (هـ) أسماء `@keyframes`

`up` (سطرا 90 و385)، `fade`، `growY`، `growX`، `draw`، `pop` (سطرا 95 و387)، `ring`، `wipe`، `strike`، `nudge`، `land`، `midin`، `navin`، `bump`، `beat`، `sheen`، `flow`، `rise`.

الكتل العشرون تبقى بنصها وبترتيبها. التعريفان المكرران لـ `up` و`pop` يبقيان كما هما، فحذف «الميت» منهما أو نقله يغيّر التوقيع وقد يغيّر الفائز.

### (و) دوال وثوابت JS

دوال الحركة (نصها الكامل ضمن التوقيع الصارم):
`anim`، `tween` (ودالتها الداخلية `step`)، `openAnim`، `nav`، `badge`، `pill`، `play`، `enter`، `route`، `toast`، `setTheme`، `causes`، `recs`، `figs`، `arcade`، `chips`، `map`، `leaf`، `leafFit`، `curves`.

ثوابت ومتغيرات:
`RM`، `EASE`، `VIEWS` (الترتيب يحدد `--i` ومواضع الحبة)، `io`، `rt`، `tt`، `figSaved`، `dpLast`، `LFit`، `SUN`، `MOON`، `IC`، `ic`، `$`، `N`، والخصائص الملحقة بالعناصر `_v`، `_t`، `_pt`.

مستمعات لا تُمس: `hashchange` ثم `route`، `resize` ثم `pill`، `pointerdown` على المستند (سطر 793)، `pointermove` على `.pitch` (سطر 1093)، `click` على `#themeBtn` (أسطر 1085 إلى 1092)، `input` على `#bud`، `click` على المستند للأقواس (سطر 845)، المراقبان `IntersectionObserver` (سطرا 783 و1076)، `document.fonts.ready.then(pill)` (سطر 1077).

أرقام التوقيت في JS: 60، 80 (ضمن `dur+80`)، 90، 120، 180 (ثلاث مرات)، 450 (افتراضي `anim`)، 480، 500 (أربع مرات)، 750، 1000 (افتراضي `tween`)، 1500، 3200، 3400، والعتبتان `.06` و`.3`.

المكتبات: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css` و`https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`. لا تُضاف مكتبة حركة ولا يُغيَّر الإصدار.

### (ز) تصريحات CSS التي تبقى بنصها

القائمة الكاملة (143 قاعدة) محفوظة في `motion-baseline.json` تحت `strict/css/motion_rules`. خلاصتها بحسب السطر:

- 46 و47: قاعدتا `::view-transition-old(root)` و`::view-transition-new(root)` كاملتان.
- 29: `--ease` و`--spring`.
- 67، 79، 81: انتقالات `.nav a` و`.btn`، و`.btn:active{transform:translateY(1px)}`.
- 90 إلى 103: كتل `@keyframes` الأربع عشرة الأولى.
- 106 إلى 162: كل القسم (الشعار، القائمة، `.pill`، `.js .pre`، `.play` وما تحتها، الخريطة، `#rBody td`، `.fund`، `.pitch.play`، `.shift`، `.flow`، حركات المرور على `.caps a svg` و`.nav a svg`).
- 189، 190، 193: انتقالات `.arch` و`.arch i` والتحويل عند المرور.
- 222، 239، 255، 271: `tbody tr.r`، `.chip`، `.map g.d circle.b`، `.fb i::after`.
- 302: خلفية `.shift s` (أساس حركة `strike`).
- 318 و319: `opacity` و`transition` على `.caps a b::after`.
- 324 و325: `.toast` و`.toast.on`.
- 336، 341، 342، 347، 349 إلى 361، 363 إلى 366، 372 إلى 375، 379، 381، 382: كل ما في قسم `theme` من `transition`، `animation`، `transform`، `@keyframes beat / sheen / flow`.
- 356: خلفية `.arch i::after` (أساس حركة `sheen`).
- 369: مرجعا `var(--mx,18%)` و`var(--my,12%)` داخل خلفية `.pitch` (بقية الخلفية لونية ويجوز تعديلها).
- 385 إلى 402: قسم `bolder motion` كاملاً.
- 406، 407، 409، 411: `.pin` (الانتقال والتحويل)، `.pin span{transform:translateX(-50%)}`، `.pin.pulse::after`.
- 430: `.play .curve path`.
- 448: `.flow .arr{transform:rotate(-90deg)}` تحت 1080px.
- 466: كتلة `prefers-reduced-motion` كاملة.
- 467: `opacity:1` في كتلة الطباعة.

خصائص لا يُضاف منها شيء جديد في أي قاعدة: `transition*`، `animation*`، `transform*`، `opacity`، `will-change`، `clip-path`، `stroke-dasharray`، `stroke-dashoffset`، `view-transition-name`، `scroll-behavior`، `translate`، `rotate`، `scale`. إضافة `transition` لوني عام على `body` أو `*` لتنعيم تبديل السمة ممنوعة لأنها تتعارض مع M66.

قيم غير حركية بذاتها لكنها أطراف في حركات، وتبقى كما هي:
`padding:11px 0` على `.rows li` و`padding-inline-start:8px` عند المرور؛ `padding:16px 0` على `.caps a` و`padding-inline-start:10px` عند المرور؛ `stroke-width` 2 / 2.5 / 4 على `circle.b`؛ `height:var(--h)`؛ `width:var(--w)`.

ترتيب القواعد: لا يُعاد ترتيب الأقسام الثلاثة (الأساس، `theme`، `bolder motion`) ولا تُدمج القواعد المكررة، فالفائز في كل حالة يتحدد بالترتيب.

---

## 3. مسموح تغييره بأمان

تغيير **قيمة** أي رمز لوني أدناه لا يمس الحركة. تغيير **اسمه** ممنوع (12 اسماً منها مكتوبة نصاً داخل JS: `--brand`، `--crit`، `--crit-f`، `--gold`، `--high`، `--high-f`، `--ink-2`، `--low`، `--low-f`، `--med`، `--med-f`، `--teal`).

عمود «الاستخدام» يعدّ مراجع `var(--الاسم)` في الملف كله (CSS و HTML و JS).

### `:root` (السمة الفاتحة)

| الرمز | القيمة الحالية | الاستخدام | ملاحظة |
|---|---|---|---|
| `--rail` | `#0b4a44` | 14 | آمن |
| `--rail-2` | `#14645a` | 5 | آمن |
| `--rail-ink` | `#ecf7f3` | 4 | طرف في انتقال لون `.nav a` (M08)، القيمة قابلة للتغيير |
| `--rail-mute` | `#a9d2c8` | 2 | آمن |
| `--brand` | `#0b4a44` | 6 | آمن. يُستخدم لوناً لحلقة المنطقة المختارة من JS |
| `--ground` | `#e2eee6` | 5 | آمن |
| `--surface` | `#f5f9f3` | 12 | طرف في انتقال خلفية `.btn` و`.chip` |
| `--sunk` | `#d8e7dd` | 7 | طرف في انتقالات hover |
| `--ink` | `#10241f` | 13 | آمن |
| `--ink-2` | `#40534b` | 38 | آمن |
| `--line` | `#c5d8cc` | 21 | آمن |
| `--teal` | `#0a7268` | 11 | آمن. بديل `--c` و`--hc` |
| `--date` | `#8a4a0a` | 7 | آمن |
| `--date-soft` | `#fbe5c0` | 2 | آمن |
| `--gold` | `#f0a73a` | 8 | لون النقطة النابضة (M64) وحلقة القوس المختار |
| `--crit` | `#a8231c` | 2 | آمن |
| `--crit-soft` | `#f8dad5` | 1 | آمن |
| `--crit-f` | `#d2413a` | 12 | لون حلقة النبض على الدبوس (M40). له نسخة صلبة في JS (`HEX.crit`) |
| `--high` | `#a04606` | 3 | آمن |
| `--high-soft` | `#fbdfc4` | 1 | آمن |
| `--high-f` | `#f08c2c` | 10 | له نسخة صلبة في JS |
| `--med` | `#715a00` | 3 | آمن |
| `--med-soft` | `#f3e7ae` | 2 | آمن |
| `--med-f` | `#e8c13c` | 7 | له نسخة صلبة في JS |
| `--low` | `#196440` | 10 | آمن |
| `--low-soft` | `#cfecdc` | 3 | طرف في انتقال `.fund` (M49) |
| `--low-f` | `#1e9a66` | 13 | له نسخة صلبة في JS |
| `--hover` | `#ebf3ed` | 1 | طرف في انتقال خلفية الصف (M33) |
| `--xbg` | `#e8f1ea` | 1 | آمن |
| `--off` | `#586b63` | 2 | طرف في انتقال لون `#rBody td` (M49) |
| `--topbg` | `rgba(245,249,243,.9)` | 2 | آمن |
| `--map` | `#d9e9df` | 3 | آمن |
| `--mapdot` | `#b9d3c5` | 1 | آمن |
| `--road` | `#f5f9f3` | 2 | آمن |
| `--road2` | `#7fae9c` | 1 | لون الخط الجاري (M38) |
| `--glow1` | `#f7e3ba` | 1 | آمن |
| `--glow2` | `#c2e6d4` | 1 | آمن |
| `--rail-bg` | `linear-gradient(168deg,#0f6257 0%,#0b4a44 46%,#083b3d 100%)` | 1 | آمن |
| `--shadow` | `0 16px 34px -26px rgba(11,74,68,.55)` | 1 | **خطر متوسط**: هو نفسه طرف انتقال `box-shadow .5s` على `.sec` و`.figs` (M63). يجوز تغيير اللون؛ تغيير عدد الظلال أو إضافة `inset` يجعل الانتقال قفزة |
| `--r` | `14px` | 4 | آمن (`.sec`، `.figs`، `.pitch`، `.synth`). لا حركة تعتمد عليه |
| `--ease` | `cubic-bezier(.16,1,.3,1)` | 55 | **ممنوع** |
| `--spring` | `cubic-bezier(.34,1.56,.64,1)` | 14 | **ممنوع** |

### `[data-theme=dark]`

| الرمز | القيمة الحالية | الاستخدام |
|---|---|---|
| `--rail` | `#167266` | 14 |
| `--rail-2` | `#1c8275` | 5 |
| `--brand` | `#62d8c6` | 6 |
| `--ground` | `#081a18` | 5 |
| `--surface` | `#102825` | 12 |
| `--sunk` | `#1a3733` | 7 |
| `--ink` | `#e7f3ee` | 13 |
| `--ink-2` | `#a8c0b8` | 38 |
| `--line` | `#244640` | 21 |
| `--teal` | `#58d4c2` | 11 |
| `--date` | `#f4b961` | 7 |
| `--date-soft` | `#3b2d13` | 2 |
| `--crit` | `#ff968d` | 2 |
| `--crit-soft` | `#4a211e` | 1 |
| `--high` | `#ffb070` | 3 |
| `--high-soft` | `#472b10` | 1 |
| `--med` | `#ecd272` | 3 |
| `--med-soft` | `#403610` | 2 |
| `--low` | `#74dfaa` | 10 |
| `--low-soft` | `#153d2c` | 3 |
| `--hover` | `#153330` | 1 |
| `--xbg` | `#0c2220` | 1 |
| `--off` | `#7b958d` | 2 |
| `--topbg` | `rgba(12,32,29,.88)` | 2 |
| `--map` | `#0c2320` | 3 |
| `--mapdot` | `#1d3b36` | 1 |
| `--road` | `#2d564f` | 2 |
| `--road2` | `#4f8a7c` | 1 |
| `--glow1` | `rgba(240,167,58,.11)` | 1 |
| `--glow2` | `rgba(46,170,140,.17)` | 1 |
| `--rail-bg` | `linear-gradient(168deg,#0c3a35 0%,#07231f 50%,#051a1b 100%)` | 1 |
| `--shadow` | `0 18px 38px -24px rgba(0,0,0,.85)` | 1 |

غير معرّفة في السمة الداكنة وتُورَّث من `:root`: `--rail-ink`، `--rail-mute`، `--gold`، `--crit-f`، `--high-f`، `--med-f`، `--low-f`، `--r`، `--ease`، `--spring`. كتلة السمة الداكنة تحمل أيضاً `color-scheme:dark`.

آمن كذلك: الألوان الصلبة داخل CSS (137 موضعاً بما فيها تعريفات الرموز، مفصّلة في `advisory/css/hardcoded_color_counts_css`) ما دام التعديل يقتصر على القيمة اللونية داخل التصريح ولا يمس `transition` أو `transform` أو `animation` في القاعدة نفسها؛ قيم `border-radius` خارج الحالات المذكورة أدناه؛ نصوص الواجهة.

### حالات خطرة يجب الانتباه لها

**1. رموز لونية أو قياسية هي نفسها أطراف في انتقال**

- `--shadow` مع `.sec:hover` (ظل صلب `rgba(11,74,68,.6)` لا يتبدل في السمة الداكنة).
- `--rail-ink` إلى `#0b4a44` الصلب في `.nav a[aria-current=page]` (سطر 69): نص الرابط الحالي فوق حبة بيضاء صلبة `#fff` (سطر 111). تغيير لون الحبة يستلزم تغيير هذا اللون معها، وكلاهما خارج نظام الرموز.
- `--off`، `--ink`، `--low-soft`، `--low`، `--sunk`، `--ink-2` في انتقال صفوف الميزانية (M49).
- `--surface`، `--sunk`، `--hover`، `--rail` في انتقالات `.btn`، `.chip`، `tbody tr.r`.
- تدرّجات `.btn.pri` (سطرا 346 و347) و`.toast` (سطر 381): `background` عليها `transition`، والتدرّجات لا تتداخل بسلاسة، فالتبديل الحالي قفزة لونية. استبدال التدرّج بلون مسطح يحوّلها إلى تلاشٍ ناعم، وهذا تغيير في الحركة.

**2. حركات يعتمد شكلها على نصف قطر أو ظل أو مقاس محدد**

- `.pill`: `border-radius:8px` يطابق `.nav a` (8px)، وكلاهما صلب وليس `--r`. مقاس الحبة وموضعها يُقرآن من `offsetWidth/Height/Left/Top` للرابط، فتغيير `padding` أو `gap` أو حجم الخط في `.nav a` يغيّر مسافة الانزلاق.
- `.arch`: `height:132px`، `border-radius:999px 999px 0 0`، `overflow:hidden`، `border-bottom-width:3px`. الامتلاء `--h` نسبة مئوية أقصاها 88 (سطر 834). الرقم في القوس: `top:12px`، `line-height:24px`.
- `.hist`: `height:34px` مربوط بالرقم 34 داخل JS (سطر 827).
- `.pbar i` (6px، نصف قطر 9px) و`.fb i` (22px، نصف قطر 5px): `overflow:hidden` على المسار ونصف قطر مماثل على `::after`.
- `.pin`: `border-radius:50%`، والحلقة `inset:-3px` بتكبير 1.6. المقاس من JS (`--s` = 34 أو محسوب) ومكرر في `iconSize` و`iconAnchor`.
- `.toast`: `translateY(140%)` مع `inset-block-end:24px` وظل `0 12px 30px -12px`. تكبير الظل أو الإزاحة السفلية قد يُبقي جزءاً ظاهراً في وضع الإخفاء.
- `.shift s`: خط الشطب عند `58%` من ارتفاع السطر، مضبوط على Readex Pro.
- `.pitch h2`: `inset(0 0 -12% 0)` و`line-height:1.4`.
- `.map.geo{height:540px}` وحشو `fitBounds` 46.
- `curves()`: أبعاد اللوحة `520×250` وهوامشها داخل JS (سطر 1026)، وسماكة الخط 2.6 في CSS.
- `.demo::before`: 7px و`border-radius:50%` بتكبير 1.7.

**3. ألوان صلبة داخل JS** (لا تتبع الرموز ولا السمة الداكنة)

| السطر | الموضع | الألوان |
|---|---|---|
| 885 | `HEX` (تعبئة دوائر التنبيهات في Leaflet) | `#d2413a`، `#f08c2c`، `#e8c13c`، `#1e9a66` |
| 887 | `SEGC` (ألوان مقاطع الطرق على Canvas) | `#58b08a`، `#e8c13c`، `#f08c2c`، `#d2413a` |
| 910 | إطار دائرة التنبيه `color:'#fff'` | `#fff` |
| 1027 | لوحة ألوان `curves()` الافتراضية | `#1e9a66`، `#d2413a`، `#0c7d72`، `#e8a02c`، `#5b8def`، `#b36bd4` |
| 1038 | `bc` لأشرطة PCI | `#62b98a` (مع أربعة رموز) |
| 1050 | لوحة `curves('#matSurv', …)` | `#1e9a66`، `#e8a02c`، `#d2413a` |

هذه مسموح تغيير قيمها (السكربت يضعها في `advisory` ويقنّعها في المقارنة الصارمة)، لكن يجب تغييرها يدوياً لأنها لا تتأثر بتغيير الرموز. ألوان Canvas و`stroke` على SVG لا تقبل `var()` في موضعي 885 و887.

ألوان صلبة في HTML خارج `<style>`: `theme-color` (سطر 7، `#0b4a44`)، أيقونة الموقع (سطر 8، `%230b4a44` و`%23f0a73a`)، ألوان الشعار (سطر 474: `#fff`، `#e9b877`).

**4. JS يبني `style=` فيه ألوان**

| السطر | الدالة | ما يُكتب |
|---|---|---|
| 827 | `figs()` | `--hc:` أحد `var(--high-f)`، `var(--gold)`، `var(--low-f)`، `var(--teal)` |
| 835 | `arcade()` | `--c:` أحد `var(--crit-f)`، `var(--high-f)`، `var(--low-f)` |
| 840، 879 | `overview()`، `map()` | `color:${tcol[…]}` أي `var(--crit)`، `var(--high)`، `var(--med)`، `var(--low)` |
| 842، 843 | `overview()` | `--c:${col[…]}`، و`color:var(--ink-2)` |
| 868 | `map()` | `color:` إما `var(--brand)` أو `col[…]`، و`fill="${col[…]}"` |
| 876، 877 | `map()` | `color:var(--ink-2)` |
| 915 | `leaf()` | `--s:…px;opacity:…` (بلا لون، لكن الأصناف `crit/high/med/low` تحدد اللون) |
| 927، 970 | `alerts()`، بناء `#rBody` | `--c:${col[s]}`، `color:var(--ink-2)` |
| 947، 993 | `causes()`، `modelView()` | `--c:` إما `var(--teal)` أو `var(--gold)` |
| 959 | `contractors()` | `--c:${col[s]}` |
| 989، 995 | `modelView()` | `color:var(--low)` |
| 991 | `modelView()` | `--c:` أحد `var(--crit-f)`، `var(--high-f)`، `var(--low-f)` |
| 1033 | `curves()` | `background:${col[i%6]}` (لون صلب)، و`stroke="${col[i%6]}"` في سطر 1032 |
| 1034، 1051 | `curves()`، `materialsView()` | `color:var(--ink-2)` |
| 1041 | `roadsExtras()` | `--c:${bc[i]}` |
| 1051، 1055 | `materialsView()` | `--c:` رموز الخطورة |
| 1054 | `materialsView()` | `background:${C[i]}` (رموز) |

الخريطتان `col` و`tcol` (سطر 710) هما مصدر أسماء الرموز في أغلب هذه القوالب.

**5. مخاطر بنيوية عند تغيير الشعار أو الأيقونات أو الترويسة أو الخط**

- الشعار: القاعدة `.brand path` تطبّق `stroke-dasharray:1;stroke-dashoffset:1` على كل `<path>` داخل `.brand`. شعار جديد بمسارات معبأة (`fill`) أو بلا `pathLength="1"` أو بعدد مسارات مختلف يكسر M01 و M02. `.brand circle` و`.brand div` كذلك محدِّدات عنصرية عامة.
- زر السمة: `setTheme()` تبحث عن أول `path` وأول `span` داخل `#themeBtn` وتكتب `d` واحدة (`SUN` أو `MOON`). أيقونة متعددة العناصر أو `span` إضافي قبل النص يكسرها. مركز الدائرة في M66 هو مركز الزر.
- الأيقونات: محدِّدات الحركة تستهدف `svg` كعنصر (`.nav a svg`، `.caps a svg`، `.shift svg`). استبدالها بخط أيقونات أو `<img>` أو `<i>` يلغي M09 و M54 و M61. `ic()` تُنتج `<svg class="ic" viewBox="0 0 24 24">`، و`IC` يُدرج محتوى داخلياً فقط.
- الترويسة `.top`: `#title` هدف M12، و`.demo` تحمل M64، و`position:sticky` يتعطل إذا أُضيف `overflow` على `.main` أو `.app`.
- إضافة `view-transition-name` لأي عنصر، أو `transform` / `filter` / `backdrop-filter` / `will-change` / `contain` على `.app` أو `.main` أو `.view`، تغيّر لقطة M66 أو سياق التراص أثناء M15.
- الخط: Readex Pro مكتوب صلباً في خمسة مواضع (أسطر 50، 258، 406، 412، 427) ورابط Google Fonts في سطر 14، بلا رمز. تغيير الخط يغيّر عرض روابط القائمة (الحبة تُقاس عند `fonts.ready` فقط)، وموضع خط الشطب، وثبات عرض الأرقام أثناء العدّ إذا لم يدعم الخط الجديد `tabular-nums`.
- بنية `.flow` (خمسة أبناء) و`.shift div` (`s` ثم `svg` ثم `b`) وأبناء كل `.view` المباشرون: محدِّدات `:nth-child` وترتيب الكشف مبنيان عليها.

---

## 4. طريقة التحقق بعد التعديل

المتطلبات: Python من البيئة المحلية للمشروع، بلا أي مكتبات إضافية.

PowerShell، من جذر المشروع:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe brand\motion_signature.py --check brand\motion-baseline.json index.html
$LASTEXITCODE
```

أو على مرحلتين (توليد توقيع جديد ثم مقارنته):

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe brand\motion_signature.py index.html brand\motion-after.json
.\.venv\Scripts\python.exe brand\motion_signature.py --compare brand\motion-baseline.json brand\motion-after.json
```

قراءة النتيجة:

| المخرج | المعنى |
|---|---|
| رمز الخروج 0 والسطر `RESULT: OK - motion signature identical` | لم يتغير شيء في القسم الصارم. الحركة كما هي |
| رمز الخروج 1 وأسطر تبدأ بـ `FAIL` | تغيّر شيء حركي. كل سطر يذكر المسار داخل التوقيع والقيمة القديمة (`-`) والجديدة (`+`) |
| أسطر تبدأ بـ `WARN` | تغيّرات في القسم الاستشاري: قيم الرموز، الألوان الصلبة، أطراف الانتقالات اللونية، بيانات الأيقونات، بنية الترويسة. متوقعة في إعادة التلوين، وتُراجَع بالعين |
| رمز الخروج 2 | خطأ في الاستخدام أو في قراءة ملف |

ما يغطيه القسم الصارم `strict`:

- `css`: كل كتل `@keyframes` بالترتيب، كل تصريح حركي مفهرس بالمحدِّد وسياق `@media`، كتلة تقليل الحركة كاملة، قواعد `::view-transition*`، تعريفات `--ease` و`--spring`، مواضع استهلاك الخصائص التي يكتبها JS، أطراف الانتقالات القياسية، الخلفيات الأساسية لحركتي `strike` و`sheen`، والأعداد.
- `js`: النص الكامل لـ 21 دالة حركية (بعد تقنيع الألوان الصلبة)، كل مواضع `.animate(` و`anim(` و`tween(` و`setTimeout` و`requestAnimationFrame` و`IntersectionObserver` و`addEventListener` و`classList` و`setProperty` بنصها، أرقام التوقيت، أسطر المستوى الأعلى الحركية وترتيب الاستدعاء عند التحميل، سكربت `<head>`، ومجموعات الأصناف والمعرّفات والمحدِّدات وسمات البيانات والخصائص المخصصة وأسماء الرموز الواردة في JS.
- `html`: `dir` و`lang`، روابط المكتبات، هياكل `.brand` و`#themeBtn` و`.pitch` و`.flow` و`.app`، أبناء كل `.view` حتى عمق 2، وجود كل معرّف يرتكز عليه JS ونوع عنصره، عدد مرات كل صنف مرتكَز عليه، وعدد `pathLength`.

حدود الفحص الآلي (تُراجَع يدوياً):

- التوقيع نصّي ولا يشغّل الصفحة. تغيير مقاس أو حشو أو خط يبدّل مسافة حركة (مثل انزلاق الحبة) لا يظهر فيه إلا إذا كان التصريح ضمن القائمة أعلاه.
- ملف `leaflet.css` الخارجي غير مفحوص، والفحص يقتصر على ثبات رابطه وإصداره.
- إضافة عنصر داخل الترويسة تظهر تحذيراً لا فشلاً. إضافة ابن مباشر لأي `.view` أو تغيير هيكل الشعار تظهر فشلاً.
- بعد نجاح الفحص يُستحسن فتح الصفحة والتأكد بالعين من: رسم الشعار، انزلاق الحبة بين رابطين، الكشف عند التمرير في «نظرة عامة»، تبديل السمة، ورسالة التأكيد بعد إصدار أمر عمل، في السمتين.

للمقارنة البصرية المباشرة مع الأصل: `brand/index.before.html` نسخة غير معدّلة. تُفتح من جذر المشروع نفسه لأنها تحمّل `data/model_output.js` و`data/segments.js` بمسار نسبي، فتُنسخ مؤقتاً بجوار `index.html` عند الحاجة.
