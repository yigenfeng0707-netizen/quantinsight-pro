# Read narration text from UTF-8 file
$text = Get-Content -Path "D:\shFintech\_tts_text.txt" -Encoding UTF8 -Raw

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

# Select Chinese voice
foreach ($v in $synth.GetInstalledVoices()) {
    if ($v.VoiceInfo.Culture.Name -eq "zh-CN") {
        $synth.SelectVoice($v.VoiceInfo.Name)
        Write-Host ("Using voice: " + $v.VoiceInfo.Name)
        break
    }
}

$synth.Rate = -2
$synth.Volume = 100
$synth.SetOutputToWaveFile("D:\shFintech\_narration.wav")

# Speak with progress events
$synth.Speak($text)
$synth.Dispose()

Write-Host "TTS done"
Get-Item "D:\shFintech\_narration.wav" | Select-Object Name, Length | Format-Table
