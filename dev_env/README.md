# Development Environment

To increase predicability, it is recommended
that ```tor_async_couchdb``` development be done on a [Vagrant](http://www.vagrantup.com/) provisioned
[VirtualBox](https://www.virtualbox.org/)
VM running [Ubuntu 16.04](http://releases.ubuntu.com/16.04/).
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
> vagrant ssh
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.4.0-119-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  Get cloud support with Ubuntu Advantage Cloud Guest:
    http://www.ubuntu.com/business/services/cloud

7 packages can be updated.
7 updates are security updates.


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
~> git clone git@github.com:simonsdave/tor-async-couchdb.git
Cloning into 'tor-async-couchdb'...
remote: Counting objects: 1605, done.
remote: Total 1605 (delta 0), reused 0 (delta 0), pack-reused 1605
Receiving objects: 100% (1605/1605), 304.17 KiB | 179.00 KiB/s, done.
Resolving deltas: 100% (995/995), done.
Checking connectivity... done.
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
(env) ~/tor-async-couchdb> nosetests --with-coverage --cover-branches --cover-erase --cover-package tor_async_couchdb
..............................................................................
Name                                       Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------------------------
tor_async_couchdb/async_model_actions.py     399      1     58      2    99%
tor_async_couchdb/clparserutil.py             47      0     10      0   100%
tor_async_couchdb/installer.py               154     69     42     10    51%
tor_async_couchdb/model.py                    16      0      6      0   100%
tor_async_couchdb/retry_strategy.py           21      0      2      0   100%
tor_async_couchdb/tamper.py                   22      0      2      0   100%
----------------------------------------------------------------------------
TOTAL                                        659     70    120     12    87%
----------------------------------------------------------------------
Ran 78 tests in 5.907s

OK
(env) ~/tor-async-couchdb>
```
