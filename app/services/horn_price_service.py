class HornPriceService:
    # Preços dos materiais brutos
    MATERIAL_PRICES = {
        "valk_0": 160,
        "valk_9": 300,
        "medalha_roxa": 300,
        "bahamut_crystal_20": 200,
        "bahamut_rune_10": 60,
        "medalha_dourada": 300,
        "medalha_vermelha": 700,
        "pl_30": 20,
        "bahamut_fury": 360,
    }

    # Custo de cada lança por nível
    @staticmethod
    def spear_cost(level: int) -> int:
        p = HornPriceService.MATERIAL_PRICES
        if level == 5:
            # 2 Valk +9, 10 Bahamut Rune, 20 Bahamut Crystal
            return 2 * p["valk_9"] + p["bahamut_rune_10"] + p["bahamut_crystal_20"]
        elif level == 10:
            # 2 Medalha Roxa, 2 Valk +9
            return 2 * p["medalha_roxa"] + 2 * p["valk_9"]
        elif level == 15:
            # 2 Medalha Roxa, 1 Medalha Dourada, 1 Medalha Vermelha
            return 2 * p["medalha_roxa"] + p["medalha_dourada"] + p["medalha_vermelha"]
        else:
            return 0

    # Cálculo do preço por Horn
    @staticmethod
    def horn_price(qtd_lancas: int, custo_lanca: int, custo_cons: int, recursos_cons: int, qtd_horn: int) -> float:
        if qtd_horn == 0:
            return 0.0
        return ((qtd_lancas * custo_lanca) + custo_cons - recursos_cons) / qtd_horn
