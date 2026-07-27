import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    stages: [
        { duration: "30s", target: 500 },
        { duration: "1m", target: 500 },
        { duration: "30s", target: 0 },
    ],
    thresholds: {
        http_req_duration: ["p(95)<100"],
        http_req_failed: ["rate<0.01"],
    },
};

export default function () {
    // Note: To test properly, replace YOUR_SHORT_CODE with a valid short code
    // from your database, or run the locust test which seeds data first.
    const res = http.get("http://localhost:8080/YOUR_SHORT_CODE", { redirects: 0 });
    check(res, { "status is 302": (r) => r.status === 302 });
    sleep(0.1);
}
