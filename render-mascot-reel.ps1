<#
================================================================================
 render-mascot-reel.ps1  —  Hadith Reels: KIDS talking-mascot reel
================================================================================
 Sibling to render-reel.ps1. DIFFERENT audio model:
   - render-reel.ps1   : background video (looped, silent) + narration.mp3 + nasheed
   - this script        : the TALKING-MASCOT clips ARE the spine. Each clip is
                          video + its own lip-synced voice (from fal Fabric).
                          Nasheed is mixed UNDERNEATH the mascot's voice.

 PRE-REQUISITE: generate the talking clip(s) first with generate-talking-clip.py
   (one clip per <=30s audio segment, per Fabric's per-clip cap). Save them under
   out\talking\ and pass them to -Clips in narration order (e.g. story then moral).

 NAMING:
   out\talking\<your-clip>.mp4            <- you generate these (Fabric)
   ---------- this script produces: ----------
   out\kids-{lang}-{slug}-mascot-reel.mp4 <- final reel (distinct from render-reel)

   lang = en | ru | uz | tj | ar
   slug = collection-number  (e.g. bukhari-1520)

 USAGE:
   # single clip:
   .\render-mascot-reel.ps1 -Lang en -Slug bukhari-1520 -Clips test-boy.mp4 -Open
   # ordered story + moral, specific nasheed:
   .\render-mascot-reel.ps1 -Lang uz -Slug muslim-1337 -Clips lamb-uz-story.mp4,lamb-uz-moral.mp4 -Nasheed ramadan-bg.mp3
   # no background music (voice only):
   .\render-mascot-reel.ps1 -Lang ru -Slug bukhari-1520 -Clips lamb-ru-story.mp4 -NoMusic -Open

 PARAMS:
   -Clips       (required) ordered talking-mascot clip name(s) in out\talking\
   -Nasheed     (optional) specific nasheed in out\backgrounds\; else random
   -NoMusic     (optional) skip background nasheed entirely (mascot voice only)
   -Subs        (optional) .srt filename in out\ to burn in (skipped for uz/tj per P078)
   -Open        (optional) auto-play the finished reel
================================================================================
#>

param(
  [Parameter(Mandatory)][ValidateSet('en','ru','uz','tj','ar')][string]$Lang,
  [Parameter(Mandatory)][string]$Slug,
  [Parameter(Mandatory)][string[]]$Clips,
  [string]$Nasheed,
  [switch]$NoMusic,
  [string]$Subs,
  [switch]$Open
)

$ErrorActionPreference = 'Stop'

# Native tools (ffmpeg) write normal output to stderr; PowerShell can mistake that
# for a terminating error. Run() executes a native command and only fails on a real
# non-zero exit code (same helper used in render-reel.ps1).
function Run($exe, [string[]]$cmdArgs) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  & $exe @cmdArgs 2>&1 | Out-Null
  $code = $LASTEXITCODE
  $ErrorActionPreference = $prev
  return $code
}

# --- operate from the repo root (where this script lives) ---------------------
Set-Location $PSScriptRoot

function Say ($m){ Write-Host $m -ForegroundColor Cyan }
function Ok  ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die ($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

$base    = "kids-$Lang-$Slug"
$talkDir = "out\talking"
$reel    = "out\$base-mascot-reel.mp4"

Say "================================================================"
Say " Mascot reel: $base   (clips: $($Clips.Count)$(if($NoMusic){'; voice-only'}))"
Say "================================================================"

# --- STEP 0: validate up front, fail loud with the full list -----------------
Say "`n[0/4] Validating prerequisites..."
$problems = @()

# ffmpeg on PATH? try the known location if missing
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  $known = "C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
  if (Test-Path "$known\ffmpeg.exe") { $env:PATH += ";$known" }
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  $problems += "ffmpeg not found on PATH. Install or add: C:\ffmpeg\...\bin"
}

# every requested clip must exist in out\talking\
$clipPaths = foreach ($name in $Clips) {
  $p = Join-Path $talkDir $name
  if (-not (Test-Path $p)) { $problems += "missing talking clip: $p" }
  $p
}

# nasheed (unless voice-only)
$chosenNasheed = $null
if (-not $NoMusic) {
  $nasheeds = @(Get-ChildItem "out\backgrounds\*.mp3" -ErrorAction SilentlyContinue)
  if ($Nasheed) {
    if (Test-Path "out\backgrounds\$Nasheed") { $chosenNasheed = "out\backgrounds\$Nasheed" }
    else { $problems += "requested nasheed not found: out\backgrounds\$Nasheed" }
  } elseif ($nasheeds.Count -ge 1) {
    $chosenNasheed = ($nasheeds | Get-Random).FullName
  } else {
    $problems += "no nasheed .mp3 in out\backgrounds\ (or pass -NoMusic)"
  }
}

# optional subtitles
$srtPath = $null
if ($Subs) {
  if (@('uz','tj') -contains $Lang) {
    Write-Host "  NOTE  -Subs ignored for $Lang (P078: Latin transliteration unreliable)." -ForegroundColor Yellow
  } elseif (Test-Path "out\$Subs") {
    $srtPath = "out\$Subs"
  } else {
    $problems += "subtitle file not found: out\$Subs"
  }
}

if (Test-Path $reel) {
  Write-Host "  NOTE  $reel already exists and will be overwritten." -ForegroundColor Yellow
}

if ($problems.Count -gt 0) {
  Write-Host "`nCannot render -- fix these first:" -ForegroundColor Red
  $problems | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
  exit 1
}
Ok "$($Clips.Count) clip(s) present; ffmpeg ready$(if($chosenNasheed){"; nasheed: $(Split-Path $chosenNasheed -Leaf)"}else{'; voice-only'})"

# --- STEP 1: normalize each clip to identical 1080x1920@30fps (KEEP audio) ----
# Unlike the background path in render-reel.ps1 (which drops audio with -an), the
# mascot's own voice IS the audio, so we re-encode video + audio to a uniform spec
# so the clips can be safely concatenated with -c copy afterwards.
Say "`n[1/4] Normalizing $($Clips.Count) talking clip(s)..."
$tmps = @()
$idx  = 0
foreach ($cp in $clipPaths) {
  $idx++
  $tmp = "$talkDir\_norm-$base-$idx.mp4"
  Write-Host "        + $(Split-Path $cp -Leaf)" -ForegroundColor DarkGray
  $rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-i",$cp,
    "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
    "-r","30","-c:v","libx264","-pix_fmt","yuv420p",
    "-c:a","aac","-ar","44100","-ac","2",$tmp)
  if (-not (Test-Path $tmp)) { Die "failed to normalize $(Split-Path $cp -Leaf)" }
  $tmps += $tmp
}
Ok "normalized to 1080x1920@30fps (audio preserved)"

# --- STEP 2: concat normalized clips into one spine (video + mascot voice) ----
Say "`n[2/4] Concatenating clips into the mascot spine..."
$spine      = "$talkDir\_spine-$base.mp4"
$concatList = "$talkDir\_concat-$base.txt"
$tmps | ForEach-Object { "file '$((Resolve-Path $_).Path -replace '\\','/')'" } |
  Out-File -Encoding ASCII -FilePath $concatList
$rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",$concatList,"-c","copy",$spine)
if (-not (Test-Path $spine)) { Die "clip concat failed ($spine not created)" }
Ok "$spine"

# --- STEP 3: final merge (title overlay + optional nasheed + optional subs) ---
Say "`n[3/4] Final merge (title$(if($chosenNasheed){' + nasheed'})$(if($srtPath){' + subs'}))..."

$title = "drawtext=text='Hadith Reels':fontsize=28:fontcolor=white:shadowcolor=black@0.9:shadowx=2:shadowy=2:box=1:boxcolor=black@0.4:boxborderw=8:x=(w-text_w)/2:y=30:font=Arial"
if ($srtPath) {
  $subStyle = "force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2,MarginV=80'"
  $vf = "subtitles='$($srtPath -replace '\\','/')':$subStyle,$title"
} else {
  $vf = $title
}

if ($chosenNasheed) {
  # mascot voice at full, nasheed softened underneath; stop at the voice length
  $rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y",
    "-i",$spine,
    "-stream_loop","-1","-i",$chosenNasheed,
    "-filter_complex","[0:a]volume=1.0[voice];[1:a]volume=0.20[music];[voice][music]amix=inputs=2:duration=first[aout]",
    "-vf",$vf,
    "-map","0:v","-map","[aout]",
    "-c:v","libx264","-c:a","aac","-shortest","-movflags","+faststart",
    $reel)
} else {
  # voice-only: keep the mascot audio as-is, just overlay the title (+subs)
  $rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y",
    "-i",$spine,
    "-vf",$vf,
    "-map","0:v","-map","0:a",
    "-c:v","libx264","-c:a","aac","-movflags","+faststart",
    $reel)
}

# clean temps regardless of music path
$tmps | ForEach-Object { Remove-Item $_ -ErrorAction SilentlyContinue }
Remove-Item $concatList -ErrorAction SilentlyContinue
Remove-Item $spine      -ErrorAction SilentlyContinue

if (-not (Test-Path $reel)) { Die "final merge failed ($reel not created)" }

# --- STEP 4: verify ----------------------------------------------------------
Say "`n[4/4] Done."
$info = Get-Item $reel
$mb   = [math]::Round($info.Length/1MB,1)
Ok "$reel  ($mb MB)"
if ($mb -gt 50) {
  Write-Host "  WARN  $mb MB exceeds Telegram's 50MB native limit -- add -b:v 3000k or trim." -ForegroundColor Yellow
}
(& ffprobe -hide_banner -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $reel 2>$null) |
  ForEach-Object { Write-Host "        resolution: $_" -ForegroundColor DarkGray }

Write-Host "`nNEXT: watch it, then post to @SahihHadithReels (human approval per hard rules)." -ForegroundColor Cyan
if ($Open) { Start-Process $reel }
