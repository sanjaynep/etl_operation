from transformers import AutoTokenizer,AutoModelForCausalLM

model_name = "Qwen/Qwen3-0.6B"
model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("Model loaded, running test...")
inputs = tokenizer("Anomaly=1 | [2026-07-22T15:39:08.345+0000] {local_task_job_runner.py:120} INFO - ::group::Pre task execution logs", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=20)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
