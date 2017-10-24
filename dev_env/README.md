# Development Environment

To increase predicability, it is recommended
that ```tor_async_couchdb``` development be done on a [Vagrant](http://www.vagrantup.com/) provisioned
[VirtualBox](https://www.virtualbox.org/)
VM running [Ubuntu 14.04](http://releases.ubuntu.com/14.04/).
Below are the instructions for spinning up such a VM.

Spin up a VM using [create_dev_env.sh](create_dev_env.sh)
(instead of using ```vagrant up``` - this is the only step
that standard vagrant commands aren't used - after provisioning
the VM you will use ```vagrant ssh```, ```vagrant halt```,
```vagrant up```, ```vagrant status```, etc).

```bash
>./create_dev_env.sh simonsdave simonsdave@gmail.com ~/.ssh/id_rsa.pub ~/.ssh/id_rsa
Bringing machine 'default' up with 'virtualbox' provider...
==> default: Importing base box 'trusty'...
.
.
.
```

SSH into the VM.

```bash
>vagrant ssh
Welcome to Ubuntu 14.04.5 LTS (GNU/Linux 3.13.0-98-generic x86_64)

 * Documentation:  https://help.ubuntu.com/

  System information as of Mon Oct 23 15:22:11 UTC 2017

  System load:  0.63              Processes:           81
  Usage of /:   3.5% of 39.34GB   Users logged in:     0
  Memory usage: 6%                IP address for eth0: 10.0.2.15
  Swap usage:   0%

  Graph this data and manage this system at:
    https://landscape.canonical.com/

  Get cloud support with Ubuntu Advantage Cloud Guest:
    http://www.ubuntu.com/business/services/cloud

0 packages can be updated.
0 updates are security updates.

New release '16.04.3 LTS' available.
Run 'do-release-upgrade' to upgrade to it.


~>
```

Start the ssh-agent in the background.

```bash
~> eval "$(ssh-agent -s)"
Agent pid 25120
~>
```

Add SSH private key for github to the ssh-agent

```bash
~> ssh-add ~/.ssh/id_rsa_github
Enter passphrase for /home/vagrant/.ssh/id_rsa_github:
Identity added: /home/vagrant/.ssh/id_rsa_github (/home/vagrant/.ssh/id_rsa_github)
~>
```

Clone the repo.

```bash
~> git clone https://github.com/simonsdave/tor-async-couchdb.git
~>
```

Install all pre-reqs.

```bash
~> cd tor-async-couchdb/
~/tor-async-couchdb> source cfg4dev.
.
.
.
~>
```

Run all unit & integration tests.

```bash
(env)vagrant@vagrant-ubuntu-trusty-64:~/tor-async-couchdb$ nosetests
............................................................................
----------------------------------------------------------------------
Ran 76 tests in 0.927s

OK
(env)vagrant@vagrant-ubuntu-trusty-64:~/tor-async-couchdb$
```
