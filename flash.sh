rm -rf ../flash
mkdir -p ../flash/apps/analogue_stick_badgemon
rsync -avs ../badgemon/ ../flash/apps/analogue_stick_badgemon
cd ../flash/apps/analogue_stick_badgemon
rm -rf .git* .vscode/ design/ docs/ TODO.md LICENCE *.ase *.gitignore README.md .env *.gitmodules flash.sh
cd ../../
mpremote cp --recursive apps :