<#
================================================================================
 generate-scene.ps1  —  POC step 2: one scene prompt -> one Kling clip
================================================================================
 Sends ONE approved scene prompt to fal.ai Kling (text-to-video) and downloads
 the resulting 9:16 clip into out\backgrounds\new\ for review.

 Reads FAL_KEY from .env.local automatically -- you never type the key.

 USAGE (run from repo root):
   # TEXT-TO-VIDEO (generate a scene from a description):
   .\scripts\generate-scene.ps1 -Name "b1520-scene1" -Prompt "Cinematic vertical 9:16, a lone anonymous figure from behind at desert dawn..."

   # IMAGE-TO-VIDEO (animate YOUR OWN photo -- fixes hands/Kaaba Kling gets wrong):
   .\scripts\generate-scene.ps1 -Name "b1520-dua" -Image "out\refs\dua-hands.jpg" -Prompt "gentle subtle motion, hands held steady in dua, soft breeze, light shifting warmly, reverent and calm"

 PARAMS:
   -Name     output filename (no extension) -> out\backgrounds\new\<Name>.mp4
   -Prompt   the approved scene prompt (from the scene-prompt JSON)
   -Duration 5 or 10 seconds (default 5; use 10 — see cost note)
   -Model    fal model id (default: Kling 3.0 Pro, text- or image-to-video
             chosen by mode. Was 2.1 Master until P156.)

 COST, CHECKED 2026-09-06. The note here used to read "~5s standard-tier clip is
 roughly $0.35-0.50" and described a tier this script does not use. The default
 is fal-ai/kling-video/v2.6/pro, and fal charges:

     Kling 2.1 Master   $1.40 for 5s, +$0.28 per additional second
     Kling 2.1 Pro      $0.49 for 5s, +$0.098 per additional second
     Kling 2.6 Pro      $0.07 per second, audio off  ($0.35 for 5s)
     Kling 3.0 Pro      $0.112/s audio off, $0.168/s audio on  ($1.12 for 10s)

DEFAULT since 2026-10-11: Kling 3.0 Pro. Evaluated against 2.6 Pro on one
still and one prompt at the #5027 set boundary - 3.0 casts physically
coherent directional light where 2.6 gives a flat warm patch. It also reads
motion instructions MORE aggressively, so phrase camera moves conservatively.
2.6 Pro is still reachable with -Model for a scene that wants less movement.

P156 switched the default to Kling 2.6 Pro and it has been in use since. Four
10s clips cost $2.80 against $11.20 on 2.1 Master, with twice the hold and no
sequence looping on a 40s reel. Always pass -Duration 10: the 5s default is a
leftover and halves the hold for no saving beyond $0.35/clip.
================================================================================
#>

param(
  [Parameter(Mandatory)][string]$Name,
  [string]$Prompt,           # text-to-video: scene desc | image-to-video: MOTION desc
  [string]$Image,                                  # optional: local image path -> image-to-video mode
  [ValidateSet('5','10','15')][string]$Duration = '5',   # 15 = Kling 3.0 only (2.6 caps at 10)
  [string]$Model,                           # auto-set by mode if not given
  [string]$Resume,        # request_id from a timed-out run: poll it, do not re-submit
  [switch]$KeepText,      # the input still carries DELIBERATE text - see P216
  # P412: refuse a -Name whose collection prefix is not this hadith's (P403, #1987)
  [switch]$SkipNameCheck
)
  


# P429: a -Resume run takes model, mode, duration, image and prompt from the sidecar the
# submitting run wrote. It used to take them from its own parameters: without -Image the
# sidecar was rewritten as a v3 text-to-video 5s job, and with -Model v4 but no -Image the
# run died ("image-to-video only") before polling a job that had already been paid for.
$resuming = -not [string]::IsNullOrWhiteSpace($Resume)
$priorSidecar = $null
if ($resuming) {
  $sidePath = Join-Path (Join-Path (Split-Path $PSScriptRoot -Parent) 'assets\scene-prompts') "$Name.json"
  if (Test-Path $sidePath) {
    try { $priorSidecar = Get-Content $sidePath -Raw | ConvertFrom-Json } catch { $priorSidecar = $null }
  }
  if ($priorSidecar) {
    if (-not $Model -and $priorSidecar.model) { $Model = [string]$priorSidecar.model }
    if (-not $PSBoundParameters.ContainsKey('Duration') -and $priorSidecar.duration_sec) { $Duration = [string]$priorSidecar.duration_sec }
    if ([string]::IsNullOrWhiteSpace($Image) -and $priorSidecar.image) { $Image = [string]$priorSidecar.image }
  } else {
    Write-Host "  note: no sidecar for $Name - the resume records only what this run knows (P429)" -ForegroundColor Yellow
  }
  if (-not [string]::IsNullOrWhiteSpace($Prompt)) {
    Write-Host "  note: -Prompt ignored on -Resume; the job already has its prompt (P429)" -ForegroundColor Yellow
    $Prompt = $null
  }
}

# Mode = image-to-video if -Image supplied, else text-to-video. Pick matching default model.
$imageMode = -not [string]::IsNullOrWhiteSpace($Image)
if (-not $Model) {
  $Model = if ($imageMode) { 'fal-ai/kling-video/v3/pro/image-to-video' }
         else            { 'fal-ai/kling-video/v3/pro/text-to-video' }
}

$ErrorActionPreference = 'Stop'
# repo root = parent of the scripts\ folder this file lives in
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

function Say($m){ Write-Host $m -ForegroundColor Cyan }
function Ok ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

# --- P412: the -Name prefix must be this hadith's collection ------------------
. (Join-Path $PSScriptRoot 'lib\SetName.ps1')
if (-not $SkipNameCheck) {
  $nameCheck = Assert-SetName -Name $Name
  if (-not $nameCheck.Ok) { Die $nameCheck.Message }
  if ($nameCheck.Message) { Write-Host "  note: $($nameCheck.Message)" -ForegroundColor Yellow }
}

# --- P215: the prompt is part of the asset -----------------------------------
# Every clip in out\backgrounds\new\ made before 2026-10-11 is unreproducible:
# the motion prompt that produced it existed only in a chat window. The Kling
# 3.0 evaluation requires 'the same prompt through both models' and could not be
# run against ANY of the 64 registered scenes for exactly that reason. A clip
# without its prompt cannot be regenerated, re-evaluated when a model ships, or
# diffed when a model's behaviour changes under it.
#
# Written at SUBMIT, before the clip exists, so a 20-minute timeout (P137) still
# leaves the prompt on disk for -Resume to carry forward. A -Resume run has no
# -Prompt of its own, so a recorded prompt is never overwritten with nothing.
#
# ConvertFrom-Json coerces an ISO-8601 string to [DateTime] with Kind=Utc, so on a
# rewrite a timestamp's TEXT may shorten (...00.0000000Z -> ...00Z) while the
# instant is preserved exactly. That is not a defect; do not add quoting to
# 'fix' it.
function Write-Sidecar {
  param([hashtable]$Extra = @{})
  $side = Join-Path $promptDir "$Name.json"
  $rec  = @{}
  if (Test-Path $side) {
    try {
      (Get-Content $side -Raw -ErrorAction Stop | ConvertFrom-Json).PSObject.Properties |
        ForEach-Object { $rec[$_.Name] = $_.Value }
    } catch { }
  }
  # P429: on -Resume the submitting run's record stands; only the run's own facts are added.
  if ($resuming -and $rec.ContainsKey('model')) {
    if ($reqId) { $rec['request_id'] = $reqId }
    foreach ($k in $Extra.Keys) { $rec[$k] = $Extra[$k] }
    [System.IO.File]::WriteAllText($side, ($rec | ConvertTo-Json -Depth 5),
      (New-Object System.Text.UTF8Encoding($false)))
    return
  }
  if (-not [string]::IsNullOrWhiteSpace($Prompt)) { $rec['prompt'] = $Prompt }
  if (-not [string]::IsNullOrWhiteSpace($Image))  { $rec['image']  = $Image }
  $rec['name']            = $Name
  $rec['model']           = $Model
  $rec['mode']            = if ($imageMode) { 'image-to-video' } else { 'text-to-video' }
  $rec['duration_sec']    = [int]$Duration
  $rec['generate_audio']  = $payload['generate_audio']   # $null = not sent (2.1 Master)
  $rec['negative_prompt'] = $payload['negative_prompt']
  if ($reqId) { $rec['request_id'] = $reqId }
  foreach ($k in $Extra.Keys) { $rec[$k] = $Extra[$k] }
  $rec['schema'] = 1
  # P255: Set-Content -Encoding UTF8 writes a BOM on PS 5.1 and this file is
    # read back as JSON. P186 found that and fixed render-reel.ps1's sidecar;
    # this sibling writer kept the BOM, so all 17 scene-prompt sidecars carried
    # one and the pre-push JSON gate blocked every push for days.
    [System.IO.File]::WriteAllText($side, ($rec | ConvertTo-Json -Depth 5),
      (New-Object System.Text.UTF8Encoding($false)))
}

# --- read FAL_KEY from .env.local (never typed on the command line) ----------
if (-not $resuming -and [string]::IsNullOrWhiteSpace($Prompt)) {
  Die "-Prompt is required unless -Resume <request_id> is given"
}
if (-not (Test-Path ".env.local")) { Die ".env.local not found in repo root" }
$keyLine = Select-String -Path ".env.local" -Pattern '^\s*FAL_KEY\s*=' | Select-Object -First 1
if (-not $keyLine) { Die "FAL_KEY not found in .env.local" }
$FAL_KEY = ($keyLine.Line -replace '^\s*FAL_KEY\s*=\s*','').Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($FAL_KEY)) { Die "FAL_KEY in .env.local is empty" }

$outDir = "out\backgrounds\new"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$outFile = Join-Path $outDir "$Name.mp4"

# P215: the clip is build output and stays under the gitignored /out/. The PROMPT
# that produced it is SOURCE - the only thing that makes a clip reproducible or a
# model comparison possible - so it is recorded beside the registry that indexes
# each scene, where it is version-controlled. A negation under /out/ cannot work:
# git does not descend into an ignored directory to re-include a file.
$promptDir = Join-Path $repo "assets\scene-prompts"   # P281: ABSOLUTE.
# [System.IO.File]::WriteAllText below resolves a RELATIVE path against
# [Environment]::CurrentDirectory, which Set-Location does NOT update, so a
# relative $promptDir wrote to wherever the shell process started.
if (-not (Test-Path $promptDir)) { New-Item -ItemType Directory -Path $promptDir | Out-Null }

$headers = @{ "Authorization" = "Key $FAL_KEY"; "Content-Type" = "application/json" }
$payload = @{
  prompt          = $Prompt
  duration        = $Duration
  aspect_ratio    = "9:16"
  negative_prompt = "blur, distort, low quality, text, watermark, deformed hands, extra fingers, extra limbs, fused fingers"
}
# P216: the default negative prompt suppresses 'text, watermark' - right for a
# scene that should carry none, and directly against the intent when the still
# carries text we PUT there. b5027-matn was animated with 'text' still in the
# negative prompt and the Arabic survived anyway; that was luck, not design, and
# it is not a thing to rely on twice.
if ($KeepText) {
  $payload['negative_prompt'] = "blur, distort, low quality, deformed hands, extra fingers, extra limbs, fused fingers"
  Write-Host "  -KeepText: text/watermark dropped from the negative prompt (P216)" -ForegroundColor DarkGray
}
# P156/P214: Kling has defaulted generate_audio to TRUE on every version so far.
# It raises the rate (2.6 Pro $0.07 -> $0.14/s; v3 Pro $0.112 -> $0.168/s) AND mixes
# generated sound into a clip meant to be a SILENT background - the nasheed and the
# narration are added at render time.
#
# P214: this guard was  if ($Model -match 'v2\.6') { ... = $false },  so passing any
# other model id dropped the field and let the PROVIDER default win. A guard whose
# non-match produces the UNSAFE outcome stops protecting the moment the model
# changes - and the model changing is the one time nobody is watching this line.
# Audio-off is unconditional now; the exception is named instead.
$payload['generate_audio'] = $false
if ($Model -match 'v2\.1/master') { $payload.Remove('generate_audio') }  # rejects the field

if ($resuming) {
  # P429: nothing is submitted, so no body is built and the image need not be on disk.
} elseif ($imageMode) {
  if (-not (Test-Path $Image)) { Die "image not found: $Image" }
  # encode the local image as a base64 data URI (fal accepts this directly as a file input)
  $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $Image))
  $ext   = ([System.IO.Path]::GetExtension($Image)).TrimStart('.').ToLower()
  if ($ext -eq 'jpg') { $ext = 'jpeg' }
  $payload["image_url"] = "data:image/$ext;base64," + [System.Convert]::ToBase64String($bytes)
  Write-Host "  mode: IMAGE-TO-VIDEO (animating $Image)" -ForegroundColor DarkGray
} else {
  Write-Host "  mode: TEXT-TO-VIDEO" -ForegroundColor DarkGray
}
# P421: Kling 4.0 (fal-ai/kling-video/v4/image-to-video) has its own input schema - start_image_url,
# an integer duration, resolution; no aspect_ratio (the still sets it), no negative_prompt, no
# generate_audio. Sending the v3 body is what returned 422 on 2026-11-16 (that try also used the
# kling/v4 id, whose status URL is not under fal-ai/kling-video).
if (-not $resuming -and $Model -match 'kling-video/v4') {
  if (-not $imageMode) { Die "Kling 4.0 path is image-to-video only here" }
  $payload['start_image_url'] = $payload['image_url']; $payload.Remove('image_url')
  $payload['duration'] = [int]$Duration
  $payload['resolution'] = '1080p'
  foreach ($k in 'aspect_ratio','negative_prompt','generate_audio') { $payload.Remove($k) }
  Write-Host "  Kling 4.0 body: start_image_url, duration=$Duration, 1080p (P421)" -ForegroundColor DarkGray
}
$body = $payload | ConvertTo-Json -Depth 5

Say "================================================================"
Say " Kling scene -> $outFile"
if ($resuming) { Say "   resuming request $Resume" }
else           { Say "   model: $Model | ${Duration}s | 9:16" }
Say "================================================================"
if (-not $resuming) { Write-Host "  prompt: $Prompt" -ForegroundColor DarkGray }

# --- 1) SUBMIT to the queue (or resume an existing job) ----------------------
if ($resuming) {
  Say "`n[1/3] Resuming request $Resume (no submission, nothing charged)..."
  $reqId     = $Resume
  $statusUrl = "https://queue.fal.run/fal-ai/kling-video/requests/$reqId/status"
  $resultUrl = "https://queue.fal.run/fal-ai/kling-video/requests/$reqId"
  Ok "resuming: $reqId"
  Write-Sidecar @{ resumed_utc = (Get-Date).ToUniversalTime().ToString('o') }
} else {
  Say "`n[1/3] Submitting to fal.ai queue..."
  try {
    $submit = Invoke-RestMethod -Method Post -Uri "https://queue.fal.run/$Model" `
      -Headers $headers -Body $body
  } catch {
    Die "submit failed: $($_.Exception.Message) -- check FAL_KEY is valid and has credits"
  }
  $reqId     = $submit.request_id
  $statusUrl = $submit.status_url
  $resultUrl = $submit.response_url
  if (-not $reqId) { Die "no request_id returned (response: $($submit | ConvertTo-Json -Compress))" }
  Ok "queued: $reqId"
  Write-Sidecar @{ submitted_utc = (Get-Date).ToUniversalTime().ToString('o') }
  Ok "prompt recorded: $promptDir\$Name.json (P215)"
}


# --- 2) POLL until completed -------------------------------------------------
Say "`n[2/3] Generating (video gen takes ~1-4 min)..."
# P134: Kling master-tier i2v regularly exceeds 8 minutes — measured at 505s
# (b527-doorway), 564s (b6446-market), and rising. The job COMPLETES; only the
# poll gives up, and the operator then pays again or recovers by hand through
# the fal status API. 20 minutes is well past observed worst case and costs
# nothing when generation is fast.
$deadline = (Get-Date).AddMinutes(20)
# P430: one failed status call used to end the run, though the job keeps going server-side.
# On 2026-11-22/23 a flaky link stopped 9 of 14 Kling runs this way and each was resumed by hand.
# Now a failed poll is retried; only 6 failures in a row stop the run, with the resume line.
$pollFails = 0
do {
  Start-Sleep -Seconds 8
  try {
    $st = Invoke-RestMethod -Method Get -Uri $statusUrl -Headers $headers
    $pollFails = 0
  } catch {
    $pollFails++
    Write-Host "        status check failed ($pollFails/6): $($_.Exception.Message)" -ForegroundColor Yellow
    if ($pollFails -ge 6) {
      Die "status check failed 6 times in a row (request $reqId). The job may still complete - resume it:`n  .\scripts\generate-scene.ps1 -Name $Name -Resume $reqId"
    }
    Start-Sleep -Seconds (5 * $pollFails)
    continue
  }
  Write-Host "        status: $($st.status)" -ForegroundColor DarkGray
  if ($st.status -eq 'COMPLETED') { break }
  if ($st.status -in @('FAILED','ERROR','CANCELLED')) { Die "generation failed (status: $($st.status), request $reqId)" }
  if ((Get-Date) -gt $deadline) {
        Die @"
timed out after 20 min (request $reqId, last status $($st.status))
The job may still COMPLETE server-side. Resume it rather than regenerating:

  .\scripts\generate-scene.ps1 -Name $Name -Resume $reqId

That polls the existing job and downloads it. Nothing is re-submitted and
nothing is charged again. (P137)
"@
  }
} while ($true)
Ok "generation complete"

# --- 3) FETCH result + download the clip -------------------------------------
Say "`n[3/3] Downloading clip..."
# P430: the result fetch and the download get the same retries as the poll - the job is done and paid for.
$res = $null
for ($try = 1; $try -le 6 -and -not $res; $try++) {
  try { $res = Invoke-RestMethod -Method Get -Uri $resultUrl -Headers $headers }
  catch {
    Write-Host "        result fetch failed ($try/6): $($_.Exception.Message)" -ForegroundColor Yellow
    if ($try -ge 6) { Die "result fetch failed 6 times (request $reqId). Resume it:`n  .\scripts\generate-scene.ps1 -Name $Name -Resume $reqId" }
    Start-Sleep -Seconds (5 * $try)
  }
}
# Kling returns { video: { url: "..." } }
$videoUrl = $res.video.url
if (-not $videoUrl) { Die "no video URL in result: $($res | ConvertTo-Json -Compress -Depth 5)" }
for ($try = 1; $try -le 6; $try++) {
  try { Invoke-WebRequest -Uri $videoUrl -OutFile $outFile; break }
  catch {
    Write-Host "        download failed ($try/6): $($_.Exception.Message)" -ForegroundColor Yellow
    if ($try -ge 6) { Die "download failed 6 times (request $reqId). Resume it:`n  .\scripts\generate-scene.ps1 -Name $Name -Resume $reqId" }
    Start-Sleep -Seconds (5 * $try)
  }
}
if (-not (Test-Path $outFile)) { Die "download failed ($outFile not created)" }

$mb = [math]::Round((Get-Item $outFile).Length/1MB,2)
Ok "$outFile ($mb MB)"

# verify it's vertical 1080x1920-ish (Kling outputs vertical for 9:16)
$dim = $null
if (Get-Command ffprobe -ErrorAction SilentlyContinue) {
  $dim = (& ffprobe -hide_banner -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $outFile 2>$null).Trim()
  Write-Host "        resolution: $dim" -ForegroundColor DarkGray
}

# P215: close the record with what the run actually produced.
Write-Sidecar @{
  completed_utc = (Get-Date).ToUniversalTime().ToString('o')
  file          = $outFile
  size_bytes    = (Get-Item $outFile).Length
  resolution    = $dim
  video_url     = $videoUrl
}

Write-Host "`nNEXT: watch $outFile -- is it reel-worthy AND religiously appropriate (MODE B)?" -ForegroundColor Cyan
Start-Process $outFile
