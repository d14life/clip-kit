# Edit the line you want, then run:  .\start.ps1
# Leave it running overnight - it waits for streams, records, clips, captions and renders by itself.
Set-Location $PSScriptRoot

# Auto mode: always watch the 3 biggest English GTA VI streams that are live right now.
python autoclip.py --game "Grand Theft Auto VI" --top 3 --lang en --only-game "Grand Theft Auto VI"
# then, in another terminal, keep the Downloads\GTA 6 folder up to date:
#   while ($true) { python export_clips.py; Start-Sleep 120 }

# Or name the channels yourself (each one is waited for until it goes live):
# python autoclip.py kaicenat theburntpeanut ohnepixel
