import random
from Classes.Constants import *
from Classes.Materials import Materials
from Classes.TradeOffer import TradeOffer
from Interfaces.AgentInterface import AgentInterface

class CarlesZaidaAgent(AgentInterface):
    town_number = 0
    material_given_more_than_three = None
    year_of_plenty_material_one = MaterialConstants.CEREAL
    year_of_plenty_material_two = MaterialConstants.MINERAL

    def __init__(self, agent_id):
        super().__init__(agent_id)

    def on_trade_offer(self, board_instance, incoming_trade_offer=TradeOffer(), player_making_offer=int):
        return incoming_trade_offer.gives.has_this_more_materials(incoming_trade_offer.receives)

    def on_turn_start(self):
        if len(self.development_cards_hand.check_hand()):
            for card in self.development_cards_hand.hand:
                if card.type == DevelopmentCardConstants.KNIGHT:
                    return self.development_cards_hand.select_card_by_id(card.id)
        return None

    def on_having_more_than_7_materials_when_thief_is_called(self):
        while self.hand.get_total() > 7:
            materials = [MaterialConstants.WOOL, MaterialConstants.CEREAL, MaterialConstants.MINERAL,
                         MaterialConstants.CLAY, MaterialConstants.WOOD]
            for material in materials:
                if self.hand.resources.get_from_id(material) > 1:
                    self.hand.remove_material(material, 1)
                    break
        return self.hand

    def on_moving_thief(self):
        terrain_with_thief_id = -1
        best_target = None
        max_block_value = 0

        for terrain in self.board.terrain:
            if not terrain['has_thief']:
                nodes = self.board.__get_contacting_nodes__(terrain['id'])
                block_value = 0
                enemy = None
                for node_id in nodes:
                    player_id = self.board.nodes[node_id]['player']
                    if player_id != self.id and player_id != -1:
                        block_value += 1  # Simple count of blocking value, can be adjusted
                        if enemy is None or block_value > max_block_value:
                            enemy = player_id
                            max_block_value = block_value
                if enemy:
                    best_target = {'terrain': terrain['id'], 'player': enemy}
            else:
                terrain_with_thief_id = terrain['id']

        return best_target if best_target else {'terrain': terrain_with_thief_id, 'player': -1}

    def on_turn_end(self):
        if len(self.development_cards_hand.check_hand()):
            for card in self.development_cards_hand.hand:
                if card.type == DevelopmentCardConstants.VICTORY_POINT:
                    return self.development_cards_hand.select_card_by_id(card.id)
        return None

    def on_commerce_phase(self):
        if self.material_given_more_than_three is not None:
            if len(self.development_cards_hand.check_hand()):
                for card in self.development_cards_hand.hand:
                    if card.effect == DevelopmentCardConstants.MONOPOLY_EFFECT:
                        return self.development_cards_hand.select_card_by_id(card.id)

        if self.town_number >= 1 and self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            self.material_given_more_than_three = None
            return None
        elif self.town_number >= 1:
            total_given_materials = (2 - self.hand.resources.cereal) + (3 - self.hand.resources.mineral)
            materials_to_give = self._determine_materials_to_give(total_given_materials,
                                                                  [MaterialConstants.CLAY, MaterialConstants.WOOD,
                                                                   MaterialConstants.WOOL])
            gives = Materials(*materials_to_give)
            receives = Materials(2, 3, 0, 0, 0)
        elif self.town_number == 0:
            if self.hand.resources.has_this_more_materials(Materials(1, 0, 1, 1, 1)):
                return None
            else:
                materials_to_receive = [max(0, 1 - self.hand.resources.cereal), 0, max(0, 1 - self.hand.resources.clay),
                                        max(0, 1 - self.hand.resources.wood), max(0, 1 - self.hand.resources.wool)]
                total_received_materials = sum(materials_to_receive)
                materials_to_give = self._determine_materials_to_give(total_received_materials,
                                                                      [MaterialConstants.CEREAL,
                                                                       MaterialConstants.MINERAL,
                                                                       MaterialConstants.CLAY, MaterialConstants.WOOD,
                                                                       MaterialConstants.WOOL])
                gives = Materials(*materials_to_give)
                receives = Materials(*materials_to_receive)

        trade_offer = TradeOffer(gives, receives)
        return trade_offer

    def _determine_materials_to_give(self, total_needed, material_ids):
        materials_to_give = [0, 0, 0, 0, 0]
        for _ in range(total_needed):
            random.shuffle(material_ids)
            for mat_id in material_ids:
                if self.hand.resources.get_from_id(mat_id) > 1 or (
                        mat_id == MaterialConstants.MINERAL and self.hand.resources.mineral > 1):
                    self.hand.remove_material(mat_id, 1)
                    materials_to_give[mat_id] += 1
                    break
        return materials_to_give

    def on_build_phase(self, board_instance):
        self.board = board_instance

        if self.hand.resources.has_this_more_materials(BuildConstants.CITY) and self.town_number > 0:
            possibilities = self.board.valid_city_nodes(self.id)
            for node_id in possibilities:
                for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                    if self.board.terrain[terrain_piece_id]['probability'] >= 4:
                        self.town_number -= 1
                        return {'building': BuildConstants.CITY, 'node_id': node_id}

        if self.hand.resources.has_this_more_materials(BuildConstants.TOWN):
            possibilities = self.board.valid_town_nodes(self.id)
            for node_id in possibilities:
                for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                    if self.board.terrain[terrain_piece_id]['probability'] >= 3:
                        self.town_number += 1
                        return {'building': BuildConstants.TOWN, 'node_id': node_id}

        if self.hand.resources.has_this_more_materials(BuildConstants.ROAD):
            possibilities = self.board.valid_road_nodes(self.id)
            for road_obj in possibilities:
                if self.board.is_it_a_coastal_node(road_obj['finishing_node']) and \
                        self.board.nodes[road_obj['finishing_node']]['harbor'] != HarborConstants.NONE:
                    return {'building': BuildConstants.ROAD, 'node_id': road_obj['starting_node'],
                            'road_to': road_obj['finishing_node']}
            if possibilities:
                road_node = possibilities[0]
                return {'building': BuildConstants.ROAD, 'node_id': road_node['starting_node'],
                        'road_to': road_node['finishing_node']}

        if self.hand.resources.has_this_more_materials(BuildConstants.CARD):
            return {'building': BuildConstants.CARD}

        return None

    def on_game_start(self, board_instance):
        self.board = board_instance
        possibilities = self.board.valid_starting_nodes()
        chosen_node_id = -1
        best_blocking_score = 0

        for node_id in possibilities:
            blocking_score = sum(1 for adj_node_id in self.board.nodes[node_id]['adjacent']
                                 if
                                 self.board.nodes[adj_node_id]['player'] != self.id and self.board.nodes[adj_node_id][
                                     'player'] != -1)
            if blocking_score > best_blocking_score:
                best_blocking_score = blocking_score
                chosen_node_id = node_id

        if chosen_node_id == -1:
            chosen_node_id = random.choice(possibilities)

        self.town_number += 1

        possible_roads = self.board.nodes[chosen_node_id]['adjacent']
        chosen_road_to_id = possible_roads[0]

        return chosen_node_id, chosen_road_to_id

    def on_monopoly_card_use(self):
        return self.material_given_more_than_three

    def on_road_building_card_use(self):
        valid_nodes = self.board.valid_road_nodes(self.id)
        if len(valid_nodes) > 1:
            road_node = valid_nodes[0]
            road_node_2 = valid_nodes[1]
            return {'node_id': road_node['starting_node'], 'road_to': road_node['finishing_node'],
                    'node_id_2': road_node_2['starting_node'], 'road_to_2': road_node_2['finishing_node']}
        elif len(valid_nodes) == 1:
            return {'node_id': valid_nodes[0]['starting_node'], 'road_to': valid_nodes[0]['finishing_node'],
                    'node_id_2': None, 'road_to_2': None}
        return None

    def on_year_of_plenty_card_use(self):
        return {'material': self.year_of_plenty_material_one, 'material_2': self.year_of_plenty_material_two}

    def generate_trade_offers(self):
        offers = []
        materials = [MaterialConstants.WOOL, MaterialConstants.CEREAL, MaterialConstants.MINERAL,
                     MaterialConstants.CLAY, MaterialConstants.WOOD]

        for material in materials:
            if self.hand.resources.get_from_id(material) > 3:
                for target_material in materials:
                    if material != target_material:
                        gives = Materials(0, 0, 0, 0, 0)
                        gives.add(material, 3)
                        receives = Materials(0, 0, 0, 0, 0)
                        receives.add(target_material, 1)
                        offers.append(TradeOffer(gives, receives))

        return offers

    def trade_resource(self, material):
        trade_offers = self.generate_trade_offers()
        for trade_option in trade_offers:
            if trade_option.gives.has_this_more_materials(trade_option.receives):
                return trade_option
        return None

    def manage_resources(self):
        resources = self.hand.resources
        if resources.get_total() > 7:
            self.on_having_more_than_7_materials_when_thief_is_called()
        if self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            self.on_build_phase(self.board)
        elif self.hand.resources.has_this_more_materials(BuildConstants.TOWN):
            self.on_build_phase(self.board)
        elif self.hand.resources.has_this_more_materials(BuildConstants.ROAD):
            self.on_build_phase(self.board)
        elif self.hand.resources.has_this_more_materials(BuildConstants.CARD):
            self.on_build_phase(self.board)
        else:
            self.trade_resource(MaterialConstants.CLAY)  # Example trading for clay if no specific preference
