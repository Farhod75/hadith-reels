// remotion/compositions/HadithReel.tsx v2
// Adults composition improvements:
//   - Scene-specific background gradients (deep purple/navy/earth/midnight)
//   - Audio wired (audioUrl prop passed to <Audio>)
//   - Larger Arabic text (58px)
//   - Gold left border on story text
//   - Crescent moon 🌙 in intro
//   - Smoother scene transitions
//   - Gold divider animation

import React from 'react'
import {
  AbsoluteFill,
  Audio,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion'

export interface HadithReelProps {
  hadithArabic:   string
  hadithText:     string
  narrator:       string
  collection:     string
  hadithNumber?:  string
  story:          string
  moral:          string
  seerahContext:  string
  attribution:    string
  lang:           string
  audioUrl?:      string
}

const SCENE_GRADIENTS: Record<string, string> = {
  intro:  'linear-gradient(160deg, #0a0614 0%, #0d0a1f 100%)',
  arabic: 'linear-gradient(160deg, #060a14 0%, #0a1428 100%)',
  trans:  'linear-gradient(160deg, #0a0a0f 0%, #141019 100%)',
  story:  'linear-gradient(160deg, #0a0c08 0%, #101408 100%)',
  moral:  'linear-gradient(160deg, #080a14 0%, #0d0f20 100%)',
  outro:  'linear-gradient(160deg, #0a0614 0%, #0d0a1f 100%)',
}

function FadeInText({ children, delay = 0, style = {} }: {
  children: React.ReactNode; delay?: number; style?: React.CSSProperties
}) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const opacity = interpolate(frame, [delay, delay + fps * 0.8], [0, 1], { extrapolateRight: 'clamp' })
  const translateY = interpolate(frame, [delay, delay + fps * 0.8], [24, 0], { extrapolateRight: 'clamp' })
  return <div style={{ opacity, transform: `translateY(${translateY}px)`, ...style }}>{children}</div>
}

function GoldDivider({ delay }: { delay: number }) {
  const frame = useCurrentFrame()
  const pct = interpolate(frame, [delay, delay + 25], [0, 100], { extrapolateRight: 'clamp' })
  return (
    <div style={{
      height: 1, width: `${pct}%`,
      background: 'linear-gradient(90deg, transparent, #D4AF37, transparent)',
      margin: '28px auto',
    }} />
  )
}

function GoldDot({ x, y, delay }: { x: number; y: number; delay: number }) {
  const frame = useCurrentFrame()
  const opacity = interpolate(frame, [delay, delay + 30], [0, 0.5], { extrapolateRight: 'clamp' })
  const pulse = Math.sin(frame * 0.03 + delay) * 0.3 + 0.7
  return (
    <div style={{
      position: 'absolute', left: x, top: y,
      width: 4, height: 4, borderRadius: '50%',
      background: '#D4AF37', opacity: opacity * pulse,
    }} />
  )
}

export const HadithReel: React.FC<HadithReelProps> = ({
  hadithArabic, hadithText, narrator, collection, hadithNumber,
  story, moral, seerahContext, attribution, lang, audioUrl,
}) => {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()

  const SCENE = {
    intro:  { start: 0,        end: fps * 5  },
    arabic: { start: fps * 5,  end: fps * 16 },
    trans:  { start: fps * 16, end: fps * 26 },
    story:  { start: fps * 26, end: fps * 44 },
    moral:  { start: fps * 44, end: fps * 54 },
    outro:  { start: fps * 54, end: durationInFrames },
  }

  const inIntro  = frame < SCENE.arabic.start
  const inArabic = frame >= SCENE.arabic.start && frame < SCENE.trans.start
  const inTrans  = frame >= SCENE.trans.start  && frame < SCENE.story.start
  const inStory  = frame >= SCENE.story.start  && frame < SCENE.moral.start
  const inMoral  = frame >= SCENE.moral.start  && frame < SCENE.outro.start
  const inOutro  = frame >= SCENE.outro.start

  const bg = inIntro ? SCENE_GRADIENTS.intro
    : inArabic ? SCENE_GRADIENTS.arabic
    : inTrans  ? SCENE_GRADIENTS.trans
    : inStory  ? SCENE_GRADIENTS.story
    : inMoral  ? SCENE_GRADIENTS.moral
    : SCENE_GRADIENTS.outro

  const LABEL = {
    story: lang === 'ar' ? 'من السيرة النبوية' : lang === 'ru' ? 'Из жизни Пророка ﷺ' : lang === 'uz' ? "Payg'ambar ﷺ hayotidan" : lang === 'tj' ? 'Аз зиндагии Паёмбар ﷺ' : 'From the life of the Prophet ﷺ',
    trans: lang === 'ar' ? 'الترجمة' : lang === 'ru' ? 'Перевод' : lang === 'uz' ? 'Tarjima' : lang === 'tj' ? 'Тарҷума' : 'Translation',
    moral: lang === 'ar' ? 'الفائدة' : lang === 'ru' ? 'Урок' : lang === 'uz' ? 'Saboq' : lang === 'tj' ? 'Дарс' : 'Moral',
  }

  return (
    <AbsoluteFill style={{
      background: bg,
      fontFamily: '"Amiri", "Noto Sans Arabic", Georgia, serif',
      color: '#F5F0E8', overflow: 'hidden',
    }}>
      {audioUrl && <Audio src={audioUrl} startFrom={0} />}

      {/* Border frame */}
      <div style={{ position: 'absolute', inset: 32, border: '1px solid rgba(212,175,55,0.25)', borderRadius: 8, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', inset: 42, border: '1px solid rgba(212,175,55,0.08)', borderRadius: 6, pointerEvents: 'none' }} />

      {/* Corner ornaments */}
      {[{ top: 32, left: 32 }, { top: 32, right: 32 }, { bottom: 32, left: 32 }, { bottom: 32, right: 32 }].map((pos, i) => (
        <div key={i} style={{
          position: 'absolute', ...pos, width: 24, height: 24,
          borderTop: i < 2 ? '2px solid #D4AF37' : 'none',
          borderBottom: i >= 2 ? '2px solid #D4AF37' : 'none',
          borderLeft: i % 2 === 0 ? '2px solid #D4AF37' : 'none',
          borderRight: i % 2 === 1 ? '2px solid #D4AF37' : 'none',
        }} />
      ))}

      {/* Ambient particles */}
      {[{ x: 70, y: 180, delay: 10 }, { x: 960, y: 320, delay: 20 }, { x: 100, y: 750, delay: 15 }, { x: 940, y: 1150, delay: 25 }, { x: 180, y: 1550, delay: 5 }, { x: 870, y: 1680, delay: 30 }].map((p, i) => <GoldDot key={i} {...p} />)}

      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '120px 72px' }}>

        {inIntro && (
          <div style={{ textAlign: 'center' }}>
            <FadeInText delay={0}><div style={{ fontSize: 72, marginBottom: 24 }}>🌙</div></FadeInText>
            <FadeInText delay={fps * 0.8}>
              <div style={{ fontSize: 44, color: '#D4AF37', letterSpacing: 6, direction: 'rtl', lineHeight: 1.8 }}>
                بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
              </div>
            </FadeInText>
            <FadeInText delay={fps * 2} style={{ marginTop: 20 }}>
              <div style={{ fontSize: 16, color: 'rgba(245,240,232,0.4)', letterSpacing: 8, textTransform: 'uppercase' }}>Hadith Reels</div>
            </FadeInText>
          </div>
        )}

        {inArabic && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.arabic.start}>
              <div style={{ fontSize: 14, color: '#D4AF37', letterSpacing: 5, textTransform: 'uppercase', marginBottom: 16 }}>
                {collection} · {hadithNumber}
              </div>
            </FadeInText>
            <GoldDivider delay={SCENE.arabic.start + 5} />
            <FadeInText delay={SCENE.arabic.start + fps * 0.6}>
              <div style={{ fontSize: 58, lineHeight: 1.9, direction: 'rtl', color: '#F5F0E8', textShadow: '0 0 60px rgba(212,175,55,0.25)', padding: '0 40px' }}>
                {hadithArabic}
              </div>
            </FadeInText>
            <GoldDivider delay={SCENE.arabic.start + fps * 2} />
            <FadeInText delay={SCENE.arabic.start + fps * 2.5}>
              <div style={{ fontSize: 18, color: 'rgba(212,175,55,0.7)', letterSpacing: 2, direction: 'rtl' }}>
                — {narrator} رضي الله عنه
              </div>
            </FadeInText>
          </div>
        )}

        {inTrans && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.trans.start}>
              <div style={{ fontSize: 13, color: '#D4AF37', letterSpacing: 5, textTransform: 'uppercase', marginBottom: 40 }}>{LABEL.trans}</div>
            </FadeInText>
            <FadeInText delay={SCENE.trans.start + fps * 0.6}>
              <div style={{ fontSize: 42, lineHeight: 1.7, color: '#F5F0E8', fontStyle: 'italic', maxWidth: 860, margin: '0 auto', direction: lang === 'ar' ? 'rtl' : 'ltr' }}>
                "{hadithText}"
              </div>
            </FadeInText>
            <FadeInText delay={SCENE.trans.start + fps * 2.5} style={{ marginTop: 48 }}>
              <div style={{ fontSize: 15, color: 'rgba(245,240,232,0.35)', letterSpacing: 3 }}>{collection} #{hadithNumber}</div>
            </FadeInText>
          </div>
        )}

        {inStory && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.story.start}>
              <div style={{ fontSize: 14, color: '#D4AF37', letterSpacing: 5, textTransform: 'uppercase', marginBottom: 32 }}>{LABEL.story}</div>
            </FadeInText>
            <FadeInText delay={SCENE.story.start + fps * 0.8}>
              <div style={{
                fontSize: 30, lineHeight: 1.85, color: 'rgba(245,240,232,0.92)', maxWidth: 880, margin: '0 auto',
                direction: lang === 'ar' ? 'rtl' : 'ltr',
                borderLeft: lang !== 'ar' ? '3px solid rgba(212,175,55,0.4)' : 'none',
                borderRight: lang === 'ar' ? '3px solid rgba(212,175,55,0.4)' : 'none',
                paddingLeft: lang !== 'ar' ? 32 : 0,
                paddingRight: lang === 'ar' ? 32 : 0,
                textAlign: 'left' as const,
              }}>
                {story}
              </div>
            </FadeInText>
            <FadeInText delay={SCENE.story.start + fps * 3.5} style={{ marginTop: 40 }}>
              <div style={{ fontSize: 13, color: 'rgba(212,175,55,0.5)', letterSpacing: 2, fontStyle: 'italic' }}>{attribution}</div>
            </FadeInText>
          </div>
        )}

        {inMoral && (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <FadeInText delay={SCENE.moral.start}>
              <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(212,175,55,0.12)', border: '1px solid rgba(212,175,55,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 28px', fontSize: 30 }}>💡</div>
            </FadeInText>
            <FadeInText delay={SCENE.moral.start + fps * 0.5}>
              <div style={{ fontSize: 13, color: '#D4AF37', letterSpacing: 5, textTransform: 'uppercase', marginBottom: 36 }}>{LABEL.moral}</div>
            </FadeInText>
            <FadeInText delay={SCENE.moral.start + fps * 1}>
              <div style={{ fontSize: 36, lineHeight: 1.65, color: '#F5F0E8', fontWeight: 500, maxWidth: 820, margin: '0 auto', direction: lang === 'ar' ? 'rtl' : 'ltr' }}>
                {moral}
              </div>
            </FadeInText>
          </div>
        )}

        {inOutro && (
          <div style={{ textAlign: 'center' }}>
            <FadeInText delay={SCENE.outro.start}>
              <div style={{ fontSize: 42, color: '#D4AF37', direction: 'rtl', marginBottom: 28 }}>جَزَاكُمُ اللَّهُ خَيْرًا</div>
            </FadeInText>
            <FadeInText delay={SCENE.outro.start + fps * 0.8}>
              <div style={{ fontSize: 16, color: 'rgba(245,240,232,0.45)', letterSpacing: 4, marginBottom: 16 }}>🔍 VERIFY · hadithverifier.com</div>
            </FadeInText>
            <FadeInText delay={SCENE.outro.start + fps * 1.5}>
              <div style={{ fontSize: 15, color: 'rgba(212,175,55,0.5)', letterSpacing: 3 }}>@HadithReels</div>
            </FadeInText>
          </div>
        )}

      </AbsoluteFill>

      {/* Scene progress */}
      <div style={{ position: 'absolute', bottom: 52, left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: 8 }}>
        {Object.entries(SCENE).map(([name, s]) => {
          const active = frame >= s.start && frame < s.end
          return <div key={name} style={{ width: active ? 24 : 6, height: 3, borderRadius: 2, background: active ? '#D4AF37' : 'rgba(212,175,55,0.2)' }} />
        })}
      </div>

    </AbsoluteFill>
  )
}
