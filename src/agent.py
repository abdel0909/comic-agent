import os, json
from typing import Dict, List
from PIL import Image
from .utils import add_bubbles, compose_page

# Torch/Diffusers optional (Mock-Fallback ohne GPU)
HAS_TORCH = False
try:
    import torch
    from diffusers import StableDiffusionXLPipeline, StableDiffusionXLControlNetPipeline, ControlNetModel
    HAS_TORCH = True
except Exception:
    pass

def load_json(p): 
    with open(p, "r", encoding="utf-8") as f: 
        return json.load(f)

def ensure_dirs():
    os.makedirs("out/panels", exist_ok=True)
    os.makedirs("out/pages", exist_ok=True)

def build_prompt(scene: Dict, panel: Dict, policy: Dict, char_db: Dict) -> str:
    style = scene.get("style", "")
    beats = ", ".join(panel.get("beats", []))
    chars = []
    for name in scene.get("characters", []):
        entry = char_db.get(name, {})
        if entry.get("prompt"):
            chars.append(entry["prompt"])
        else:
            chars.append(name)
    boosters = policy.get("prompt_boosters", {})
    boost = []
    if boosters.get("lineart",0)>0.1: boost.append("clean lineart")
    if boosters.get("cel_shading",0)>0.1: boost.append("soft cel shading")
    if boosters.get("color_harmony",0)>0.1: boost.append("color harmony")

    prompt = (
        f"comic style, {style}, {', '.join(boost)}, "
        f"{panel['setting']}, {beats}, "
        f"characters: {', '.join(chars)}, "
        "professional composition, coherent lighting, consistent character design"
    )
    return prompt

def _pipe(policy, device):
    if not policy.get("use_controlnet_openpose"):
        pipe = StableDiffusionXLPipeline.from_pretrained(
            policy["model"],
            torch_dtype=torch.float16 if device=="cuda" else torch.float32
        ).to(device)
        return pipe, None
    # ControlNet OpenPose (SDXL)
    cn = ControlNetModel.from_pretrained(
        policy.get("openpose_model","thibaud/controlnet-openpose-sdxl-1.0"),
        torch_dtype=torch.float16 if device=="cuda" else torch.float32
    )
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        policy["model"], controlnet=cn,
        torch_dtype=torch.float16 if device=="cuda" else torch.float32
    ).to(device)
    return pipe, cn

def load_loras(pipe, char_db: Dict):
    # lade alle einzigartigen LoRAs einmalig
    loaded = set()
    for name, v in char_db.items():
        path = v.get("lora")
        if path and os.path.exists(path) and path not in loaded:
            pipe.load_lora_weights(path, adapter_name=path)
            loaded.add(path)
    # Setze Standard-Adapter-Gewichte (alle aktiv)
    if loaded:
        adapters = list(loaded)
        weights = [char_db[n]["weight"] for n,v in char_db.items() if v.get("lora") in adapters]
        # Falls Gewichte nicht in gleicher Reihenfolge sind, alles 0.8
        if len(weights) != len(adapters):
            weights = [0.8]*len(adapters)
        pipe.set_adapters(adapters, weights)

def render_panel(prompt, policy, pose_hint):
    device = "cuda" if HAS_TORCH and torch.cuda.is_available() else "cpu"
    w, h = policy.get("width", 832), policy.get("height", 1152)
    steps = policy.get("num_inference_steps", 28)
    guidance = policy.get("guidance_scale", 6.5)

    if HAS_TORCH:
        try:
            pipe, _ = _pipe(policy, device)
            load_loras(pipe, char_db)  # char_db aus Closure → siehe run() unten
            if policy.get("use_controlnet_openpose") and pose_hint and os.path.exists(pose_hint):
                hint = Image.open(pose_hint).convert("RGB")
                img = pipe(prompt, image=hint, num_inference_steps=steps, guidance_scale=guidance,
                           height=h, width=w).images[0]
            else:
                img = pipe(prompt, num_inference_steps=steps, guidance_scale=guidance,
                           height=h, width=w).images[0]
            return img
        except Exception:
            pass
    # Mock Fallback
    from PIL import ImageDraw, ImageFont
    img = Image.new("RGB", (w,h), (245,245,245))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except:
        font = ImageFont.load_default()
    d.multiline_text((20,20), "MOCK\n"+prompt[:400], fill=(20,20,20), font=font, spacing=6)
    d.rectangle([40, h*0.6, w-40, h-40], outline=(60,60,60), width=3)
    return img

def run(scene_path="prompts/example_scene.json", policy_path="configs/policy.json", chars_path="configs/characters.json"):
    global char_db
    ensure_dirs()
    scene = load_json(scene_path)
    policy = load_json(policy_path)
    char_db = load_json(chars_path)

    panels: List[Image.Image] = []
    for p in scene["panels"]:
        prompt = build_prompt(scene, p, policy, char_db)
        pose_hint = p.get("pose_hint")
        k = max(1, int(policy.get("variants_per_panel", 1)))
        best_img = None
        # einfache 1..k Variants (hier ohne Scoring – alle speichern)
        for i in range(k):
            img = render_panel(prompt, policy, pose_hint)
            with_bubbles = add_bubbles(img, p.get("dialogue", []))
            suffix = f"_{i+1}" if k>1 else ""
            out_path = f"out/panels/{p['id']}{suffix}.png"
            with_bubbles.save(out_path)
            print(f"[ok] {out_path}")
            best_img = best_img or with_bubbles
        panels.append(best_img)

    page = compose_page(panels)
    page.save("out/pages/page_01.png")
    print("[ok] out/pages/page_01.png")

if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("--scene", default="prompts/example_scene.json")
    a.add_argument("--policy", default="configs/policy.json")
    a.add_argument("--chars",  default="configs/characters.json")
    args = a.parse_args()
    run(args.scene, args.policy, args.chars)
