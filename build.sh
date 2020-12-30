#!/usr/bin/env bash

# stop and remove old service
/bin/systemctl disable db-audio-pi
/bin/systemctl stop db-audio-pi
/usr/bin/dpkg -P db-audio-pi
/bin/systemctl daemon-reload

# build and install new package
/usr/bin/dpkg-deb --build db-audio-pi_1.0-1
/usr/bin/dpkg -i db-audio-pi_1.0-1.deb

# start new service
/bin/systemctl daemon-reload
/bin/systemctl start db-audio-pi
/bin/systemctl enable db-audio-pi