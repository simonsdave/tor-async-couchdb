//
// Required Environment variables
//
//  SERVICE
//
//  PERCENT_GET
//  PERCENT_PUT
//

import http from "k6/http";
import { check } from "k6";
import { fruit_ids } from "/k6imports/fruit_ids.js";

let service_base_url = `${__ENV.SERVICE}/v1.0/fruits/`;

let colors = ["red", "orange", "blue", "brown", "yellow", "pink", "white", "black"];

function getRandomFruitID() {
  return fruit_ids[Math.floor(Math.random() * fruit_ids.length)];
}

function httpGet() {
  let url = service_base_url + getRandomFruitID();
  let res = http.get(url);
  check(res, {
    "get status was 200": (r) => r.status == 200
  });
}

function httpPut() {
  let url = service_base_url + getRandomFruitID();
  let payload = {
    "color": colors[Math.floor(Math.random() * colors.length)]
  };
  let params = {
    headers: {
      "Content-Type": "application/json"
    }
  };
  let res = http.put(url, JSON.stringify(payload), params);
  check(res, {
    "put status was 200": (r) => r.status == 200
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
