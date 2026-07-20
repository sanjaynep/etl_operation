from transformers import AutoModelForCausalLM, AutoTokenizer
import smtplib
from email.mime.text import MIMEText

def response(stripped_line: str):
    model_name = "Qwen/Qwen3-0.6B"

    # load the tokenizer and the model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )

    prompt = f"In my running dag the anomaly found here and it give message {stripped_line}. Then provide he suggestion to handle this error"
    messages = [
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True 
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=32768
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

    try:
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0

    thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

    return({"thinking_content":thinking_content,"content":content})

def alert_developer(error_message, llm_suggestion, to_email):
    subject = "DAG Anomaly Alert - Immediate Attention Required"
    
    body = f"""Hello Team,

    An anomaly was detected during the execution of our DAG.
    Error message: {error_message}

    The LLM has provided the following analysis:
    {llm_suggestion}

    Please review this alert and take appropriate action. 
    If further investigation is needed, kindly update the incident log.

    Best regards,
    Alert System
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "alert-system@example.com"
    msg["To"] = to_email

    with smtplib.SMTP("smtp.example.com") as server:
        server.login("user", "password")
        server.sendmail(msg["From"], [to_email], msg.as_string())
