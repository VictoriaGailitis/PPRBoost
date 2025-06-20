# !pip install unsloth
# !pip uninstall unsloth -y && pip install --upgrade --no-cache-dir "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# import torch
# if torch.cuda.get_device_capability()[0] >= 8:
#     !pip install --no-deps packaging ninja einops "flash-attn>=2.6.3"

import torch
import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import FastLanguageModel
from unsloth import is_bfloat16_supported

max_seq_length = 2048
dtype = None
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name='unsloth/gemma-2-9b-it-bnb-4bit',
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit
)

model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
    lora_alpha=16,
    lora_dropout=0,
    bias='none',
    use_gradient_checkpointing='unsloth',
    random_state=52,
    use_rslora=False,
    loftq_config=None
)

# input - данные, полученные после ретрива + вопрос из эксель файла (ретрив делался по четырем pdf)
# output - ответ из эксель файлы
prompt = """
### Instruction:
Ты — интеллектуальный ассистент, отвечающий на вопросы пользователей на основе базы знаний ППР. 
Твоя задача:
- Отвечать кратко, понятно и по существу.
- Использовать исключительно факты, содержащиеся в базе (не выдумывай).
- Если информация отсутствует, честно сообщай, что она не найдена.
- Структура и стиль ответа должны соответствовать официальному тону.

### Input:
{}

### Response:
{}
"""

EOS_TOKEN = tokenizer.eos_token
def formatting_prompts_func(examples):
    inputs = examples["input"]
    outputs = examples["output"]
    texts = []
    for input_, output in zip(inputs, outputs):
        text = prompt.format(input_, output) + EOS_TOKEN
        texts.append(text)
    return {"text": texts}

# w/ retrieved data in Заголовок Статьи - это заголовок + данные, заретривленные из базы знаний для трейна
data = pd.read_excel('ppr-train-data/train.xls')
data.dropna(inplace=True)

input_template = '''
{question}
'''

output_template = '''
{answer}
'''

train_df = pd.DataFrame({
    'input': data.apply(lambda row: input_template.format(
        question=row['Заголовок статьи'],
    ), axis=1),
    'output': data.apply(lambda row: output_template.format(
        answer=row['Описание']
    ), axis=1)
})

# train_df, val_df = train_test_split(train_df, test_size=0.1, random_state=52)

train_dataset = Dataset.from_pandas(train_df)
# val_dataset = Dataset.from_pandas(val_df)

train_dataset = train_dataset.map(formatting_prompts_func, batched=True)
# val_dataset = val_dataset.map(formatting_prompts_func, batched=True)

args = TrainingArguments(
    report_to='none',
    num_train_epochs=4,
    per_device_train_batch_size=2,
    # per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_ratio=0.02,
    learning_rate=2e-4,
    fp16=(not is_bfloat16_supported()),
    bf16=(is_bfloat16_supported()),
    # eval_strategy="steps",
    save_strategy="steps",
    save_steps=20,
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    seed=52,
    output_dir="outputs"
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    # eval_dataset=val_dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=args,
    # compute_metrics=compute_metrics
)

trainer_stats = trainer.train()