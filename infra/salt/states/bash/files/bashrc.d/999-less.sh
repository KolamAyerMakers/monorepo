export LESS="--RAW-CONTROL-CHARS --quit-if-one-screen --chop-long-lines"

# Some options do not exist on old versions, only add them when available
if [ $(less --version | head -1 | cut -d' ' -f2) -ge 551 ]
then
    export LESS="$LESS --mouse --no-histdups"
fi
