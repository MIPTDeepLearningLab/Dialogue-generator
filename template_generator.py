import json

YES = 1
NO = 0

synonim_fillings = {"appeal": ("Скажите ,", "Хочу узнать ,"),
                    "goods_presence_cust": ("имеются", "есть в наличии", "можно заказать"),
                    "goods_presence_wiz": ("в ассортименте", "у нас", "в наличии"),
                    "decision_begin": ("Тогда", "Значит ,", "Ладно ,", "Пожалуй ,", "ОК ,", "Замечательно ,"),
                    "decision_end": ("пожалуйста", "", "если можно"),
                    "delivery_presence": ("есть", "осуществляется")
                    }
slot_fillings = {
    r"пицца": ("баварская", "вегетарианская", "гавайская", "домашняя", "оригинальная", "куриная"),
    r"салат": ("греческий", "овощной", "пикантный", "фруктовый", "итальянский"),
    r"напиток": ("минералка", "сок", "кофе", "кола", "пиво"),
    r"доставка": ("Калиниский", "Металлургический", "Советский", "Центральный")
}

intentions = {
    ("goods_presence general"): {"templates": [(("*appeal", [], "synonim"), "у вас", ("*goods_presence_cust", [], "synonim"), ("*", ["plur", ], "slot"), "?"),
                                               ],
                                 "responses": [(YES, ("Да", ("*goods_presence_wiz", [], "synonim"), "есть следующие", ("*", ["plur", ], "slot"), ":", ("*+", [], "value"))),
                                               (YES, ("Да", ("*goods_presence_wiz", [], "synonim"), "есть", ("*", ["plur", ], "slot"))),
                                               (NO, ("К сожалению", ("*", ["plur", ], "slot"), "закончились"))
                                               ]},

    ("goods_presence specific"): {"templates": [(("*decision_begin", [], "synonim"), "мне", ("*", ["gent", ], "value"), ("*", ["gent", ], "slot"), ("*decision_end", [], "synonim")),
                                                ("А", ("*", [], "value"), ("*", [], "slot"), "есть ?")
                                                ],
                                  "responses": [(YES, ("Хорошо", )),
                                                (NO, ("К сожалению", ("*", ["gent", ], "slot"), "нет"))
                                                ]},

    ("delivery_presence general"): {"templates": [(("*appeal", [], "synonim"), "у вас", ("*delivery_presence", [], "synonim"), ("гы", [], "slot"), "?"),
                                                  ],
                                    "responses": [(YES, ("Да ,", ("", [], "slot"), ("*delivery_presence", [], "synonim"), "в следующие районы:", ("*+", [], "value"))),
                                                  (YES, ("Да", "у нас есть", ("*", [], "slot")))]},

    ("delivery_presence specific"): {"templates": [(("*decision_begin", [], "synonim"), "мне", ("*", ["accs", ], "slot"), "в", ("*", [], "value"), "район"),
                                                   ("А", ("*", [], "slot"), "в", ("*", [], "value"), "район есть ?")
                                                   ],
                                     "responses": [(YES, ("Хорошо", )),
                                                   (NO, ("К сожалению", ("*", [], "slot"), "не доступна"))
                                                   ]}
}


substitutions = (
    ("goods_presence general", {0: "пицца"}),
    ("goods_presence specific", {0: "пицца",
                                 1: "пицца"}),
    ("goods_presence general", {0: "напиток"}),
    ("goods_presence specific", {0: ["_", "_", "", "_"],
                                 1: ["_", ""]}),
    ("goods_presence general", {0: "салат"}),
    ("goods_presence specific", {0: "салат",
                                 1: "салат"}),
    ("delivery_presence general", {0: ["_", "_", "доставка"]}),
    ("delivery_presence specific", {0: "доставка",
                                    1: "доставка"})
)

greetings = ("Здравствуйте", "Добрый день", "Рады приветствовать")
farewells = ("Всего хорошего !", "Спасибо за покупку !", "До свидания")

data = [greetings, synonim_fillings, slot_fillings, intentions, substitutions, farewells]

with open("Data/data.json", "w") as f:
    json.dump(data, f)
