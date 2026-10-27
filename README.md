# LastLap

An autonomous 2D racing simulation built with Python and Pygame, powered by the NEAT (NeuroEvolution of Augmenting Topologies) algorithm. The project trains a population of neural networks to navigate custom-drawn circuits using distance-based raycast sensors, optimizing for speed and smooth steering.

## Features
* **Image-Based Collision Masking:** Design tracks in any image editor using solid colors. The physics engine reads pixel data to calculate track boundaries.
* **Raycast Vision:** Vehicles perceive the track using 5 directional raycasts that calculate the exact distance to the nearest wall.
* **NEAT Integration:** Evolve neural networks dynamically. The fitness function rewards distance traveled while penalizing crashes, hard steering, and stagnant behaviors (like standing still or driving in circles).
* **Headless-Ready:** The architecture separates the scaled Pygame display from the massive underlying world coordinates, making it ready for remote server training.
* **Model Serialization:** Save the highest-performing genome as a `.pkl` file to test or race against other algorithms on brand-new circuits.

## Requirements
Ensure you have Python 3 installed, then install the required dependencies:

```bash
pip install pygame neat-python
```

## Project Structure
* `train_neat.py`: The main evolutionary loop. Evaluates generations, handles mutations, and saves the best model.
* `test_model.py`: Loads a saved `.pkl` model and runs it on a target track for testing and visualization.
* `config.txt`: The NEAT configuration parameters defining population size, mutation rates, and network architecture.
* `circuit.png`: The default 4000x2251 training track mask (black asphalt on a solid green background).

## Usage
### 1. Train the Model
Run the training script to spawn the initial population. The simulation will run until a genome hits the fitness threshold or the maximum generation count is reached.

```bash
python train_neat.py
```
*Note: You can manually interrupt training (if coded to catch it) or let it finish to generate the `winner.pkl` file.*

### 2. Test the Winner
Once training completes and `winner.pkl` is generated, you can test this trained model on a new track layout by running:

```bash
python test_model.py
```

## Customizing Tracks
To create a new circuit for training or testing:
1. Draw a `4000x2251` image in any editor.
2. Fill the drivable racing line with pure black `(0, 0, 0)`.
3. Fill the off-track areas with solid green `(0, 255, 0)`. 
4. **Avoid anti-aliasing, soft brushes, or watermarks.**
5. Update the initial spawn coordinates `(self.x, self.y)` in the `Car` class of your scripts to match a valid starting location on your new asphalt.
