from Classes.Constants import *
from Classes.Materials import Materials
from Classes.TradeOffer import TradeOffer
from Interfaces.AgentInterface import AgentInterface


class CarlesZaidaAgent(AgentInterface):
    """
    Es necesario poner super().nombre_de_funcion() para asegurarse de que coge la función del padre
    """
    town_number = 0
    material_given_more_than_three = None
    # Son los materiales más necesarios en construcciones, luego se piden con year of plenty para tener en mano
    year_of_plenty_material_one = MaterialConstants.CEREAL
    year_of_plenty_material_two = MaterialConstants.MINERAL

    def __init__(self, agent_id):
        super().__init__(agent_id)

    def on_trade_offer(self, board_instance, incoming_trade_offer=TradeOffer(), player_making_offer=int):
        """
        Hay que tener en cuenta que gives se refiere a los materiales que da el jugador que hace la oferta,
        luego en este caso es lo que recibe
        :param incoming_trade_offer:
        :return:
        """
        if incoming_trade_offer.gives.has_this_more_materials(incoming_trade_offer.receives):
            return True
        else:
            return False

    def on_turn_start(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un caballero
                if self.development_cards_hand.hand[i].type == DevelopmentCardConstants.KNIGHT:
                    # La juega
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)
        return None

    def on_having_more_than_7_materials_when_thief_is_called(self):
        # Comprueba si tiene materiales para construir una ciudad. Si los tiene, descarta el resto que no le sirvan.
        if self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            while self.hand.get_total() > 7:
                if self.hand.resources.wool > 0:
                    self.hand.remove_material(4, 1)

                if self.hand.resources.cereal > 2:
                    self.hand.remove_material(0, 1)
                if self.hand.resources.mineral > 3:
                    self.hand.remove_material(1, 1)

                if self.hand.resources.clay > 0:
                    self.hand.remove_material(2, 1)
                if self.hand.resources.wood > 0:
                    self.hand.remove_material(3, 1)
        # Si no tiene materiales para hacer una ciudad descarta de manera aleatoria cartas de su mano
        return self.hand

    def on_moving_thief(self):
        # Bloquea un número 6 u 8 donde no tenga un pueblo, pero que tenga uno del rival
        # Si no se dan las condiciones lo deja donde está, lo que hace que el GameManager lo ponga en un lugar aleatorio
        terrain_with_thief_id = -1
        for terrain in self.board.terrain:
            if not terrain['has_thief']:
                if terrain['probability'] == 6 or terrain['probability'] == 8:
                    nodes = self.board.__get_contacting_nodes__(terrain['id'])
                    has_own_town = False
                    has_enemy_town = False
                    enemy = -1
                    for node_id in nodes:
                        if self.board.nodes[node_id]['player'] == self.id:
                            has_own_town = True
                            break
                        if self.board.nodes[node_id]['player'] != -1:
                            has_enemy_town = True
                            enemy = self.board.nodes[node_id]['player']

                    if not has_own_town and has_enemy_town:
                        return {'terrain': terrain['id'], 'player': enemy}
            else:
                terrain_with_thief_id = terrain['id']

        return {'terrain': terrain_with_thief_id, 'player': -1}

    def on_turn_end(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un punto de victoria
                if self.development_cards_hand.hand[i].type == DevelopmentCardConstants.VICTORY_POINT:
                    # La juega
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)
        return None

    def on_commerce_phase(self):
        """
        Se podría complicar mucho más la negociación, cambiando lo que hace en función de si tiene o no puertos y demás
        """
        # Juega monopolio si ha entregado más de 3 del mismo tipo de material a un jugador en el intercambio
        if self.material_given_more_than_three is not None:
            if len(self.development_cards_hand.check_hand()):
                # Mira todas las cartas
                for i in range(0, len(self.development_cards_hand.check_hand())):
                    # Si una es un punto de monopolio
                    if self.development_cards_hand.hand[i].effect == DevelopmentCardConstants.MONOPOLY_EFFECT:
                        # La juega
                        return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)

        gives = Materials()
        receives = Materials()

        # No pide nada porque puede hacer una ciudad
        if self.town_number >= 1 and self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            self.material_given_more_than_three = None
            return None
        # Pedir lo que falte para una ciudad, ofrece el resto de materiales iguales a los que pide
        elif self.town_number >= 1:
            cereal_hand = self.hand.resources.cereal
            mineral_hand = self.hand.resources.mineral
            wood_hand = self.hand.resources.wood
            clay_hand = self.hand.resources.clay
            wool_hand = self.hand.resources.wool
            total_given_materials = (2 - cereal_hand) + (3 - mineral_hand)

            materials_to_give = [0, 0, 0, 0, 0]
            for i in range(0, total_given_materials):
                if self.hand.resources.clay > 0:
                    self.hand.remove_material(MaterialConstants.CLAY, 1)
                    materials_to_give[MaterialConstants.CLAY] += 1
                elif self.hand.resources.wood > 0:
                    self.hand.remove_material(MaterialConstants.WOOD, 1)
                    materials_to_give[MaterialConstants.WOOD] += 1
                elif self.hand.resources.wool > 0:
                    self.hand.remove_material(MaterialConstants.WOOL, 1)
                    materials_to_give[MaterialConstants.WOOL] += 1

            gives = Materials(materials_to_give[0], materials_to_give[1], materials_to_give[2],
                              materials_to_give[3], materials_to_give[4])
            receives = Materials(2, 3, 0, 0, 0)

        # Como no puede construir una ciudad pide materiales para hacer un pueblo
        elif self.town_number == 0:
            # Si tiene materiales para hacer un pueblo directamente no comercia
            if self.hand.resources.has_this_more_materials(Materials(1, 0, 1, 1, 1)):
                return None
            # Si no los tiene hace un intercambio
            else:
                # Puedes cambiar materiales repetidos o minerales
                materials_to_receive = [0, 0, 0, 0, 0]
                materials_to_give = [0, 0, 0, 0, 0]

                number_of_materials_received = 0

                materials_to_receive[0] = 1 - self.hand.resources.cereal
                materials_to_receive[1] = 0 - self.hand.resources.mineral
                materials_to_receive[2] = 1 - self.hand.resources.clay
                materials_to_receive[3] = 1 - self.hand.resources.wood
                materials_to_receive[4] = 1 - self.hand.resources.wool

                for i in range(0, len(materials_to_receive)):
                    if materials_to_receive[i] <= 0:
                        materials_to_receive[i] = 0
                    else:
                        number_of_materials_received += 1

                for j in range(0, number_of_materials_received):
                    if self.hand.resources.cereal > 1:
                        self.hand.remove_material(MaterialConstants.CEREAL, 1)
                        materials_to_give[MaterialConstants.CEREAL] += 1
                    elif self.hand.resources.mineral > 1:
                        self.hand.remove_material(MaterialConstants.MINERAL, 1)
                        materials_to_give[MaterialConstants.MINERAL] += 1
                    elif self.hand.resources.clay > 1:
                        self.hand.remove_material(MaterialConstants.CLAY, 1)
                        materials_to_give[MaterialConstants.CLAY] += 1
                    elif self.hand.resources.wood > 1:
                        self.hand.remove_material(MaterialConstants.WOOD, 1)
                        materials_to_give[MaterialConstants.WOOD] += 1
                    elif self.hand.resources.wool > 1:
                        self.hand.remove_material(MaterialConstants.WOOL, 1)
                        materials_to_give[MaterialConstants.WOOL] += 1

                gives = Materials(materials_to_give[0], materials_to_give[1], materials_to_give[2],
                                  materials_to_give[3], materials_to_give[4])
                receives = Materials(materials_to_receive[0], materials_to_receive[1], materials_to_receive[2],
                                     materials_to_receive[3], materials_to_receive[4])

        trade_offer = TradeOffer(gives, receives)
        return trade_offer

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
                    return {'building': BuildConstants.ROAD,
                            'node_id': road_obj['starting_node'],
                            'road_to': road_obj['finishing_node']}
            if len(possibilities):
                road_node = possibilities[0]
                return {'building': BuildConstants.ROAD,
                        'node_id': road_node['starting_node'],
                        'road_to': road_node['finishing_node']}

        if self.hand.resources.has_this_more_materials(BuildConstants.CARD):
            return {'building': BuildConstants.CARD}

        return None

    def on_game_start(self, board_instance):
        self.board = board_instance
        possibilities = self.board.valid_starting_nodes()
        chosen_node_id = -1
        for node_id in possibilities:
            for terrain_id in self.board.nodes[node_id]['contacting_terrain']:
                if self.board.terrain[terrain_id]['probability'] == 6 or self.board.terrain[terrain_id]['probability'] == 8:
                    chosen_node_id = node_id

        if chosen_node_id == -1:
            chosen_node_id = possibilities[0]

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
            return {'node_id': road_node['starting_node'],
                    'road_to': road_node['finishing_node'],
                    'node_id_2': road_node_2['starting_node'],
                    'road_to_2': road_node_2['finishing_node'],
                    }
        elif len(valid_nodes) == 1:
            return {'node_id': valid_nodes[0]['starting_node'],
                    'road_to': valid_nodes[0]['finishing_node'],
                    'node_id_2': None,
                    'road_to_2': None,
                    }
        return None

    def on_year_of_plenty_card_use(self):
        return {'material': self.year_of_plenty_material_one, 'material_2': self.year_of_plenty_material_two}
