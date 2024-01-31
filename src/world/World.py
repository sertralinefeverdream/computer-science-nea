import json
import random
import pygame

class World:
    def __init__(self, game, camera, region_generator):
        self._game = game
        self._camera = camera
        self._region_generator = region_generator

        self._player = None

        self._draw_list = []
        self._data = \
            {
                '0':
                    {
                        '0': self._region_generator.create_generated_region(self._game, self, (0, 0))
                    }
            }

        self._test_enemy = self._game.character_factory.create_character(self._game, self, "test")
        self._test_enemy.position = (0, 0)
        self.test_points = []

    @property
    def game(self):
        return self._game

    @property
    def camera(self):
        return self._camera

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = value

    @property
    def region_generator(self):
        return self._region_generator

    @property
    def draw_list(self):
        return self._draw_list

    def reset(self):
        self._region_generator.randomise_seed()
        self._data.clear()
        self._draw_list.clear()
        self._data['0'] = {}
        self._data['0']['0'] = self._region_generator.create_generated_region(self._game, self, (0, 0))
        self._data["0"]["0"].add_entity(self._test_enemy)

        self._camera.x = 0
        self._camera.y = 0
        self._player = None

    def find_player_reference(self):
        for column in self._data.values():
            for region in column.values():
                for entity in region.entity_list:
                    if entity.entity_id == "player":
                        return entity
        return None

    def update(self):
        player_reference = self.find_player_reference()
        if player_reference is None: # Case when player does not exist.
            #print("PLAYER REFERENCE IS BEING CREATED")
            if self._player is None:
                print("FIRST CASE")
                self._player = self._game.character_factory.create_character(self._game, self, "player")
            else:
                print("SECOND CASE")
                self._player.health = self._player.max_health
                self._player.is_killed = False
            #print(f"REGION WITH PLAYER IN IT", self.get_region_at_position((0, 0)).entity_list)
            self.get_region_at_position(self._player.position).add_entity(self._player)
            self._camera.x = self._player.position[0] - 600
            self._camera.y = self._player.position[1] - 400

        self.reassign_entities_to_regions() # Must be done in this order to prevent player stuttering
        self.update_draw_list()

        for index, (x, y) in enumerate(self._draw_list):
            self._data[x][y].update()
            if index == 0:
                self._camera.x = self._player.position[0] - 600
                self._camera.y = self._player.position[1] - 400

    def draw_blocks(self):
        for x, y in self._draw_list:
            screen_position = self._camera.get_screen_position((int(x), int(y)))
            if (-800 <= screen_position[0] <= 1200) and (-800 <= screen_position[1] <= 800):
                self._data[x][y].draw_blocks()

        for points in self.test_points:
            screen_pos = self._camera.get_screen_position(points)
            pygame.draw.circle(self._game.window, (0,0,0), screen_pos, 5, 5)

    def draw_entities(self):
        for x, y in self._draw_list:
            self._data[x][y].draw_entities()

    def get_region_indexes_from_position(self, position):
        if (type(position) is list or type(position) is tuple) and len(position) == 2:

            x_index = int((position[0] // 800)) * 800
            y_index = int((position[1] // 800)) * 800

            return str(x_index), str(y_index)

    def check_region_exists_at_position(self, position):
        if (type(position) is list or type(position) is tuple) and len(position) == 2:
            x_index, y_index = self.get_region_indexes_from_position(position)

            if x_index in self._data.keys():
                if y_index in self._data[x_index].keys():
                    return True
                else:
                    return False
            else:
                return False

    def get_region_at_position(self, position):
        if (type(position) is list or type(position) is tuple) and len(position) == 2:
            if self.check_region_exists_at_position(position):
                x_index, y_index = self.get_region_indexes_from_position(position)
                return self._data[x_index][y_index]
            else:
                print("Region no long exist")
                return None

    def get_block_at_position(self, position):
        if (type(position) is list or type(position) is tuple) and len(position) == 2:
            if self.check_region_exists_at_position(position):
                region = self.get_region_at_position(position)
                return region.get_block_at_position(position)
            else:
                return None

    def get_entities_at_position(self, position, ignore_player=True):
        if (type(position) is list or type(position) is tuple) and len(position) == 2:
            regions_to_check = []
            entities = []
            for x in range(3):
                for y in range(3):
                    region_check_x = position[0] + (x-1)*800
                    region_check_y = position[1] + (x-1)*800
                    if self.check_region_exists_at_position((region_check_x, region_check_y)):
                        regions_to_check.append(self.get_region_at_position((region_check_x, region_check_y)))
            #print(regions_to_check)
            for region in regions_to_check:
                entities += region.get_entities_at_position(position, ignore_player)
            return entities

    def set_block_at_position(self, position, block_id, state_data=None):
        if (type(position) is list or type(position) is tuple) and len(position) == 2:
            if self.check_region_exists_at_position(position):
                region = self.get_region_at_position(position)
                region.set_block_at_position(position, block_id, state_data)

    def serialize(self):
        return json.dumps(self.convert_data())

    def load_from_serialized(self, data):
        self.load_from_data(json.loads(data))

    def convert_data(self):  # Converts classes to dict and array representations in preparation for json serialization
        data = {}
        data["world_data"] = {}
        data["seed"] = self._region_generator.seed
        for x_index, column in self._data.items():
            data["world_data"][str(x_index)] = {}
            for y_index, region in column.items():
                data["world_data"][str(x_index)][str(y_index)] = region.convert_data()
        return data

    def load_from_data(self, data):
        self.reset()
        self._region_generator.seed = data["seed"]
        for x_index, column in data["world_data"].items():
            for y_index, region in column.items():
                if str(x_index) not in self._data.keys():
                    self._data[str(x_index)] = {}
                self._data[str(x_index)][str(y_index)] = self._region_generator.create_region_from_data(self._game, self, (
                    int(x_index), int(y_index)), region)

    def reassign_entities_to_regions(self): # Make sure entities are being updated by the region that they actually reside in.
        for region in [self.get_region_at_position((int(x), int(y))) for x, y in self._draw_list]:
            for entity in region.entity_list[::]:
                if not region.is_position_in_region(entity.position):
                    region_index_x, region_index_y = self.get_region_indexes_from_position(entity.position)
                    if self.check_region_exists_at_position(entity.position):
                        self._data[region_index_x][region_index_y].add_entity(entity)
                    region.remove_entity(entity)


    def update_draw_list(self): # Responsible for updating draw list and creating non-existent regions that need to be drawn
        self._draw_list.clear()
        camera_x = self._camera.x
        camera_y = self._camera.y

        region_with_player = None
        regions_to_generate_trees_for = []

        for x in range(7):
            for y in range(7):
                region_check_x = camera_x + (x-3)*800
                region_check_y = camera_y + (y-3)*800

                region_index_x, region_index_y = self.get_region_indexes_from_position((region_check_x, region_check_y))

                region_exists = self.check_region_exists_at_position((region_check_x, region_check_y))

                if not region_exists:
                    if region_index_x not in self._data.keys():
                        self._data[region_index_x] = {}
                    #self._data[region_index_x][region_index_y] = self._region_generator.create_region_from_data(self._game, self, (int(region_index_x), int(region_index_y)), self._default)
                    self._data[region_index_x][region_index_y] = self._region_generator.create_generated_region(self._game, self, (int(region_index_x), int(region_index_y)))


                if self._player not in self._data[region_index_x][region_index_y].entity_list:
                    self._draw_list.append((region_index_x, region_index_y))
                else:
                    region_with_player = (region_index_x, region_index_y)

        if region_with_player is not None:
            self._draw_list.insert(0, region_with_player)





