import queue_simulation as qs
import pandas as pd
import pathlib
import matplotlib.pyplot as plt

pathlib.Path("data").mkdir(exist_ok=True)

SCENARIOS = {
    "Baseline": {
        "arrival_rate": 1.0,
        "service_duration": 2.0,
        "num_agents": 2
    },
    "Optimistic": {
        "arrival_rate": 0.8,
        "service_duration": 1.8,
        "num_agents": 3
    },
    "Pessimistic": {
        "arrival_rate": 1.3,
        "service_duration": 2.2,
        "num_agents": 1
    }
}

QUEUE_TYPES = {
    "FIFO": qs.simulate_fifo,
    "Priority": qs.simulate_priority,
    "Random": qs.simulate_random
}

records = []

for scen_name, params in SCENARIOS.items():
    for qname, qfunc in QUEUE_TYPES.items():
        qs.RUN_META.update({
            "run_id": f"SCEN_{scen_name}",
            "queue_type": qname,
            "mode": "RNG",
            "num_customers": 50
        })
        qs.INTERARRIVAL_MEAN = 1 / params["arrival_rate"]
        qs.RNG_SERVICE_MEAN = params["service_duration"]

        avg, served, reneged = qs.run_simulation_type(
            qfunc, "RNG", qname, 50, params["num_agents"])

        records.append({
            "scenario": scen_name,
            "queue": qname,
            "arrival_rate": params["arrival_rate"],
            "service_duration": params["service_duration"],
            "num_agents": params["num_agents"],
            "avg_wait": avg,
            "served": served,
            "reneged": reneged
        })

df = pd.DataFrame(records)
df.to_csv("data/scenario_results.csv", index=False)

# Bar chart: average wait by queue per scenario
pivot = df.pivot(index="queue", columns="scenario", values="avg_wait")
pivot.plot(kind="bar", title="Avg Wait by Queue Type Across Scenarios")
plt.ylabel("Avg Waiting Time (min)")
plt.tight_layout()
plt.savefig("scenario_chart.png")
plt.show()
