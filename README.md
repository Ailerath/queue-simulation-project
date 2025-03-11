# Queue Simulation Project

Overview:

This project implements a discrete-event simulation of a customer service queue system using SimPy. The simulation models different queueing strategies and incorporates reneging, where customers may leave the queue if their issue is not resolved in time.

The goal of this project is to study how different queue types handle customer service interactions and evaluate their efficiency in both randomized and LLM-simulated service time scenarios.

The simulation implements three queue types:
FIFO Queue: Customers are served in order of arrival.
Priority Queue: Customers have different priority levels (randomly assigned) and are served accordingly.
Random Queue: Customers are selected randomly from the waiting queue when a server becomes available.

Each queue type supports reneging, where customers leave if they exceed a randomly assigned waiting threshold (between 2-3 minutes). Service times are generated either by:
RNG Mode: A uniform distribution between 1.5 and 2.5 minutes.
LLM Mode: A stub function simulates LLM response processing time. (LLM functionality not yet implemented)

Installation:

To run the simulation, install Python and the required dependencies:

```bash
pip install simpy numpy
