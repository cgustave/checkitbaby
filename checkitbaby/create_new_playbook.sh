#! /bin/bash

# Creates a new playbook with directory tree
PBNAME=$1

if [[ $PBNAME == "" ]]; then 
	echo "Usage : ./create_new_playbook.sh <playbook_name>";
	exit 
fi

echo "Creating playbook $PBNAME file structure"

mkdir playbooks/$PBNAME
mkdir playbooks/$PBNAME/conf
mkdir playbooks/$PBNAME/runs
mkdir playbooks/$PBNAME/runs/1
mkdir playbooks/$PBNAME/runs/1/testcases
mkdir playbooks/$PBNAME/testcases


