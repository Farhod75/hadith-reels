// remotion/compositions/KidsReel.tsx
// Kids composition — bright, colorful, animated, age 6-14
// 1080×1920 vertical format

import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion'

export interface KidsReelProps {
  hadithArabic:  string
  hadithText:    string
  narrator:      string
  collection:    string
  story:         string
  moral:         string
  lang:          string
  audioUrl?:     string
}

// ─── Bouncing star ────────────────────────────────────────────────────────────
function BouncingStar({ x, y, delay, size = 24, emoji = '⭐' }: {
  x: number; y: number; delay: number; size?: number; emoji?: string
}) {
  const frame = useCurrentFrame()
  const bounce = Math.sin((frame + delay) * 0.05) * 8
  const opacity = interpolate(frame, [delay, delay + 20], [0, 1], { extrapolateRight: 'clamp' })
  return (
    <div style={{
      position: 'absolute', left: x, top: y + bounce,
      fontSize: size, opacity, userSelect: 'none',
    }}>
      {emoji}
    </div>
  )
}

// ─── Animated text ────────────────────────────────────────────────────────────
function PopIn({ children, delay = 0, style = {} }: {
  children: React.ReactNode; delay?: number; style?: React.CSSProperties
}) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const scale = spring({ frame: frame - delay, fps, config: { damping: 12, stiffness: 200 } })
  const opacity = interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateRight: 'clamp' })
  return (
    <div style={{ transform: `scale(${scale})`, opacity, ...style }}>
      {children}
    </div>
  )
}

// ─── Colored word (highlight key words) ──────────────────────────────────────
function ColorWord({ word, color }: { word: string; color: string }) {
  return <span style={{ color, fontWeight: 700 }}>{word} </span>
}

export const KidsReel: React.FC<KidsReelProps> = ({
  hadithArabic,
  hadithText,
  narrator,
  collection,
  story,
  moral,
  lang,
  audioUrl,
}) => {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()

  const SCENE = {
    intro:  { start: 0,        end: fps * 4  },
    arabic: { start: fps * 4,  end: fps * 14 },
    story:  { start: fps * 14, end: fps * 36 },
    moral:  { start: fps * 36, end: fps * 52 },
    outro:  { start: fps * 52, end: durationInFrames },
  }

  const inIntro  = frame < SCENE.arabic.start
  const inArabic = frame >= SCENE.arabic.start && frame < SCENE.story.start
  const inStory  = frame >= SCENE.story.start  && frame < SCENE.moral.start
  const inMoral  = frame >= SCENE.moral.start  && frame < SCENE.outro.start
  const inOutro  = frame >= SCENE.outro.start

  // Animated background gradient shift
  const hue = interpolate(frame, [0, durationInFrames], [200, 280])

  return (
    <AbsoluteFill style={{
      background: `linear-gradient(160deg, hsl(${hue}, 70%, 12%) 0%, hsl(${hue + 30}, 60%, 8%) 100%)`,
      fontFamily: '"Nunito", "Noto Sans Arabic", sans-serif',
      color: '#FFFFFF',
      overflow: 'hidden',
    }}>

      {/* Audio */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* Decorative stars */}
      <BouncingStar x={40}  y={80}   delay={5}  emoji="⭐" size={32} />
      <BouncingStar x={980} y={120}  delay={15} emoji="🌟" size={28} />
      <BouncingStar x={60}  y={1600} delay={10} emoji="✨" size={24} />
      <BouncingStar x={960} y={1650} delay={20} emoji="⭐" size={30} />
      <BouncingStar x={500} y={50}   delay={8}  emoji="🌙" size={36} />

      {/* Colorful dots */}
      {[
        { x: 80, y: 400, color: '#FF6B6B' },
        { x: 950, y: 600, color: '#4ECDC4' },
        { x: 100, y: 1200, color: '#FFE66D' },
        { x: 940, y: 1400, color: '#A8E6CF' },
      ].map((dot, i) => {
        const pulse = interpolate(
          frame % (fps * 2),
          [0, fps, fps * 2],
          [8, 12, 8]
        )
        return (
          <div key={i} style={{
            position: 'absolute', left: dot.x, top: dot.y,
            width: pulse, height: pulse, borderRadius: '50%',
            background: dot.color, opacity: 0.6,
          }} />
        )
      })}

      {/* Content */}
      <AbsoluteFill style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '100px 64px',
        gap: 24,
      }}>

        {/* ── INTRO ──────────────────────────────────────────── */}
        {inIntro && (
          <div style={{ textAlign: 'center' }}>
            <PopIn delay={0}>
              <div style={{ fontSize: 80 }}>📖</div>
            </PopIn>
            <PopIn delay={fps * 0.5} style={{ marginTop: 16 }}>
              <div style={{
                fontSize: 40, fontWeight: 900,
                background: 'linear-gradient(135deg, #FFE66D, #FF6B6B)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                Hadith Reels
              </div>
            </PopIn>
            <PopIn delay={fps * 1} style={{ marginTop: 8 }}>
              <div style={{
                fontSize: 20,
                color: 'rgba(255,255,255,0.6)',
                letterSpacing: 2,
              }}>
                🌟 Kids Series 🌟
              </div>
            </PopIn>
          </div>
        )}

        {/* ── ARABIC ─────────────────────────────────────────── */}
        {inArabic && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <PopIn delay={SCENE.arabic.start}>
              <div style={{
                background: 'rgba(255,255,255,0.08)',
                borderRadius: 24,
                padding: '40px 48px',
                border: '2px solid rgba(255,230,109,0.3)',
              }}>
                <div style={{
                  fontSize: 44,
                  lineHeight: 1.8,
                  direction: 'rtl',
                  color: '#FFE66D',
                  textShadow: '0 0 30px rgba(255,230,109,0.4)',
                }}>
                  {hadithArabic}
                </div>
              </div>
            </PopIn>

            <PopIn delay={SCENE.arabic.start + fps * 1.5} style={{ marginTop: 24 }}>
              <div style={{
                fontSize: 24,
                lineHeight: 1.6,
                color: 'rgba(255,255,255,0.9)',
                fontStyle: 'italic',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
              }}>
                "{hadithText}"
              </div>
            </PopIn>

            <PopIn delay={SCENE.arabic.start + fps * 2.5} style={{ marginTop: 16 }}>
              <div style={{
                display: 'inline-block',
                background: 'rgba(78,205,196,0.2)',
                border: '1px solid rgba(78,205,196,0.4)',
                borderRadius: 20,
                padding: '6px 20px',
                fontSize: 14,
                color: '#4ECDC4',
                letterSpacing: 1,
              }}>
                {collection} · {narrator}
              </div>
            </PopIn>
          </div>
        )}

        {/* ── STORY ──────────────────────────────────────────── */}
        {inStory && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <PopIn delay={SCENE.story.start}>
              <div style={{ fontSize: 56, marginBottom: 16 }}>🕌</div>
            </PopIn>

            <PopIn delay={SCENE.story.start + fps * 0.5}>
              <div style={{
                fontSize: 20,
                color: '#FFE66D',
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: 24,
              }}>
                {lang === 'ar' ? 'قصة من حياته ﷺ' :
                 lang === 'ru' ? 'История из жизни ﷺ' :
                 lang === 'uz' ? 'Hayotdan bir hikoya ﷺ' :
                 'A story from his life ﷺ'}
              </div>
            </PopIn>

            <PopIn delay={SCENE.story.start + fps * 1}>
              <div style={{
                fontSize: 28,
                lineHeight: 1.7,
                color: '#FFFFFF',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 20,
                padding: '32px 40px',
                borderLeft: lang !== 'ar' ? '4px solid #FF6B6B' : 'none',
                borderRight: lang === 'ar' ? '4px solid #FF6B6B' : 'none',
              }}>
                {story}
              </div>
            </PopIn>
          </div>
        )}

        {/* ── MORAL ──────────────────────────────────────────── */}
        {inMoral && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <PopIn delay={SCENE.moral.start}>
              <div style={{ fontSize: 64 }}>💡</div>
            </PopIn>

            <PopIn delay={SCENE.moral.start + fps * 0.5} style={{ marginTop: 16 }}>
              <div style={{
                fontSize: 22,
                color: '#4ECDC4',
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: 24,
              }}>
                {lang === 'ar' ? 'ماذا نتعلم؟' :
                 lang === 'ru' ? 'Что мы узнали?' :
                 lang === 'uz' ? 'Nima o\'rgandik?' :
                 'What did we learn?'}
              </div>
            </PopIn>

            <PopIn delay={SCENE.moral.start + fps * 1}>
              <div style={{
                fontSize: 34,
                fontWeight: 800,
                lineHeight: 1.5,
                color: '#FFFFFF',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
                background: 'linear-gradient(135deg, rgba(255,107,107,0.15), rgba(78,205,196,0.15))',
                borderRadius: 24,
                padding: '36px 44px',
                border: '2px solid rgba(255,230,109,0.2)',
              }}>
                {moral}
              </div>
            </PopIn>

            {/* Verification reminder for kids */}
            <PopIn delay={SCENE.moral.start + fps * 3} style={{ marginTop: 32 }}>
              <div style={{
                fontSize: 16,
                color: 'rgba(255,255,255,0.5)',
                letterSpacing: 1,
              }}>
                ✅ Only authentic (sahih) hadiths
              </div>
            </PopIn>
          </div>
        )}

        {/* ── OUTRO ──────────────────────────────────────────── */}
        {inOutro && (
          <div style={{ textAlign: 'center' }}>
            <PopIn delay={SCENE.outro.start}>
              <div style={{ fontSize: 80 }}>🌟</div>
            </PopIn>
            <PopIn delay={SCENE.outro.start + fps * 0.5} style={{ marginTop: 16 }}>
              <div style={{
                fontSize: 32, fontWeight: 900,
                background: 'linear-gradient(135deg, #FFE66D, #4ECDC4)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                JazakAllahu Khairan!
              </div>
            </PopIn>
            <PopIn delay={SCENE.outro.start + fps * 1} style={{ marginTop: 16 }}>
              <div style={{ fontSize: 18, color: 'rgba(255,255,255,0.5)' }}>
                🔍 hadithverifier.com · @HadithReels
              </div>
            </PopIn>
          </div>
        )}

      </AbsoluteFill>
    </AbsoluteFill>
  )
}
