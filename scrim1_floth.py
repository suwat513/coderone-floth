'''
TEMPLATE for creating your own Agent to compete in
'Dungeons and Data Structures' at the Coder One AI Sports Challenge 2020.
For more info and resources, check out: https://bit.ly/aisportschallenge

BIO:
Floth - The fastest ~Sloth~
Use A* Search approach to find the shortest path from agent to the target tile
- Heuristic function used Manhattan Distance (City Block)
- But just A* Search is not enough since there are many scenarios and targets
- Implement the rules on top of A* Search to determine the target tiles on each scenarios
'''

import random
from heapq import heapify, heappush, heappop
from collections import deque, defaultdict


class Agent:

    def __init__(self):
        self.name = "Floth"
        self.rows = 10
        self.cols = 12
        self.bomb_tick = 35
        self.prev_action = 0
        self.prev_position = None
        self.player_position = (0, 0)
        self.bomb_dict = {}
        self.ore_dict = {}
        self.init_ore_dict = True
        self.queue_action = ""
        self.lag = False

    def get_surrounding_tiles(self, tile):
        if tile[1] > 0:
            yield (tile[0], tile[1] - 1), "d"
        if tile[1] < self.rows - 1:
            yield (tile[0], tile[1] + 1), "u"
        if tile[0] > 0:
            yield (tile[0] - 1, tile[1]), "l"
        if tile[0] < self.cols - 1:
            yield (tile[0] + 1, tile[1]), "r"

    def get_bomb_range_tiles(self, game_state, tile):
        if tile[1] > 0:
            yield (tile[0], tile[1] - 1)
        if tile[1] < self.rows - 1:
            yield (tile[0], tile[1] + 1)
        if tile[0] > 0:
            yield (tile[0] - 1, tile[1])
        if tile[0] < self.cols - 1:
            yield (tile[0] + 1, tile[1])
        if tile[1] > 1 and game_state.entity_at((tile[0], tile[1] - 1)) is None:
            yield (tile[0], tile[1] - 2)
        if tile[1] < self.rows - 2 and game_state.entity_at((tile[0], tile[1] + 1)) is None:
            yield (tile[0], tile[1] + 2)
        if tile[0] > 1 and game_state.entity_at((tile[0] - 1, tile[1])) is None:
            yield (tile[0] - 2, tile[1])
        if tile[0] < self.cols - 2 and game_state.entity_at((tile[0] + 1, tile[1])) is None:
            yield (tile[0] + 2, tile[1])

    def astar(self, impassable_positions, end, exploding_tiles):
        start_node = Node(None, self.player_position, None)
        end_node = Node(None, end, None)
        open_set = [start_node]
        heapify(open_set)
        closed_set = set()

        while open_set:
            current = heappop(open_set)
            closed_set.add(current.position)
            if current == end_node:
                path = deque()
                while current:
                    path.appendleft(current)
                    current = current.parent
                return path
            for tile, action in self.get_surrounding_tiles(current.position):
                if tile in impassable_positions or tile in closed_set or tile in exploding_tiles[current.g]:
                    continue
                neighbour = Node(current, tile, action)
                neighbour.g = current.g + 1
                neighbour.h = abs(tile[0] - end_node.position[0]) + abs(tile[1] - end_node.position[1])
                neighbour.f = neighbour.g + neighbour.h
                if neighbour not in open_set:
                    heappush(open_set, neighbour)

    def path_to_target_tile(self, game_state, impassable_positions, target_tiles, neighbour, exploding_tiles):
        # search for a target tile
        result = defaultdict(set)
        if neighbour:
            for x in range(self.cols):
                for y in range(self.rows):
                    position = (x, y)

                    # ignore if not passable
                    if position in impassable_positions:
                        continue

                    # calculate score of target tile
                    score = 0
                    for tile in self.get_bomb_range_tiles(game_state, position):
                        if tile in target_tiles:
                            score += 1

                    # ignore if no score
                    if score:
                        # find path with A*
                        path = self.astar(impassable_positions, position, exploding_tiles)
                        # path not exist
                        if not path:
                            continue
                        # shorter path has higher value
                        score += (self.rows + self.cols - len(path)) / 100
                        # store result
                        if len(path) > 3:
                            result[score].add(path[1].action + path[2].action + path[3].action)
                        elif len(path) > 2:
                            result[score].add(path[1].action + path[2].action)
                        else:
                            result[score].add(path[1].action)
                        # print(" -> ".join(str(node.position) for node in path), score)
        else:
            for target_tile in target_tiles:
                # find path with A*
                path = self.astar(impassable_positions, target_tile, exploding_tiles)
                # path not exist
                if not path:
                    continue
                # shorter path has higher value
                score = (self.rows + self.cols - len(path)) / 100
                # store result
                if len(path) > 3:
                    result[score].add(path[1].action + path[2].action + path[3].action)
                elif len(path) > 2:
                    result[score].add(path[1].action + path[2].action)
                else:
                    result[score].add(path[1].action)
                # print(" -> ".join(str(node.position) for node in path), score)
        return result

    def not_in_bomb_range(self, game_state, position):
        for tile in self.get_bomb_range_tiles(game_state, position):
            if game_state.entity_at(tile) == "b":
                return False
        return True

    def place_bomb(self, game_state, impassable_positions, target_block, exploding_tiles, empty):
        next_move = ""
        # calculate score of target tile
        if game_state.entity_at(self.player_position) != "b":
            max_score = 0
            for tile in self.get_bomb_range_tiles(game_state, self.player_position):
                if tile in target_block:
                    max_score += 1
                    next_move = "p"
            # if going to place bomb check if neighbour tile give better score
            if next_move:
                for tile, action in self.get_surrounding_tiles(self.player_position):
                    score = 0
                    for sub_tile in self.get_bomb_range_tiles(game_state, tile):
                        if sub_tile in target_block:
                            score += 1
                    if score > max_score:
                        max_score = score
                        next_move = action
                escape_path = self.path_to_target_tile(game_state, impassable_positions, empty, True, exploding_tiles)
                if not escape_path:
                    return ""
        return next_move

    def update_bomb_dict(self, game_state, position):
        if position in self.bomb_dict:
            if self.bomb_dict[position] - 1 <= 0:
                for tile in self.get_bomb_range_tiles(game_state, position):
                    if tile in self.bomb_dict:
                        self.bomb_dict[tile] = min(0, self.bomb_dict[tile])
                del self.bomb_dict[position]
            else:
                self.bomb_dict[position] -= 1
        else:
            self.bomb_dict[position] = self.bomb_tick
            for tile in self.get_bomb_range_tiles(game_state, position):
                if tile in self.ore_dict:
                    self.ore_dict[tile] -= 1
                    if self.ore_dict[tile] <= 0:
                        del self.ore_dict[tile]

    def strategy1(self, game_state, player_state):
        # initialize
        exploding_tiles = defaultdict(set)
        impassable_positions = game_state.all_blocks + game_state.bombs
        soft_blocks = []
        ore_blocks = []
        treasure = []
        ammo = []
        empty = []
        for x in range(self.cols):
            for y in range(self.rows):
                position = (x, y)
                entity = game_state.entity_at(position)
                if isinstance(entity, int):
                    impassable_positions.append(position)
                elif entity == "b":
                    if position not in self.bomb_dict:
                        self.bomb_dict[position] = self.bomb_tick
                    for tile in self.get_bomb_range_tiles(game_state, position):
                        if game_state.entity_at(tile) is None:
                            for i in range(-5, 11 - player_state.hp, 1):
                                exploding_tiles[max(0, self.bomb_dict[position] + i)].add(tile)
                elif entity == "t":
                    treasure.append(position)
                elif entity == "a":
                    ammo.append(position)
                elif self.not_in_bomb_range(game_state, position):
                    if entity == "sb":
                        soft_blocks.append(position)
                    elif entity == "ob":
                        ore_blocks.append(position)
                    else:
                        empty.append(position)
        soft_ore_blocks = []
        for tile, hp in self.ore_dict.items():
            if hp == 1:
                soft_ore_blocks.append(tile)

        # if player have ammo and ore block in bomb range
        if player_state.ammo and soft_ore_blocks:
            action = self.place_bomb(game_state, impassable_positions, soft_ore_blocks, exploding_tiles, empty)
            if action:
                return action
            # find all path to ore block
            result = self.path_to_target_tile(game_state, impassable_positions, soft_ore_blocks, True, exploding_tiles)
            if result:
                return random.choice(list(result[max(result.keys())]))

        # if player have ammo and soft block in bomb range
        if player_state.ammo:
            action = self.place_bomb(game_state, impassable_positions, soft_blocks, exploding_tiles, empty)
            if action:
                return action
            # find all path to soft block
            result = self.path_to_target_tile(game_state, impassable_positions, soft_blocks, True, exploding_tiles)
            if result:
                score = max(result.keys())
                # if only 1 soft block at target tile and ammo distance shorter get ammo first
                temp = self.path_to_target_tile(game_state, impassable_positions, ammo, False, exploding_tiles)
                if temp:
                    temp_score = max(temp.keys())
                    if score < 2 and score % 1 < temp_score:
                        return random.choice(list(temp[temp_score]))
                return random.choice(list(result[score]))

        # find all path to ammo
        result = self.path_to_target_tile(game_state, impassable_positions, ammo, False, exploding_tiles)
        if result:
            return random.choice(list(result[max(result.keys())]))

        # find all path to treasure
        result = self.path_to_target_tile(game_state, impassable_positions, treasure, False, exploding_tiles)
        if result:
            return random.choice(list(result[max(result.keys())]))

        # if player have ammo and ore block in bomb range
        if player_state.ammo:
            action = self.place_bomb(game_state, impassable_positions, ore_blocks, exploding_tiles, empty)
            if action:
                return action
            # find all path to ore block
            result = self.path_to_target_tile(game_state, impassable_positions, ore_blocks, True, exploding_tiles)
            if result:
                return random.choice(list(result[max(result.keys())]))

        # if player have ammo
        if player_state.ammo:
            action = self.place_bomb(game_state, impassable_positions, empty, exploding_tiles, empty)
            if action:
                return action
        # find all path to safe place
        result = self.path_to_target_tile(game_state, impassable_positions, empty, True, exploding_tiles)
        if result:
            return random.choice(list(result[max(result.keys())]))
        # no path exist
        return ""

    def next_move(self, game_state, player_state):
        # self.print_map(game_state)
        # init ore block hp
        if self.init_ore_dict:
            for ore_block in game_state.ore_blocks:
                self.ore_dict[ore_block] = 3
            self.init_ore_dict = False
        # update bomb timer in memory
        for bomb in game_state.bombs:
            self.update_bomb_dict(game_state, bomb)
        # workaround for game_state lag
        if self.prev_position and self.prev_action and not self.lag:
            flag = False
            if self.prev_action == "d" and self.prev_position[1] <= player_state.location[1]:
                flag = True
            elif self.prev_action == "u" and self.prev_position[1] >= player_state.location[1]:
                flag = True
            elif self.prev_action == "l" and self.prev_position[0] <= player_state.location[0]:
                flag = True
            elif self.prev_action == "r" and self.prev_position[0] >= player_state.location[0]:
                flag = True
            elif self.prev_action == "p" and game_state.entity_at(player_state.location) != "b":
                flag = True
            if flag:
                self.lag = True
                if len(self.queue_action) > 1:
                    self.prev_action, self.queue_action = self.queue_action[0], self.queue_action[1:]
                else:
                    self.prev_action, self.queue_action = self.queue_action, ""
                # print("flag", self.prev_action, self.queue_action)
                self.prev_position = player_state.location
                return self.prev_action
        elif self.lag:
            if len(self.queue_action) > 1:
                self.prev_action, self.queue_action = self.queue_action[0], self.queue_action[1:]
            else:
                self.prev_action, self.queue_action = self.queue_action, ""
            if not self.prev_action:
                self.lag = False
            return self.prev_action
        self.player_position = (player_state.location[0], player_state.location[1])
        action = self.strategy1(game_state, player_state)
        if len(action) > 1:
            action, self.queue_action = action[0], action[1:]
        else:
            self.queue_action = ""
        self.prev_position = player_state.location
        self.prev_action = action
        # print(action, self.queue_action)
        return action

    def print_map(self, game_state):
        mapping = {
            "sb": 2,
            "ib": 3,
            "ob": 4,
            "b": 5,
            "a": 6,
            "t": 7
        }
        game_map = []
        for y in range(self.rows - 1, -1, -1):
            game_row = []
            for x in range(self.cols):
                entity = game_state.entity_at((x, y))
                if entity is not None:
                    game_row.append(mapping.get(entity, entity))
                else:
                    game_row.append(8)
            print(game_row)
            game_map.append(game_row)
        return repr(game_map)


class Node:

    def __init__(self, parent=None, position=None, action=None):
        self.parent = parent
        self.position = position
        self.action = action
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

    def __lt__(self, other):
        return self.f < other.f
