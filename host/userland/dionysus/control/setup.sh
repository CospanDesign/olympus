#! /bin/bash


LUSER=$USER

#copy over the correct files
sudo cp 66-dionysus.rules /etc/udev/rules.d/

#add the group dionysus
sudo groupadd dionysus

#add the user to the group
sudo usermod -a -G dionysus $LUSER

#restart udev
sudo restart udev

