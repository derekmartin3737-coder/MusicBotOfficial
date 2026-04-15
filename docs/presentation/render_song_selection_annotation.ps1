param(
    [string]$InputPath = (Join-Path $PSScriptRoot "song_selection_input.png"),
    [string]$OutputPath = (Join-Path $PSScriptRoot "song_selection_annotated.png")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Input image not found at '$InputPath'. Save the screenshot there or pass -InputPath explicitly."
}

Add-Type -AssemblyName System.Drawing

function New-ColorFromHex {
    param(
        [Parameter(Mandatory = $true)][string]$Hex,
        [int]$Alpha = 255
    )

    $clean = $Hex.TrimStart("#")
    if ($clean.Length -ne 6) {
        throw "Expected a 6-digit hex color, got '$Hex'."
    }

    $r = [Convert]::ToInt32($clean.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($clean.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($clean.Substring(4, 2), 16)
    return [System.Drawing.Color]::FromArgb($Alpha, $r, $g, $b)
}

function New-RoundedRectanglePath {
    param(
        [System.Drawing.RectangleF]$Rect,
        [float]$Radius
    )

    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $diameter = [Math]::Max(1.0, $Radius * 2.0)
    $path.AddArc($Rect.X, $Rect.Y, $diameter, $diameter, 180, 90)
    $path.AddArc($Rect.Right - $diameter, $Rect.Y, $diameter, $diameter, 270, 90)
    $path.AddArc($Rect.Right - $diameter, $Rect.Bottom - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($Rect.X, $Rect.Bottom - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function Convert-PctRect {
    param(
        [float]$ImageWidth,
        [float]$ImageHeight,
        [hashtable]$RectPercent
    )

    return [System.Drawing.RectangleF]::new(
        [float]($ImageWidth * $RectPercent.left / 100.0),
        [float]($ImageHeight * $RectPercent.top / 100.0),
        [float]($ImageWidth * $RectPercent.width / 100.0),
        [float]($ImageHeight * $RectPercent.height / 100.0)
    )
}

function Convert-PctPoint {
    param(
        [float]$ImageWidth,
        [float]$ImageHeight,
        [hashtable]$PointPercent
    )

    return [System.Drawing.PointF]::new(
        [float]($ImageWidth * $PointPercent.left / 100.0),
        [float]($ImageHeight * $PointPercent.top / 100.0)
    )
}

$annotations = @(
    @{
        Number = "1"
        Color = "#4DD4FF"
        Box = @{ left = 0.3; top = 0.2; width = 40.5; height = 49.4 }
        Marker = @{ left = 41.7; top = 2.0 }
        Label = @{ left = 50.5; top = 3.0; width = 36.5; height = 10.5 }
        Title = "Project MIDI Library"
        Body = "The script lists the saved MIDI files that can be converted and played through the piano system."
    },
    @{
        Number = "2"
        Color = "#8EFF8A"
        Box = @{ left = 0.3; top = 50.7; width = 22.0; height = 4.1 }
        Marker = @{ left = 23.5; top = 50.4 }
        Label = @{ left = 50.5; top = 14.7; width = 36.5; height = 10.0 }
        Title = "Select A Song"
        Body = "The user enters the number for the song. Option 10 selects the Pirates MIDI."
    },
    @{
        Number = "3"
        Color = "#FFCF5A"
        Box = @{ left = 0.3; top = 55.7; width = 83.0; height = 15.1 }
        Marker = @{ left = 84.8; top = 55.6 }
        Label = @{ left = 50.5; top = 25.8; width = 36.5; height = 10.0 }
        Title = "Confirm Keyboard Mapping"
        Body = "The saved layout maps 12 solenoids across C3 to B3. Press Enter to keep it."
    },
    @{
        Number = "4"
        Color = "#FF8AC2"
        Box = @{ left = 0.3; top = 72.2; width = 97.7; height = 17.8 }
        Marker = @{ left = 94.3; top = 70.5 }
        Label = @{ left = 50.5; top = 36.9; width = 36.5; height = 10.0 }
        Title = "Fit Song To Hardware"
        Body = "The scan compares the song range to the playable octave. Transpose keeps more notes."
    },
    @{
        Number = "5"
        Color = "#B59CFF"
        Box = @{ left = 0.3; top = 92.0; width = 98.0; height = 7.5 }
        Marker = @{ left = 94.5; top = 90.8 }
        Label = @{ left = 50.5; top = 48.0; width = 36.5; height = 10.0 }
        Title = "Confirm Playback Plan"
        Body = "The output confirms the selected Pirates file and source path before playback."
    }
)

$sourceImage = [System.Drawing.Image]::FromFile($InputPath)
try {
    $bitmap = New-Object System.Drawing.Bitmap $sourceImage.Width, $sourceImage.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
        $graphics.DrawImage($sourceImage, 0, 0, $sourceImage.Width, $sourceImage.Height)

        $titleFont = New-Object System.Drawing.Font("Segoe UI", [Math]::Max(16.0, $sourceImage.Width * 0.012), [System.Drawing.FontStyle]::Bold)
        $bodyFont = New-Object System.Drawing.Font("Segoe UI", [Math]::Max(12.0, $sourceImage.Width * 0.0093), [System.Drawing.FontStyle]::Regular)
        $markerFont = New-Object System.Drawing.Font("Segoe UI", [Math]::Max(13.0, $sourceImage.Width * 0.0105), [System.Drawing.FontStyle]::Bold)

        try {
            foreach ($annotation in $annotations) {
                $baseColor = New-ColorFromHex -Hex $annotation.Color
                $focusRect = Convert-PctRect -ImageWidth $sourceImage.Width -ImageHeight $sourceImage.Height -RectPercent $annotation.Box
                $labelRect = Convert-PctRect -ImageWidth $sourceImage.Width -ImageHeight $sourceImage.Height -RectPercent $annotation.Label
                $markerPoint = Convert-PctPoint -ImageWidth $sourceImage.Width -ImageHeight $sourceImage.Height -PointPercent $annotation.Marker

                $focusFill = New-Object System.Drawing.SolidBrush((New-ColorFromHex -Hex $annotation.Color -Alpha 36))
                $focusPen = New-Object System.Drawing.Pen($baseColor, [Math]::Max(3.0, $sourceImage.Width * 0.0022))
                $focusPath = New-RoundedRectanglePath -Rect $focusRect -Radius ([Math]::Max(12.0, $sourceImage.Width * 0.008))
                try {
                    $graphics.FillPath($focusFill, $focusPath)
                    $graphics.DrawPath($focusPen, $focusPath)
                } finally {
                    $focusPath.Dispose()
                    $focusPen.Dispose()
                    $focusFill.Dispose()
                }

                $labelFill = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(236, 12, 18, 32))
                $labelPen = New-Object System.Drawing.Pen($baseColor, [Math]::Max(2.0, $sourceImage.Width * 0.0018))
                $labelPath = New-RoundedRectanglePath -Rect $labelRect -Radius ([Math]::Max(14.0, $sourceImage.Width * 0.009))
                try {
                    $graphics.FillPath($labelFill, $labelPath)
                    $graphics.DrawPath($labelPen, $labelPath)
                } finally {
                    $labelPath.Dispose()
                    $labelPen.Dispose()
                    $labelFill.Dispose()
                }

                $markerDiameter = [Math]::Max(28.0, $sourceImage.Width * 0.02)
                $markerRect = [System.Drawing.RectangleF]::new($markerPoint.X, $markerPoint.Y, $markerDiameter, $markerDiameter)
                $markerBrush = New-Object System.Drawing.SolidBrush($baseColor)
                $markerTextBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 8, 17, 28))
                try {
                    $graphics.FillEllipse($markerBrush, $markerRect)
                    $numberSize = $graphics.MeasureString($annotation.Number, $markerFont)
                    $numberX = $markerRect.X + (($markerRect.Width - $numberSize.Width) / 2.0)
                    $numberY = $markerRect.Y + (($markerRect.Height - $numberSize.Height) / 2.0) - 1.0
                    $graphics.DrawString($annotation.Number, $markerFont, $markerTextBrush, $numberX, $numberY)
                } finally {
                    $markerBrush.Dispose()
                    $markerTextBrush.Dispose()
                }

                $titleBrush = New-Object System.Drawing.SolidBrush($baseColor)
                $bodyBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 237, 242, 255))
                $stringFormat = New-Object System.Drawing.StringFormat
                $stringFormat.Alignment = [System.Drawing.StringAlignment]::Near
                $stringFormat.LineAlignment = [System.Drawing.StringAlignment]::Near
                try {
                    $paddingX = [Math]::Max(12.0, $sourceImage.Width * 0.008)
                    $paddingY = [Math]::Max(9.0, $sourceImage.Width * 0.0065)
                    $titleRect = [System.Drawing.RectangleF]::new(
                        $labelRect.X + $paddingX,
                        $labelRect.Y + $paddingY,
                        $labelRect.Width - ($paddingX * 2.0),
                        [Math]::Min($labelRect.Height * 0.32, 38.0)
                    )
                    $bodyRect = [System.Drawing.RectangleF]::new(
                        $labelRect.X + $paddingX,
                        $labelRect.Y + $paddingY + $titleRect.Height + 1.0,
                        $labelRect.Width - ($paddingX * 2.0),
                        $labelRect.Height - ($paddingY * 2.0) - $titleRect.Height - 1.0
                    )

                    $graphics.DrawString("$($annotation.Number). $($annotation.Title)", $titleFont, $titleBrush, $titleRect, $stringFormat)
                    $graphics.DrawString($annotation.Body, $bodyFont, $bodyBrush, $bodyRect, $stringFormat)
                } finally {
                    $titleBrush.Dispose()
                    $bodyBrush.Dispose()
                    $stringFormat.Dispose()
                }
            }
        } finally {
            $titleFont.Dispose()
            $bodyFont.Dispose()
            $markerFont.Dispose()
        }

        $outputDirectory = Split-Path -Parent $OutputPath
        if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
            New-Item -ItemType Directory -Path $outputDirectory | Out-Null
        }

        $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Host "Annotated song-selection image written to: $OutputPath"
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
} finally {
    $sourceImage.Dispose()
}
