<#
================================================================================
 edit-still.ps1  -  edit an existing still with FLUX Kontext (image + instruction)
================================================================================
 P412 (from P402, #1987): Kling would not erase footprints from a still - an
 image-to-video model keeps its first frame. Editing the STILL with FLUX Kontext
 [pro] did it in one call. That ran once as out\explain-src\edit1987.ps1; this is
 the repo version, with the prompt recorded like every other still (P250).

 USAGE (run from repo root):
   .\scripts\edit-still.ps1 -Name "t1987-sand-smooth" -Source "out\refs\t1987-sand-2.jpg" `
     -Prompt "Remove all the footprints. Keep exactly the same camera angle, horizon, sky, light and sand colour. No people."

 PARAMS:
   -Name     output -> out\refs\<Name>.jpg, sidecar assets\still-prompts\<Name>-still.json
   -Source   the still to edit (a local file)
   -Prompt   the edit instruction - say what to change AND what to keep
   -Model    fal model id (default fal-ai/flux-pro/kontext)
   -Force    overwrite out\refs\<Name>.jpg if it exists
   -SkipNameCheck  skip the P412 collection-prefix check

 COST: one Kontext [pro] image, about $0.04.
================================================================================
#>

param(
  [Parameter(Mandatory)][string]$Name,
  [Parameter(Mandatory)][string]$Source,
  [Parameter(Mandatory)][string]$Prompt,
  [string]$Model = 'fal-ai/flux-pro/kontext',
  [string]$AspectRatio = '9:16',
  [switch]$Force,
  [switch]$SkipNameCheck
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

function Say($m){ Write-Host $m -ForegroundColor Cyan }
function Ok ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

. (Join-Path $PSScriptRoot 'lib\SetName.ps1')
if (-not $SkipNameCheck) {
  $nameCheck = Assert-SetName -Name $Name
  if (-not $nameCheck.Ok) { Die $nameCheck.Message }
  if ($nameCheck.Message) { Write-Host "  note: $($nameCheck.Message)" -ForegroundColor Yellow }
}

if (-not (Test-Path -LiteralPath $Source)) { Die "source still not found: $Source" }
$srcFull = (Resolve-Path -LiteralPath $Source).Path
$ext = [IO.Path]::GetExtension($srcFull).ToLower()
$mime = @{ '.jpg' = 'image/jpeg'; '.jpeg' = 'image/jpeg'; '.png' = 'image/png'; '.webp' = 'image/webp' }[$ext]
if (-not $mime) { Die "source must be .jpg, .png or .webp (got '$ext')" }

$refDir = 'out\refs'
if (-not (Test-Path $refDir)) { New-Item -ItemType Directory -Path $refDir | Out-Null }
$dest = Join-Path $refDir "$Name.jpg"
if ((Test-Path -LiteralPath $dest) -and -not $Force) { Die "$dest exists - pick another -Name or pass -Force" }

if (-not (Test-Path '.env.local')) { Die '.env.local not found in repo root' }
$keyLine = Select-String -Path '.env.local' -Pattern '^\s*FAL_KEY\s*=' | Select-Object -First 1
if (-not $keyLine) { Die 'FAL_KEY not found in .env.local' }
$FAL_KEY = ($keyLine.Line -replace '^\s*FAL_KEY\s*=\s*','').Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($FAL_KEY)) { Die 'FAL_KEY in .env.local is empty' }

# P228: .NET calls get absolute paths only
$bytes = [System.IO.File]::ReadAllBytes($srcFull)
$srcSha = (Get-FileHash -LiteralPath $srcFull -Algorithm SHA256).Hash.ToLower()
$body = @{
  prompt        = $Prompt
  image_url     = "data:$mime;base64," + [Convert]::ToBase64String($bytes)
  aspect_ratio  = $AspectRatio
  output_format = 'jpeg'
} | ConvertTo-Json

Say '================================================================'
Say " Kontext edit: $Source -> $dest"
Say " model: $Model"
Say '================================================================'
Write-Host "  prompt: $Prompt" -ForegroundColor DarkGray

$submittedUtc = (Get-Date).ToUniversalTime().ToString('o')
try {
  $res = Invoke-RestMethod -Method Post -Uri "https://fal.run/$Model" -Headers @{ Authorization = "Key $FAL_KEY" } `
    -ContentType 'application/json' -Body $body -TimeoutSec 240
} catch {
  Die "edit failed: $($_.Exception.Message) -- check FAL_KEY / credits"
}
$completedUtc = (Get-Date).ToUniversalTime().ToString('o')
if (-not $res.images -or -not $res.images[0].url) { Die "no image in result: $($res | ConvertTo-Json -Compress -Depth 5)" }
$img = $res.images[0]
Invoke-WebRequest -Uri $img.url -OutFile $dest
if (-not (Test-Path -LiteralPath $dest)) { Die "download failed: $($img.url)" }
Ok "$dest  ($($img.width)x$($img.height))"

# P250: the prompt is part of the asset - same folder and shape as generate-image.ps1
try {
  $stillDir = 'assets\still-prompts'
  if (-not (Test-Path $stillDir)) { New-Item -ItemType Directory -Force -Path $stillDir | Out-Null }
  $sidecar = [ordered]@{
    schema        = 1
    mode          = 'kontext-edit'
    name          = $Name
    model         = $Model
    prompt        = $Prompt
    aspect_ratio  = $AspectRatio
    source        = [ordered]@{ file = $Source; sha256 = $srcSha; bytes = $bytes.Length }
    submitted_utc = $submittedUtc
    completed_utc = $completedUtc
    output        = [ordered]@{ file = $dest; url = $img.url; width = $img.width; height = $img.height }
    chosen        = $null
  }
  if ($res.PSObject.Properties.Name -contains 'seed') { $sidecar.seed = $res.seed }
  $stillPath = Join-Path (Resolve-Path $stillDir).Path "$Name-still.json"
  [System.IO.File]::WriteAllText($stillPath, ($sidecar | ConvertTo-Json -Depth 5),
    (New-Object System.Text.UTF8Encoding($false)))
  Ok "prompt recorded: $stillDir\$Name-still.json"
} catch {
  Write-Host "  could not write the still sidecar: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nNEXT: review $dest, then animate it:  .\scripts\generate-scene.ps1 -Name `"$Name`" -Image `"$dest`" -Prompt `"...`"" -ForegroundColor Cyan
