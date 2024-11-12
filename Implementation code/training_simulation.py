import traci
import numpy as np
import random
import timeit
import os

PHASE_NS_GREEN = 0  # action 0 code 00
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2  # action 1 code 01
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4  # action 2 code 10
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6  # action 3 code 11
PHASE_EWL_YELLOW = 7

PHASE_NS_GREEN2 = 0  # action 0 code 00
PHASE_NS_YELLOW2 = 1
PHASE_NSL_GREEN2 = 2  # action 1 code 01
PHASE_NSL_YELLOW2 = 3
PHASE_EW_GREEN2 = 4  # action 2 code 10
PHASE_EW_YELLOW2 = 5
PHASE_EWL_GREEN2 = 6  # action 3 code 11
PHASE_EWL_YELLOW2 = 7

class Simulation:
    def __init__(self, Model, Memory, TrafficGen, sumo_cmd, gamma, max_steps, green_duration, yellow_duration, num_states, num_actions, training_epochs):
        self._Model = Model
        self._Memory = Memory
        self._TrafficGen = TrafficGen
        self._gamma = gamma
        self._step = 0
        self._sumo_cmd = sumo_cmd
        self._max_steps = max_steps
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._num_states = num_states
        self._num_actions = num_actions
        self._reward_store = []
        self._cumulative_wait_store = []
        self._avg_queue_length_store = []
        self._training_epochs = training_epochs


    def run(self, episode, epsilon):

        start_time = timeit.default_timer()
        traci.start(self._sumo_cmd)
        print("Simulating...")

        # inits
        self._step = 0
        self._waiting_times = {}
        self._sum_neg_reward = 0
        self._sum_queue_length = 0
        self._sum_waiting_time = 0
        old_total_wait = 0
        old_state = -1
        old_action = -1

        while self._step < self._max_steps:


            current_state = self._get_state()
            current_total_wait = self._collect_waiting_times()
            reward = 0.6 * (old_total_wait - current_total_wait) - 0.5 * (self._get_queue_length())

            if self._step != 0:
                self._Memory.add_sample((old_state, old_action, reward, current_state))

            action = self._choose_action(current_state, epsilon)

            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(self._yellow_duration)

            self._set_green_phase(action)
            self._simulate(self._green_duration)

            old_state = current_state
            old_action = action
            old_total_wait = current_total_wait

            if reward < 0:
                self._sum_neg_reward += reward

        self._save_episode_stats()
        print("Total reward:", self._sum_neg_reward, "- Epsilon:", round(epsilon, 2))
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        print("Training...")
        start_time = timeit.default_timer()
        for _ in range(self._training_epochs):
            self._replay()
        training_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time, training_time


    def _simulate(self, steps_todo):

        if (self._step + steps_todo) >= self._max_steps:
            steps_todo = self._max_steps - self._step

        while steps_todo > 0:
            traci.simulationStep()
            self._step += 1
            steps_todo -= 1
            queue_length = self._get_queue_length()
            self._sum_queue_length += queue_length
            self._sum_waiting_time += queue_length


    def _collect_waiting_times(self):

        incoming_roads_1 = ["E2TL", "N2TL", "W2TL", "S2TL"]
        incoming_roads_2 = ["TL2E", "E1", "E0"]
        car_list = traci.vehicle.getIDList()
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)
            if road_id in incoming_roads_1:
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times:
                    del self._waiting_times[car_id]
        total_waiting_time_1 = sum(self._waiting_times.values())
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)
            if road_id in incoming_roads_2:
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times:
                    del self._waiting_times[car_id]
        total_waiting_time_2 = sum(self._waiting_times.values())
        total_waiting_time = total_waiting_time_2
        ped_list = traci.person.getIDList()
        for ped_id in ped_list:
            wait_time = traci.person.getWaitingTime(ped_id)
            self._waiting_times[ped_id] = wait_time
        total_waiting_time += sum(self._waiting_times.values())
        self._waiting_time_V.append(total_waiting_time)
        return total_waiting_time


    def _choose_action(self, state, epsilon):

        if random.random() < epsilon:
            return random.randint(0, self._num_actions - 1) # random action
        else:
            return np.argmax(self._Model.predict_one(state)) # the best action given the current state


    def _set_yellow_phase(self, old_action):

        yellow_phase_code = old_action * 2 + 1 # obtain the yellow phase code, based on the old action (ref on environment.net.xml)
        traci.trafficlight.setPhase("TL", yellow_phase_code)


    def _set_green_phase(self, action_number):

        if action_number == 0:
            traci.trafficlight.setPhase("TL", PHASE_NS_GREEN)
            traci.trafficlight.setPhase("DE", PHASE_EWL_GREEN2)
        elif action_number == 1:
            traci.trafficlight.setPhase("TL", PHASE_NSL_GREEN)
            traci.trafficlight.setPhase("DE", PHASE_EW_GREEN2)
        elif action_number == 2:
            traci.trafficlight.setPhase("TL", PHASE_EW_GREEN)
            traci.trafficlight.setPhase("DE", PHASE_NSL_GREEN2)
        elif action_number == 3:
            traci.trafficlight.setPhase("TL", PHASE_EWL_GREEN)
            traci.trafficlight.setPhase("DE", PHASE_NS_GREEN2)


    def _get_queue_length(self):

        halt_N = traci.edge.getLastStepHaltingNumber("N2TL")
        halt_S = traci.edge.getLastStepHaltingNumber("S2TL")
        halt_E = traci.edge.getLastStepHaltingNumber("E2TL")
        halt_W = traci.edge.getLastStepHaltingNumber("W2TL")
        halt_i1 = traci.edge.getLastStepHaltingNumber("TL2E")
        halt_i2 = traci.edge.getLastStepHaltingNumber("E0")
        halt_i3 = traci.edge.getLastStepHaltingNumber("E1")
        queue_length = ( (halt_N + halt_S + halt_E + halt_W) + (halt_i1 + halt_i2 + halt_i3) ) / 2
        return queue_length


    def _get_state(self):

        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            lane_pos = traci.vehicle.getLanePosition(car_id)
            lane_id = traci.vehicle.getLaneID(car_id)
            lane_pos = 750 - lane_pos


            if lane_pos < 7:
                lane_cell = 0
            elif lane_pos < 14:
                lane_cell = 1
            elif lane_pos < 21:
                lane_cell = 2
            elif lane_pos < 28:
                lane_cell = 3
            elif lane_pos < 40:
                lane_cell = 4
            elif lane_pos < 60:
                lane_cell = 5
            elif lane_pos < 100:
                lane_cell = 6
            elif lane_pos < 160:
                lane_cell = 7
            elif lane_pos < 400:
                lane_cell = 8
            elif lane_pos <= 750:
                lane_cell = 9

            if lane_id == "W2TL_1" or lane_id == "W2TL_2" or lane_id == "W2TL_3":
                lane_group = 0
            elif lane_id == "W2TL_4":
                lane_group = 1
            elif lane_id == "N2TL_1" or lane_id == "N2TL_2" or lane_id == "N2TL_3" or lane_id == "E0_1" or lane_id == "E1_1" or lane_id == "E1_2":
                lane_group = 2
            elif lane_id == "N2TL_4":
                lane_group = 3
            elif lane_id == "E2TL_1" or lane_id == "E2TL_2" or lane_id == "E2TL_3" or lane_id == "TL2E_2" or lane_id == "TL2E_3" or lane_id == "TL2E_4":
                lane_group = 4
            elif lane_id == "E2TL_4" or lane_id == "TL2E_1":
                lane_group = 5
            elif lane_id == "S2TL_1" or lane_id == "S2TL_2" or lane_id == "S2TL_3":
                lane_group = 6
            elif lane_id == "S2TL_4":
                lane_group = 7
            else:
                lane_group = -1

            if lane_group >= 1 and lane_group <= 7:
                car_position = int(str(lane_group) + str(lane_cell))
                valid_car = True
            elif lane_group == 0:
                car_position = lane_cell
                valid_car = True
            else:
                valid_car = False

            if valid_car:
                state[car_position] = 1
        return state


    def _replay(self):

        batch = self._Memory.get_samples(self._Model.batch_size)

        if len(batch) > 0:
            states = np.array([val[0] for val in batch])
            next_states = np.array([val[3] for val in batch])

            q_s_a = self._Model.predict_batch(states)
            q_s_a_d = self._Model.predict_batch(next_states)

            x = np.zeros((len(batch), self._num_states))
            y = np.zeros((len(batch), self._num_actions))

            for i, b in enumerate(batch):
                state, action, reward, _ = b[0], b[1], b[2], b[3]
                current_q = q_s_a[i]
                current_q[action] = reward + self._gamma * np.amax(q_s_a_d[i])
                x[i] = state
                y[i] = current_q
            self._Model.train_batch(x, y)


    def _save_episode_stats(self):

        self._reward_store.append(self._sum_neg_reward)
        self._cumulative_wait_store.append(self._sum_waiting_time)
        self._avg_queue_length_store.append(self._sum_queue_length / self._max_steps)


    @property
    def reward_store(self):
        return self._reward_store


    @property
    def cumulative_wait_store(self):
        return self._cumulative_wait_store


    @property
    def avg_queue_length_store(self):
        return self._avg_queue_length_store

