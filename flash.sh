mkdir tmp
find -not -path "*.venv*" -not -path "*tmp*" -name "*py" -newer .lastsynced -exec cp --parents {} tmp \;
cd tmp
mpremote cp -r . :
cd ..
rm -r tmp
touch .lastsynced