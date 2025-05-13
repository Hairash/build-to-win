import random


class RESOURCE_TYPES:
    EMPTY = "empty"
    DIRT = "dirt"  # impossible to build there
    WOOD = "wood"


class BUILDING_TYPES:
    SAWMILL = "sawmill"
    TOWER = "tower"


COSTS = {
    BUILDING_TYPES.SAWMILL: {
        RESOURCE_TYPES.WOOD: 3,
    },
    BUILDING_TYPES.TOWER: {
        RESOURCE_TYPES.WOOD: 10,
    },
}


class Building:
    def __init__(self, player, _type):
        self.player = player
        self.type = _type

    def to_dict(self):
        return {
            "player": self.player,
            "type": self.type
        }


class Cell:
    def __init__(self, resource):
        self.resource = resource
        self.building = None

    def to_dict(self):
        return {
            "resource": self.resource,
            "building": self.building.to_dict() if self.building else None
        }


class Field:
    def __init__(self, size, players):
        self.size = size
        self.cells = []
        self.generate()

        self.resources = self.generate_resources(players)

    def to_dict(self):
        return {
            'field': [[cell.to_dict() for cell in row] for row in self.cells],
            'resources': self.resources,
        }

    def generate(self):
        for i in range(self.size):
            row = []
            for j in range(self.size):
                r = random.randint(1, 100)
                if r < 20:
                    row.append(Cell(RESOURCE_TYPES.WOOD))
                else:
                    row.append(Cell(RESOURCE_TYPES.EMPTY))
            self.cells.append(row)


    @staticmethod
    def generate_resources(players):
        resources = {}
        cur_resource = 5
        for i in range(len(players)):
            player = players[i]
            resources[player] = {
                RESOURCE_TYPES.WOOD: cur_resource,
            }
            if i == 0:
                cur_resource += 3
            else:
                cur_resource += 1
        return resources

    def is_build_possible(self, x, y):
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return False
        cell = self.cells[x][y]
        if cell.building is not None:
            return False
        if cell.resource != RESOURCE_TYPES.EMPTY:
            return False
        if self.get_buildings_around(x, y, _type=BUILDING_TYPES.TOWER):
            return False
        return True

    def is_enough_resources(self, player, building_type):
        # TODO: Iterate over all resources
        if self.resources[player][RESOURCE_TYPES.WOOD] < COSTS[building_type][RESOURCE_TYPES.WOOD]:
            return False
        return True

    def build(self, x, y, building_type, player):
        cell = self.cells[x][y]
        cell.building = Building(player, building_type)
        self.resources[player][RESOURCE_TYPES.WOOD] -= COSTS[building_type][RESOURCE_TYPES.WOOD]
        self.apply_effect(building_type, x, y, player)

    def update_resources(self, player):
        for resource in self.resources[player]:
            self.resources[player][resource] += 1
        sawmills = self.get_player_buildings(player, BUILDING_TYPES.SAWMILL)
        wood_income = 0
        for x, y in sawmills:
            wood_income += self.count_resources_around(x, y, RESOURCE_TYPES.WOOD)
        self.resources[player][RESOURCE_TYPES.WOOD] += wood_income

    def get_player_buildings(self, player=None, _type=None):
        """
        Returns a list of buildings coords for a player.
        :param player:
        :param _type:
        :return: (x, y) list of buildings
        """
        buildings = []
        for x in range(self.size):
            for y in range(self.size):
                cell = self.cells[x][y]
                if (
                    cell.building and
                    (player is None or cell.building.player == player) and
                    (_type is None or cell.building.type == _type)
                ):
                    buildings.append((x, y))
        return buildings

    def get_resources_on_field(self, _type=None):
        """
        Returns a list of resources on the field.
        :return: (x, y) list of resources
        """
        resources = []
        for x in range(self.size):
            for y in range(self.size):
                cell = self.cells[x][y]
                if (
                    cell.resource and
                    (cell.resource == _type or _type is None)
                ):
                    resources.append((x, y))
        return resources

    def get_empty_cells(self):
        """
        Returns a list of empty cells on the field.
        :return: (x, y) list of empty cells
        """
        empty_cells = []
        for x in range(self.size):
            for y in range(self.size):
                cell = self.cells[x][y]
                if cell.resource == RESOURCE_TYPES.EMPTY and cell.building is None:
                    empty_cells.append((x, y))
        return empty_cells

    def count_resources_around(self, x, y, resource=None):
        """
        Counts resources around a building.
        :param x:
        :param y:
        :param resource:
        :return:
        """
        ctr = 0
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if i < 0 or i >= self.size or j < 0 or j >= self.size:
                    continue
                cell = self.cells[i][j]
                if cell.resource == RESOURCE_TYPES.EMPTY:
                    continue
                if resource is None or cell.resource == resource:
                    ctr += 1
        return ctr

    def get_buildings_around(self, x, y, player=None, _type=None):
        """
        Returns a list of buildings coords around a building.
        :param x:
        :param y:
        :param player:
        :param _type:
        :return: (x, y) list of buildings
        """
        buildings = []
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if i == x and j == y:  # Skip the center cell
                    continue
                if i < 0 or i >= self.size or j < 0 or j >= self.size:
                    continue
                cell = self.cells[i][j]
                if (
                    cell.building and
                    (player is None or cell.building.player == player) and
                    (_type is None or cell.building.type == _type)
                ):
                    buildings.append((i, j))
        return buildings

    def apply_effect(self, building_type, x, y, player):
        """
        Applies the effect of the building.
        :param building_type:
        :param x:
        :param y:
        :param player:
        :return:
        """
        if building_type == BUILDING_TYPES.TOWER:  # Destroy all buildings around
            buildings_around = self.get_buildings_around(x, y)
            for i, j in buildings_around:
                cell = self.cells[i][j]
                cell.building = None
            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if i == x and j == y:
                        continue
                    if i < 0 or i >= self.size or j < 0 or j >= self.size:
                        continue
                    cell = self.cells[i][j]
                    if cell.resource == RESOURCE_TYPES.EMPTY:
                        cell.resource = RESOURCE_TYPES.DIRT

    def is_end_game(self, players, turn_ctr, end_turn_ctr=0):
        """
        Check if the game is over.
        :return: player name or None
        """
        if turn_ctr < 1:
            return None

        players_in_game = [
            player for player in players if self.is_in_game(player, turn_ctr)
        ]
        if len(players_in_game) == 1:
            return players_in_game[0]

        if not self.get_empty_cells() or end_turn_ctr >= len(players_in_game) * 3:
            # The player with the most resources wins
            max_resources = -1
            winner = None
            for player in players_in_game:
                resources = self.resources[player][RESOURCE_TYPES.WOOD]
                if resources > max_resources:
                    max_resources = resources
                    winner = player
            return winner
        return None

    def is_in_game(self, player, turn_ctr):
        """
        Check if the player is in the game.
        :param player:
        :param turn_ctr:
        :return:
        """
        if turn_ctr < 1:
            return True
        return len(self.get_player_buildings(player, BUILDING_TYPES.SAWMILL)) > 0
