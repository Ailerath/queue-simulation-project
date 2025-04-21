import simpy
import random
import numpy as np
import pathlib
import pandas as pd
import datetime
import requests
import json

INTERARRIVAL_MEAN = 1.0
RNG_SERVICE_MEAN = 2.0
RENEGE_MIN = 2.0
RENEGE_MAX = 3.0

RUN_META = {
    "run_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    "queue_type": "",
    "mode": "",
    "num_customers": 10,
    "num_servers": 2
}

RESULTS_HEADERS = [
    "run_id", "queue_type", "mode",
    "customer_name", "arrival", "start",
    "waiting_time", "service_time",
    "status", "was_helpful", "satisfaction_rating"
]

pathlib.Path("data").mkdir(exist_ok=True)

def call_local_llm(prompt: str) -> str:
    return None

def llm_service_stub(customer_name):
    chat = f"Hello {customer_name}, let's diagnose your issue..."
    real = call_local_llm(chat)
    if real:
        chat = real
    return len(chat) / 100.0

def simulate_customer_feedback():
    return {
        "was_helpful": random.choice([True, False]),
        "satisfaction_rating": random.randint(4, 10)
    }

def fifo_customer(env, name, resource, mode, results):
    arrival = env.now
    with resource.request() as req:
        yield req
        start = env.now
        waiting = start - arrival
        renege_thr = random.uniform(RENEGE_MIN, RENEGE_MAX)
        service_time = random.uniform(RNG_SERVICE_MEAN - 0.5, RNG_SERVICE_MEAN + 0.5) if mode == "RNG" else llm_service_stub(name)
        if service_time > renege_thr:
            status = "reneged"
            departure = env.now
        else:
            yield env.timeout(service_time)
            status = "served"
            departure = env.now
        row = {
            "run_id": RUN_META["run_id"],
            "queue_type": RUN_META["queue_type"],
            "mode": RUN_META["mode"],
            "customer_name": name,
            "arrival": arrival,
            "start": start,
            "waiting_time": waiting,
            "service_time": service_time,
            "status": status,
            "was_helpful": None,
            "satisfaction_rating": None
        }
        if mode == "LLM" and status == "served":
            row.update(simulate_customer_feedback())
        results.append(row)

def simulate_fifo(env, num_customers, num_servers, mode, results):
    resource = simpy.Resource(env, capacity=num_servers)
    for i in range(1, num_customers + 1):
        env.process(fifo_customer(env, f"FIFO_Customer_{i}", resource, mode, results))
        yield env.timeout(random.expovariate(1.0 / INTERARRIVAL_MEAN))

def priority_customer(env, name, resource, mode, results, priority):
    arrival = env.now
    with resource.request(priority=priority) as req:
        yield req
        start = env.now
        waiting = start - arrival
        renege_thr = random.uniform(RENEGE_MIN, RENEGE_MAX)
        service_time = random.uniform(RNG_SERVICE_MEAN - 0.5, RNG_SERVICE_MEAN + 0.5) if mode == "RNG" else llm_service_stub(name)
        if service_time > renege_thr:
            status = "reneged"
            departure = env.now
        else:
            yield env.timeout(service_time)
            status = "served"
            departure = env.now
        row = {
            "run_id": RUN_META["run_id"],
            "queue_type": RUN_META["queue_type"],
            "mode": RUN_META["mode"],
            "customer_name": name,
            "arrival": arrival,
            "start": start,
            "waiting_time": waiting,
            "service_time": service_time,
            "status": status,
            "priority": priority,
            "was_helpful": None,
            "satisfaction_rating": None
        }
        if mode == "LLM" and status == "served":
            row.update(simulate_customer_feedback())
        results.append(row)

def simulate_priority(env, num_customers, num_servers, mode, results):
    resource = simpy.PriorityResource(env, capacity=num_servers)
    for i in range(1, num_customers + 1):
        priority = random.choice([0, 1])
        env.process(priority_customer(env, f"Priority_Customer_{i}", resource, mode, results, priority))
        yield env.timeout(random.expovariate(1.0 / INTERARRIVAL_MEAN))

def simulate_random(env, num_customers, num_servers, mode, results):
    waiting_list = []
    processed_count = [0]
    def arrival_process():
        for i in range(1, num_customers + 1):
            name = f"Random_Customer_{i}"
            arrival = env.now
            waiting_list.append((name, arrival))
            yield env.timeout(random.expovariate(1.0 / INTERARRIVAL_MEAN))
    def server_process(server_id):
        while processed_count[0] < num_customers:
            if waiting_list:
                idx = random.randrange(len(waiting_list))
                name, arrival = waiting_list.pop(idx)
                start = env.now
                waiting = start - arrival
                renege_thr = random.uniform(RENEGE_MIN, RENEGE_MAX)
                service_time = random.uniform(RNG_SERVICE_MEAN - 0.5, RNG_SERVICE_MEAN + 0.5) if mode == "RNG" else llm_service_stub(name)
                if service_time > renege_thr:
                    status = "reneged"
                    departure = env.now
                else:
                    yield env.timeout(service_time)
                    status = "served"
                    departure = env.now
                row = {
                    "run_id": RUN_META["run_id"],
                    "queue_type": RUN_META["queue_type"],
                    "mode": RUN_META["mode"],
                    "customer_name": name,
                    "arrival": arrival,
                    "start": start,
                    "waiting_time": waiting,
                    "service_time": service_time,
                    "status": status,
                    "was_helpful": None,
                    "satisfaction_rating": None
                }
                if mode == "LLM" and status == "served":
                    row.update(simulate_customer_feedback())
                results.append(row)
                processed_count[0] += 1
            else:
                yield env.timeout(0.1)
    env.process(arrival_process())
    for s in range(num_servers):
        env.process(server_process(s + 1))
    while processed_count[0] < num_customers:
        yield env.timeout(0.1)

def run_simulation_type(sim_func, mode, queue_name, num_customers, num_servers):
    RUN_META.update({"queue_type": queue_name, "mode": mode})
    env = simpy.Environment()
    results = []
    env.process(sim_func(env, num_customers, num_servers, mode, results))
    env.run()
    df = pd.DataFrame(results, columns=RESULTS_HEADERS)
    outfile = "data/results_{}_{}.csv".format(RUN_META['run_id'], queue_name.replace(' ', '_'))
    df.to_csv(outfile, index=False)
    print("Saved {} rows to {}".format(len(df), outfile))
    served = (df["status"] == "served").sum()
    reneged = (df["status"] == "reneged").sum()
    return df["waiting_time"].mean(), served, reneged

if __name__ == "__main__":
    random.seed(1)
    np.random.seed(1)
    print("Queue Simulation")
    mode_input = input("Service-time mode [1 RNG / 2 LLM]: ").strip()
    mode = "LLM" if mode_input == "2" else "RNG"
    RUN_META["num_customers"] = 20
    servers_fifo_priority = 2
    servers_random = 1
    print("\nRunning FIFO Queue Simulation...")
    fifo_avg, fifo_served, fifo_reneged = run_simulation_type(
        simulate_fifo, mode, "FIFO", RUN_META["num_customers"], servers_fifo_priority)
    print("\nRunning Priority Queue Simulation...")
    pr_avg, pr_served, pr_reneged = run_simulation_type(
        simulate_priority, mode, "Priority", RUN_META["num_customers"], servers_fifo_priority)
    print("\nRunning Random Queue Simulation...")
    rd_avg, rd_served, rd_reneged = run_simulation_type(
        simulate_random, mode, "Random", RUN_META["num_customers"], servers_random)
    print("\nSimulation Results:")
    print("FIFO Queue:    Average Waiting Time: {:.2f} min, Served: {}, Reneged: {}, Total: {}".format(
        fifo_avg, fifo_served, fifo_reneged, RUN_META["num_customers"]))
    print("Priority Queue:Average Waiting Time: {:.2f} min, Served: {}, Reneged: {}, Total: {}".format(
        pr_avg, pr_served, pr_reneged, RUN_META["num_customers"]))
    print("Random Queue:  Average Waiting Time: {:.2f} min, Served: {}, Reneged: {}, Total: {}".format(
        rd_avg, rd_served, rd_reneged, RUN_META["num_customers"]))

