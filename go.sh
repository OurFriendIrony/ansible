#!/bin/bash

source ./.ansible-sys/scripts/setup.sh

#######################################################################
# Functions

usage () {
  PRG=$(basename $0)
  echo "$PRG -p PLAYBOOK [-u USER] [-l LIMIT] [-t TAGS] [-z SKIP] [-v VERBOSITY] [-k KEY] [-e EXTRAVARS] [-s] [-c] [-h]"
  echo "     -p PLAYBOOK      path to playbook"
  echo "     -u USER          user profile to load"
  echo "     -l LIMIT         limit to host"
  echo "     -t TAGS          run only tasks with provided tags"
  echo "     -z SKIP          skips tasks with provided tags"
  echo "     -v VERBOSITY     v, vv, vvv, vvvv"
  echo "     -k KEY           use private key"
  echo "     -e EXTRAVARS     include as extra vars"
  echo "     -s               run as sudo"
  echo "     -c               run in check mode"
  echo "     -h               show help"
  exit 0
}

get_playbook () {
  playbook="playbooks/${1}.yml"
  echo $playbook
}

#######################################################################
# Get Input

while getopts ":p:u:l:t:z:v:e:k:sch" arg; do
  case $arg in
    p)
      playbook=$(get_playbook "${OPTARG}")
      ;;
    u)
      user="${OPTARG}"
      uservars=" --extra-vars \"@user_profiles/${user}.yml\""
      ;;
    l)
      limit=" --limit \"${OPTARG}\""
      ;;
    t)
      tags=" --tags \"${OPTARG}\""
      ;;
    z)
      skip=" --skip-tags \"${OPTARG}\""
      ;;
    v)
      verbosity=" -${OPTARG}"
      ;;
    k)
      key=" --private-key \"${OPTARG}\""
      ;;
    e)
      extravars=" --extra-vars \"${OPTARG}\""
      ;;
    s)
      sudo=" --ask-become-pass"
      ;;
    c)
      check=" --check"
      ;;
    h)
      usage
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

# Check mandatory fields
mandatory_fields=( "playbook" )
#mandatory_fields=( "playbook" "user" )
mandatory_fields_set=true
for arg in ${mandatory_fields[@]}; do
  if [ -z "${!arg}" ]; then
    echo "Missing argument: ${arg^^}"
    mandatory_fields_set=false
  fi
done
if [ ${mandatory_fields_set} = false ]; then
  usage
  exit 1
fi

# Check playbook exists
if [ ! -f ${playbook} ]; then
  echo "'${playbook}' does not exist"
  exit 1
fi

#######################################################################

exe="ansible-playbook ${playbook} --diff${limit}${tags}${skip}${verbosity}${sudo}${check}${key}${uservars}${extravars}"
echo "${exe}"
eval "${exe}"

rm "$(find . -type f -name "*.retry")" 2> /dev/null

