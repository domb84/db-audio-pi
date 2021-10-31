#!/bin/bash -x

read $TRACK_ID
[[ ${#TRACK_ID} -gt 2 ]] && cat <<EOF >/tmp/.spot_track
[INFO]
ID=$TRACK_ID
EVENT=$PLAYER_EVENT
EOF
