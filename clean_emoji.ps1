# clean_emoji.ps1 - removes all non-ASCII characters from a Python file
# Safe: the script itself is pure ASCII, uses codepoint-based regex.

$path = "app\main_1.py"
$content = Get-Content $path -Raw -Encoding UTF8

# Replace common mojibake sequences using codepoint escapes
# (ðŸ = U+00F0 U+0178, â = U+00E2, Ã = U+00C3, Â = U+00C2)
$content = $content -replace "[\u00C0-\u00FF][\u0080-\u00FF]*", ""

# Also catch the specific multibyte leftovers as raw sequences
$content = $content -replace "\u00E2\u20AC\u201D", "-"      # em dash
$content = $content -replace "\u00E2\u20AC\u201C", "-"      # en dash
$content = $content -replace "\u00E2\u20AC\u00A6", "..."    # ellipsis
$content = $content -replace "\u00C3\u2014", "x"            # multiplication x
$content = $content -replace "\u00C2\u00B7", "-"            # middle dot
$content = $content -replace "\u00E2\u201E\u00A2", ""       # info emoji
$content = $content -replace "\u00E2\u0153\u2026", ""       # checkmark
$content = $content -replace "\u00E2\u0161\u2122\u00EF\u00B8\u008F", ""

# Final sweep: any remaining non-ASCII in the file, replace with empty
$content = [regex]::Replace($content, "[^\x00-\x7F]", "")

Set-Content -Path $path -Value $content -Encoding UTF8
Write-Host "Done. All non-ASCII characters removed."
