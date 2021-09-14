#!/bin/bash

home=$( dirname "${BASH_SOURCE[0]}" )
fact_dir="${home}/../facts/"

source "${home}/setup.sh"

#######################################################################

hosts=$( ansible all --list-hosts | awk '{if (NR!=1) {print $1}}' )
for host in ${hosts}; do

  # ALL
  resp=$( ansible ${host} -m setup )
  if ! [[ "$( cut -d ' ' -f3 <<< $resp )" =~ "SUCCESS" ]]; then
    echo "${host} - Can't Reach"
    continue
  fi
  echo "${host} - Recording Facts: All"
  json="$( cut -d ' ' -f5- <<< $resp | sed 's/.*=>//g' )"
  mkdir -p "${fact_dir}/all/"
  echo "$json" | jq -r '.' > "${fact_dir}/all/${host}"


  # dist
  resp=$( ansible ${host} -m setup -a filter=*dist* )
  if ! [[ "$( cut -d ' ' -f3 <<< $resp )" =~ "SUCCESS" ]]; then
    echo "${host} - Can't Reach"
    continue
  fi
  echo "${host} - Recording Facts: Distribution"
  json="$( cut -d ' ' -f5- <<< $resp | sed 's/.*=>//g' )"
  mkdir -p "${fact_dir}/dist/"
  echo "$json" | jq -r '.' > "${fact_dir}/dist/${host}"
done

#######################################################################

