import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8001";
const SHORT_CODE = __ENV.SHORT_CODE;
const RPS = Number(__ENV.RPS || 10);

if (!SHORT_CODE) {
  throw new Error("Provide SHORT_CODE using -e SHORT_CODE=yourcode");
}

export const options = {
  discardResponseBodies: true,

  summaryTrendStats: ["avg", "med", "p(90)", "p(95)", "p(99)", "max"],

  scenarios: {
    redirect_load: {
      executor: "constant-arrival-rate",
      rate: RPS,
      timeUnit: "1s",
      duration: __ENV.DURATION || "30s",
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
};

export default function () {
  const response = http.get(`${BASE_URL}/${SHORT_CODE}`, {
    redirects: 0,
    tags: { endpoint: "redirect" },
  });

  check(response, {
    "redirect returned 307": (res) => res.status === 307,
  });
}
