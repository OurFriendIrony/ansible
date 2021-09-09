  * [User Profiles](#user-profiles)
  * [Tags](#tags)
  * [Playbooks](#playbooks)
    * [Ubuntu](./READMES/ubuntu.md)
    * [Windows](./READMES/windows.md)
    * [Retropie](./READMES/retropie.md)
  * [Help](#help)
  * [Ansible Module Index](#ansible-module-index)
___
# User Profiles
Your user profile can be used to override every roles `defaults` values. For example, adding:
```
terraform_version : "0.9.6"
```
will install that specific version of terraform, instead of the default values.  
  
If you want to see what you can override for a given role, check `roles/{ROLE_NAME}/defaults/main.yml`  
If you want to see what you can override across all roles, you can try the following:
```
for dir in $(find . -type d -name "defaults"); do grep -vE "^---" ${dir}/main.yml ; done
```
___
# Tags
Every role contains tags that you can specifically execute instead of running a full playbook.  
There is a standard behind the tags naming, so if you just want to install intellij, which exists in `developer/ide/intellij` you can run either `-t developer`, `-t ide` or `-t intellij`.
___
# Playbooks
The sections below cover install and build steps to get a full functioning linux box meeting whatever requirements you have. 
## ubuntu
Installs Ubuntu configurations  
[README](./READMES/ubuntu.md)
## windows
Installs Windows configurations  
[README](./READMES/windows.md)
## retropie
Installs all configurations for a [**Retropie 4.4**](https://retropie.org.uk/2018/04/retropie-4-4-is-released/) install  
[README](./READMES/retropie.md)
___
# Help
`./go.sh -h`
```
go.sh -p PLAYBOOK -u USER [-l LIMIT] [-t TAGS] [-z SKIP] [-v VERBOSITY] [-k KEY] [-e EXTRAVARS] [-s] [-c] [-h]
     -p PLAYBOOK      path to playbook
     -u USER          user profile to load
     -l LIMIT         limit to host
     -t TAGS          run only tasks with provided tags
     -z SKIP          skips tasks with provided tags
     -v VERBOSITY     v, vv, vvv, vvvv
     -k KEY           use private key
     -e EXTRAVARS     include as extra vars
     -s               run as sudo
     -c               run in check mode
     -h               show help
```
___
# Ansible Module Index
All Modules are documented [**here**](http://docs.ansible.com/ansible/latest/list_of_all_modules.html)
