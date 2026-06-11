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
   -Duration 5 or 10 seconds (default 5 -- cheapest for POC)
   -Model    fal model id (default = cheapest current standard tier)

 COST NOTE: ~5s standard-tier clip is roughly $0.35-0.50. A single POC test is
 well under $1. You also have ~$10 free signup credits.
================================================================================
#>

param(
  [Parameter(Mandatory)][string]$Name,
  [Parameter(Mandatory)][string]$Prompt,           # text-to-video: scene desc | image-to-video: MOTION desc
  [string]$Image,                                  # optional: local image path -> image-to-video mode
  [ValidateSet('5','10')][string]$Duration = '5',
  [string]$Model                                   # auto-set by mode if not given
)

# Mode = image-to-video if -Image supplied, else text-to-video. Pick matching default model.
$imageMode = -not [string]::IsNullOrWhiteSpace($Image)
if (-not $Model) {
  $Model = if ($imageMode) { 'fal-ai/kling-video/v2.1/master/image-to-video' }
           else            { 'fal-ai/kling-video/v2.1/master/text-to-video' }
}

$ErrorActionPreference = 'Stop'
# repo root = parent of the scripts\ folder this file lives in
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

function Say($m){ Write-Host $m -ForegroundColor Cyan }
function Ok ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

# --- read FAL_KEY from .env.local (never typed on the command line) ----------
if (-not (Test-Path ".env.local")) { Die ".env.local not found in repo root" }
$keyLine = Select-String -Path ".env.local" -Pattern '^\s*FAL_KEY\s*=' | Select-Object -First 1
if (-not $keyLine) { Die "FAL_KEY not found in .env.local" }
$FAL_KEY = ($keyLine.Line -replace '^\s*FAL_KEY\s*=\s*','').Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($FAL_KEY)) { Die "FAL_KEY in .env.local is empty" }

$outDir = "out\backgrounds\new"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$outFile = Join-Path $outDir "$Name.mp4"

$headers = @{ "Authorization" = "Key $FAL_KEY"; "Content-Type" = "application/json" }
$payload = @{
  prompt          = $Prompt
  duration        = $Duration
  aspect_ratio    = "9:16"
  negative_prompt = "blur, distort, low quality, text, watermark, deformed hands, extra fingers, extra limbs, fused fingers"
}
if ($imageMode) {
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
$body = $payload | ConvertTo-Json -Depth 5

Say "================================================================"
Say " Kling scene -> $outFile"
Say "   model: $Model | ${Duration}s | 9:16"
Say "================================================================"
Write-Host "  prompt: $Prompt" -ForegroundColor DarkGray

# --- 1) SUBMIT to the queue --------------------------------------------------
Say "`n[1/3] Submitting to fal.ai queue..."
try {
  $submit = Invoke-RestMethod -Method Post -Uri "https://queue.fal.run/$Model" `
    -Headers $headers -Body $body
} catch {
  Die "submit failed: $($_.Exception.Message) -- check FAL_KEY is valid and has credits"
}
$reqId    = $submit.request_id
$statusUrl = $submit.status_url
$resultUrl = $submit.response_url
if (-not $reqId) { Die "no request_id returned (response: $($submit | ConvertTo-Json -Compress))" }
Ok "queued: $reqId"

# --- 2) POLL until completed -------------------------------------------------
Say "`n[2/3] Generating (video gen takes ~1-4 min)..."
$deadline = (Get-Date).AddMinutes(8)
do {
  Start-Sleep -Seconds 8
  try {
    $st = Invoke-RestMethod -Method Get -Uri $statusUrl -Headers $headers
  } catch {
    Die "status check failed: $($_.Exception.Message)"
  }
  Write-Host "        status: $($st.status)" -ForegroundColor DarkGray
  if ((Get-Date) -gt $deadline) { Die "timed out after 8 min (request $reqId still $($st.status))" }
} while ($st.status -ne 'COMPLETED')
Ok "generation complete"

# --- 3) FETCH result + download the clip -------------------------------------
Say "`n[3/3] Downloading clip..."
try {
  $res = Invoke-RestMethod -Method Get -Uri $resultUrl -Headers $headers
} catch {
  Die "result fetch failed: $($_.Exception.Message)"
}
# Kling returns { video: { url: "..." } }
$videoUrl = $res.video.url
if (-not $videoUrl) { Die "no video URL in result: $($res | ConvertTo-Json -Compress -Depth 5)" }
Invoke-WebRequest -Uri $videoUrl -OutFile $outFile
if (-not (Test-Path $outFile)) { Die "download failed ($outFile not created)" }

$mb = [math]::Round((Get-Item $outFile).Length/1MB,2)
Ok "$outFile ($mb MB)"

# verify it's vertical 1080x1920-ish (Kling outputs vertical for 9:16)
if (Get-Command ffprobe -ErrorAction SilentlyContinue) {
  $dim = (& ffprobe -hide_banner -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $outFile 2>$null).Trim()
  Write-Host "        resolution: $dim" -ForegroundColor DarkGray
}

Write-Host "`nNEXT: watch $outFile -- is it reel-worthy AND religiously appropriate (MODE B)?" -ForegroundColor Cyan
Start-Process $outFile
