# !/bin/sh
echo "Installing MillionaireMakers dependencies..."
echo "Installing setuptools..."
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
echo "Checking for praw installation..."
pip list | grep praw > /dev/null
if [ $? -eq 0 ]
then
    echo "Upgrading praw..."
	easy_install --upgrade praw
else
    echo "Installing praw..."
	easy_install praw
fi
echo "Checking for flask installation..."
pip list | grep flask > /dev/null
if [ $? -eq 0 ]
then
    echo "Upgrading flask..."
    easy_install --upgrade flask
else
    echo "Installing flask..."
    easy_install flask
fi
echo "Checking for flask-basicauth installation..."
pip list | grep flask-basicauth > /dev/null
if [ $? -eq 0 ]
then
    echo "Upgrading flask-basicauth..."
    easy_install --upgrade flask-basicauth
else
    echo "Installing flask-basicauth..."
    easy_install flask-basicauth
fi
echo "Checking for dropbox installation..."
pip list | grep dropbox > /dev/null
if [ $? -eq 0 ]
then
    echo "Upgrading dropbox..."
    easy_install --upgrade dropbox
else
    echo "Installing dropbox..."
    easy_install dropbox
fi
echo "Checking for websocket-client installation..."
pip list | grep websocket-client > /dev/null
if [ $? -eq 0 ]
then
    echo "Upgrading websocket-client..."
    easy_install --upgrade websocket-client
else
    echo "Installing websocket-client..."
    easy_install websocket-client
fi
echo "Checking for requests installation..."
pip list | grep requests > /dev/null
if [ $? -eq 0 ]
then
    echo "Upgrading requests..."
    easy_install --upgrade requests
else
    echo "Installing requests..."
    easy_install requests
fi

echo "Installation Complete!"
