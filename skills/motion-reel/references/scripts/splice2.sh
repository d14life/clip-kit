set -e
# usage: splice2.sh SRC RENDER RENDER_FIRST_G CH_A CH_B BLK_A BLK_B OUT
V=$1; R=$2; RF=$3; A=$4; B=$5; BA=$6; BB=$7; OUT=$8
X="-c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -color_primaries bt709 -color_trc iec61966-2-1 -color_range tv"
ffmpeg -v error -y -i $V -i $R -filter_complex "[0:v]trim=start_frame=$BA:end_frame=$A,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame=$((A-RF)):end_frame=$((B+1-RF)),setpts=PTS-STARTPTS[b];[0:v]trim=start_frame=$((B+1)):end_frame=$((BB+1)),setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0,fps=30[v]" -map "[v]" $X mid.mp4
ffmpeg -v error -y -i $V -map 0:v -c copy -frames:v $BA head.mp4
ffmpeg -v error -y -ss $(python3 -c "print(($BB+1)/30)") -i $V -map 0:v -c copy tail.mp4
for p in head mid tail; do ffmpeg -v error -y -i $p.mp4 -c copy -bsf:v h264_mp4toannexb $p.ts; done
ffmpeg -v error -y -i "concat:head.ts|mid.ts|tail.ts" -i $V -map 0:v -map 1:a -c copy -r 30 $OUT
for p in head mid tail $OUT; do echo $p $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 ${p%.mp4}.mp4); done
ffprobe -v error -show_entries stream=codec_name,duration -of compact $OUT
ffmpeg -v error -i $OUT -f null - && echo decode-clean
