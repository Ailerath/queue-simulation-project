import itertools
import queue_simulation as qs
import pandas as pd
import pathlib

pathlib.Path("data").mkdir(exist_ok=True)
pathlib.Path("sensitivity").mkdir(exist_ok=True)

PARAM_GRID = {
    "arrival_rate": [0.5, 1.0, 1.5],
    "service_duration": [1.5, 2.0, 2.5],
    "num_agents": [1, 2, 3],
    "patience_limit": [2.5, 3.0, 3.5]
}

QUEUE_TYPES = {
    "FIFO": qs.simulate_fifo,
    "Priority": qs.simulate_priority,
    "Random": qs.simulate_random
}

results = []
run_id = 0

for (arrival_rate, service_duration, num_agents, patience_limit), (qname, qfunc) in itertools.product(
    itertools.product(*PARAM_GRID.values()), QUEUE_TYPES.items()
):
    run_id += 1
    qs.RUN_META.update({
        "run_id": f"SENS_{run_id:03d}",
        "queue_type": qname,
        "mode": "RNG",
        "num_customers": 50
    })
    qs.INTERARRIVAL_MEAN = 1 / arrival_rate
    qs.RNG_SERVICE_MEAN = service_duration
    qs.RENEGE_MAX = patience_limit

    avg, served, reneged = qs.run_simulation_type(
        qfunc, "RNG", qname, 50, num_agents)

    results.append({
        "run_id": run_id,
        "queue": qname,
        "arrival_rate": arrival_rate,
        "service_duration": service_duration,
        "num_agents": num_agents,
        "patience_limit": patience_limit,
        "avg_wait": avg,
        "served": served,
        "reneged": reneged
    })

df = pd.DataFrame(results)
df.to_csv("sensitivity/sensitivity_results.csv", index=False)
print("Sensitivity complete and saved.")
