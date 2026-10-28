Add-Type -AssemblyName System.Drawing

$srcPath = "c:\Users\deaor\Downloads\finnk\icon.jpg"
$resBase = "c:\Users\deaor\Downloads\finnk\frontend\android\app\src\main\res"

if (-not (Test-Path $srcPath)) {
    Write-Error "Source icon not found at $srcPath"
    exit 1
}

$srcImage = [System.Drawing.Image]::FromFile($srcPath)

$configs = @(
    @{ Folder = "mipmap-mdpi"; Size = 48; ForeSize = 108 },
    @{ Folder = "mipmap-hdpi"; Size = 72; ForeSize = 162 },
    @{ Folder = "mipmap-xhdpi"; Size = 96; ForeSize = 216 },
    @{ Folder = "mipmap-xxhdpi"; Size = 144; ForeSize = 324 },
    @{ Folder = "mipmap-xxxhdpi"; Size = 192; ForeSize = 432 }
)

function Resize-SquareImage($image, $width, $height) {
    $bmp = New-Object System.Drawing.Bitmap $width, $height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.DrawImage($image, 0, 0, $width, $height)
    $g.Dispose()
    return $bmp
}

function Create-ForegroundImage($image, $size) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

    # Adaptive icon foreground has safe zone in center 66% (diameter 66 of 108)
    $iconSize = [int]($size * 0.72)
    $offset = [int](($size - $iconSize) / 2)
    $g.DrawImage($image, $offset, $offset, $iconSize, $iconSize)
    $g.Dispose()
    return $bmp
}

function Create-RoundImage($image, $size) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddEllipse(0, 0, $size, $size)
    $g.SetClip($path)
    $g.DrawImage($image, 0, 0, $size, $size)
    $g.Dispose()
    return $bmp
}

foreach ($cfg in $configs) {
    $dir = Join-Path $resBase $cfg.Folder
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    # 1. ic_launcher.png
    $launcherBmp = Resize-SquareImage $srcImage $cfg.Size $cfg.Size
    $launcherPath = Join-Path $dir "ic_launcher.png"
    $launcherBmp.Save($launcherPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $launcherBmp.Dispose()
    Write-Host "Generated $launcherPath"

    # 2. ic_launcher_round.png
    $roundBmp = Create-RoundImage $srcImage $cfg.Size
    $roundPath = Join-Path $dir "ic_launcher_round.png"
    $roundBmp.Save($roundPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $roundBmp.Dispose()
    Write-Host "Generated $roundPath"

    # 3. ic_launcher_foreground.png
    $foreBmp = Create-ForegroundImage $srcImage $cfg.ForeSize
    $forePath = Join-Path $dir "ic_launcher_foreground.png"
    $foreBmp.Save($forePath, [System.Drawing.Imaging.ImageFormat]::Png)
    $foreBmp.Dispose()
    Write-Host "Generated $forePath"
}

$srcImage.Dispose()
Write-Host "All Android icons generated successfully!"
