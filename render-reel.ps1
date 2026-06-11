<#
================================================================================
 render-reel.ps1  —  Hadith Reels: automated render pipeline (Steps 4-7)
================================================================================
 Replaces the manual FFmpeg/Whisper drudgery in reel-creation-pipeline.md.

 NAMING CONVENTION (required):
   out\{style}-{lang}-{slug}-story.mp3      <- from admin Step 2 (you save this)
   out\{style}-{lang}-{slug}-moral.mp3      <- from admin Step 2 (you save this)
   ---------- this script produces: ----------
   out\{style}-{lang}-{slug}-narration.mp3  <- Step 4 (story+moral concat)
   out\{style}-{lang}-{slug}-narration.srt  <- Step 5 (en/ru/ar only, per P078)
   out\{style}-{lang}-{slug}-reel.mp4       <- Step 7 (final reel)

   style = adults | kids
   lang  = en | ru | ar | uz | tj
   slug  = collection-number  (e.g. bukhari-1520)  -> machine-dedupable

 USAGE:
   .\render-reel.ps1 -Style adults -Lang ru -Slug bukhari-1520
   .\render-reel.ps1 -Style kids   -Lang uz -Slug muslim-1337 -Nasheed ramadan-bg.mp3
   .\render-reel.ps1 -Style adults -Lang en -Slug bukhari-1773 -Open
   # ANIMATED reel (ordered scene clips from out\backgrounds\new\normalized\):
   .\render-reel.ps1 -Style adults -Lang ru -Slug bukhari-1520 -Scenes b1520-scene1.mp4,b1520-dua.mp4,kaaba.mp4 -Open

 PARAMS:
   -Nasheed     (optional) specific nasheed filename in out\backgrounds\; else random
   -ForceNoSubs (optional) skip subtitles even for en/ru/ar
   -NoReview    (optional) skip the subtitle proofreading pause (for trusted reels)
   -Open        (optional) auto-play the finished reel
================================================================================
#>

param(
  [Parameter(Mandatory)][ValidateSet('adults','kids')][string]$Style,
  [Parameter(Mandatory)][ValidateSet('en','ru','ar','uz','tj')][string]$Lang,
  [Parameter(Mandatory)][string]$Slug,
  [string]$Nasheed,
  [string[]]$Scenes,     # ordered clip names (in normalized\) for an ANIMATED reel; omit = random 3
  [switch]$ForceNoSubs,
  [switch]$NoReview,
  [switch]$Open
)

$ErrorActionPreference = 'Stop'
# Native tools (ffmpeg/whisper) write normal output to stderr; PowerShell can mistake that
# for a terminating error. Helper runs a native command and only fails on a real exit code.
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

function Say  ($m){ Write-Host $m -ForegroundColor Cyan }
function Ok   ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die  ($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

$base    = "$Style-$Lang-$Slug"
$story   = "out\$base-story.mp3"
$moral   = "out\$base-moral.mp3"
$narr    = "out\$base-narration.mp3"
$srt     = "out\$base-narration.srt"
$bgMixed = "out\backgrounds\$base-bg-mixed.mp4"
$reel    = "out\$base-reel.mp4"
$normDir = "out\backgrounds\new\normalized"

# subtitles routing per P078: Latin transliteration breaks UZ/TJ -> skip
$subLangs = @('en','ru','ar')
$useSubs  = ($subLangs -contains $Lang) -and (-not $ForceNoSubs)

Say "================================================================"
Say " Render: $base   (subtitles: $(if($useSubs){'YES'}else{'NO (P078 / forced)'}))"
Say "================================================================"

# --- STEP 0: validate everything up front, fail loud with full list ----------
Say "`n[0/5] Validating prerequisites..."
$problems = @()

# ffmpeg on PATH? try to add the known location if missing
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  $known = "C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
  if (Test-Path "$known\ffmpeg.exe") { $env:PATH += ";$known" }
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  $problems += "ffmpeg not found on PATH. Install or add: C:\ffmpeg\...\bin"
}

# whisper only needed if we're making subs
if ($useSubs -and -not (Get-Command whisper -ErrorAction SilentlyContinue)) {
  $problems += "whisper not found (needed for $Lang subtitles). Run: pip install openai-whisper  (or use -ForceNoSubs)"
}

if (-not (Test-Path $story)) { $problems += "missing story narration: $story" }
if (-not (Test-Path $moral)) { $problems += "missing moral narration: $moral" }

# need >=3 normalized background clips
$clips = @(Get-ChildItem "$normDir\*.mp4" -ErrorAction SilentlyContinue)
if ($clips.Count -lt 3) { $problems += "need >=3 background clips in $normDir (found $($clips.Count))" }

# nasheeds: all *.mp3 directly under out\backgrounds\
$nasheeds = @(Get-ChildItem "out\backgrounds\*.mp3" -ErrorAction SilentlyContinue)
if ($nasheeds.Count -lt 1) { $problems += "no nasheed .mp3 found in out\backgrounds\" }
if ($Nasheed -and -not (Test-Path "out\backgrounds\$Nasheed")) {
  $problems += "requested nasheed not found: out\backgrounds\$Nasheed"
}

# guard: don't silently overwrite an existing final reel
if (Test-Path $reel) {
  Write-Host "  NOTE  $reel already exists and will be overwritten." -ForegroundColor Yellow
}

if ($problems.Count -gt 0) {
  Write-Host "`nCannot render -- fix these first:" -ForegroundColor Red
  $problems | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
  exit 1
}
Ok "story + moral present; ffmpeg ready; $($clips.Count) bg clips; $($nasheeds.Count) nasheeds"

# --- STEP 4: concat story + moral (1s pause) into one narration --------------
Say "`n[1/5] Step 4 - concatenating story + moral narration..."
$rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-i",$story,"-i",$moral,
  "-filter_complex","[0:a]apad=pad_dur=1[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
  "-map","[out]",$narr)
if (-not (Test-Path $narr)) { Die "narration concat failed ($narr not created)" }
Ok "$narr ($([math]::Round((Get-Item $narr).Length/1KB)) KB)"

# --- STEP 5: subtitles (conditional by language) -----------------------------
if ($useSubs) {
  Say "`n[2/5] Step 5 - generating subtitles via Whisper ($Lang)..."
  if (Test-Path $srt) {
    Ok "subtitles already present ($srt) - skipping Whisper"
  } else {
    # Build args as an array of literal strings; pass the path quoted to avoid
    # PowerShell mangling the backslash path into whisper.exe (which prints usage).
    & whisper "$narr" --model small --language $Lang --output_format srt --output_dir "out" 2>&1 |
      ForEach-Object { if ("$_" -match 'Warning|FP16|usage:') {} else { Write-Host "        $_" -ForegroundColor DarkGray } }
    if (-not (Test-Path $srt)) { Die "Whisper did not produce $srt (run it manually to see the error)" }
    Ok "$srt"
  }

} else {
  Say "`n[2/5] Step 5 - SKIPPED (no subtitles for $Lang)"
  if (Test-Path $srt) { Remove-Item $srt }  # avoid a stale SRT sneaking into 7A
}

# --- SUBTITLE REVIEW CHECKPOINT (human approval before burn-in) --------------
# Catches grammar/transcription errors BEFORE they are burned into the video.
if ($useSubs -and -not $NoReview) {
  Write-Host "`n--------------------------------------------------------------" -ForegroundColor Yellow
  Write-Host " REVIEW SUBTITLES before they are burned into the reel:" -ForegroundColor Yellow
  Write-Host "   $srt" -ForegroundColor Yellow
  if (Get-Command code -ErrorAction SilentlyContinue) {
    & code $srt   # open in VS Code for proofreading
    Write-Host "   (opened in VS Code -- edit + SAVE, then return here)" -ForegroundColor DarkGray
  } else {
    Write-Host "   (open it in your editor, fix any errors, save)" -ForegroundColor DarkGray
  }
  Write-Host "--------------------------------------------------------------" -ForegroundColor Yellow
  $ans = Read-Host "Press ENTER to burn these subtitles, or type S to skip subtitles for this reel"
  if ($ans -match '^[Ss]') {
    $useSubs = $false
    Write-Host "  -> subtitles will be SKIPPED for this reel." -ForegroundColor DarkGray
  } else {
    Ok "subtitles approved"
  }
}

# --- STEP 6: build background -- ORDERED scenes (animated) OR random 3 -------
$animated = ($Scenes -and $Scenes.Count -gt 0)
if ($animated) {
  Say "`n[3/5] Step 6 - stitching $($Scenes.Count) ordered scene clips (animated reel)..."
  $picked = foreach ($name in $Scenes) {
    $clip = Join-Path $normDir $name
    if (-not (Test-Path $clip)) { Die "scene clip not found: $clip" }
    Get-Item $clip
  }
} else {
  Say "`n[3/5] Step 6 - building background (3 random clips)..."
  $picked = $clips | Get-Random -Count 3
}
$picked | ForEach-Object { Write-Host "        + $($_.Name)" -ForegroundColor DarkGray }

# resolution guard for RANDOM mode only (it uses -c copy, needs pre-normalized clips).
# Animated mode normalizes each clip below, so it tolerates any source res/fps.
if (-not $animated) {
  $badRes = @()
  foreach ($c in $picked) {
    $dim = (& ffprobe -hide_banner -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $c.FullName 2>$null).Trim()
    if ($dim -ne '1080x1920') { $badRes += "$($c.Name) is $dim (need 1080x1920)" }
  }
  if ($badRes.Count -gt 0) {
    Write-Host "`nClip(s) wrong resolution -- normalize before use:" -ForegroundColor Red
    $badRes | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    Die "non-1080x1920 clip in the random pick"
  }
}

$concatList = "out\backgrounds\new\concat-$base.txt"
if ($animated) {
  # Normalize EACH clip to identical 1080x1920 @ 30fps BEFORE concat. This is the
  # robust fix for the framerate/resolution traps: a stray 24fps or off-size clip
  # can no longer flash-by or distort, because every clip is rebuilt uniform first.
  $tmps = @()
  $idx = 0
  foreach ($c in $picked) {
    $idx++
    $tmp = "out\backgrounds\new\_norm-$base-$idx.mp4"
    $rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-i",$c.FullName,
      "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
      "-c:v","libx264","-pix_fmt","yuv420p","-r","30","-an",$tmp)
    if (-not (Test-Path $tmp)) { Die "failed to normalize $($c.Name)" }
    $tmps += $tmp
  }
  $tmps | ForEach-Object { "file '$((Resolve-Path $_).Path -replace '\\','/')'" } |
    Out-File -Encoding ASCII -FilePath $concatList
  # all temps now identical -> safe -c copy concat
  $rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",$concatList,"-c","copy",$bgMixed)
  $tmps | ForEach-Object { Remove-Item $_ -ErrorAction SilentlyContinue }
} else {
  $picked | ForEach-Object { "file '$($_.FullName -replace '\\','/')'" } |
    Out-File -Encoding ASCII -FilePath $concatList
  $rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",$concatList,"-c","copy",$bgMixed)
}
Remove-Item $concatList -ErrorAction SilentlyContinue
if (-not (Test-Path $bgMixed)) { Die "background concat failed ($bgMixed not created)" }
Ok "$bgMixed"

# --- STEP 7: final merge (7A with subs / 7B without) -------------------------
Say "`n[4/5] Step 7 - final merge (bg + narration + nasheed$(if($useSubs){' + subs'}))..."

# choose nasheed (specific or random from local library)
$chosen = if ($Nasheed) { "out\backgrounds\$Nasheed" } else { ($nasheeds | Get-Random).FullName }
Write-Host "        nasheed: $(Split-Path $chosen -Leaf)" -ForegroundColor DarkGray

$title = "drawtext=text='Hadith Reels':fontsize=28:fontcolor=white:shadowcolor=black@0.9:shadowx=2:shadowy=2:box=1:boxcolor=black@0.4:boxborderw=8:x=(w-text_w)/2:y=30:font=Arial"

if ($useSubs) {
  $subStyle = "force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2,MarginV=80'"
  $vf = "subtitles='$($srt -replace '\\','/')':$subStyle,$title"
} else {
  $vf = $title
}

$rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y",
  "-stream_loop","-1","-i",$bgMixed,
  "-i",$narr,
  "-stream_loop","-1","-i",$chosen,
  "-filter_complex","[1:a]volume=1.0[narration];[2:a]volume=0.25[music];[narration][music]amix=inputs=2:duration=first[aout]",
  "-vf",$vf,
  "-map","0:v","-map","[aout]",
  "-c:v","libx264","-c:a","aac","-shortest","-movflags","+faststart",
  $reel)

if (-not (Test-Path $reel)) { Die "final merge failed ($reel not created)" }

# --- STEP 8: verify ----------------------------------------------------------
Say "`n[5/5] Done."
$info = Get-Item $reel
$mb   = [math]::Round($info.Length/1MB,1)
Ok "$reel  ($mb MB)"
if ($mb -gt 50) {
  Write-Host "  WARN  $mb MB exceeds Telegram's 50MB native limit -- add -b:v 3000k or trim." -ForegroundColor Yellow
}
(& ffprobe -hide_banner -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $reel 2>$null) | ForEach-Object { Write-Host "        resolution: $_" -ForegroundColor DarkGray }

Write-Host "`nNEXT: watch it, then post to @SahihHadithReels (human approval per hard rules)." -ForegroundColor Cyan
if ($Open) { Start-Process $reel }
