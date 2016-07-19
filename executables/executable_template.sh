#!/bin/bash -e

while [[ "$#" > 1 ]]; do case $1 in
    --deploy) DEPLOY="$2";;
    --uglify) UGLIFY="$2";;
    *);;
  esac; shift
done

echo $DEPLOY
echo $UGLIFY

#Environmental variable checking
if [ x${DTITK_ROOT} == x ] ; then
    echo "DTITK_ROOT is not set "
fi


if [ x${EXECUTABLE_DIR} == x ] ; then
    echo "EXECUTABLE_DIR is not set "
fi

echo "System PATH is set to ${PATH}"

#<SOMETIMES>
#Source dtitk_common.sh
source ${DTITK_ROOT}/scripts/dtitk_common.sh
#</SOMETIMES>
