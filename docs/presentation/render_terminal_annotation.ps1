param(
    [string]$InputPath = (Join-Path $PSScriptRoot "terminal_input.png"),
    [string]$OutputPath = (Join-Path $PSScriptRoot "terminal_annotated.png")
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
        Box = @{ left = 1.2; top = 3.1; width = 57.0; height = 5.4 }
        Marker = @{ left = 58.8; top = 2.4 }
        Label = @{ left = 61.5; top = 1.8; width = 24.0; height = 10.8 }
        Title = "Start The Script"
        Body = "This is the one command the user runs. It starts the piano-player workflow and looks for the latest MIDI file."
    },
    @{
        Number = "2"
        Color = "#8EFF8A"
        Box = @{ left = 1.2; top = 11.3; width = 61.0; height = 12.9 }
        Marker = @{ left = 63.2; top = 12.2 }
        Label = @{ left = 66.0; top = 10.6; width = 24.5; height = 13.0 }
        Title = "Confirm Keyboard Layout"
        Body = "This section checks the saved note mapping. If the piano hardware has not changed, the user just presses Enter to keep it."
    },
    @{
        Number = "3"
        Color = "#FFCF5A"
        Box = @{ left = 1.2; top = 25.7; width = 72.0; height = 17.2 }
        Marker = @{ left = 74.7; top = 27.1 }
        Label = @{ left = 77.1; top = 25.0; width = 21.0; height = 16.0 }
        Title = "Fit The Song To The Piano"
        Body = "The script scans the MIDI note range and compares it to the playable octave. The user then chooses whether to skip or transpose out-of-range notes."
    },
    @{
        Number = "4"
        Color = "#FF8AC2"
        Box = @{ left = 1.2; top = 45.8; width = 55.0; height = 18.5 }
        Marker = @{ left = 57.8; top = 47.2 }
        Label = @{ left = 60.5; top = 45.4; width = 23.0; height = 17.0 }
        Title = "Choose Playback Speed"
        Body = "This prompt lets the user keep the original tempo or slow down or speed up the song. Values like .5 are treated as a multiplier."
    },
    @{
        Number = "5"
        Color = "#B59CFF"
        Box = @{ left = 1.2; top = 66.1; width = 88.8; height = 28.8 }
        Marker = @{ left = 90.9; top = 67.0 }
        Label = @{ left = 62.5; top = 78.0; width = 32.0; height = 15.0 }
        Title = "Playback Plan Summary"
        Body = "This final block confirms the selected MIDI, detected range, transpose choice, and the mapped notes and channels used for playback."
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
        $bodyFont = New-Object System.Drawing.Font("Segoe UI", [Math]::Max(12.0, $sourceImage.Width * 0.0095), [System.Drawing.FontStyle]::Regular)
        $markerFont = New-Object System.Drawing.Font("Segoe UI", [Math]::Max(13.0, $sourceImage.Width * 0.0105), [System.Drawing.FontStyle]::Bold)

        try {
            foreach ($annotation in $annotations) {
                $baseColor = New-ColorFromHex -Hex $annotation.Color
                $focusRect = Convert-PctRect -ImageWidth $sourceImage.Width -ImageHeight $sourceImage.Height -RectPercent $annotation.Box
                $labelRect = Convert-PctRect -ImageWidth $sourceImage.Width -ImageHeight $sourceImage.Height -RectPercent $annotation.Label
                $markerPoint = Convert-PctPoint -ImageWidth $sourceImage.Width -ImageHeight $sourceImage.Height -PointPercent $annotation.Marker

                $focusFill = New-Object System.Drawing.SolidBrush((New-ColorFromHex -Hex $annotation.Color -Alpha 40))
                $focusPen = New-Object System.Drawing.Pen($baseColor, [Math]::Max(3.0, $sourceImage.Width * 0.0022))
                $focusPath = New-RoundedRectanglePath -Rect $focusRect -Radius ([Math]::Max(14.0, $sourceImage.Width * 0.008))
                try {
                    $graphics.FillPath($focusFill, $focusPath)
                    $graphics.DrawPath($focusPen, $focusPath)
                } finally {
                    $focusPath.Dispose()
                    $focusPen.Dispose()
                    $focusFill.Dispose()
                }

                $labelFill = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(234, 12, 18, 32))
                $labelPen = New-Object System.Drawing.Pen($baseColor, [Math]::Max(2.0, $sourceImage.Width * 0.0018))
                $labelPath = New-RoundedRectanglePath -Rect $labelRect -Radius ([Math]::Max(16.0, $sourceImage.Width * 0.01))
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
                    $paddingY = [Math]::Max(10.0, $sourceImage.Width * 0.007)
                    $titleRect = [System.Drawing.RectangleF]::new(
                        $labelRect.X + $paddingX,
                        $labelRect.Y + $paddingY,
                        $labelRect.Width - ($paddingX * 2.0),
                        [Math]::Min($labelRect.Height * 0.32, 40.0)
                    )
                    $bodyRect = [System.Drawing.RectangleF]::new(
                        $labelRect.X + $paddingX,
                        $labelRect.Y + $paddingY + $titleRect.Height + 2.0,
                        $labelRect.Width - ($paddingX * 2.0),
                        $labelRect.Height - ($paddingY * 2.0) - $titleRect.Height - 2.0
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
        Write-Host "Annotated image written to: $OutputPath"
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
} finally {
    $sourceImage.Dispose()
}
