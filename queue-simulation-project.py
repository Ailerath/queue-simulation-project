import simpy
import random
import numpy as np

def llm_service_stub(customer_name):
    """
    LLM service stub
    API for the LLM server would be called here
    Currently a chat is simulated with a fixed message.
    """
    simulated_chat = "This is a simulated LLM chat for resolving customer issues."
    num_characters = len(simulated_chat)
    print(f"LLM processing for {customer_name}: simulated chat length is {num_characters} characters.")
    #Scale factor to convert character count into minutes
    service_time = num_characters / 100.0  
    return service_time

def fifo_customer(env, name, resource, mode, results):
    arrival = env.now
    print(f"{name} arrives at {arrival:.2f}")
    with resource.request() as req:
        yield req
        start = env.now
        waiting_time = start - arrival
        #Generate reneging threshold and solution time
        renege_threshold = random.uniform(2, 3)
        if mode == "RNG":
            service_time = random.uniform(1.5, 2.5)
        else:
            service_time = llm_service_stub(name)
        if service_time > renege_threshold:
            #Customer reneges immediately when service is about to start
            print(f"{name} reneged (service_time {service_time:.2f} > threshold {renege_threshold:.2f}) at {env.now:.2f}")
            results.append({'name': name, 'arrival': arrival, 'start': start, 'departure': env.now,
                            'waiting': waiting_time, 'service_time': service_time, 'status': 'reneged'})
        else:
            yield env.timeout(service_time)
            departure = env.now
            print(f"{name} served and departs at {departure:.2f}")
            results.append({'name': name, 'arrival': arrival, 'start': start, 'departure': departure,
                            'waiting': waiting_time, 'service_time': service_time, 'status': 'served'})

def simulate_fifo(env, num_customers, num_servers, mode, results):
    resource = simpy.Resource(env, capacity=num_servers)
    for i in range(1, num_customers + 1):
        env.process(fifo_customer(env, f"FIFO_Customer {i}", resource, mode, results))
        #Random interarrival time (mean = 1 minute)
        yield env.timeout(random.expovariate(1.0))

def priority_customer(env, name, resource, mode, results, priority):
    arrival = env.now
    print(f"{name} (priority {priority}) arrives at {arrival:.2f}")
    with resource.request(priority=priority) as req:
        yield req
        start = env.now
        waiting_time = start - arrival
        renege_threshold = random.uniform(2, 3)
        if mode == "RNG":
            service_time = random.uniform(1.5, 2.5)
        else:
            service_time = llm_service_stub(name)
        if service_time > renege_threshold:
            print(f"{name} reneged (service_time {service_time:.2f} > threshold {renege_threshold:.2f}) at {env.now:.2f}")
            results.append({'name': name, 'arrival': arrival, 'start': start, 'departure': env.now,
                            'waiting': waiting_time, 'service_time': service_time, 'status': 'reneged', 'priority': priority})
        else:
            yield env.timeout(service_time)
            departure = env.now
            print(f"{name} served and departs at {departure:.2f}")
            results.append({'name': name, 'arrival': arrival, 'start': start, 'departure': departure,
                            'waiting': waiting_time, 'service_time': service_time, 'status': 'served', 'priority': priority})

def simulate_priority(env, num_customers, num_servers, mode, results):
    resource = simpy.PriorityResource(env, capacity=num_servers)
    for i in range(1, num_customers + 1):
        #Priority: 0 for high, 1 for normal.
        priority = random.choice([0, 1])
        env.process(priority_customer(env, f"Priority_Customer {i}", resource, mode, results, priority))
        yield env.timeout(random.expovariate(1.0))

def simulate_random(env, num_customers, num_servers, mode, results):
    waiting_list = []
    processed_count = [0]  #counter to track processed customers

    def arrival_process():
        for i in range(1, num_customers + 1):
            name = f"Random_Customer {i}"
            arrival = env.now
            print(f"{name} arrives at {arrival:.2f}")
            waiting_list.append((name, arrival))
            yield env.timeout(random.expovariate(1.0))

    def server_process(server_id):
        while processed_count[0] < num_customers:
            if waiting_list:
                #Pick a random customer from the waiting list
                idx = random.randrange(len(waiting_list))
                name, arrival = waiting_list.pop(idx)
                start = env.now
                waiting_time = start - arrival
                renege_threshold = random.uniform(2, 3)
                if mode == "RNG":
                    service_time = random.uniform(1.5, 2.5)
                else:
                    service_time = llm_service_stub(name)
                if service_time > renege_threshold:
                    print(f"{name} (server {server_id}) reneged (service_time {service_time:.2f} > threshold {renege_threshold:.2f}) at {env.now:.2f}")
                    results.append({'name': name, 'arrival': arrival, 'start': start, 'departure': env.now,
                                    'waiting': waiting_time, 'service_time': service_time, 'status': 'reneged'})
                else:
                    yield env.timeout(service_time)
                    departure = env.now
                    print(f"{name} (server {server_id}) served and departs at {departure:.2f}")
                    results.append({'name': name, 'arrival': arrival, 'start': start, 'departure': departure,
                                    'waiting': waiting_time, 'service_time': service_time, 'status': 'served'})
                processed_count[0] += 1
            else:
                yield env.timeout(0.1)

    env.process(arrival_process())
    for s in range(num_servers):
        env.process(server_process(s + 1))
    #Keep the simulation running until all customers are processed
    while processed_count[0] < num_customers:
        yield env.timeout(0.1)

def run_simulation_type(sim_func, mode, queue_name, num_customers, num_servers):
    env = simpy.Environment()
    results = []
    env.process(sim_func(env, num_customers, num_servers, mode, results))
    env.run()
    served = sum(1 for r in results if r['status'] == 'served')
    reneged = sum(1 for r in results if r['status'] == 'reneged')
    avg_waiting = np.mean([r['waiting'] for r in results]) if results else 0
    return {
        'queue_type': queue_name,
        'avg_waiting_time': avg_waiting,
        'served': served,
        'reneged': reneged,
        'total': len(results)
    }

if __name__ == "__main__":
    print("Queue Simulation with 3 Queue Types")
    print("Select simulation mode for service times:")
    print("1. RNG-based service times")
    print("2. LLM-based service times (stub)")
    mode_input = input("Enter 1 or 2: ").strip()
    mode = "LLM" if mode_input == "2" else "RNG"
    
    num_customers = 10
    #FIFO and Priority will use 2 servers, the Random queue will use 1 server
    servers_fifo_priority = 2
    servers_random = 1
    
    print("\nRunning FIFO Queue Simulation...")
    stats_fifo = run_simulation_type(simulate_fifo, mode, "FIFO Queue", num_customers, servers_fifo_priority)
    
    print("\nRunning Priority Queue Simulation...")
    stats_priority = run_simulation_type(simulate_priority, mode, "Priority Queue", num_customers, servers_fifo_priority)
    
    print("\nRunning Random Queue Simulation...")
    stats_random = run_simulation_type(simulate_random, mode, "Random Queue", num_customers, servers_random)
    
    #Output results
    print("\nSimulation Results:")
    print("FIFO Queue:    Average Waiting Time: {:.2f} min, Served: {}, Reneged: {}, Total: {}"
          .format(stats_fifo['avg_waiting_time'], stats_fifo['served'], stats_fifo['reneged'], stats_fifo['total']))
    print("Priority Queue:Average Waiting Time: {:.2f} min, Served: {}, Reneged: {}, Total: {}"
          .format(stats_priority['avg_waiting_time'], stats_priority['served'], stats_priority['reneged'], stats_priority['total']))
    print("Random Queue:  Average Waiting Time: {:.2f} min, Served: {}, Reneged: {}, Total: {}"
          .format(stats_random['avg_waiting_time'], stats_random['served'], stats_random['reneged'], stats_random['total']))
