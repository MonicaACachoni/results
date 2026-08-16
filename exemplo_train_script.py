"""
Script de treinamento (train.py)
Este arquivo deve ser criado e usado como entry_point no HuggingFace Estimator
"""

import argparse
import os
import json
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset

def parse_args():
    parser = argparse.ArgumentParser()
    
    # Hyperparameters
    parser.add_argument("--model_name", type=str, default="gpt2")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--per_device_train_batch_size", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--fp16", type=bool, default=True)
    
    # Data, model, and output directories
    parser.add_argument("--output_data_dir", type=str, default=os.environ["SM_OUTPUT_DATA_DIR"])
    parser.add_argument("--model_dir", type=str, default=os.environ["SM_MODEL_DIR"])
    parser.add_argument("--train", type=str, default=os.environ["SM_CHANNEL_TRAINING"])
    
    return parser.parse_args()

def preprocess_function(examples, tokenizer):
    """
    Preprocessa os dados de treinamento
    """
    # Formato esperado: {"instruction": "...", "input": "...", "output": "..."}
    texts = []
    for i in range(len(examples.get("instruction", []))):
        instruction = examples["instruction"][i] if "instruction" in examples else ""
        input_text = examples["input"][i] if "input" in examples else ""
        output = examples["output"][i] if "output" in examples else ""
        
        # Formatar como prompt + resposta
        text = f"{instruction}\n{input_text}\n{output}"
        texts.append(text)
    
    # Tokenizar
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=512,
        padding="max_length",
        return_tensors="pt"
    )
    
    return tokenized

def main():
    args = parse_args()
    
    # Carregar modelo e tokenizer
    print("Carregando modelo e tokenizer...")
    model = AutoModelForCausalLM.from_pretrained(args.model_name)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    # Adicionar padding token se não existir
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Carregar dados de treinamento
    print("Carregando dados de treinamento...")
    data_files = {"train": os.path.join(args.train, "bedrock_faqs_training.jsonl")}
    dataset = load_dataset("json", data_files=data_files)
    
    # Preprocessar dados
    print("Preprocessando dados...")
    tokenized_dataset = dataset.map(
        lambda x: preprocess_function(x, tokenizer),
        batched=True,
        remove_columns=dataset["train"].column_names
    )
    
    # Configurar argumentos de treinamento
    training_args = TrainingArguments(
        output_dir=args.model_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        learning_rate=args.learning_rate,
        fp16=args.fp16,
        logging_steps=10,
        save_steps=500,
        evaluation_strategy="no",
        save_total_limit=2,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # Causal LM, não masked LM
    )
    
    # Criar trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        data_collator=data_collator,
    )
    
    # Treinar
    print("Iniciando treinamento...")
    trainer.train()
    
    # Salvar modelo e tokenizer
    print("Salvando modelo...")
    trainer.save_model()
    tokenizer.save_pretrained(args.model_dir)
    
    print("Treinamento concluído!")

if __name__ == "__main__":
    main()

