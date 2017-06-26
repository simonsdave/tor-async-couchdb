# loadgen

A [k6](https://k6.io) based utility which drives CRUD style
load through the sample services demonstrating ```tor-async-couchdb```'s
conflict resolution logic.

[loadgen.sh](loadgen.sh):

* assumes a sample service is listening on ```http://127.0.0.1:8445```
* runs [create_fruit.py](create_fruit.py) to create a bunch of fruit
* starts [k6](https://k6.io) to drive requests through the sample service

```bash
> ./loadgen.sh --help
usage: loadgen.sh [OPTION...]

  -h, --help                          this message
  -v                                  verbose output
  -nf, --number-fruit [NUMBER FRUIT]  number fruit (50 = default)
  -pg, --percent-get [PERCENT]        % get requests (100% = default)
  -pp, --percent-put [PERCENT]        % put requests (0% = default)
>
```

When selecting [loadgen.sh](loadgen.sh) is designed to exercise ```tor-async-couchdb```'s
conflict resolution logic which is trigged when multiple requests simultaneously
attempt to do things to the same resource.
The probability of a conflict being triggered increases both as the number
of concurrent requests increases, the percentage of ```PUT``` requests increases
and the number of resources decreases.
