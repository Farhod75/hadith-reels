// lib/ui-strings.ts
// P363: the public page's own words in the four languages the toggle offers.
// Before this, switching to RU / UZ / TJ changed the hadith text and nothing else -
// tabs, search, buttons, grades and the whole Watch tab stayed English (operator,
// 2026-11-04). Hadith text, tags, collections and narrators come from their own
// sources (the library row, lib/tags.ts, lib/refs.ts); this file is only the chrome.
//
// UZ is Cyrillic, like every Uzbek line the channel publishes (P169).

export type UiLang = 'en' | 'ru' | 'uz' | 'tj'

type Tile = { title: string; desc: string }

export interface UiStrings {
  htmlLang: string
  subtitle: string
  hadiths: string
  sahihStat: string
  verifyBanner: string
  tabLibrary: string
  tabWatch: string
  searchPlaceholder: string
  grade: string
  gradeLabel: Record<'all' | 'sahih' | 'hasan', string>
  count: (n: number) => string
  loading: string
  retry: string
  empty: string
  searchFailed: string
  loadFailed: string
  loadingMore: string
  loadMore: (shown: number, total: number) => string
  footer: string
  footerLink: string
  listen: string
  pause: string
  copy: string
  copied: string
  source: string
  verify: string
  watchTitle: string
  watchDesc: string
  tiles: [Tile, Tile, Tile, Tile]
  reelsOnlyPre: string
  reelsOnlyStrong: string
  reelsOnlyPost: string
}

// Russian needs three noun forms: 1 хадис, 2-4 хадиса, 5+ хадисов (11-14 -> хадисов).
function ruPlural(n: number, one: string, few: string, many: string) {
  const m10 = n % 10, m100 = n % 100
  if (m10 === 1 && m100 !== 11) return one
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few
  return many
}

export const UI: Record<UiLang, UiStrings> = {
  en: {
    htmlLang: 'en',
    subtitle: 'Authentic hadith · EN · UZ · RU · TJ',
    hadiths: 'Hadiths',
    sahihStat: 'Sahih',
    verifyBanner: 'Verify any hadith before sharing at',
    tabLibrary: '📚 Hadith library',
    tabWatch: '🎬 Watch reels',
    searchPlaceholder: 'Search hadiths, tags, narrators...',
    grade: 'Grade:',
    gradeLabel: { all: 'all', sahih: 'sahih', hasan: 'hasan' },
    count: n => `${n} ${n === 1 ? 'hadith' : 'hadiths'}`,
    loading: 'Loading authenticated hadiths...',
    retry: 'Retry',
    empty: 'No hadiths found. Try a different search or grade.',
    searchFailed: 'Search failed',
    loadFailed: 'Failed to load',
    loadingMore: 'Loading…',
    loadMore: (s, t) => `Load more (${s} of ${t})`,
    footer: 'All hadiths are sahih or hasan — authenticated from major collections.',
    footerLink: 'Verify at hadithverifier.com →',
    listen: '▶ Listen',
    pause: '⏸ Pause',
    copy: 'Copy',
    copied: 'Copied ✓',
    source: 'Source ↗',
    verify: '🔍 Verify',
    watchTitle: 'Watch our reels',
    watchDesc: 'Authentic hadith reels with verified Islamic sources — new reels added regularly. Follow us on your favourite platform.',
    tiles: [
      { title: 'Adults series', desc: 'One authentic hadith per reel, its narrator named, over bright scenes with no faces.' },
      { title: 'Kids series', desc: 'The same hadiths in simple words, told by our lamb friends.' },
      { title: '4 languages', desc: 'English, Russian, Uzbek and Tajik narration, with the Arabic matn.' },
      { title: 'Checked at the source', desc: 'Every matn is matched to a Tier 1 collection before it is narrated.' },
    ],
    reelsOnlyPre: 'All our reels use only ',
    reelsOnlyStrong: 'sahih and hasan',
    reelsOnlyPost: ' authenticated hadiths. Verify any hadith at ',
  },
  ru: {
    htmlLang: 'ru',
    subtitle: 'Достоверные хадисы · EN · UZ · RU · TJ',
    hadiths: 'Хадисов',
    sahihStat: 'Сахих',
    verifyBanner: 'Проверьте хадис, прежде чем делиться им, на',
    tabLibrary: '📚 Библиотека хадисов',
    tabWatch: '🎬 Смотреть рилсы',
    searchPlaceholder: 'Поиск по хадисам, тегам, передатчикам...',
    grade: 'Степень:',
    gradeLabel: { all: 'все', sahih: 'сахих', hasan: 'хасан' },
    count: n => `${n} ${ruPlural(n, 'хадис', 'хадиса', 'хадисов')}`,
    loading: 'Загружаем достоверные хадисы…',
    retry: 'Повторить',
    empty: 'Хадисы не найдены. Измените запрос или степень.',
    searchFailed: 'Поиск не удался',
    loadFailed: 'Не удалось загрузить',
    loadingMore: 'Загрузка…',
    loadMore: (s, t) => `Показать ещё (${s} из ${t})`,
    footer: 'Все хадисы — степени сахих или хасан, из основных сборников.',
    footerLink: 'Проверить на hadithverifier.com →',
    listen: '▶ Слушать',
    pause: '⏸ Пауза',
    copy: 'Копировать',
    copied: 'Скопировано ✓',
    source: 'Источник ↗',
    verify: '🔍 Проверить',
    watchTitle: 'Смотрите наши рилсы',
    watchDesc: 'Рилсы с достоверными хадисами из проверенных источников — новые выходят регулярно. Подписывайтесь на удобной вам платформе.',
    tiles: [
      { title: 'Серия для взрослых', desc: 'В каждом рилсе один достоверный хадис с именем передатчика — на ярких сценах без лиц.' },
      { title: 'Серия для детей', desc: 'Те же хадисы простыми словами — рассказывают наши барашки.' },
      { title: '4 языка', desc: 'Озвучка на английском, русском, узбекском и таджикском, с арабским текстом хадиса.' },
      { title: 'Сверено с источником', desc: 'Каждый текст хадиса сверяется с основным сборником (Tier 1) до озвучки.' },
    ],
    reelsOnlyPre: 'Во всех наших рилсах — только хадисы степени ',
    reelsOnlyStrong: 'сахих и хасан',
    reelsOnlyPost: '. Проверить любой хадис можно на ',
  },
  uz: {
    htmlLang: 'uz-Cyrl',
    subtitle: 'Саҳиҳ ҳадислар · EN · UZ · RU · TJ',
    hadiths: 'Ҳадислар',
    sahihStat: 'Саҳиҳ',
    verifyBanner: 'Ҳадисни улашишдан олдин текширинг:',
    tabLibrary: '📚 Ҳадислар кутубхонаси',
    tabWatch: '🎬 Рилсларни кўриш',
    searchPlaceholder: 'Ҳадис, тег ёки ровий бўйича қидириш...',
    grade: 'Даражаси:',
    gradeLabel: { all: 'барчаси', sahih: 'саҳиҳ', hasan: 'ҳасан' },
    count: n => `${n} та ҳадис`,
    loading: 'Саҳиҳ ҳадислар юкланмоқда…',
    retry: 'Қайта уриниш',
    empty: 'Ҳадис топилмади. Бошқа сўз ёки даражани танланг.',
    searchFailed: 'Қидирувда хато',
    loadFailed: 'Юклаб бўлмади',
    loadingMore: 'Юкланмоқда…',
    loadMore: (s, t) => `Яна кўрсатиш (${t} тадан ${s} та)`,
    footer: 'Барча ҳадислар саҳиҳ ёки ҳасан — асосий тўпламлардан олинган.',
    footerLink: 'hadithverifier.com да текшириш →',
    listen: '▶ Тинглаш',
    pause: '⏸ Тўхтатиш',
    copy: 'Нусха олиш',
    copied: 'Нусха олинди ✓',
    source: 'Манба ↗',
    verify: '🔍 Текшириш',
    watchTitle: 'Рилсларимизни кўринг',
    watchDesc: 'Ишончли манбалардан саҳиҳ ҳадислар билан рилслар — янгилари мунтазам чиқади. Ўзингизга қулай платформада обуна бўлинг.',
    tiles: [
      { title: 'Катталар учун', desc: 'Ҳар бир рилсда ровийси номи билан битта саҳиҳ ҳадис — юзсиз ёрқин саҳналарда.' },
      { title: 'Болалар учун', desc: 'Ўша ҳадислар оддий сўзлар билан — қўзичоқларимиз ҳикоя қилади.' },
      { title: '4 тил', desc: 'Инглиз, рус, ўзбек ва тожик тилларида овоз, ҳадиснинг арабча матни билан.' },
      { title: 'Манбага солиштирилган', desc: 'Ҳар бир матн овоз беришдан олдин асосий тўплам (Tier 1) билан солиштирилади.' },
    ],
    reelsOnlyPre: 'Барча рилсларимизда фақат ',
    reelsOnlyStrong: 'саҳиҳ ва ҳасан',
    reelsOnlyPost: ' ҳадислар. Ҳар қандай ҳадисни текширинг: ',
  },
  tj: {
    htmlLang: 'tg',
    subtitle: 'Ҳадисҳои саҳеҳ · EN · UZ · RU · TJ',
    hadiths: 'Ҳадисҳо',
    sahihStat: 'Саҳеҳ',
    verifyBanner: 'Ҳадисро пеш аз нашр тафтиш кунед:',
    tabLibrary: '📚 Китобхонаи ҳадисҳо',
    tabWatch: '🎬 Тамошои рилсҳо',
    searchPlaceholder: 'Ҷустуҷӯ аз рӯи ҳадис, тег ё ровӣ...',
    grade: 'Дараҷа:',
    gradeLabel: { all: 'ҳама', sahih: 'саҳеҳ', hasan: 'ҳасан' },
    count: n => `${n} ҳадис`,
    loading: 'Ҳадисҳои саҳеҳ бор мешаванд…',
    retry: 'Аз нав кӯшиш',
    empty: 'Ҳадис ёфт нашуд. Калимаи дигар ё дараҷаи дигарро интихоб кунед.',
    searchFailed: 'Ҷустуҷӯ иҷро нашуд',
    loadFailed: 'Бор кардан муяссар нашуд',
    loadingMore: 'Бор мешавад…',
    loadMore: (s, t) => `Боз нишон додан (${s} аз ${t})`,
    footer: 'Ҳамаи ҳадисҳо саҳеҳ ё ҳасананд — аз маҷмӯаҳои асосӣ.',
    footerLink: 'Тафтиш дар hadithverifier.com →',
    listen: '▶ Гӯш кардан',
    pause: '⏸ Таваққуф',
    copy: 'Нусхабардорӣ',
    copied: 'Нусха шуд ✓',
    source: 'Манбаъ ↗',
    verify: '🔍 Тафтиш',
    watchTitle: 'Рилсҳои моро тамошо кунед',
    watchDesc: 'Рилсҳо бо ҳадисҳои саҳеҳ аз манбаъҳои боэътимод — навҳо мунтазам илова мешаванд. Дар платформаи дӯстдоштаатон обуна шавед.',
    tiles: [
      { title: 'Барои калонсолон', desc: 'Дар ҳар рилс як ҳадиси саҳеҳ бо номи ровӣ — дар саҳнаҳои равшан бе чеҳра.' },
      { title: 'Барои кӯдакон', desc: 'Ҳамон ҳадисҳо бо суханони содда — барраҳои мо нақл мекунанд.' },
      { title: '4 забон', desc: 'Овоз бо забонҳои англисӣ, русӣ, ӯзбекӣ ва тоҷикӣ, бо матни арабии ҳадис.' },
      { title: 'Бо манбаъ санҷида шуд', desc: 'Ҳар матн пеш аз овоздиҳӣ бо маҷмӯаи асосӣ (Tier 1) муқоиса мешавад.' },
    ],
    reelsOnlyPre: 'Дар ҳамаи рилсҳои мо танҳо ҳадисҳои ',
    reelsOnlyStrong: 'саҳеҳ ва ҳасан',
    reelsOnlyPost: '. Ҳар ҳадисро тафтиш кунед: ',
  },
}
