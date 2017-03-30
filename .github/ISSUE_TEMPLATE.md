# Issue Type

- Bug report
- Feature request

# Environment detail

```
sh -x << EOF
cat /etc/os-release
python3 --version
ansible-playbook --version
lxc --version
dpkg -l | grep "\(lxd\|ansible\)"
EOF
```

- Edi installation method: One of source, pip, ppa
- Ansible installation method: One of source, pip, OS package
- LXD installation method: One of source, pip, OS package

# Desired Behaviour

Please give some details of the feature being requested or what
should happen if providing a bug report.

# Actual Behaviour (Bug report only)

Please give some details of what is actually happening.
Include a [minimum complete verifiable example](http://stackoverflow.com/help/mcve) with
output of running `edi -v`.
