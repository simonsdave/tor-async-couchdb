# loadgen

A [k6](https://k6.io) based utility which drives CRUD style
load through the sample services exercising ```tor-async-couchdb```'s
conflict resolution logic.

[loadgen.sh](loadgen.sh):

* assumes a sample service is listening on ```http://docker0:8445```
* runs [create_fruit.py](create_fruit.py) to create a bunch of fruit
* starts [k6](https://k6.io) to drive requests through the sample service

```bash
>./loadgen.sh --help
usage: loadgen.sh [OPTION...]

  -h, --help                              this message
  -v, --verbose                           verbose output
  -k6di, --k6-docker-image [IMAGE NAME]   k6 docker image (loadimpact/k6:0.16.0 = default)
  -nf, --number-fruit [NUMBER FRUIT]      number fruit (50 = default)
  -cur, --concurrency [NUMBER]            concurrency level (10 = default)
  -dur, --duration [DURATION]             duration (1m = default)
  -pg, --percent-get [PERCENT]            % get requests (100% = default)
  -pp, --percent-put [PERCENT]            % put requests (0% = default)
>
```

> [loadgen.sh](loadgen.sh) is designed to exercise ```tor-async-couchdb```'s
> conflict resolution logic which is trigged when multiple requests simultaneously
> attempt to do things to the same resource.
> The probability of a conflict being triggered increases both as the number
> of concurrent requests increases, the percentage of ```PUT``` requests increases
> and the number of resources decreases.
