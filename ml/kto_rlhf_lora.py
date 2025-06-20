# !pip install unsloth
# !pip uninstall unsloth -y && pip install --upgrade --no-cache-dir "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# import torch
# if torch.cuda.get_device_capability()[0] >= 8:
#     !pip install --no-deps packaging ninja einops "flash-attn>=2.6.3"

import pandas as pd
import torch
from unsloth import FastLanguageModel
from datasets import Dataset
from trl import KTOConfig, KTOTrainer

max_seq_length = 2048
dtype = None
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name='unsloth/gemma-2-9b-it-bnb-4bit',
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit
)

# dataset format from https://huggingface.co/docs/trl/kto_trainer

# w/ retrieved data in Заголовок Статьи - это заголовок + данные, заретривленные из базы знаний для трейна
# вид (prompt, ans, binary label) для трейна
# лейбл считается True если оценка 4 или 5; False если 1 или 2; сэмплы с оценкой 3 мы не используем
data = pd.read_csv('ppr-train-data/kto_train.csv')
data['Оценка'] = data['Оценка'].apply(lambda x: get_label(x)) # конвертируем оценку в лейбл
data.dropna(inplace=True) # те строки, у которых была оценка 3
rename_mapping = {
    'Заголовок статьи': 'prompt',
    'Описание': 'completion',
    'Оценка': 'label'
}
data = data.rename(columns=rename_mapping, axis=1)
train_dataset = Dataset.from_pandas(data)

training_args = KTOConfig(
    report_to='none',
    num_train_epochs=4,
    per_device_train_batch_size=2,
    # per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_ratio=0.02,
    learning_rate=2e-5, # lower than in sft
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
    output_dir="outputs2", 
)

trainer = KTOTrainer(
    model=model, 
    processing_class=tokenizer, 
    train_dataset=train_dataset,
    args=training_args,
    dataset_num_proc=2
)

trainer.train()