# -*- coding: utf-8 -*-
"""เติมคำอธิบายภาษาไทย (description_th) ให้ repo ใน data/repos.json"""
import json
import io

TH = {
    "microsoft/PowerToys": "ชุดเครื่องมือฟรีจาก Microsoft สำหรับปรับแต่งและเพิ่มความสะดวกในการใช้ Windows เช่น จัดหน้าต่าง ครอบหน้าจอ คัดลอกสี และอื่น ๆ อีกมาก",
    "vercel-labs/agent-browser": "เอเจนต์ AI สำหรับควบคุมเบราว์เซอร์อัตโนมัติจาก Vercel Labs สั่งงานเว็บด้วยภาษาธรรมชาติได้",
    "deepseek-ai/deepseek-harness": "ชุดเครื่องมือและเฟรมเวิร์กของ DeepSeek สำหรับสร้างและฝึกโมเดล AI",
    "heygen-com/hyperframes": "เฟรมเวิร์กสร้างวิดีโอด้วย AI ประกอบฉาก แอนิเมชัน และเสียงได้จากโค้ด",
    "debpalash/OmniVoice-Studio": "สตูดิโอสังเคราะห์เสียงพูดและโคลนเสียง (TTS) คุณภาพสูง รองรับหลายภาษา",
    "CodebuffAI/freebuff": "เอเจนต์ AI เขียนโค้ดแบบฟรี ทำงานอัตโนมัติได้เอง (autonomous coding agent)",
    "multica-ai/multica": "แพลตฟอร์ม AI แบบหลายเอเจนต์ที่ทำงานร่วมกันและประสานงานกันได้",
    "Continuum-AI-Corp/OrcaRouter-Lite": "ตัวจัดเส้นทางโมเดล AI (LLM router) เลือกโมเดลให้เหมาะกับงานเพื่อประหยัดต้นทุนและเพิ่มความเร็ว",
    "shanraisshan/claude-code-best-practice": "รวมแนวทางปฏิบัติที่ดีที่สุดและเทคนิคการใช้ Claude Code",
    "Open-Finance-Lab/AgenticTrading": "ระบบเทรดอัตโนมัติที่ขับเคลื่อนด้วย AI Agent วิเคราะห์และตัดสินใจซื้อขายเอง",
    "FujiwaraChoki/MoneyPrinter": "บอทเทรดอัตโนมัติและเครื่องมือช่วยวิเคราะห์การเงิน",
    "harry0703/MoneyPrinterTurbo": "ระบบเทรดอัตโนมัติความเร็วสูงสำหรับตลาดคริปโตและหุ้น",
    "soemsri/BotTrade": "บอทเทรดอัตโนมัติสำหรับคริปโตเคอร์เรนซีและหุ้น",
    "jim-schwoebel/awesome_ai_agents": "คลังรวมโปรเจกต์ AI Agent ที่น่าสนใจ คัดสรรและจัดหมวดหมู่ไว้แล้ว",
    "Alishahryar1/free-claude-code": "ทางเลือกโอเพนซอร์สแบบฟรีของ Claude Code CLI",
    "Tencent/teamai-cli": "เครื่องมือ AI บนบรรทัดคำสั่งจาก Tencent สำหรับการทำงานเป็นทีม",
    "tashfeenahmed/freellmapi": "รวม API ของโมเดล LLM ฟรีหลายตัวไว้ใน API เดียว เรียกใช้ได้สะดวก",
    "tt-a1i/archify": "เครื่องมือออกแบบและวางสถาปัตยกรรมแอปพลิเคชันด้วย AI",
    "krillinai/OpenCreator": "ชุดเครื่องมือสร้างคอนเทนต์แบบโอเพนซอร์ส",
    "smartnfe/focusdock": "ตัวจับเวลาโฟกัสและเครื่องมือช่วยเพิ่มประสิทธิภาพการทำงาน",
    "thx0701/openclaw-virtual-office": "พื้นที่ทำงานและห้องทำงานเสมือนจริงสำหรับการทำงานร่วมกันเป็นทีม",
    "Osmantic/ODS": "เซิร์ฟเวอร์ AI ครบวงจรในตัวเดียว รวม Ollama, OpenWebUI, n8n และ ComfyUI",
}

with io.open('data/repos.json', encoding='utf-8') as f:
    data = json.load(f)

hit = miss = 0
for repo in data['repos']:
    name = repo.get('full_name')
    if name in TH:
        repo['description_th'] = TH[name]
        hit += 1
    else:
        repo['description_th'] = repo.get('description') or 'ไม่มีคำอธิบาย'
        miss += 1

data['_meta']['th_descriptions'] = hit

with io.open('data/repos.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print('translated: %d, fallback: %d, total: %d' % (hit, miss, len(data['repos'])))
