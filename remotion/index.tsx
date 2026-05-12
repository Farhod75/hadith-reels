// remotion/index.tsx
// P052: .tsx extension required for JSX
// P053: cast component to React.ComponentType<any> for Remotion LooseComponentType compatibility

import React from 'react'
import { Composition } from 'remotion'
import { HadithReel, type HadithReelProps } from './compositions/HadithReel'
import { KidsReel, type KidsReelProps } from './compositions/KidsReel'

// Cast to any to satisfy Remotion's LooseComponentType<Record<string, unknown>>
// This is safe — Remotion passes inputProps at runtime which match the typed props
const HadithReelComp = HadithReel as React.ComponentType<any>
const KidsReelComp   = KidsReel   as React.ComponentType<any>

export const RemotionRoot: React.FC = () => {
  const adultDefaults: HadithReelProps = {
    hadithArabic:  'الصِّيَامُ جُنَّةٌ',
    hadithText:    'Fasting is a shield.',
    narrator:      'Abu Hurairah',
    collection:    'Sahih al-Bukhari',
    hadithNumber:  '1894',
    story:         'One day the Prophet ﷺ saw his companions struggling with their desires and reminded them of this shield...',
    moral:         'Protect yourself with fasting — it shields the soul from harm.',
    seerahContext: 'During the blessed months in Madinah, the Prophet ﷺ taught his companions the power of voluntary fasting.',
    attribution:   '📖 Source: Ar-Raheeq Al-Makhtum',
    lang:          'en',
    audioUrl:      undefined,
  }

  const kidsDefaults: KidsReelProps = {
    hadithArabic: 'تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ',
    hadithText:   'Your smile for your brother is charity!',
    narrator:     'Abu Dharr',
    collection:   'Jami at-Tirmidhi',
    story:        'One day a little boy came to the Prophet ﷺ feeling very sad. The Prophet ﷺ smiled at him warmly — and the boy felt better right away!',
    moral:        'A simple smile can make someone\'s whole day better — and Allah rewards you for it!',
    lang:         'en',
    audioUrl:     undefined,
  }

  return (
    <>
      <Composition
        id="HadithReel"
        component={HadithReelComp}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={adultDefaults as Record<string, unknown>}
      />

      <Composition
        id="KidsReel"
        component={KidsReelComp}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={kidsDefaults as Record<string, unknown>}
      />
    </>
  )
}
