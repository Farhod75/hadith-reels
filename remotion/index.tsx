// remotion/index.tsx
// P056: Must call registerRoot() — required by Remotion CLI entry point

import React from 'react'
import { Composition, registerRoot } from 'remotion'
import { HadithReel, type HadithReelProps } from './compositions/HadithReel'
import { KidsReel, type KidsReelProps } from './compositions/KidsReel'

const adultDefaults: HadithReelProps = {
  hadithArabic:  'الصِّيَامُ جُنَّةٌ',
  hadithText:    'Fasting is a shield.',
  narrator:      'Abu Hurairah',
  collection:    'Sahih al-Bukhari',
  hadithNumber:  '1894',
  story:         'One day the Prophet ﷺ saw his companions struggling with their desires and reminded them of fasting as a shield against temptation.',
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
  moral:        "A simple smile can make someone's whole day better — and Allah rewards you for it!",
  lang:         'en',
  audioUrl:     undefined,
}

const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="HadithReel"
        component={HadithReel as React.ComponentType<any>}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={adultDefaults as unknown as Record<string, unknown>}
      />
      <Composition
        id="KidsReel"
        component={KidsReel as React.ComponentType<any>}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={kidsDefaults as unknown as Record<string, unknown>}
      />
    </>
  )
}

// Required by Remotion CLI — must be called in the entry point file
registerRoot(Root)
