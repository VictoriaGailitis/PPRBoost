import os
from langchain_community.llms import VLLM

llm = VLLM(
    model='Qwen/Qwen2.5-14B-Instruct',
    trust_remote_code=True,
    max_new_tokens=128,
    top_k=10,
    top_p=0.95,
    temperature=0.8,
)

category_id_to_name = {
    "CAT_001": "_",
    "CAT_002": "_",
    "CAT_003": "_",
    "CAT_004": "_",
    "CAT_005": "_",
    "CAT_006": "_",
    "CAT_007": "_",
    "CAT_008": "_",
    "CAT_009": "_",
    "CAT_010": "_",
    "CAT_011": "UNKNOWN - неопределенный класс"
}

subcategory_id_to_name = {
    "CAT_001": {
        "SUB_001_01": "_",
        "SUB_001_02": "_",
        "SUB_001_03": "_",
        "SUB_001_04": "_",
        "SUB_001_05": "_",
    },
    "CAT_002": {
        "SUB_002_01": "_",
        "SUB_002_02": "_",
        "SUB_002_03": "_",
        "SUB_002_04": "_",
        "SUB_002_05": "_",
        "SUB_002_06": "_",
        "SUB_002_07": "_",
    },
    "CAT_003": {
        "SUB_003_01": "_",
        "SUB_003_02": "_",
        "SUB_003_03": "_",
        "SUB_003_04": "_",
        "SUB_003_05": "_",
        "SUB_003_06": "_",
        "SUB_003_07": "_",
    },
    "CAT_004": {
        "SUB_004_01": "_",
        "SUB_004_02": "_",
        "SUB_004_03": "_",
        "SUB_004_04": "_",
        "SUB_004_05": "_",
    },
    "CAT_005": {
        "SUB_005_01": "_",
        "SUB_005_02": "_",
        "SUB_005_03": "_",
        "SUB_005_04": "_",
        "SUB_005_05": "_",
    },
    "CAT_006": {
        "SUB_006_01": "_",
        "SUB_006_02": "_",
        "SUB_006_03": "_",
        "SUB_006_04": "_",
        "SUB_006_05": "_",
        "SUB_006_06": "_",
        "SUB_006_07": "_",
    },
    "CAT_007": {
        "SUB_007_01": "_",
        "SUB_007_02": "_",
        "SUB_007_03": "_",
        "SUB_007_04": "_",
        "SUB_007_05": "_",
    },
    "CAT_008": {
        "SUB_008_01": "_",
        "SUB_008_02": "_",
        "SUB_008_03": "_",
        "SUB_008_04": "_",
    },
    "CAT_009": {
        "SUB_009_01": "_",
        "SUB_009_02": "_",
    },
    "CAT_010": {
        "SUB_010_01": "_",
        "SUB_010_02": "_",
        "SUB_010_03": "_",
    }
}

def classify_text(text: str) -> tuple[str, str | None]:
    try:
        categories_list = "\n".join([f"{k}: {v}" for k, v in category_id_to_name.items()])
        level_1_prompt = f'''
        Ты — интеллектуальный классификатор пользовательских вопросов по работе с ППР.

        Вот список категорий первого уровня:
        {categories_list}

        Выбери ID наиболее подходящей категории из списка выше для следующего запроса:

        "{text}"

        Ответь **только** ID, например: CAT_003. Выбирай CAT_011 в том случае, если запрос не относится ни к одной из остальных категорий или если запрос непонятен.
        '''
        response_1 = llm.invoke(level_1_prompt)
        category_level_1 = response_1.strip()

        if category_level_1 == "CAT_011":
            return category_level_1, None

        subcategories_list = "\n".join([
            f"{k}: {v}" for k, v in subcategory_id_to_name[category_level_1].items()
        ])
        level_2_prompt = f'''
        Ты — интеллектуальный классификатор пользовательских запросов для ППР.

        На предыдущем этапе запрос был отнесён к категории первого уровня: **{category_level_1} ({category_id_to_name[category_level_1]})**

        Теперь выбери одну наиболее подходящую подкатегорию второго уровня из этого списка:
        {subcategories_list}

        Запрос:
        "{text}"

        Ответь **только** ID, например: SUB_003_02.
        '''
        response_2 = llm.invoke(level_2_prompt)
        category_level_2 = response_2.strip()

        return category_level_1, category_level_2

    except Exception as e:
        return "CAT_011", None


# text = '_'
# res = classify_text(text)

# cat_1_name = category_id_to_name[res[0]]
# cat_2_name = subcategory_id_to_name[res[0]][res[1]]
# cat_1_name, cat_2_name