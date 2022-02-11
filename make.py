#!/usr/bin/env python

# by: Kwabena W. Agyeman - kwagyeman@openmv.io

import argparse, glob, multiprocessing, os, re, shutil, stat, sys, subprocess

def make():

    __folder__ = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description =
    "Make Script")

    parser.add_argument("--rpi", nargs = '?',
    help = "Cross Compile QTDIR for the Raspberry Pi")

    parser.add_argument("-u", "--upload", nargs = '?',
    help = "FTP Password")

    args = parser.parse_args()

    if args.rpi and not sys.platform.startswith('linux'):
        sys.exit("Linux Only")

    ###########################################################################

    cpus = multiprocessing.cpu_count()
    builddir = os.path.join(__folder__, "build")
    installdir = os.path.join(builddir, "install")
    qtcdir = glob.glob(os.path.join(os.environ["IQTA_TOOLS"], "QtCreator"))[0]
    os.environ["PATH"] += os.pathsep + os.path.join(qtcdir, "bin")
    os.environ["PATH"] += os.pathsep + os.path.join(os.path.join(qtcdir, "bin"), "jom")
    ifwdir = glob.glob(os.path.join(os.environ["IQTA_TOOLS"], "QtInstallerFramework", "*"))[0]
    os.environ["PATH"] += os.pathsep + os.path.join(ifwdir, "bin")

    if not os.path.exists(builddir):
        os.mkdir(builddir)

    installer = ""

    if args.rpi:
        # Add Fonts...
        if os.path.exists(os.path.join(installdir, "lib/Qt/lib/fonts")):
            shutil.rmtree(os.path.join(installdir, "lib/Qt/lib/fonts"), ignore_errors = True)
        shutil.copytree(os.path.join(__folder__, "dejavu-fonts/fonts/"),
                        os.path.join(installdir, "lib/Qt/lib/fonts"))
        # Add README.txt...
        with open(os.path.join(installdir, "README.txt"), 'w') as f:
            f.write("Please run setup.sh to install OpenMV IDE dependencies... e.g.\n\n")
            f.write("./setup.sh\n\n")
            f.write("source ~/.profile\n\n")
            f.write("./bin/openmvide\n\n")
        # Add setup.sh...
        with open(os.path.join(installdir, "setup.sh"), 'w') as f:
            f.write("#! /bin/sh\n\n")
            f.write("DIR=\"$(dirname \"$(readlink -f \"$0\")\")\"\n")
            f.write("sudo apt-get install -y ibxcb* libGLES* libts* libsqlite* libodbc* libsybdb* libusb-1.0 python-pip libgles2-mesa-dev libpng12-dev qt5-default libts-dev\n")
            f.write("sudo pip install pyusb\n\n")
            f.write("sudo cp $( dirname \"$0\" )/share/qtcreator/pydfu/50-openmv.rules /etc/udev/rules.d/50-openmv.rules\n")
            f.write("sudo udevadm control --reload-rules\n\n")
            f.write("if [ -z \"${QT_QPA_PLATFORM}\" ]; then\n")
            f.write("    echo >> ~/.profile\n")
            f.write("    echo \"# Force Qt Apps to use xcb\" >> ~/.profile\n")
            f.write("    echo \"export QT_QPA_PLATFORM=xcb\" >> ~/.profile\n")
            f.write("    echo\n")
            f.write("    echo Please type \"source ~/.profile\".\n")
            f.write("fi\n\n")
            f.write("# Make sure hard linked libts library is there\n\n")
            f.write("LINK=/usr/lib/arm-linux-gnueabihf/libts-0.0.so.0\n")
            f.write("if [ ! -e ${LINK} ]\n")
            f.write("then\n")
            f.write("    TSLIB=`find /usr/lib/arm-linux-gnueabihf/ -type f -name libts.so*`\n")
            f.write("    if [ ! -z ${TSLIB} ]\n")
            f.write("    then\n")
            f.write("        sudo ln -s ${TSLIB} ${LINK}\n")
            f.write("    else\n")
            f.write("        echo \"Could not find libts library\"\n")
            f.write("        exit 1\n")
            f.write("    fi\n")
            f.write("fi\n\n")
            f.write("while true; do\n")
            f.write("    read -r -p \"\nInstall Desktop Shortcut? [y/n] \" _response\n")
            f.write("    case \"$_response\" in\n")
            f.write("        [Yy][Ee][Ss]|[Yy])\n")
            f.write("            cat > /home/$USER/Desktop/openmvide.desktop << EOM\n")
            f.write("[Desktop Entry]\n")
            f.write("Type=Application\n")
            f.write("Comment=The IDE of choice for OpenMV Cam Development.\n")
            f.write("Name=OpenMV IDE\n")
            f.write("Exec=$DIR/bin/openmvide\n")
            f.write("Icon=$DIR/share/icons/hicolor/512x512/apps/OpenMV-openmvide.png\n")
            f.write("Terminal=false\n")
            f.write("StartupNotify=true\n")
            f.write("Categories=Development\n")
            f.write("MimeType=text/x-python\n")
            f.write("EOM\n")
            f.write("            echo \"You must logout and login again for the desktop shortcut to work.\"\n")
            f.write("            exit 0\n")
            f.write("            ;;\n")
            f.write("        [Nn][Oo]|[Nn])\n")
            f.write("            exit 0\n")
            f.write("            ;;\n")
            f.write("        *)\n")
            f.write("            ;;\n")
            f.write("    esac\n")
            f.write("done\n\n")
        os.chmod(os.path.join(installdir, "setup.sh"),
            os.stat(os.path.join(installdir, "setup.sh")).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        # Build...
        if os.system("cd " + builddir +
        " && qmake ../qt-creator/qtcreator.pro -r" +
        " && make -r -w -j" + str(cpus) +
        " && make bindist INSTALL_ROOT="+installdir):
            sys.exit("Make Failed...")
        installer = glob.glob(os.path.join(builddir, "openmv-ide-*.tar.gz"))[0]

    elif sys.platform.startswith('win'):
        if os.system("cd " + builddir +
        " && qmake ../qt-creator/qtcreator.pro -r -spec win32-g++" +
        " && jom -j" + str(cpus) +
        " && jom installer INSTALL_ROOT="+installdir + " IFW_PATH="+ifwdir):
            sys.exit("Make Failed...")
        installer = glob.glob(os.path.join(builddir, "openmv-ide-*.exe"))[0]

    elif sys.platform.startswith('darwin'):
        if os.system("cd " + builddir +
        " && qmake ../qt-creator/qtcreator.pro -r -spec macx-clang CONFIG+=x86_64" +
        " && make -s -j" + str(cpus) +
        " && make deployqt"):
            sys.exit("Make Failed...")
        os.system("cd " + builddir + " && make codesign SIGNING_IDENTITY=Application")
        if os.system("cd " + builddir + " && make dmg"):
            sys.exit("Make Failed...")
        installer = glob.glob(os.path.join(builddir, "openmv-ide-*.dmg"))[0]

    elif sys.platform.startswith('linux'):
        # Add Fonts...
        if os.path.exists(os.path.join(installdir, "lib/Qt/lib/fonts")):
            shutil.rmtree(os.path.join(installdir, "lib/Qt/lib/fonts"), ignore_errors = True)
        shutil.copytree(os.path.join(__folder__, "dejavu-fonts/fonts/"),
                        os.path.join(installdir, "lib/Qt/lib/fonts"))
        # Add README.txt...
        with open(os.path.join(installdir, "README.txt"), 'w') as f:
            f.write("Please run setup.sh to install OpenMV IDE dependencies... e.g.\n\n")
            f.write("./setup.sh\n\n")
            f.write("./bin/openmvide.sh\n\n")
        # Add setup.sh...
        with open(os.path.join(installdir, "setup.sh"), 'w') as f:
            f.write("#! /bin/sh\n\n")
            f.write("sudo apt-get install -y libpng* libusb-1.0 python-pip\n")
            f.write("sudo pip install pyusb\n\n")
            f.write("sudo cp $( dirname \"$0\" )/share/qtcreator/pydfu/50-openmv.rules /etc/udev/rules.d/50-openmv.rules\n")
            f.write("sudo udevadm control --reload-rules\n\n")
        os.chmod(os.path.join(installdir, "setup.sh"),
            os.stat(os.path.join(installdir, "setup.sh")).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        # Build...
        if os.system("cd " + builddir +
        " && qmake ../qt-creator/qtcreator.pro -r -spec linux-g++" +
        " && make -r -s -w -j" + str(cpus) +
        " && make installer INSTALL_ROOT="+installdir + " IFW_PATH="+str(ifwdir)):
            sys.exit("Make Failed...")
        installer = glob.glob(os.path.join(builddir, "openmv-ide-*.run"))[0]

    else:
        sys.exit("Unknown Platform")

    ###########################################################################

    if args.upload:
        remotedir = os.path.splitext(os.path.basename(installer))[0]
        if args.rpi: # Remove .tar
            remotedir = os.path.splitext(remotedir)[0]
        uploaddir = os.path.join(builddir, remotedir)

        if not os.path.exists(uploaddir):
            os.mkdir(uploaddir)

        shutil.copy2(installer, uploaddir)

        subprocess.check_call(["python", "ftpsync.py", "-u", "-l",
        "ftp://upload@openmv.io:"+args.upload+"@ftp.openmv.io/"+remotedir,
        uploaddir])

if __name__ == "__main__":
    make()
