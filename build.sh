#!/usr/bin/env bash

# stop and remove old service
/bin/systemctl disable db-audio-pi
/bin/systemctl stop db-audio-pi
/usr/bin/dpkg -P db-audio-pi
/bin/systemctl daemon-reload

# build and install new package
chmod +x db-audio-pi_1.1-1/DEBIAN/preinst
/usr/bin/dpkg-deb --build db-audio-pi_1.1-1
/usr/bin/dpkg -i --force-overwrite db-audio-pi_1.1-1.deb
# start new service
/bin/systemctl daemon-reload
/bin/systemctl start db-audio-pi
/bin/systemctl enable db-audio-pi
