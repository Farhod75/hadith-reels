// scripts/merge-reel.js
// Merges AI video + ElevenLabs audio + hadith text overlay into final MP4
// Usage: node scripts/merge-reel.js --video <url> --audio <path> --text "hadith text" --out <output.mp4>

const { execSync } = require('child_process')
const https = require('https')
const fs = require('fs')
const path = require('path')
const os = require('os')

const args = process.argv.slice(2)
const get = (flag) => { const i = args.indexOf(flag); return i !== -1 ? args[i + 1] : null }

const videoUrl  = get('--video')
const audioPath = get('--audio')
const text      = get('--text') || 'Hadith Reels'
const arabicText = get('--arabic') || ''
const outPath   = get('--out') || 'out/final-reel.mp4'
const lang      = get('--lang') || 'en'

if (!videoUrl) { console.error('--video required'); process.exit(1) }

// ── Download video from fal.ai URL ───────────────────────────────────────────
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest)
    https.get(url, res => {
      res.pipe(file)
      file.on('finish', () => { file.close(); resolve() })
    }).on('error', reject)
  })
}

// ── Build FFmpeg drawtext filter ──────────────────────────────────────────────
function escapeText(t) {
  return t.replace(/'/g, "\\'").replace(/:/g, '\\:').replace(/\[/g, '\\[').replace(/\]/g, '\\]')
}

async function merge() {
  const tmpDir   = os.tmpdir()
  const videoTmp = path.join(tmpDir, `hr-video-${Date.now()}.mp4`)

  // If local file, use directly. If URL, download it.
  let videoSource
  if (videoUrl.startsWith('http')) {
    console.log('⬇️  Downloading video from URL...')
    await downloadFile(videoUrl, videoTmp)
    videoSource = videoTmp
    console.log('✅ Video downloaded')
  } else {
    videoSource = videoUrl
    console.log('✅ Using local video:', videoSource)
  }

  // Ensure output directory exists
  fs.mkdirSync(path.dirname(outPath), { recursive: true })

  // Build FFmpeg command
  const isRTL = lang === 'ar'
  const fontSize = 48
  const fontColor = 'white'
  const shadowColor = 'black@0.8'

  // Text overlay — hadith text at bottom, arabic at top if present
  let filterComplex = ''

  if (audioPath && fs.existsSync(audioPath)) {
    // With audio
    filterComplex = `-i "${audioPath}"`
  }

  // Drawtext filters
  const drawtextFilters = []

  // Arabic text at top
if (arabicText) {
  drawtextFilters.push(
    `drawtext=text='${escapeText(arabicText)}':` +
    `fontsize=52:fontcolor=white:` +
    `shadowcolor=black@0.9:shadowx=3:shadowy=3:` +
    `box=1:boxcolor=black@0.5:boxborderw=12:` +
    `x=(w-text_w)/2:y=60:` +
    `font=Arial`
  )
}

// Main hadith text — centered middle of screen
drawtextFilters.push(
  `drawtext=text='${escapeText(text)}':` +
  `fontsize=54:fontcolor=white:` +
  `shadowcolor=black@0.9:shadowx=3:shadowy=3:` +
  `box=1:boxcolor=black@0.5:boxborderw=14:` +
  `x=(w-text_w)/2:y=(h-text_h)/2:` +
  `font=Arial`
)

// Watermark bottom
drawtextFilters.push(
  `drawtext=text='hadithreels.com':` +
  `fontsize=22:fontcolor=white@0.6:` +
  `shadowcolor=black@0.8:shadowx=2:shadowy=2:` +
  `x=(w-text_w)/2:y=h-40:` +
  `font=Arial`
)

  const vf = drawtextFilters.join(',')

  // Replace the cmd building section with this:

let cmd
if (audioPath && fs.existsSync(audioPath)) {
  // Loop video to match audio duration, add text overlay
  cmd = `ffmpeg -y -stream_loop -1 -i "${videoSource}" -i "${audioPath}" ` +
    `-vf "${vf}" ` +
    `-c:v libx264 -c:a aac -shortest ` +
    `-movflags +faststart ` +
    `"${outPath}"`
} else {
  cmd = `ffmpeg -y -i "${videoSource}" ` +
    `-vf "${vf}" ` +
    `-c:v libx264 -an ` +
    `-movflags +faststart ` +
    `"${outPath}"`
}

  console.log('🎬 Merging video + audio + text...')
  console.log('CMD:', cmd)

  try {
    execSync(cmd, { stdio: 'inherit' })
    console.log('✅ Done! Output:', outPath)

    // Cleanup temp video
    if (videoUrl.startsWith('http') && fs.existsSync(videoTmp)) {
  fs.unlinkSync(videoTmp)
}
  } catch (err) {
    console.error('❌ FFmpeg error:', err.message)
    process.exit(1)
  }
}

merge().catch(console.error)