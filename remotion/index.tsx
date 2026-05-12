// remotion/index.tsx   ← MUST be .tsx not .ts (contains JSX)
// Composition registry

import React from 'react'
import { Composition } from 'remotion'
import { HadithReel, type HadithReelProps } from './compositions/HadithReel'
import { KidsReel, type KidsReelProps } from './compositions/KidsReel'

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="HadithReel"
        component={HadithReel}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          hadithArabic:  'الصِّيَامُ جُنَّةٌ',
          hadithText:    'Fasting is a shield.',
          narrator:      'Abu Hurairah',
          collection:    'Sahih al-Bukhari',
          hadithNumber:  '1894',
          story:         'One day the Prophet ﷺ saw his companions struggling...',
          moral:         'Protect yourself with fasting.',
          seerahContext: 'During Ramadan in Madinah...',
          attribution:   '📖 Source: Ar-Raheeq Al-Makhtum',
          lang:          'en',
          audioUrl:      undefined,
        } as HadithReelProps}
      />

      <Composition
        id="KidsReel"
        component={KidsReel}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          hadithArabic: 'تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ',
          hadithText:   'Your smile for your brother is charity!',
          narrator:     'Abu Dharr',
          collection:   'Jami at-Tirmidhi',
          story:        'One day a boy came to the Prophet ﷺ feeling sad...',
          moral:        'A smile can make someone\'s whole day better!',
          lang:         'en',
          audioUrl:     undefined,
        } as KidsReelProps}
      />
    </>
  )
}
