
# Monumental Take-Home Assignment

This repository contains an interactive brick wall builder implemented in Python as a take-home assignment for Monumental. The application allows users to build a brick wall using different bonding patterns, simulating the process of a robot placing bricks.

## Installation

Install uv: <https://docs.astral.sh/uv/getting-started/installation/>

Setup the virtual environment and install dependencies:

```bash
uv sync
```

## Usage

Run the application:

```bash
uv run python src/app.py
```

## Implementation overview

The codebase is structured into several classes to represent the different components of the brick wall building process:

- `Brick`: Represents a single brick with its dimensions, position, and state.
- `Course`: Represents a horizontal layer of bricks in the wall.
- `Bond`: Represents the brick bonding pattern (e.g., Stretcher Bond, Flemish Bond and Wild Bond).
- `Wall`: Represents the wall being built, containing multiple courses and handling the placement of bricks using the specified bond pattern.
- `Build Algorithm`: Contains the logic for the robot to place bricks, possibly taking into account the build envelope of the robot and gathering statistics about the build process.
- `App`: The main application class that initializes the wall, bond, and build algorithm, and provides a GUI for user interaction.

## Assigment questions

**Can you figure out why a brick is slightly more than two times longer than it is deep?**

*The length of a brick is slightly more than two times its depth to allow for proper bonding on the corner of walls. This way, the side of a brick is the same size as a half-brick.*

**Bonus A: Do the same assignment but for a different brick bond, for example English Cross Bond, or Flemish Bond. What needs to change in order to support multiple bonds? What assumptions need to change?**

*I've implemented the Flemish Bond. I set up most of the classes and methods to be bond-agnostic, knowing that I was going to implement different bonds. The specific bond class place `empty` bricks into the `courses` object in the wall. The build algorithm then just looks at the courses and places bricks accordingly.*

*One assumption that I had the change for the build algorithm was that bricks only require at most two supports. For the Flemish bond, some bricks require three supports.*

**Bonus B: Wild bond**

*I've implemented the Wild Bond as a constraint satisfaction problem. The comments in `src/bonds/wild.py` explain the approach I took.*
