#! /bin/bash
cd ~/projects
rm -rf ./sycamore_projects
~/Projects/olympus/ibuilder/sap ~/Projects/olympus/ibuilder/saplib/example_project/dionysus_debug_hi.json
./pa_no_gui.sh
cd ~/Projects/olympus/host/userland/dionysus/control
./dionysus_control.py ~/projects/sycamore_projects/test_project/test_project.runs/impl_1/top.bin
cd ../../../
./test_dionysus.py
sleep 5
./dionysus.py -d -m

