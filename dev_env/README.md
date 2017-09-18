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
Welcome to Ubuntu 14.04 LTS (GNU/Linux 3.13.0-27-generic x86_64)

 * Documentation:  https://help.ubuntu.com/

 System information disabled due to load higher than 1.0

  Get cloud support with Ubuntu Advantage Cloud Guest:
    http://www.ubuntu.com/business/services/cloud

0 packages can be updated.
0 updates are security updates.


vagrant@vagrant-ubuntu-trusty-64:~$
```

Start the ssh-agent in the background.

```bash
~> eval "$(ssh-agent -s)"
Agent pid 25657
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
vagrant@vagrant-ubuntu-trusty-64:~$ git clone https://github.com/simonsdave/tor-async-couchdb.git
Cloning into 'tor-async-couchdb'...
remote: Counting objects: 1114, done.
remote: Compressing objects: 100% (7/7), done.
remote: Total 1114 (delta 0), reused 0 (delta 0), pack-reused 1107
Receiving objects: 100% (1114/1114), 237.13 KiB | 0 bytes/s, done.
Resolving deltas: 100% (678/678), done.
Checking connectivity... done.
vagrant@vagrant-ubuntu-trusty-64:~$
```

Install all pre-reqs.

```bash
vagrant@vagrant-ubuntu-trusty-64:~$ cd tor-async-couchdb/
vagrant@vagrant-ubuntu-trusty-64:~/tor-async-couchdb$ source cfg4dev
New python executable in env/bin/python
Installing setuptools, pip...done.
.
.
.
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
