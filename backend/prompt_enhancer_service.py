import os
import re
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

logger = logging.getLogger(__name__)

class LowVramPromptEnhancer:
    def __init__(self, models_root_path):
        """
        Loads the HunyuanPromptEnhancer model using 4-bit Quantization
        so it can run on an 8GB RAM + RTX 3050 machine.
        """
        # Ensure the model path exists; if nested under reprompt, handle it
        if os.path.exists(os.path.join(models_root_path, "reprompt")):
            models_root_path = os.path.join(models_root_path, "reprompt")

        if not os.path.exists(models_root_path):
            logger.warning(f"Model path {models_root_path} empty! Needs downloading.")
            self.model = None
            self.tokenizer = None
            return

        print("[PromptEnhancer] Yukleniyor... Bu islem biraz zaman alabilir (4-bit)...")
        # 4-bit quant config for low VRAM
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                models_root_path, 
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                models_root_path, 
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )
            print("[PromptEnhancer] Model basariyla yüklendi (4-bit mode)!")
        except Exception as e:
            logger.error(f"Model yuklenirken hata: {e}")
            self.model = None

    def replace_single_quotes(self, text):
        pattern = r"\B'([^']*)'\B"
        replaced_text = re.sub(pattern, r'"\1"', text)
        replaced_text = replaced_text.replace("’", "”").replace("‘", "“")
        return replaced_text

    @torch.inference_mode()
    def enhance(
        self,
        prompt_cot: str,
        sys_prompt: str = "你是一位图像生成提示词撰写专家，请根据用户输入的提示词，改写生成新的提示词...", # Default from Hunyuan
        temperature: float = 0.3,
        max_new_tokens: int = 256
    ) -> str:
        
        if not self.model or not self.tokenizer:
            print("Model is not loaded! Returning original prompt.")
            return prompt_cot

        # Ensure system prompt is fully defined if cut short in default
        if sys_prompt == "你是一位图像生成提示词撰写专家，请根据用户输入的提示词，改写生成新的提示词...":
            sys_prompt = "你是一位图像生成提示词撰写专家，请根据用户输入的提示词，改写生成新的提示词，改写后的提示词要求：1 改写后提示词包含的主体/动作/数量/风格/布局/关系/属性/文字等 必须和改写前的意图一致； 2 在宏观上遵循“总-分-总”的结构，确保信息的层次清晰；3 客观中立，避免主观臆断和情感评价；4 由主到次，始终先描述最重要的元素，再描述次要和背景元素；5 逻辑清晰，严格遵循空间逻辑或主次逻辑，使读者能在大脑中重建画面；6 结尾点题，必须用一句话总结图像的整体风格或类型。"

        org_prompt = prompt_cot
        try:
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": org_prompt},
            ]
            tokenized_chat = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt"
            )
            inputs = tokenized_chat.to(self.model.device)
            
            outputs = self.model.generate(
                inputs,
                max_new_tokens=int(max_new_tokens),
                do_sample=True,
                temperature=float(temperature),
                top_p=0.9,
            )

            prompt_length = inputs.shape[-1]
            new_tokens = outputs[0][prompt_length:]
            output_res = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

            answer_pattern = r"<answer>(.*?)</answer>"
            answer_matches = re.findall(answer_pattern, output_res, re.DOTALL)
            if answer_matches:
                prompt_cot = answer_matches[0].strip()
            else:
                output_clean = re.sub(r"<think>[\s\S]*?</think>", "", output_res).strip()
                prompt_cot = output_clean if output_clean else org_prompt
            prompt_cot = self.replace_single_quotes(prompt_cot)
            return prompt_cot
        except Exception as e:
            logger.error(f"Geliştirme sırasinda hata olustu: {e}")
            return org_prompt

# Singleton instance - will not load until the model folder actually has content or called
_enhancer_instance = None

def get_prompt_enhancer() -> LowVramPromptEnhancer:
    global _enhancer_instance
    if _enhancer_instance is None:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "promptenhancer-7b")
        _enhancer_instance = LowVramPromptEnhancer(model_dir)
    return _enhancer_instance

def enhance_image_prompt(base_prompt: str) -> str:
    """
    Kullanicinin girdiği bir görüntü prompt'unu (metnini)
    Hunyuan 7B kullanarak yapisal ve kaliteli hale getirir.
    """
    enhancer = get_prompt_enhancer()
    return enhancer.enhance(base_prompt)

if __name__ == "__main__":
    # Test script for local verification
    print("Testing Prompt Enhancer Model (Low VRAM)...")
    result = enhance_image_prompt("Third-person view, a race car speeding on a city track...")
    print("Original: Third-person view, a race car speeding on a city track...")
    print(f"Enhanced:\n{result}")
