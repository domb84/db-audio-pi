#!/usr/bin/env bash

# pycharm will mess up the encoding from windows. Run this to fix.
dos2unix build.sh
dos2unix db-audio-pi_1.2-1/DEBIAN/control
dos2unix db-audio-pi_1.2-1/DEBIAN/postinst
dos2unix db-audio-pi_1.2-1/DEBIAN/preinst
dos2unix db-audio-pi_1.2-1/etc/bt_speaker/startup
dos2unix db-audio-pi_1.2-1/etc/bt_speaker/track

dos2unix db-audio-pi_1.2-1/opt/db/db-audio-pi/scripts/spotify.sh

# fix permissions
chmod 0775 db-audio-pi_1.2-1/DEBIAN/preinst
chmod 0775 db-audio-pi_1.2-1/DEBIAN/postinst
chmod 0775 db-audio-pi_1.2-1/DEBIAN/control

# stop and remove old service
/bin/systemctl disable db-audio-pi
/bin/systemctl stop db-audio-pi
/usr/bin/dpkg -P db-audio-pi
/bin/systemctl daemon-reload

# build and install new package
chmod +x db-audio-pi_1.2-1/DEBIAN/preinst

/usr/bin/dpkg-deb --build db-audio-pi_1.2-1
/usr/bin/dpkg -i --force-overwrite db-audio-pi_1.2-1.deb
# start new service
/bin/systemctl daemon-reload
/bin/systemctl start db-audio-pi
/bin/systemctl enable db-audio-pi
