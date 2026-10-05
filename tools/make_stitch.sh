# Stitch shot1 + bridge + shot2 + shot3 + shot4 from shots/final. Run from the project root: bash shots/stitch/make4.sh <out.mp4>
# (File name kept: it was the 4-clip script; it now joins 5 clips.)
OUT=$1
V='crop=iw:trunc(iw*9/16/2)*2,scale=854:480,setsar=1,fps=24,format=yuv420p'
A='aresample=44100,aformat=channel_layouts=stereo'
ffmpeg -v error -y -i shots/final/shot1.mp4 -i shots/final/shot1b.mp4 -i shots/final/shot2.mp4 -i shots/final/shot3.mp4 -i shots/final/shot4.mp4 \
 -filter_complex "[0:v]${V}[v0];[1:v]${V}[v1];[2:v]${V}[v2];[3:v]${V}[v3];[4:v]${V}[v4];[0:a]${A}[a0];[1:a]${A}[a1];[2:a]${A}[a2];[3:a]${A}[a3];[4:a]${A}[a4];[v0][a0][v1][a1][v2][a2][v3][a3][v4][a4]concat=n=5:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 160k $OUT
