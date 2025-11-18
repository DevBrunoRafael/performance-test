import { check } from "k6";
import http from "k6/http";
import { Trend } from "k6/metrics";

export let latency = new Trend("latency");

export default function () {
  const target = __ENV.TARGET || "http://nginx:80/file1.txt";
  let res = http.get(target);
  latency.add(res.timings.duration);
  check(res, { "status is 200": (r) => r.status === 200 });
}
