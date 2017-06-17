//
// docker run loadimpact/k6 --version
// docker inspect -f '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}' couchdb
// docker run -i loadimpact/k6 run --vus 10 --duration 30s - <script.js
// docker run -v "$PWD":/k6output -v "$PWD":/k6imports -i loadimpact/k6 run --out json=/k6output/foo.json - <script.js
//
// Required Environment variables
//
//  SERVICE_IP
//  SERVICE_PORT
//
//  PERCENT_GET
//  PERCENT_PUT
//

import http from "k6/http";
import { check } from "k6";
import { fruit_ids } from "/k6imports/fruit_ids.js";

export let options = {
  vus: 10,
  duration: "5s"
};

let baseurl = `http://${__ENV.SERVICE_IP}:${__ENV.SERVICE_PORT}/v1.0/fruits/`;

function getRandomFruitID() {
  return fruit_ids[Math.floor(Math.random() * fruit_ids.length)];
}

function httpGet() {
  let url = baseurl + getRandomFruitID();
  let res = http.get(url);
  check(res, {
    "get status was 200": (r) => r.status == 200,
    "get time OK": (r) => r.timings.duration < 150
  });
}

function httpPut() {
  let url = baseurl + getRandomFruitID();
  let payload = {};
  let params = {
    headers: {
      "Content-Type": "application/json"
    }
  };
  let res = http.put(url, JSON.stringify(payload), params);
  check(res, {
    "put status was 200": (r) => r.status == 200,
    "put time OK": (r) => r.timings.duration < 150
  });
}

let http_functions = [];

let percent_get = parseInt(`${__ENV.PERCENT_GET}`);
for(var i = 0; i < percent_get; i++){
  http_functions.push(httpGet);
}

let percent_put = parseInt(`${__ENV.PERCENT_PUT}`);
for(var i = 0; i < percent_put; i++){
  http_functions.push(httpPut);
}

export default function() {
  let http_function = http_functions[Math.floor(Math.random() * http_functions.length)];
  http_function();
};
