#!/bin/sh
set -xe
apk add supervisor python3 --update
apk add python3-dev musl-dev gcc libffi-dev openssl-dev
pip3 install --upgrade pip
pip3 install PyGithub errbot
pip3 install sleekxmpp pyasn1 pyasn1-modules irc hypchat \
  slackclient python-telegram-bot prometheus_client

apk del musl-dev gcc libffi-dev --purge

cat >> /usr/local/bin/entry.sh << EOF
#!/bin/sh
if [ ! -f /errbot/config.py ]; then
    mkdir -p /errbot/data
    errbot --init
fi
supervisord
EOF

chmod a+x /usr/local/bin/entry.sh
