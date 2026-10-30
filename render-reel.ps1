<#
================================================================================
 render-reel.ps1  —  Hadith Reels: automated render pipeline (Steps 4-7)
================================================================================
 Replaces the manual FFmpeg/Whisper drudgery in reel-creation-pipeline.md.

 NAMING CONVENTION (required):
   out\work\{style}\{slug}\{lang}\{style}-{lang}-{slug}-story.mp3   <- from admin (you save this)
   out\work\{style}\{slug}\{lang}\{style}-{lang}-{slug}-moral.mp3   <- from admin (you save this)
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
   -Draft       (optional) source text for the subtitle validator (default draft.txt)
                It MUST hold this language's S:/M: blocks — a mismatch shows
                as ~0.01 similarity, which is the validator telling you the
                draft was never re-synced after the last admin edit.
   -NoReview    (optional) skip the subtitle proofreading PAUSE. It does NOT
                skip the validator, which still runs and prints (P188).
   -Open        (optional) auto-play the finished reel
   -ValidateOnly (optional) run step 0 and exit — smoke test for the pre-push hook
================================================================================
#>

param(
  [Parameter(Mandatory)][ValidateSet('adults','kids')][string]$Style,
  [Parameter(Mandatory)][ValidateSet('en','ru','ar','uz','tj')][string]$Lang,
  [Parameter(Mandatory)][string]$Slug,
  [string]$Nasheed,
  [string[]]$Scenes,     # ordered clip names (in normalized\) for an ANIMATED reel; omit = random 3
  [string]$Draft = 'draft.txt',   # source text for the subtitle validator
  [switch]$ForceNoSubs,
  [switch]$FitScenes,     # trim each scene clip to narration/clips so ALL of them appear
  [switch]$NoReview,
  [switch]$Open,
  [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
# Native tools (ffmpeg/whisper) write normal output to stderr; PowerShell can mistake that
# for a terminating error. Helper runs a native command and only fails on a real exit code.
function Run($exe, [string[]]$cmdArgs) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  # P154: this was `2>&1 | Out-Null` - every ffmpeg error, in every step, was
  # discarded. When the final merge started failing, nothing could say why,
  # because the only thing that could was being thrown away. Captured now and
  # printed ONLY on a non-zero exit: quiet when it works, loud when it does not.
  $out = & $exe @cmdArgs 2>&1
  $code = $LASTEXITCODE
  $ErrorActionPreference = $prev
  if ($code -ne 0) {
    Write-Host "  --- $exe exit $code ---" -ForegroundColor DarkYellow
    $out | Select-Object -Last 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkYellow }
  }
  return $code
}

# --- SRT hygiene (P154) ------------------------------------------------------
# Two problems, one place. A caption was once pasted into an open SRT tab in
# VS Code and saved; libass then reported "Unable to open" and, because Run
# discarded ffmpeg's stderr and the merge check only tested whether the output
# EXISTED, three days of renders reported success while silently reusing the
# previous file. And Whisper cuts at pauses, so a long sentence becomes one
# 17-word cue that wraps to five lines and covers a third of the frame.
function Assert-ValidSrt([string]$path) {
  $first = (Get-Content $path -TotalCount 1)
  if ($null -eq $first -or $first -notmatch '^\uFEFF?\d+\s*$') {
    Write-Host "  first line: $first" -ForegroundColor Red
    Die "$path is not a subtitle file - an SRT starts with a cue number. Delete it and re-run to regenerate."
  }
}

function ConvertFrom-SrtTime([string]$t) {
  $x = $t.Trim() -split '[:,]'
  return [TimeSpan]::FromMilliseconds([int]$x[0]*3600000 + [int]$x[1]*60000 + [int]$x[2]*1000 + [int]$x[3])
}

function ConvertTo-SrtTime([TimeSpan]$ts) {
  return ('{0:00}:{1:00}:{2:00},{3:000}' -f [int]$ts.TotalHours, $ts.Minutes, $ts.Seconds, $ts.Milliseconds)
}

# Splits at a punctuation boundary nearest the midpoint, falling back to the
# midpoint itself. Timing divides by CHARACTER COUNT, not word count - words
# differ enough in length that word-count splitting drifts audibly.
function Split-Cue($start, $end, [string]$text, [int]$maxWords, [double]$minSec) {
  $words = $text -split '\s+' | Where-Object { $_ }
  $dur = ($end - $start).TotalSeconds
    # P154 tuning: also refuse to split when either half would fall below six
  # words. RU produced two 2-word tails - "же правилу" and "сверх предписанного"
  # - because the midpoint fallback ignores grammar and the recursion re-splits
  # each half. A floor is simpler than teaching it syntax.
  if ($words.Count -le $maxWords -or $dur -lt ($minSec * 2) -or $words.Count -lt 12) {
    return ,([pscustomobject]@{ Start = $start; End = $end; Text = $text })
  }
  $mid = [int]($words.Count / 2)
  $best = -1; $bestDist = [int]::MaxValue
  for ($i = 0; $i -lt $words.Count - 1; $i++) {
    if ($words[$i] -match '[,;:.!?]$') {
      $d = [math]::Abs($i - $mid)
      if ($d -lt $bestDist) { $bestDist = $d; $best = $i }
    }
  }
  if ($best -lt 0) { $best = $mid - 1 }
  $left  = ($words[0..$best] -join ' ')
  $right = ($words[($best + 1)..($words.Count - 1)] -join ' ')
  $ratio = $left.Length / [double]($left.Length + $right.Length)
  $cut = $start.Add([TimeSpan]::FromSeconds($dur * $ratio))
  return (@(Split-Cue $start $cut $left $maxWords $minSec) + @(Split-Cue $cut $end $right $maxWords $minSec))
}

function Split-LongCues([string]$path, [int]$maxWords = 10) {
  Assert-ValidSrt $path
  $raw = (Get-Content $path -Raw -Encoding UTF8).Trim()
  $blocks = [regex]::Split($raw, '\r?\n\s*\r?\n') | Where-Object { $_ -match '\S' }
  $out = @()
  foreach ($b in $blocks) {
    $lines = $b -split '\r?\n'
    if ($lines.Count -lt 3) { continue }
    $t = $lines[1] -split '-->'
    $start = ConvertFrom-SrtTime $t[0]
    $end   = ConvertFrom-SrtTime $t[1]
    $text  = (($lines[2..($lines.Count - 1)]) -join ' ').Trim()
    $out += Split-Cue $start $end $text $maxWords 0.8
  }
  $sb = New-Object System.Text.StringBuilder
  for ($i = 0; $i -lt $out.Count; $i++) {
    [void]$sb.AppendLine([string]($i + 1))
    [void]$sb.AppendLine("$(ConvertTo-SrtTime $out[$i].Start) --> $(ConvertTo-SrtTime $out[$i].End)")
    [void]$sb.AppendLine($out[$i].Text)
    [void]$sb.AppendLine()
  }
  # No BOM: libass is happier without one and VS Code will not add it back
  # unless someone saves over the file.
  [System.IO.File]::WriteAllText((Resolve-Path $path).Path, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
  return @{ Before = $blocks.Count; After = $out.Count }
}

# --- operate from the repo root (where this script lives) ---------------------
Set-Location $PSScriptRoot

function Say  ($m){ Write-Host $m -ForegroundColor Cyan }
function Ok   ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die  ($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

$base    = "$Style-$Lang-$Slug"
$workDir = "out\work\$Style\$Slug\$Lang"
New-Item -ItemType Directory -Force $workDir | Out-Null

$story   = "$workDir\$base-story.mp3"
$moral   = "$workDir\$base-moral.mp3"
$narr    = "$workDir\$base-narration.mp3"
$srt     = "$workDir\$base-narration.srt"
$bgMixed = "$workDir\$base-bg-mixed.mp4"
$reel    = "$workDir\$base-reel.mp4"

# P229: the reel runs ONE SECOND longer than the narration (P143 pads the
# narration so the music does not cut dead on the last syllable). -FitScenes
# sized the background off the UNPADDED narration, so the last second had no
# background left and the video looped back to scene 1 - #6423 ended on a
# 1s flash of its opening gate instead of the closing hearth. Two correct
# fixes, each hard-coding its own 1.0. One constant now, used by all three.
$tailPad = 1.0
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

# nasheeds: lane-eligible *.mp3 directly under out\backgrounds\ (P162)
# Filter here rather than let the P117 gate at step 7 kill the render after all
# the ffmpeg work. Eligibility comes from the registry (P168), not the
# filename — a retired bed used to be drawn and then blocked.
$approved = @(& python "scripts\audit-assets.py" --list --lane $Style --section audio)
if ($LASTEXITCODE -ne 0 -or $approved.Count -eq 0) {
  $problems += "could not read the approved nasheed list from the registry (lane: $Style)"
  $approved = @()
}
$nasheeds = @(Get-ChildItem "out\backgrounds\*.mp3" -ErrorAction SilentlyContinue |
              Where-Object { $approved -contains $_.Name })
if ($nasheeds.Count -lt 1) { $problems += "no lane-eligible nasheed .mp3 in out\backgrounds\ (lane: $Style)" }
if ($Nasheed -and -not (Test-Path "out\backgrounds\$Nasheed")) {
  $problems += "requested nasheed not found: out\backgrounds\$Nasheed"
}

# P162: pick the nasheed and gate it HERE, not at step 7. The pick used to sit
# after the background mix, so a lane-rejected bed killed the render only after
# all the ffmpeg work had run -- and the picker itself could never be tested
# without a full paid render.
$chosen = $null
# P251: defaults, overridden from the registry once a bed is chosen.
$nasheedVol    = 0.12
$nasheedVolStr = '0.12'
$gainNote      = ''
if ($nasheeds.Count -ge 1) {
  $stateFile = "out\backgrounds\.last-used.json"
  if ($Nasheed) {
    $chosen = "out\backgrounds\$Nasheed"
    $avoided = 'n/a (override)'
  } else {
    $state = @{}
    if (Test-Path $stateFile) {
      try { (Get-Content $stateFile -Raw | ConvertFrom-Json).PSObject.Properties |
              ForEach-Object { $state[$_.Name] = $_.Value } }
      catch { Write-Host "  last-used state unreadable, ignoring" -ForegroundColor DarkGray }
    }
    $last = $state[$Style]
    $cand = @($nasheeds | Where-Object { $_.Name -ne $last })
    if ($cand.Count -eq 0) { $cand = $nasheeds }
    $pick = $cand | Get-Random
    $chosen = $pick.FullName
    $avoided = if ($last) { $last } else { 'none' }
    $state[$Style] = $pick.Name
    # P249: written HERE until 2026-10-25, at pick time. An aborted render then
    # burned the slot - a bed counted as used by a reel that does not exist, and
    # the next render avoided something nothing had ever shipped. Deferred to
    # STEP 7b, after the merge returns 0.
  }
  # P251: the adults mix is ONE level for every bed (narration 1.4 / nasheed
  # 0.12, P171) and the beds are not one loudness. Measured 2026-10-16: the
  # eight Aswati masters run -13.35 to -20.22 LUFS against light-of-my-heart-bg
  # at -13.38, the bed the 0.12 was tuned on, so the quiet ones land
  # under-audible. The operator heard it; no gate measures loudness. `gain` in
  # the registry is the per-bed multiplier - absent means 1.0, so every bed
  # without one is unchanged.
  try {
    $audioReg = (Get-Content "assets\asset-registry.json" -Raw | ConvertFrom-Json).audio
    $bedName  = Split-Path $chosen -Leaf
    $entry    = $audioReg.PSObject.Properties | Where-Object { $_.Name -eq $bedName }
    if ($entry -and ($entry.Value.PSObject.Properties.Name -contains 'gain')) {
      $g = [double]$entry.Value.gain
      if ($g -gt 0 -and $g -le 4) {
        $nasheedVol = [math]::Round(0.12 * $g, 4)
        $gainNote   = ", gain x$g -> vol $nasheedVol"
      } else {
        Write-Host "  registry gain out of range for ${bedName}: $g - using 0.12" -ForegroundColor Yellow
      }
    }
  } catch { Write-Host "  could not read the bed gain from the registry - using 0.12" -ForegroundColor DarkGray }
  # InvariantCulture: a comma-decimal locale would hand ffmpeg volume=0,2640
  # and the filter graph would not parse.
  $nasheedVolStr = $nasheedVol.ToString([System.Globalization.CultureInfo]::InvariantCulture)
  Write-Host "  nasheed: $(Split-Path $chosen -Leaf)  (lane: $Style, $($nasheeds.Count) beds, avoided: $avoided$gainNote)" -ForegroundColor DarkGray

  # P201: the tracker has a Nasheed column per reel and the asset-reuse audit
  # depends on it, but .last-used.json keeps ONE value per lane and the next
  # render overwrites it. On the R110-R113 set three of the four bed names
  # survived nowhere but a console buffer that was then closed. The picker is
  # the only thing that knows; it writes it down, beside the output, now.
  # WriteAllText and not Set-Content -Encoding utf8: on PS 5.1 that writes a
  # BOM and this file is read back as JSON (P186).
  # P249: the sidecar used to be written HERE, at pick time, and it is
  # EVIDENCE - on 2026-10-24 it was what established which bed a published reel
  # carried, after a Content ID claim had been attributed to the wrong one. A
  # record a failed run can write is not evidence, and -ValidateOnly rewrote it
  # while promising to write nothing. Moved to STEP 7b.

  # P117: asset lane gate. A bed approved for the other lane is a lookup
  # failure, not a judgement call - twice on 2026-08-15 the picker crossed lanes.
  $assetName = Split-Path $chosen -Leaf
  $auditOut  = & python "scripts\audit-assets.py" --check $assetName --lane $Style 2>&1
  if ($LASTEXITCODE -ne 0) { $problems += "nasheed rejected by the asset registry: $assetName - $auditOut" }
}

# guard: don't silently overwrite an existing final reel
if (Test-Path $reel) {
  Write-Host "  NOTE  $reel already exists and will be overwritten." -ForegroundColor Yellow
}

# P319: the matn-vs-number GATE. Bukhari #3559 shipped two reels whose stored
# Arabic belonged to reference 3759, 3760 - real Bukhari, right narrator, wrong
# number - and nothing in this pipeline could see it for roughly five months.
# verify-matn-number.py was written after that and swept all 71 rows BY HAND.
# Running a check by hand is not a gate: it protects only the sets somebody
# remembered. So it runs here, at STEP 0, before the render and before any paid
# step. --gate blocks on MISMATCH and ALSO on 'could not check', per HARD RULE 4.
$hadithNumber = ($Slug -split '-')[-1]
if ($hadithNumber -match '^\d+$') {
  Say "`n      matn-vs-number gate (P319): #$hadithNumber"
  $matnOut  = & python "scripts\verify-matn-number.py" --number $hadithNumber --gate 2>&1
  $matnCode = $LASTEXITCODE
  if ($matnCode -ne 0) {
    $matnOut | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkYellow }
    $problems += "matn-vs-number gate BLOCKED #$hadithNumber (exit $matnCode) - " +
                 "the row's stored Arabic is not confirmed to sit at the number it " +
                 "cites. See P306, P319. Fix the library row before rendering."
  } else {
    Ok "matn sits at the cited number (#$hadithNumber)"
  }
} else {
  $problems += "could not derive a hadith number from -Slug '$Slug', so the " +
               "matn-vs-number gate (P319) could not run - and a gate that " +
               "cannot run is not a pass."
}

if ($problems.Count -gt 0) {
  Write-Host "`nCannot render -- fix these first:" -ForegroundColor Red
  $problems | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
  exit 1
}
Ok "story + moral present; ffmpeg ready; $($clips.Count) bg clips; $($nasheeds.Count) nasheeds"

  # P282: draft.txt is the text stt-validate compares the burned subtitles
  # against, and nothing enforced that it holds THIS language's words. It has
  # failed in both directions - a stale same-language draft scoring 0.958 while
  # a whole clause differed, and the EN blocks sitting in place through a RU
  # render, which scored correct Russian subtitles at 0.291 with "source is
  # latin" on every cue. The first shape is the dangerous one, which is why
  # this compares against the DATABASE rather than a threshold on the SRT.
  if (Test-Path -LiteralPath $Draft) {
    $prevPyIO = $env:PYTHONIOENCODING
    $env:PYTHONIOENCODING = 'utf-8'
    & python "scripts\check-draft-sync.py" --lang $Lang --slug $Slug --draft $Draft --style $Style
    $draftRc = $LASTEXITCODE
    $env:PYTHONIOENCODING = $prevPyIO
    if ($draftRc -ne 0) {
      Die "$Draft is not in sync with the row being rendered (P282) - see above. Re-sync it before TTS: the subtitle validator's authority rests entirely on this file."
    }
  } else {
    Say "  NOTE  $Draft not found - draft sync check skipped (P282)."
  }

  # P302 and the preflight gap: scene clips were resolved and registry-checked
  # in Step 6, which runs AFTER Step 4 concatenates the narration and, on
  # en/ru/ar, after Whisper. On 2026-10-24 the Tajik leg died at [3/5] with the
  # narration already built, on a -Scenes list that had bound as one string;
  # #1903 EN failed twice the same way in October, once on unregistered clips
  # after Whisper had run. All of it is knowable before any slow or paid work.
  # This VALIDATES ONLY - Step 6 still resolves and still gates, so the render
  # path is unchanged and this can fail earlier, never differently.
  if ($Scenes -and $Scenes.Count -gt 0) {
    $sceneProblems = @()
    foreach ($name in $Scenes) {
      if ($name -like '*,*') {
        # P302: PowerShell splits a comma list at the PARSER, so -Scenes a,b
        # becomes an array when typed and stays one string when passed through
        # Start-Process -ArgumentList with -File. Say which it is.
        $sceneProblems += "-Scenes arrived as ONE string rather than a list (P302) - launch with -Command, not -File: $name"
        continue
      }
      $clip = Join-Path $normDir $name
      if (-not (Test-Path $clip)) { $clip = Join-Path "out\backgrounds\new" $name }
      if (-not (Test-Path $clip)) {
        $sceneProblems += "scene clip not found in out\backgrounds\new\normalized\ or out\backgrounds\new\: $name"
        continue
      }
      $preAudit = & python "scripts\audit-assets.py" --check $name --lane $Style 2>&1
      if ($LASTEXITCODE -ne 0) {
        $preAudit | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray }
        $sceneProblems += "scene clip rejected by the asset registry (P121): $name"
      }
    }
    if ($sceneProblems.Count -gt 0) {
      Write-Host "`nCannot render -- fix these first:" -ForegroundColor Red
      $sceneProblems | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
      exit 1
    }
    Ok "$($Scenes.Count) scene clip(s) resolved and registry-approved"
  }

  if ($ValidateOnly) {
    # P288: this switch is documented as "run step 0 and exit - smoke test for
    # the pre-push hook". It was declared in param() and referenced NOWHERE
    # else, so it silently performed a FULL render instead. Run against a
    # published slug it overwrote that reel with three random background clips
    # and a different nasheed. A no-op flag is worse than a missing one,
    # because the doc promised a safe check and the name says so twice.
    Say "`n  -ValidateOnly: prerequisites OK, exiting before Step 4. Nothing written."
    exit 0
  }

# --- STEP 4: concat story + moral (0.5s pause, P135) into one narration ------
Say "`n[1/5] Step 4 - concatenating story + moral narration..."
$rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y","-i",$story,"-i",$moral,
  # P135: pad was 1s, but ElevenLabs leaves trailing silence on the story MP3,
  # so the perceived gap ran to ~2s. 0.5 here reads as ~1.5s in the finished
  # reel. The real fix is trimming the source silence before padding
  # (silenceremove) — deferred, since that needs testing across languages.
  "-filter_complex","[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
  "-map","[out]",$narr)
if (-not (Test-Path $narr)) { Die "narration concat failed ($narr not created)" }
Ok "$narr ($([math]::Round((Get-Item $narr).Length/1KB)) KB)"

# --- STEP 5: subtitles (conditional by language) -----------------------------
if ($useSubs) {
  Say "`n[2/5] Step 5 - generating subtitles via Whisper ($Lang)..."
  # P211: this cache must invalidate when the NARRATION changes, and it must
  # survive a hand-edit, which is why it exists: the operator corrects the SRT
  # at the review pause, and re-running the render must not throw that away.
  #
  # It was a bare Test-Path, so a re-render after a per-block re-narration
  # (P125) kept the PREVIOUS run's SRT and never transcribed the new audio.
  # Caught on at-tirmidhi-3895 EN: the story mp3 was re-narrated to replace a
  # mangled honorific, the new audio was correct, and the stale SRT still
  # carried the mangled form - which would have been burned into the reel,
  # contradicting its own soundtrack.
  #
  # mtime cannot express this: restore-srt-casing.py rewrites the SRT after
  # Whisper, so the stale file was NEWER than the audio it failed to describe.
  # Fingerprint the SOURCE mp3s instead - they change only on re-narration.
  # ($narr is rebuilt by step 4 every run, so it can never anchor a cache.)
  $srtStamp = "$srt.src"
  $fp = "{0}:{1}|{2}:{3}" -f (Get-Item $story).Length, (Get-Item $story).LastWriteTimeUtc.Ticks,
                             (Get-Item $moral).Length, (Get-Item $moral).LastWriteTimeUtc.Ticks
  $srtFresh = (Test-Path $srt) -and (Test-Path $srtStamp) -and
              ((Get-Content $srtStamp -Raw -ErrorAction SilentlyContinue).Trim() -eq $fp)
  if ((Test-Path $srt) -and -not $srtFresh) {
    Say "   narration changed since this SRT was made - discarding it (P211)"
    Remove-Item $srt -Force
  }
  if ($srtFresh) {
    Ok "subtitles already present and still match the narration - skipping Whisper"
  } else {
    # Build args as an array of literal strings; pass the path quoted to avoid
    # PowerShell mangling the backslash path into whisper.exe (which prints usage).
    # P083: whisper writes a harmless "FP16 not supported on CPU" warning to stderr.
    # Under $ErrorActionPreference='Stop' that stderr line TERMINATES the script, so we
    # flip to 'Continue' around the call (same pattern as Run()) and rely on the SRT check.
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    # P100: whisper prints progress lines to stdout; on Windows the console codec is
    # CP1252, so Cyrillic output raises UnicodeEncodeError inside transcribe.py and the
    # transcription is abandoned. Forcing UTF-8 on the child process fixes it.
    $prevPyIO = $env:PYTHONIOENCODING
    $env:PYTHONIOENCODING = 'utf-8'
    # P252: PYTHONIOENCODING fixes the CHILD's encoder. This fixes the PARENT's
    # DECODER. PowerShell decodes a piped child's bytes using
    # [Console]::OutputEncoding - CP437 on PS 5.1 - so a correctly-UTF-8 child
    # whose output is PIPED still arrives mangled. restore-srt-casing.py prints
    # straight to the console and reads fine; everything piped through
    # ForEach-Object did not, which made the RU/UZ/TJ lint findings unreadable.
    $prevConsoleEnc = [Console]::OutputEncoding
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    & whisper "$narr" --model small --language $Lang --output_format srt --output_dir "$workDir" 2>&1 |
      ForEach-Object { if ("$_" -match 'Warning|FP16|usage:') {} else { Write-Host "   $_" -ForegroundColor DarkGray } }
    $env:PYTHONIOENCODING = $prevPyIO
    [Console]::OutputEncoding = $prevConsoleEnc
    $ErrorActionPreference = $prevEAP
    if (-not (Test-Path $srt)) { Die "Whisper did not produce $srt (run it manually to see the error)" }
    # P211: stamp the sources this transcript was made from, so a later run can
    # tell a hand-edited SRT (keep) from one describing replaced audio (discard).
    [System.IO.File]::WriteAllText((Join-Path $PWD $srtStamp), $fp, (New-Object System.Text.UTF8Encoding($false)))
    Ok "$srt"
  }

} else {
  Say "`n[2/5] Step 5 - SKIPPED (no subtitles for $Lang)"
  if (Test-Path $srt) { Remove-Item $srt }  # avoid a stale SRT sneaking into 7A
}

# P154: split long cues BEFORE the review gate, so what is proofread is
# exactly what gets burned in. Whisper cuts at pauses, so a long sentence
# arrives as one 17-word cue that wraps to five lines and covers a third of
# the frame. Shorter cues read better than a smaller font does.
if ($useSubs) {
  $splitStats = Split-LongCues $srt 12
  if ($splitStats.After -gt $splitStats.Before) {
    Ok "cues split for readability: $($splitStats.Before) -> $($splitStats.After)"
  }
}

# --- RESTORE WHAT WHISPER COULD NOT HEAR (P200) -----------------------------
# Whisper transcribes SOUND. Capitalisation and Russian yo are properties of
# the TEXT and were never given to it, so divine pronouns come back lowercased
# and yo flattened on EVERY en/ru reel. On the #2759 set that was four of five
# RU findings and two of three EN ones - all of them mechanical, all corrected
# by hand at the pause below. This runs BEFORE the validator so the validator
# reports only what actually needs a human: word-boundary errors, mishearings,
# punctuation. It takes its spelling from $Draft, never from a word list.
if ($useSubs) {
  $prevPyIO = $env:PYTHONIOENCODING
  $env:PYTHONIOENCODING = 'utf-8'
  & python "scripts\restore-srt-casing.py" --srt "$srt" --source "$Draft" --lang $Lang
  $restoreRc = $LASTEXITCODE
  $env:PYTHONIOENCODING = $prevPyIO
  if ($restoreRc -eq 2) {
    Write-Host "  casing restore could not run - correct the SRT by hand at the pause" -ForegroundColor Yellow
  }
}

# --- SUBTITLE VALIDATION (automatic, before the human sees it) --------------
# P188: stt-validate.py existed for seven weeks and nothing called it. It was
# documented in CLAUDE.md as Workflow F, in FEATURES.md, in the README and in
# two agent SKILLs — and it ran only when somebody remembered. Over that time
# it caught three defects that human review had already passed:
#   R039  «Аллахам» still burned into RU cue 2 AFTER hand-correction
#   R043  an SRT whose structure the editing itself had broken, 9 cues -> 8
#   R051  narration said «это второе, а не первое», the draft stopped at
#         «это второе» — a three-word divergence nobody saw
# Same shape as P119, P126, P185 and P187: a correct check with no caller.
# It reads no network and costs nothing, so it runs unconditionally whenever
# there are subtitles — including under -NoReview, where there is no human
# about to look and the automated check matters MORE, not less.
if ($useSubs) {
  if (-not (Test-Path $Draft)) {
    Write-Host "`n  [skip] subtitle validator: no $Draft to compare against." -ForegroundColor DarkYellow
    Write-Host "         Pass -Draft <file> holding this language's S:/M: blocks." -ForegroundColor DarkYellow
  } else {
    Say "`n[2b/5] Validating subtitles against $Draft..."
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $prevPyIO = $env:PYTHONIOENCODING
    $env:PYTHONIOENCODING = 'utf-8'      # P100: Cyrillic through a CP1252 console
    # P252: PYTHONIOENCODING fixes the CHILD's encoder. This fixes the PARENT's
    # DECODER. PowerShell decodes a piped child's bytes using
    # [Console]::OutputEncoding - CP437 on PS 5.1 - so a correctly-UTF-8 child
    # whose output is PIPED still arrives mangled. restore-srt-casing.py prints
    # straight to the console and reads fine; everything piped through
    # ForEach-Object did not, which made the RU/UZ/TJ lint findings unreadable.
    $prevConsoleEnc = [Console]::OutputEncoding
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    & python "scripts\stt-validate.py" --srt "$srt" --source "$Draft" --lang $Lang --narration "$narr" 2>&1 |
      ForEach-Object { Write-Host "   $_" }
    $sttRc = $LASTEXITCODE
    $env:PYTHONIOENCODING = $prevPyIO
    [Console]::OutputEncoding = $prevConsoleEnc
    $ErrorActionPreference = $prevEAP
    if ($sttRc -ne 0) {
      # Warn-only by design: the validator is a reader's aid, not a gate. The
      # human at the checkpoint decides. Under -NoReview there is no human, so
      # say loudly that something was found and nobody was asked.
      if ($NoReview) {
        Write-Host "`n  WARN  the validator reported findings and -NoReview skipped the gate." -ForegroundColor Yellow
        Write-Host "        Those subtitles are about to be burned in unreviewed." -ForegroundColor Yellow
      }
    }
  }
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
    # P217: generate-scene.ps1 writes to new\, this read normalized\ only, and
    # the gap between them has blocked three separate sets (June #1520, 8/11 #1,
    # 8/16 #527) on a Move-Item nobody remembers. ANIMATED mode normalizes every
    # clip below - see the resolution-guard note - so it never needed
    # pre-normalized input: the folder was a LOCATION, not a state. Look in both.
    # The registry gate immediately below is the real check, not the directory.
    # RANDOM mode still reads normalized\ only, because it stitches with -c copy
    # and genuinely requires clips that are already 1080x1920.
    $clip = Join-Path $normDir $name
    if (-not (Test-Path $clip)) {
      $alt = Join-Path "out\backgrounds\new" $name
      if (Test-Path $alt) {
        $clip = $alt
        Write-Host "        (resolved from new\ rather than normalized\ - P217)" -ForegroundColor DarkGray
      }
    }
    if (-not (Test-Path $clip)) {
      Die "scene clip not found in out\backgrounds\new\normalized\ or out\backgrounds\new\: $name"
    }
    # P121: the same lane gate the nasheed gets. Before this, -Scenes clips
    # reached the render unchecked -- eight reels shipped over clips the audit
    # itself reported as unregistered. A gate protects the inputs it is NAMED.
    $clipAudit = & python "scripts\audit-assets.py" --check $name --lane $Style 2>&1
    if ($LASTEXITCODE -ne 0) {
      $clipAudit | ForEach-Object { Write-Host "        $_" -ForegroundColor Red }
      Die "scene clip rejected by the asset registry: $name"
    }
    Get-Item $clip
  }
} else {
  Say "`n[3/5] Step 6 - building background (3 random clips)..."
  # P237: the gate -Scenes got in P121 and the nasheed got in P168, which this
  # path never had. It globs normalized\*.mp4 and draws three, so a clip that is
  # unregistered - or RETIRED, like vocal-hamd-kids-01 was on the audio side -
  # could reach a reel simply by sitting in the folder. Low traffic is not a
  # gate: every recent set passes explicit -Scenes, which is exactly why nobody
  # would notice this one failing.
  # Draw from the APPROVED set rather than checking after the draw, so a
  # retired clip cannot be picked and then re-rolled around.
  $clipApproved = @(& python "scripts\audit-assets.py" --list --lane $Style --section scenes)
  if ($LASTEXITCODE -ne 0 -or $clipApproved.Count -lt 1) {
    Die "could not read the approved clip list from the registry (lane: $Style). " +
        "Pass -Scenes explicitly, or fix the registry."
  }
  $eligible = @($clips | Where-Object { $clipApproved -contains $_.Name })
  $skipped  = @($clips | Where-Object { $clipApproved -notcontains $_.Name })
  if ($skipped.Count -gt 0) {
    Write-Host "        skipped (not approved for lane '$Style'): $($skipped.Name -join ', ')" -ForegroundColor DarkGray
  }
  if ($eligible.Count -lt 3) {
    Die "only $($eligible.Count) registry-approved clip(s) in $normDir for lane '$Style' - need 3."
  }
  $picked = $eligible | Get-Random -Count 3
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
  # P194: four 10s clips behind 23s of narration played the first two and part of
  # the third; the closing beat never appeared in the reel at all. The concat is
  # built at full clip length and the final merge truncates to narration, so any
  # reel shorter than clips x duration silently drops its tail. -FitScenes trims
  # each clip to an equal share of the narration instead, so every clip appears.
  # Non-destructive: the masters on disk keep full length for the longer
  # languages in the same set, which still need all 10s.
  $fitDur = $null
  if ($FitScenes) {
    $nd = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $narr)
    $fitDur = [math]::Round(($nd + $tailPad) / $picked.Count, 3)
    Say ("        -FitScenes: {0}s narration / {1} clips -> {2}s per clip" -f [math]::Round($nd,2), $picked.Count, $fitDur)
    # P240: -t TRIMS a clip, it cannot stretch one. If the equal share is
    # longer than the shortest source clip, every clip comes back at its own
    # length, the background is SHORT of the narration, and -stream_loop -1
    # on the merge wraps it back to clip 1 instead of failing - so the reel
    # ends on its opening image with no error anywhere. #6570 UZ: 52.22s of
    # narration over five 10.04s clips asked for 10.644s each, got 50.16s of
    # background against 53.22s of audio, and replayed the lamp for the last
    # 3.0s. EN, RU and TJ in the same set were all under the ceiling and
    # passed, so only the longest language was exposed - and UZ is also the
    # one with no subtitles (P078), i.e. one less reason to watch it closely.
    $shortest = ($picked | ForEach-Object {
      [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $_.FullName)
    } | Measure-Object -Minimum).Minimum
    if ($fitDur -gt $shortest) {
      $needed = [math]::Ceiling(($nd + $tailPad) / $shortest)
      $short  = [math]::Round($shortest, 3)
      $have   = [math]::Round($shortest * $picked.Count, 2)
      $want   = [math]::Round($nd + $tailPad, 2)
      Die "-FitScenes needs ${fitDur}s per clip but the shortest clip is only ${short}s. $($picked.Count) clips cover ${have}s of the ${want}s of audio. Pass $needed scene clips (or fewer, shorter) - otherwise the background wraps to clip 1 and the reel ends on its opening image."
    }

  }
  else {
    # P286: -FitScenes is opt-in for behaviour that should be asserted. It was
    # omitted twice in the Sunan Abu Dawud #1488 set and the RU reel shipped
    # showing roughly 2.5 of its 4 clips, live on four platforms before anyone
    # noticed. P194 describes the drop itself; what was missing was anything
    # that REFUSES. This does not second-guess a deliberate full-length render -
    # it fires only when the arithmetic says clips will actually be lost.
    $nd  = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $narr)
    $acc = 0.0
    $shown = 0
    foreach ($c in $picked) {
      if ($acc -ge $nd) { break }
      $acc += [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $c.FullName)
      $shown++
    }
    if ($shown -lt $picked.Count) {
      $ndr = [math]::Round($nd, 2)
      Die "$($picked.Count) scene clips passed but the narration is only ${ndr}s, so only $shown of them reach the screen - the rest sit past the end of the audio and never render. Pass -FitScenes to trim each clip to an equal share, or pass $shown clips. P194/P286."
    }
  }
  $tmps = @()
  $idx = 0
  foreach ($c in $picked) {
    $idx++
    $tmp = "out\backgrounds\new\_norm-$base-$idx.mp4"
    $ffArgs = @("-hide_banner","-loglevel","error","-y","-i",$c.FullName,
      "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
      "-c:v","libx264","-pix_fmt","yuv420p","-r","30","-an")
    if ($fitDur) { $ffArgs += @("-t","$fitDur") }
    $ffArgs += $tmp
    $rc = Run "ffmpeg" $ffArgs
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
# hard-bound output to narration length (amix can otherwise run past it)
$narrDur = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $narr)
Say "`n[4/5] Step 7 - final merge (bg + narration + nasheed$(if($useSubs){' + subs'}))..."

# P170: the nasheed was chosen and lane-gated in the validation block above
# (P162). A second, older picker used to sit here and ran AFTER it -- so the
# bed that shipped was drawn from an ungated pool with the pre-P168 filename
# filter, the P117 gate checked a different file than the one in the reel, and
# .last-used.json was written twice per render. $chosen is already set.

$title = "drawtext=text='Hadith Reels':fontsize=28:fontcolor=white:shadowcolor=black@0.9:shadowx=2:shadowy=2:box=1:boxcolor=black@0.4:boxborderw=8:x=(w-text_w)/2:y=30:font=Arial"

if ($useSubs) {
  $subStyle = "force_style='FontName=Arial,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2,MarginV=55'"
  # P154: the relative path failed with "Unable to open" - a filtergraph does
  # not resolve paths the way an input argument does. Absolute, forward slashes,
  # and the drive colon escaped as C\: because ':' separates filter arguments.
  # Invisible for three days: Run discarded ffmpeg's stderr and the merge check
  # tested only whether the file existed, which it did, from the previous run.
  # P154: libass could not open the SRT at its real path. Absolute vs relative
  # made no difference and neither did escaping the drive colon - the cause is
  # the SPACE in "Hadith verification AI app", which does not survive the
  # filtergraph parser. Copy to a space-free temp path for the burn only.
  # Invisible for three days: Run discarded ffmpeg's stderr, and the merge
  # check tested only whether the output file existed - which it did, from the
  # previous run.
  $srtTmp = Join-Path $env:TEMP ("hr-" + [IO.Path]::GetFileName($srt))
  Copy-Item $srt $srtTmp -Force
  $srtEsc = ($srtTmp -replace '\\','/').Replace(':', '\:')
  $vf = "subtitles='$srtEsc':$subStyle,$title"
} else {
  $vf = $title
}

$rc = Run "ffmpeg" @("-hide_banner","-loglevel","error","-y",
  "-stream_loop","-1","-i",$bgMixed,
  "-i",$narr,
  "-stream_loop","-1","-i",$chosen,
  # P143: apad on the narration BEFORE amix. amix=duration=first makes [aout]
  # exactly as long as its first input, and -shortest then cuts the video
  # there — so -t alone could not add a tail. Padding the narration makes the
  # shortest stream genuinely 1s longer and all three agree.
  "-filter_complex","[1:a]volume=1.4,apad=pad_dur=$tailPad[narration];[2:a]volume=${nasheedVolStr}[music];[narration][music]amix=inputs=2:duration=first:dropout_transition=0[aout]",
  "-vf",$vf,
  "-map","0:v","-map","[aout]",
  # P143: was -t $narrDur exactly, so the video ended on the last syllable and
  # the loop restarted before the final word and the outro card had any time on
  # screen. On Instagram that reads as the end being cut off. 1s tail.
  "-c:v","libx264","-c:a","aac","-shortest","-t",[string][math]::Round($narrDur + $tailPad,2),"-movflags","+faststart",
  $reel)

# P154: this tested only whether $reel EXISTS. ffmpeg can fail before writing
# anything, in which case -y overwrites nothing, Test-Path finds the PREVIOUS
# run's file and the script reports success - printing that stale file's size
# as confirmation. Three checks now: the exit code, the file, and its age.
if ($rc -ne 0) { Die "final merge failed (ffmpeg exit $rc)" }
if (-not (Test-Path $reel)) { Die "final merge failed ($reel not created)" }
$reelAgeMin = [int]((Get-Date) - (Get-Item $reel).LastWriteTime).TotalMinutes
if ($reelAgeMin -gt 5) {
  Die "final merge wrote nothing - $reel is $reelAgeMin min old. ffmpeg returned 0 but produced no new file."
}

# --- STEP 7b: record what was actually rendered (P249) -----------------------
# Everything below describes a file that now exists and was written by THIS
# run: the merge returned 0, the reel is on disk, and it is newer than five
# minutes (P154's three checks, immediately above).

if ($chosen) {
  # P201: the tracker has a Nasheed column per reel and the asset-reuse audit
  # depends on it, but .last-used.json keeps ONE value per lane and the next
  # render overwrites it. On the R110-R113 set three of the four bed names
  # survived nowhere but a console buffer that was then closed. The picker is
  # the only thing that knows; it writes it down, beside the output.
  try {
    if (-not (Test-Path $workDir)) { New-Item -ItemType Directory -Force -Path $workDir | Out-Null }
    $sidecar = [ordered]@{
      nasheed   = (Split-Path $chosen -Leaf)
      nasheedVol = $nasheedVol
      scenes    = $Scenes
      fitScenes = [bool]$FitScenes
      style     = $Style
      lang      = $Lang
      slug      = $Slug
      rendered  = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    } | ConvertTo-Json
    # P228: WriteAllText is a .NET call, and .NET resolves a RELATIVE path
    # against [Environment]::CurrentDirectory - which PowerShell does NOT
    # update on Set-Location. PS cwd was the repo root while .NET cwd was
    # the user profile, so every write went to C:\Users\<me>\out\work\...
    # and threw. No reel has EVER had a render.json. Absolute path, always.
    # WriteAllText and not Set-Content -Encoding utf8: on PS 5.1 that writes a
    # BOM and this file is read back as JSON (P186).
    $sidecarPath = Join-Path (Resolve-Path $workDir).Path "$base-render.json"
    [System.IO.File]::WriteAllText($sidecarPath, $sidecar,
      (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "  recorded: $base-render.json" -ForegroundColor DarkGray
  } catch {
    Write-Host "  could not write $base-render.json: $($_.Exception.Message)" -ForegroundColor Yellow
  }

  # The lane's last-used bed, for the avoid-a-repeat rule. Only when the picker
  # actually drew one: with -Nasheed the operator chose, and an override should
  # not steer the next random draw.
  if ($state -and $stateFile) {
    try { $state | ConvertTo-Json | Out-File -FilePath $stateFile -Encoding utf8 }
    catch { Write-Host "  could not record last-used nasheed" -ForegroundColor DarkGray }
  }
}

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
