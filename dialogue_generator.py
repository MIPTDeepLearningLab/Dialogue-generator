import json
import pymorphy2
from numpy.random import choice
from random import shuffle
from random import random
from random import randrange
from collections import defaultdict
import copy


class Generator:

    def __init__(self, greetings, synonim_fills, slot_fills, substitutions, templates, farewells, tagging_type="word"):
        self._greetings = greetings
        self._synonim_fills = synonim_fills
        self._slot_fills = slot_fills
        self._slot_fills_copy = {key: slot_fills[key][:] for key in slot_fills.keys()}
        self._templates = templates
        self._substitutions = substitutions
        self._dialogue = []
        self._tagging = []
        self._morph = pymorphy2.MorphAnalyzer()
        self._tagging_type = tagging_type
        self._lookup_table = {("пицца", ("plur", )): "пиццы", }
        self._available_products = None
        self._farewells = farewells
        self._codes = defaultdict(int)
        self._process_substitutions()

    def _process_substitutions(self):
        self._substitutions = [self._substitutions[i:i + 2] for i in
                               range(0, len(self._substitutions), 2)]
        for idx, elem in enumerate(self._slot_fills.items()):
            slot, values = elem
            self._codes[slot] = 2 * (idx + 1) - 1
            for value in values:
                self._codes[value] = 2 * (idx + 1)

    def _simulate_bernoulli_rv(self, p=0.5):
        return random() < p

    def _initialize_products(self, products):
        self._all_products = set(products)
        self._available_products = choice(products, replace=False, size=int(0.5 * len(products)))
        self._rest_products = list(set(products) - set(self._available_products))

    def _substitutite_template(self, template, substitute):
        if substitute is None:
            substitute = self._current_slot
        if isinstance(substitute, str):
            if self._current_slot is None:
                self._current_slot = substitute
            for idx, item in enumerate(template):
                if isinstance(item, list):
                    val, case, type_ = item
                    if type_ == "slot":
                        template[idx] = [self._current_slot, case, type_]
                        break
        else:
            it = iter(substitute)
            for idx, item in enumerate(template):
                if isinstance(item, list):
                    val, case, type_ = item
                    sub = next(it)
                    if sub != "_":
                        template[idx] = [sub, case, type_]
                    if type_ == "slot":
                        if self._current_slot is None:
                            self._current_slot = sub

        if self._available_products is None:
            self._initialize_products(self._slot_fills[self._current_slot])

        for idx, item in enumerate(template):
            if isinstance(item, list):
                val, case, type_ = item
                if val.startswith("*"):
                    if val == "*":
                        if type_ == "value":
                            template[idx] = [choice(self._slot_fills[self._current_slot]), case, type_]
                        elif type == "synonim":
                            template[idx] = [choice(self._synonim_fills[self._current_slot]), case, type_]
                    elif val == "*+":
                        template[idx] = tuple([[v, case, type_] for v in self._available_products])
                    else:
                        template[idx] = [choice(self._synonim_fills[val[1:]]), case, type_]

    def _tag_sentence(self, template):
        if self._tagging_type:
            tagged_string = []
            for item in template:
                case = []
                if isinstance(item, list):
                    string_to_tag = item[0].split()
                    case = item[1]
                elif isinstance(item, tuple):
                    string_to_tag = []
                    for it in item:
                        string_to_tag.append(it[0])
                        string_to_tag.append(",")
                    string_to_tag = string_to_tag[:-1]
                    case = item[0][1]
                else:
                    string_to_tag = item.split()

                if self._tagging_type == "word":
                    tagged_string.extend([self._codes[substring] for substring in string_to_tag])
                else:
                    if string_to_tag == []:
                        tagged_string.append(0)
                    if len(case) == 0:
                        for substring in string_to_tag:
                            print("  ", substring)
                            tagged_string.extend([self._codes[substring] for _ in range(len(substring))] + [0, ])
                    else:
                        for substring in string_to_tag:
                            conjugated_string = self._conjugate_word(substring, case)
                            tagged_string.extend([self._codes[substring] for _ in range(len(conjugated_string))] + [0, ])
            if self._tagging_type == "symbol":
                tagged_string = tagged_string[:-1]
            self._tagging.append(tagged_string)

    def _conjugate_word(self, word, case):
        if len(case) > 0:
            try:
                return self._morph.parse(word)[0].inflect(set(case)).word
            except:
                try:
                    return self._lookup_table[(word, tuple(case))]
                except:
                    return ""
        else:
            return word

    def _fill_template(self, template, substitute):
        filled_template = copy.deepcopy(template)
        self._substitutite_template(filled_template, substitute)
        dialogue_phrase = []
        for item in filled_template:
            if isinstance(item, list):
                val, case, type_ = item
                dialogue_phrase.append(self._conjugate_word(val, case))
            elif isinstance(item, tuple):
                products_string = ' , '.join(self._conjugate_word(product[0], product[1]) for product in item)
                dialogue_phrase.append(products_string)
            else:
                dialogue_phrase.append(item)
        dialogue_phrase = ' '.join(dialogue_phrase)
        self._dialogue.append(dialogue_phrase)
        self._tag_sentence(filled_template)
        return filled_template

    def _sample_question_until(self, name, condition=None):
        response_type, response_template = self._templates[name]["responses"][randrange(len(self._templates[name]["responses"]))]
        if condition is None:
            return response_type, response_template
        while response_type != condition:
            response_type, response_template = self._templates[name]["responses"][randrange(len(self._templates[name]["responses"]))]
        return response_type, response_template

    def _get_template_and_substitution(self, intention):
        name, template_fillings = intention
        templates_indices = list(template_fillings.keys())

        chosen_index = choice(templates_indices)
        question_template = self._templates[name]["templates"][int(chosen_index)]
        substitution = template_fillings[chosen_index]

        if "specific" in name:
            if isinstance(question_template[-1], str) and question_template[-1].endswith("?"):
                self._slot_fills[self._current_slot] = [choice(self._rest_products), ]
                self._rest_products.remove(self._slot_fills[self._current_slot][0])
                response_type, response_template = self._sample_question_until(name, False)
            else:
                self._slot_fills[self._current_slot] = self._available_products
                response_type, response_template = self._sample_question_until(name, True)
        else:
            response_type, response_template = self._sample_question_until(name)
        return question_template, substitution, response_template, response_type

    def _process_simple(self, templates):
        chosen = choice(templates)
        self._dialogue.append(chosen)
        self._tag_sentence((chosen, ))

    def generate_dialogue(self):
        self._reset()
        self._process_simple(self._greetings)
        for general_intention, specific_intention in self._substitutions:
            self._current_slot = None
            self._available_products = None
            question_template, substitution, response_template, response_type = self._get_template_and_substitution(general_intention)
            self._fill_template(question_template, substitution)
            self._fill_template(response_template, None)
            self.hide_general = self._simulate_bernoulli_rv()
            if self.hide_general:
                self._dialogue = self._dialogue[:-2]
                self._tagging = self._tagging[:-2]
            if self.hide_general or response_type:
                response_type = None
                while not response_type and len(self._rest_products) > 0:
                    question_template, substitution, response_template, response_type = self._get_template_and_substitution(specific_intention)
                    self._fill_template(question_template, substitution)
                    self._fill_template(response_template, None)
        self._process_simple(self._farewells)
        return '\n'.join(self._dialogue), self._tagging

    def _reset(self):
        self._dialogue = []
        self._tagging = []
        self._current_slot = None
        self._available_products = None
        self._slot_fills = {key: self._slot_fills_copy[key][:] for key in self._slot_fills_copy.keys()}

        shuffle(self._substitutions)


if __name__ == "__main__":
    path = "data/data.json"
    with open(path) as f:
        greetings, synonim_fillings, slot_fillings, templates, substitutions, farewells = json.load(f)
    generator = Generator(greetings=greetings, synonim_fills=synonim_fillings, slot_fills=slot_fillings,
                          templates=templates, substitutions=substitutions, farewells=farewells, tagging_type="word")
    for _ in range(100):
        dialogue, tagging = generator.generate_dialogue()
        dialogue = dialogue.split("\n")
        for quote, tagging in zip(dialogue, tagging):
            print(quote, tagging)
            # assert len(quote) == len(tagging)
            assert len(quote.split()) == len(tagging)
        print ("*" * 40)
