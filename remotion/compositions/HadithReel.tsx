// remotion/compositions/HadithReel.tsx
// Adults composition — dark elegant, calligraphy style
// 1080×1920 vertical (Reels/Shorts/TikTok format)
// Duration: ~60 seconds at 30fps = 1800 frames

import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from 'remotion'

export interface HadithReelProps {
  hadithArabic:   string
  hadithText:     string   // translation in selected language
  narrator:       string
  collection:     string
  hadithNumber?:  string
  story:          string
  moral:          string
  seerahContext:  string
  attribution:    string   // e.g. "📖 Source: Ar-Raheeq Al-Makhtum"
  lang:           string
  audioUrl?:      string   // ElevenLabs MP3 URL
}

// ─── Animated text line ───────────────────────────────────────────────────────
function FadeInText({
  children,
  delay = 0,
  style = {},
}: {
  children: React.ReactNode
  delay?: number
  style?: React.CSSProperties
}) {
  const frame  = useCurrentFrame()
  const { fps } = useVideoConfig()

  const opacity = interpolate(
    frame,
    [delay, delay + fps * 0.8],
    [0, 1],
    { extrapolateRight: 'clamp' }
  )
  const translateY = interpolate(
    frame,
    [delay, delay + fps * 0.8],
    [30, 0],
    { extrapolateRight: 'clamp' }
  )

  return (
    <div style={{ opacity, transform: `translateY(${translateY}px)`, ...style }}>
      {children}
    </div>
  )
}

// ─── Particle dot decoration ─────────────────────────────────────────────────
function GoldDot({ x, y, delay }: { x: number; y: number; delay: number }) {
  const frame = useCurrentFrame()
  const opacity = interpolate(frame, [delay, delay + 30], [0, 0.6], { extrapolateRight: 'clamp' })
  return (
    <div style={{
      position: 'absolute', left: x, top: y,
      width: 4, height: 4, borderRadius: '50%',
      background: '#D4AF37', opacity,
    }} />
  )
}

// ─── Main composition ─────────────────────────────────────────────────────────
export const HadithReel: React.FC<HadithReelProps> = ({
  hadithArabic,
  hadithText,
  narrator,
  collection,
  hadithNumber,
  story,
  moral,
  seerahContext,
  attribution,
  lang,
  audioUrl,
}) => {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()

  // Scene timing (frames at 30fps)
  const SCENE = {
    intro:   { start: 0,           end: fps * 4 },    // 0-4s: logo + bismillah
    arabic:  { start: fps * 4,     end: fps * 14 },   // 4-14s: Arabic text
    trans:   { start: fps * 14,    end: fps * 24 },   // 14-24s: translation
    story:   { start: fps * 24,    end: fps * 42 },   // 24-42s: seerah story
    moral:   { start: fps * 42,    end: fps * 54 },   // 42-54s: moral
    outro:   { start: fps * 54,    end: durationInFrames }, // 54-60s: attribution
  }

  // Detect active scene
  const inIntro  = frame < SCENE.arabic.start
  const inArabic = frame >= SCENE.arabic.start && frame < SCENE.trans.start
  const inTrans  = frame >= SCENE.trans.start  && frame < SCENE.story.start
  const inStory  = frame >= SCENE.story.start  && frame < SCENE.moral.start
  const inMoral  = frame >= SCENE.moral.start  && frame < SCENE.outro.start
  const inOutro  = frame >= SCENE.outro.start

  // Background pulse
  const bgOpacity = interpolate(
    frame % (fps * 4),
    [0, fps * 2, fps * 4],
    [0.15, 0.25, 0.15],
    { extrapolateRight: 'clamp' }
  )

  return (
    <AbsoluteFill style={{
      background: 'linear-gradient(160deg, #0a0a0f 0%, #0d1117 50%, #0a0a1a 100%)',
      fontFamily: '"Amiri", "Noto Sans Arabic", serif',
      color: '#F5F0E8',
      overflow: 'hidden',
    }}>

      {/* Audio */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* Decorative gold geometric border */}
      <div style={{
        position: 'absolute', inset: 24,
        border: '1px solid rgba(212, 175, 55, 0.3)',
        borderRadius: 4,
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', inset: 32,
        border: '1px solid rgba(212, 175, 55, 0.1)',
        borderRadius: 4,
        pointerEvents: 'none',
      }} />

      {/* Corner ornaments */}
      {[
        { top: 24, left: 24 },
        { top: 24, right: 24 },
        { bottom: 24, left: 24 },
        { bottom: 24, right: 24 },
      ].map((pos, i) => (
        <div key={i} style={{
          position: 'absolute', ...pos,
          width: 20, height: 20,
          borderTop: i < 2 ? '2px solid #D4AF37' : 'none',
          borderBottom: i >= 2 ? '2px solid #D4AF37' : 'none',
          borderLeft: i % 2 === 0 ? '2px solid #D4AF37' : 'none',
          borderRight: i % 2 === 1 ? '2px solid #D4AF37' : 'none',
        }} />
      ))}

      {/* Ambient particles */}
      {[
        { x: 80,  y: 200,  delay: 10 },
        { x: 950, y: 350,  delay: 20 },
        { x: 120, y: 800,  delay: 15 },
        { x: 900, y: 1200, delay: 25 },
        { x: 200, y: 1600, delay: 5  },
        { x: 850, y: 1700, delay: 30 },
      ].map((p, i) => <GoldDot key={i} {...p} />)}

      {/* Content area */}
      <AbsoluteFill style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '80px 60px',
        gap: 32,
      }}>

        {/* ── INTRO SCENE ─────────────────────────────────────── */}
        {inIntro && (
          <div style={{ textAlign: 'center' }}>
            <FadeInText delay={0}>
              <div style={{
                fontSize: 48,
                color: '#D4AF37',
                letterSpacing: 8,
                fontWeight: 300,
                direction: 'rtl',
              }}>
                بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
              </div>
            </FadeInText>
            <FadeInText delay={fps * 1.5} style={{ marginTop: 24 }}>
              <div style={{
                fontSize: 18,
                color: 'rgba(245,240,232,0.5)',
                letterSpacing: 6,
                textTransform: 'uppercase',
              }}>
                Hadith Reels
              </div>
            </FadeInText>
          </div>
        )}

        {/* ── ARABIC SCENE ────────────────────────────────────── */}
        {inArabic && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.arabic.start}>
              <div style={{
                fontSize: 13,
                color: '#D4AF37',
                letterSpacing: 4,
                textTransform: 'uppercase',
                marginBottom: 40,
              }}>
                {collection}{hadithNumber ? ` · ${hadithNumber}` : ''}
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.arabic.start + fps * 0.5}>
              {/* Gold divider */}
              <div style={{
                height: 1,
                background: 'linear-gradient(90deg, transparent, #D4AF37, transparent)',
                marginBottom: 40,
              }} />

              <div style={{
                fontSize: 52,
                lineHeight: 1.8,
                direction: 'rtl',
                color: '#F5F0E8',
                textShadow: '0 0 40px rgba(212,175,55,0.2)',
                fontWeight: 400,
              }}>
                {hadithArabic}
              </div>

              <div style={{
                height: 1,
                background: 'linear-gradient(90deg, transparent, #D4AF37, transparent)',
                marginTop: 40,
              }} />
            </FadeInText>

            <FadeInText delay={SCENE.arabic.start + fps * 2} style={{ marginTop: 32 }}>
              <div style={{
                fontSize: 16,
                color: 'rgba(212,175,55,0.7)',
                letterSpacing: 2,
              }}>
                — {narrator} رضي الله عنه
              </div>
            </FadeInText>
          </div>
        )}

        {/* ── TRANSLATION SCENE ───────────────────────────────── */}
        {inTrans && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.trans.start}>
              <div style={{
                fontSize: 13,
                color: '#D4AF37',
                letterSpacing: 4,
                textTransform: 'uppercase',
                marginBottom: 32,
              }}>
                {lang === 'ar' ? 'الترجمة' :
                 lang === 'ru' ? 'Перевод' :
                 lang === 'uz' ? 'Tarjima' :
                 lang === 'tj' ? 'Тарҷума' : 'Translation'}
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.trans.start + fps * 0.5}>
              <div style={{
                fontSize: 36,
                lineHeight: 1.6,
                color: '#F5F0E8',
                fontStyle: 'italic',
                maxWidth: 900,
                margin: '0 auto',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
              }}>
                "{hadithText}"
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.trans.start + fps * 2} style={{ marginTop: 40 }}>
              <div style={{
                fontSize: 14,
                color: 'rgba(245,240,232,0.4)',
                letterSpacing: 3,
              }}>
                {collection}{hadithNumber ? ` #${hadithNumber}` : ''}
              </div>
            </FadeInText>
          </div>
        )}

        {/* ── STORY SCENE ─────────────────────────────────────── */}
        {inStory && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.story.start}>
              <div style={{
                fontSize: 13,
                color: '#D4AF37',
                letterSpacing: 4,
                textTransform: 'uppercase',
                marginBottom: 32,
              }}>
                {lang === 'ar' ? 'من السيرة النبوية' :
                 lang === 'ru' ? 'Из жизни Пророка ﷺ' :
                 lang === 'uz' ? 'Payg\'ambar ﷺ hayotidan' :
                 lang === 'tj' ? 'Аз зиндагии Паёмбар ﷺ' :
                 'From the life of the Prophet ﷺ'}
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.story.start + fps * 0.5}>
              <div style={{
                fontSize: 26,
                lineHeight: 1.8,
                color: 'rgba(245,240,232,0.9)',
                maxWidth: 900,
                margin: '0 auto',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
              }}>
                {story}
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.story.start + fps * 3} style={{ marginTop: 40 }}>
              <div style={{
                fontSize: 13,
                color: 'rgba(212,175,55,0.5)',
                letterSpacing: 2,
                fontStyle: 'italic',
              }}>
                {attribution}
              </div>
            </FadeInText>
          </div>
        )}

        {/* ── MORAL SCENE ─────────────────────────────────────── */}
        {inMoral && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.moral.start}>
              <div style={{
                width: 60, height: 60,
                borderRadius: '50%',
                background: 'rgba(212,175,55,0.1)',
                border: '1px solid rgba(212,175,55,0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 32px',
                fontSize: 28,
              }}>
                💡
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.moral.start + fps * 0.5}>
              <div style={{
                fontSize: 13,
                color: '#D4AF37',
                letterSpacing: 4,
                textTransform: 'uppercase',
                marginBottom: 32,
              }}>
                {lang === 'ar' ? 'الفائدة' :
                 lang === 'ru' ? 'Урок' :
                 lang === 'uz' ? 'Saboq' :
                 lang === 'tj' ? 'Дарс' : 'Moral'}
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.moral.start + fps * 1}>
              <div style={{
                fontSize: 32,
                lineHeight: 1.6,
                color: '#F5F0E8',
                fontWeight: 500,
                maxWidth: 860,
                margin: '0 auto',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
              }}>
                {moral}
              </div>
            </FadeInText>
          </div>
        )}

        {/* ── OUTRO SCENE ─────────────────────────────────────── */}
        {inOutro && (
          <div style={{ textAlign: 'center' }}>
            <FadeInText delay={SCENE.outro.start}>
              <div style={{
                fontSize: 36,
                color: '#D4AF37',
                direction: 'rtl',
                marginBottom: 24,
              }}>
                جزاكم الله خيرًا
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.outro.start + fps * 0.5}>
              <div style={{
                fontSize: 16,
                color: 'rgba(245,240,232,0.5)',
                letterSpacing: 3,
                marginBottom: 16,
              }}>
                🔍 VERIFY · hadithverifier.com
              </div>
            </FadeInText>

            <FadeInText delay={SCENE.outro.start + fps * 1}>
              <div style={{
                fontSize: 14,
                color: 'rgba(212,175,55,0.6)',
                letterSpacing: 2,
              }}>
                @HadithReels
              </div>
            </FadeInText>
          </div>
        )}

      </AbsoluteFill>

      {/* Scene progress indicator */}
      <div style={{
        position: 'absolute',
        bottom: 48,
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        gap: 6,
      }}>
        {Object.keys(SCENE).map((scene, i) => {
          const s = SCENE[scene as keyof typeof SCENE]
          const active = frame >= s.start && frame < s.end
          return (
            <div key={scene} style={{
              width: active ? 20 : 6,
              height: 3,
              borderRadius: 2,
              background: active ? '#D4AF37' : 'rgba(212,175,55,0.2)',
              transition: 'width 0.3s',
            }} />
          )
        })}
      </div>

    </AbsoluteFill>
  )
}
