## retropie
Installs all configurations for a [**Retropie 4.4**](https://retropie.org.uk/2018/04/retropie-4-4-is-released/) install

#### Allow SSH connectivity
- Connect Wifi
- sudo raspi-config
  - 5 --> 2 [Turn on SSH client]
  - 7 --> 1 [Expand FileSystem]

#### Setup
- Bootstrap
  - Copy 'Bootstrap' to terminal
  - Execute Bootstrap
- Configure your profile
    - Create a user profile in "**user_profiles/**" from template "**user_profiles/\_\_DEMO\_\_.yml**"

#### Run
`./go.sh -s -p retropie -u pi`

#### Bootstrap
```bash
sudo apt install -y python3 python3-pip python3-setuptools git \
  && sudo pip3 install ansible \
  && git clone https://github.com/OurFriendIrony/ansible.git /tmp/ansible \
  && cd /tmp/ansible
```

