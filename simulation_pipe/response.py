import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))


@lru_cache(maxsize=1)
def _load_llm():
    model_name = "Qwen/Qwen3-0.6B"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    model.eval()
    return tokenizer, model


def _generate_response(stripped_line: str) -> dict[str, str]:
    tokenizer, model = _load_llm()

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
        max_new_tokens=256,
        do_sample=False,
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

    try:
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0

    thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

    return {"thinking_content": thinking_content, "content": content}


def Response(stripped_line: str):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_generate_response, stripped_line)
        try:
            return future.result(timeout=LLM_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            return {
                "thinking_content": "",
                "content": (
                    "LLM generation timed out on the local model. "
                    "The alert was still sent so you can continue investigating the anomaly."
                ),
            }
        except Exception as exc:
            return {
                "thinking_content": "",
                "content": f"LLM generation failed: {exc}",
            }

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
    msg["From"] = os.environ["ALERT_EMAIL_FROM"]
    msg["To"] = to_email

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.sendmail(msg["From"], [to_email], msg.as_string())
