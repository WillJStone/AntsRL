import pickle
from tqdm import tqdm
import datetime
import time
import sys
import tensorflow as tf

from gui.visualize import Visualizer

from environment.RL_api import RLApi
from generator.environment_generator import EnvironmentGenerator
from generator.map_generators import *
from agents.random_agent import RandomAgent
from environment.rewards.exploration_reward import ExplorationReward

from agents.explore_agent_pytorch import ExploreAgentPytorch
from agents.explore_agent import ExploreAgent

# -------------------------------------------
#               Main parameters
# -------------------------------------------
aggregate_stats_every = 5
save_model = True
training = False
#use_model = None
only_visualize = False
use_model = "6_4_14_explore_agent_pytorch.h5"
save_file_name = "explore_agent_pytorch.arl"


# -------------------------------------------


def main():
    episodes = 10
    steps = 500
    n_ants = 50
    states = []

    # Setting up environment
    generator = EnvironmentGenerator(w=200,
                                     h=200,
                                     n_ants=n_ants,
                                     n_pheromones=2,
                                     n_rocks=0,
                                     food_generator=CirclesGenerator(10, 5, 10),
                                     walls_generator=PerlinGenerator(scale=22.0, density=0.06),
                                     max_steps=steps)

    # Setting up RL Reward
    reward = ExplorationReward()

    # Setting up RL Api
    api = RLApi(reward=reward,
                max_speed=1,
                max_rot_speed=45,
                carry_speed_reduction=0.05,
                backward_speed_reduction=0.5)
    api.save_perceptive_field = True

    # Setting up RL Agent
    agent = ExploreAgentPytorch(epsilon=0.1,
                         discount=0.5,
                         rotations=3)
    agent_is_setup = False

    avg_loss = None
    avg_time = None

    print("Starting simulation...")
    for episode in range(episodes):
        env = generator.generate(api)
        print('\n--- Episode {}/{} ---'.format(episode, episodes))

        # Setups the agents only once
        if not agent_is_setup:
            agent.setup(api, use_model)
            agent_is_setup = True

        # Initializes the agents on the new environment
        agent.initialize(api)

        obs, state = api.observation()
        episode_reward = np.zeros(n_ants)

        for s in range(steps):
            now = time.time()

            if (episode + 1) % 10 == 0 or episode == 0 or not training:
                states.append(env.save_state())

            # Compute the next action of the agents
            action = agent.get_action(obs, training)

            # Execute the action
            new_state, reward, done = api.step(*action)

            # Add the reward to total reward of episode
            episode_reward += reward

            # Update replay memory with new action and states
            agent.update_replay_memory(obs, action, reward, new_state, done)

            # Train the neural network
            if training:
                loss = agent.train(done, s)

                if avg_loss is None:
                    avg_loss = loss
                else:
                    avg_loss = 0.99 * avg_loss + 0.01 * loss
            else:
                avg_loss = 0

            # Set obs to the new state
            obs = new_state

            if (s + 1) % 50 == 0:
                mean_reward = episode_reward.mean()
                max_reward = episode_reward.max()
                min_reward = episode_reward.min()
                var_reward = episode_reward.std()
                total_reward = episode_reward.sum()

                print("\rAverage loss: {:.5f} --".format(avg_loss),
                      "Episode reward stats: mean {:.2f} - min {:.2f} - max {:.2f} - std {:.2f} - total {:.2f} --".format(
                          mean_reward, min_reward, max_reward, var_reward, total_reward),
                      "Avg-time per step: {:.3f}ms".format(avg_time),
                      end="")

            # Pass new step
            env.update()

            elapsed = (time.time() - now) * 1000
            if avg_time is None:
                avg_time = elapsed
            else:
                avg_time = 0.99 * avg_time + 0.01 * elapsed

    pickle.dump(states, open("saved/" + save_file_name, "wb"))

    if save_model and training:
        date = datetime.datetime.now()
        model_name = str(date.day) + '_' + str(date.month) + '_' + str(date.hour) + '_' + agent.name + '.h5'
        agent.save_model(model_name)


if __name__ == '__main__':
    if not only_visualize:
        main()

    visualiser = Visualizer()
    visualiser.big_dim = 700
    visualiser.visualize(save_file_name)
