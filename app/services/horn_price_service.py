class HornPriceService:
    MATERIAL_PRICES = {
        "valk_0": 160,
        "valk_9": 350,
        "medalha_roxa": 300,
        "bahamut_crystal_20": 70,
        "bahamut_rune_10": 60,
        "medalha_dourada": 300,
        "medalha_vermelha": 700,
        "pl_30": 20,
        "bahamut_fury": 230,
    }

    @staticmethod
    def spear_cost(level: int) -> int:
        p = HornPriceService.MATERIAL_PRICES
        if level == 5:
            return 2 * p["valk_9"] + p["bahamut_rune_10"] + p["bahamut_crystal_20"]
        elif level == 10:
            return 2 * p["medalha_roxa"] + 2 * p["valk_9"]
        elif level == 15:
            return 2 * p["medalha_roxa"] + p["medalha_dourada"] + p["medalha_vermelha"]
        return 0

    @staticmethod
    def cons_cost():
        p = HornPriceService.MATERIAL_PRICES

        fury_total = 5 * p["bahamut_fury"]
        pl_total = 30 * p["pl_30"]

        total = fury_total + pl_total

        return {
            "fury_unit": p["bahamut_fury"],
            "fury_qtd": 5,
            "fury_total": fury_total,
            "pl_unit": p["pl_30"],
            "pl_qtd": 30,
            "pl_total": pl_total,
            "total": total
        }

    @staticmethod
    def calculate(qtd_lancas: int, level: int, qtd_horn: int, recursos: dict):
        p = HornPriceService.MATERIAL_PRICES

        # Lança
        spear_unit = HornPriceService.spear_cost(level)
        spear_total = qtd_lancas * spear_unit

        # CONS (custo fixo)
        cons = HornPriceService.cons_cost()

        # 🔥 NOVO: calcular valor dos recursos obtidos
        recursos_detalhe = []
        recursos_total = 0

        for nome, qtd in recursos.items():
            if qtd > 0:
                valor_unit = p.get(nome, 0)
                total = qtd * valor_unit

                recursos_detalhe.append({
                    "nome": nome,
                    "qtd": qtd,
                    "unit": valor_unit,
                    "total": total
                })

                recursos_total += total

        # TOTAL FINAL
        total_cost = spear_total + cons["total"] - recursos_total
        price_per_horn = total_cost / qtd_horn if qtd_horn else 0

        return {
            "spear": {
                "level": level,
                "unit": spear_unit,
                "qtd": qtd_lancas,
                "total": spear_total
            },
            "cons": cons,
            "recursos": {
                "itens": recursos_detalhe,
                "total": recursos_total
            },
            "total_cost": total_cost,
            "qtd_horn": qtd_horn,
            "price_per_horn": price_per_horn
        }