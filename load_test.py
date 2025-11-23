import time
import random
import json
import threading
import statistics
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = "http://localhost:8080"
RPS = 5
DURATION_SECONDS = 60

TEAMS = []
USERS = []
PRS = []
LOCK = threading.RLock()

COUNTERS = {"create_team": 0, "get_team": 0, "create_pr": 0, "get_user_reviews": 0, "merge_pr": 0}


def make_request(method, endpoint, data=None, params=None):
    url = BASE_URL + endpoint
    if params:
        url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    req = Request(url, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode("utf-8")

    start = time.time()
    try:
        with urlopen(req, timeout=10) as response:
            latency = (time.time() - start) * 1000
            return {
                "status": response.status,
                "latency": latency,
                "success": True,
                "body": json.loads(response.read().decode()),
            }
    except HTTPError as e:
        latency = (time.time() - start) * 1000
        return {"status": e.code, "latency": latency, "success": e.code < 500, "error": str(e)}
    except URLError as e:
        latency = (time.time() - start) * 1000
        return {"status": 0, "latency": latency, "success": False, "error": str(e)}
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {"status": 0, "latency": latency, "success": False, "error": str(e)}


def scenario_create_team():
    with LOCK:
        COUNTERS["create_team"] += 1
    team_name = f"team_{random.randint(1, 10000)}"
    members = [
        {
            "user_id": f"u_{random.randint(1, 100000)}",
            "username": f"user_{random.randint(1, 100000)}",
            "is_active": True,
        }
        for _ in range(random.randint(2, 5))
    ]
    res = make_request("POST", "/team/add", data={"team_name": team_name, "members": members})
    if res["status"] == 201:
        with LOCK:
            TEAMS.append(team_name)
            for m in members:
                USERS.append(m["user_id"])
    return res


def scenario_get_team():
    with LOCK:
        COUNTERS["get_team"] += 1
    with LOCK:
        if not TEAMS:
            return scenario_create_team()
        team_name = random.choice(TEAMS)
    return make_request("GET", "/team/get", params={"team_name": team_name})


def scenario_create_pr():
    with LOCK:
        COUNTERS["create_pr"] += 1
    with LOCK:
        if not USERS:
            return scenario_create_team()
        author_id = random.choice(USERS)
    pr_id = f"pr_{random.randint(1, 100000)}"
    res = make_request(
        "POST",
        "/pullRequest/create",
        data={"pull_request_id": pr_id, "pull_request_name": f"PR {pr_id}", "author_id": author_id},
    )
    if res["status"] == 201:
        with LOCK:
            PRS.append(pr_id)
    return res


def scenario_get_user_reviews():
    with LOCK:
        COUNTERS["get_user_reviews"] += 1
    with LOCK:
        if not USERS:
            return scenario_create_team()
        user_id = random.choice(USERS)
    return make_request("GET", "/users/getReview", params={"user_id": user_id})


def scenario_merge_pr():
    with LOCK:
        COUNTERS["merge_pr"] += 1
    with LOCK:
        if not PRS:
            return scenario_create_pr()
        pr_id = random.choice(PRS)
    return make_request("POST", "/pullRequest/merge", data={"pull_request_id": pr_id})


def scenario_stats():
    with LOCK:
        COUNTERS["stats"] += 1
    return make_request("GET", "/stats/")


def scenario_health():
    with LOCK:
        COUNTERS["health"] += 1
    return make_request("GET", "/health")


SCENARIOS = [
    (scenario_create_team, 0.1),
    (scenario_get_team, 0.2),
    (scenario_create_pr, 0.3),
    (scenario_get_user_reviews, 0.2),
    (scenario_merge_pr, 0.1),
]


def run_load_test():
    results = []
    threads = []

    print(f"Starting load test...", flush=True)
    start_time = time.time()
    requests_dispatched = 0

    while time.time() - start_time < DURATION_SECONDS:
        now = time.time()
        target_requests = int((now - start_time) * RPS)
        to_send = target_requests - requests_dispatched

        for _ in range(to_send):
            r = random.random()
            cumulative = 0
            selected_scenario = SCENARIOS[0][0]
            for func, weight in SCENARIOS:
                cumulative += weight
                if r < cumulative:
                    selected_scenario = func
                    break

            t = threading.Thread(target=lambda: results.append(selected_scenario()))
            t.start()
            threads.append(t)
            requests_dispatched += 1

        time.sleep(0.1)

    for t in threads:
        t.join()

    total = len(results)
    if total == 0:
        print("No requests")
        return

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = [r["latency"] for r in results]

    avg_latency = statistics.mean(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    success_rate = (len(successes) / total) * 100

    print("\nResults")
    print(f"Total Requests: {total}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Avg Latency: {avg_latency:.2f} ms")
    print(f"P95 Latency: {p95_latency:.2f} ms")
    print(f"Failures: {len(failures)}")

    print("\nCounters")
    for k, v in COUNTERS.items():
        print(f"{k}: {v}")

    if failures:
        print(f"Sample error: {failures[0].get('error') or failures[0].get('status')}")


if __name__ == "__main__":
    run_load_test()
