import os
from huggingface_hub import snapshot_download

model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "promptenhancer-7b")

print(f"Downloading model to {model_dir}...")
snapshot_download(
    repo_id="tencent/HunyuanImage-2.1",
    allow_patterns=["reprompt/*"],
    local_dir=model_dir,
    local_dir_use_symlinks=False
)
print("Download finished!")
