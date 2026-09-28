# -*- coding: utf-8 -*-
"""
ตัวแปลคำอธิบาย repo เป็นไทยแบบคร่าว ๆ (ไม่ใช้ LLM / ไม่ต้องมี API key)

วิธีทำงาน: จับคู่คำ/วลีเทคนิคในคำอธิบายอังกฤษกับคำไทย แล้วประกอบเป็นประโยคสั้น ๆ
ถ้าจับคู่ไม่ได้เลย จะใช้ประโยคกลางตามหมวดหมู่แทน
"""
import re

# (pattern, คำไทย) — เรียงจากเฉพาะเจาะจงไปหาคำกว้าง เพราะหยุดที่ 4 แนวคิดแรก
GLOSSARY = [
    # --- AI / ML ---
    (r'large language model|\bllms?\b', 'โมเดลภาษาขนาดใหญ่ (LLM)'),
    (r'retrieval.augmented|\brag\b', 'RAG ค้นคู่บริบท'),
    (r'multi[- ]?agent', 'ระบบหลายเอเจนต์'),
    (r'\bagents?\b|agentic', 'เอเจนต์ AI'),
    (r'fine[- ]?tun', 'ปรับจูนโมเดล'),
    (r'\btraining\b|\btrain\b', 'ฝึกโมเดล'),
    (r'inference|model serving', 'ให้บริการโมเดล'),
    (r'embedding', 'เวกเตอร์ฝังคำ'),
    (r'vector (db|database|store|search)', 'ฐานข้อมูลเวกเตอร์'),
    (r'computer vision|image recognition|image classification', 'การมองเห็นของคอมพิวเตอร์'),
    (r'\bocr\b|text extraction from image', 'อ่านข้อความจากภาพ (OCR)'),
    (r'text.to.speech|\btts\b', 'สังเคราะห์เสียงพูด'),
    (r'speech.to.text|\basr\b|transcri', 'ถอดเสียงเป็นข้อความ'),
    (r'voice clon|voice synth|\bvoice\b', 'เสียงพูด/โคลนเสียง'),
    (r'image generation|diffusion|text.to.image', 'สร้างภาพด้วย AI'),
    (r'prompt', 'พรอมป์ต'),
    (r'openai|anthropic|\bgemini\b|\bclaude\b|\bgpt\b', 'โมเดล AI ชั้นนำ'),
    (r'deep learning|neural network', 'โครงข่ายประสาทเทียม'),
    (r'machine learning|\bml\b', 'แมชชีนเลิร์นนิง'),
    (r'\bnlp\b|natural language', 'ประมวลผลภาษาธรรมชาติ'),
    (r'benchmark|evaluation|eval', 'วัดผล/ประเมินโมเดล'),
    # --- เขียนโค้ด ---
    (r'coding agent|code generation|programming assistant|\bcoding\b', 'ช่วยเขียนโค้ด'),
    (r'model context protocol|\bmcp\b', 'MCP'),
    (r'command.line|\bcli\b', 'เครื่องมือบรรทัดคำสั่ง'),
    (r'\bterminal\b', 'เทอร์มินัล'),
    (r'\bide\b|\beditor\b', 'ตัวแก้ไขโค้ด'),
    # --- Automation ---
    (r'\bautomation\b|automate', 'ทำงานอัตโนมัติ'),
    (r'workflow', 'เวิร์กโฟลว์'),
    (r'n8n|zapier|low.code|no.code', 'เชื่อมต่อบริการแบบไม่ต้องเขียนโค้ด'),
    (r'scrap|crawl', 'ดึงข้อมูลจากเว็บ'),
    (r'\bbrowser\b', 'เบราว์เซอร์'),
    (r'\brobot\b|\bbots?\b', 'บอท'),
    (r'scheduler|cron|task queue', 'ตั้งเวลาทำงาน'),
    (r'\bapi\b', 'API'),
    (r'notification|\balert', 'แจ้งเตือน'),
    (r'telegram|discord|slack|\bline\b', 'เชื่อมต่อแชต'),
    (r'home assistant|\biot\b|smart home', 'สมาร์ตโฮม/IoT'),
    (r'docker|kubernetes|container', 'คอนเทนเนอร์'),
    (r'self.host', 'ติดตั้งเองได้'),
    (r'\bemail\b|smtp', 'อีเมล'),
    # --- Trading / Finance ---
    (r'backtest', 'ทดสอบกลยุทธ์ย้อนหลัง'),
    (r'\btrading\b|\btrade\b|\btrader\b', 'เทรด'),
    (r'crypto|bitcoin|ethereum|blockchain', 'คริปโต'),
    (r'forex|currency', 'ค่าเงิน/ฟอเร็กซ์'),
    (r'\bstocks?\b|equit|market data', 'หุ้น/ข้อมูลตลาด'),
    (r'portfolio', 'พอร์ตการลงทุน'),
    (r'indicator|technical analysis|chart', 'อินดิเคเตอร์/วิเคราะห์ทางเทคนิค'),
    (r'strateg(y|ies)', 'กลยุทธ์'),
    (r'financ|monetary', 'การเงิน'),
    (r'exchange', 'ตลาดแลกเปลี่ยน'),
    # --- Dev tools ทั่วไป ---
    (r'\bframework', 'เฟรมเวิร์ก'),
    (r'\blibrar(y|ies)', 'ไลบรารี'),
    (r'\bsdk\b', 'SDK'),
    (r'database|\bsql\b|postgres|sqlite|mongo', 'ฐานข้อมูล'),
    (r'devops|ci/cd|\bpipeline\b', 'DevOps/CI-CD'),
    (r'monitoring|observability|logging', 'มอนิเตอร์ระบบ'),
    (r'productivity', 'เพิ่มประสิทธิภาพการทำงาน'),
    (r'note.taking|knowledge base|markdown|wiki', 'จดโน้ต/ฐานความรู้'),
    (r'\bui\b|dashboard|frontend', 'หน้าจอ/แดชบอร์ด'),
    (r'backend|\bserver\b', 'เซิร์ฟเวอร์'),
    (r'security|pentest|vulnerabilit|encrypt', 'ความปลอดภัย'),
    (r'cross.platform|multi.platform', 'ข้ามแพลตฟอร์ม'),
    (r'\bextension\b|\bplugin\b|addon', 'ส่วนขยาย'),
    (r'real.time', 'เรียลไทม์'),
    (r'scalable|high.performance|\bfast\b|lightweight|blazing', 'เร็ว/ขยายระบบได้'),
    (r'offline|local.first', 'ทำงานออฟไลน์'),
    (r'\bgame\b|gaming', 'เกม'),
    (r'template|boilerplate|starter', 'เทมเพลตเริ่มต้น'),
    (r'awesome|curated|collection|list of', 'รวมลิงก์/คอลเลกชัน'),
    (r'learning|tutorial|course|guide|book', 'สื่อการเรียนรู้'),
    (r'open.source|opensource', 'โอเพนซอร์ส'),
    (r'\bfree\b', 'ฟรี'),
]

CATEGORY_LABEL = {
    'ai': 'โปรเจกต์ AI ด้าน',
    'automation': 'เครื่องมืออัตโนมัติสำหรับ',
    'trading': 'เครื่องมือเทรด/การเงินด้าน',
    'tool': 'เครื่องมือสำหรับนักพัฒนาด้าน',
    'tools': 'เครื่องมือสำหรับนักพัฒนาด้าน',
}

MAX_CONCEPTS = 4


def translate_th(description, language=None, category=None):
    """แปลงคำอธิบายอังกฤษเป็นไทยคร่าว ๆ"""
    desc = (description or '').strip()
    label = CATEGORY_LABEL.get(category or '', 'โปรเจกต์โอเพนซอร์สด้าน')

    concepts = []
    if desc:
        text = desc.lower()
        for pattern, thai in GLOSSARY:
            if re.search(pattern, text):
                if thai not in concepts:
                    concepts.append(thai)
                if len(concepts) >= MAX_CONCEPTS:
                    break

    if concepts:
        out = label + ' ' + ', '.join(concepts)
    else:
        out = label + ' ซอฟต์แวร์โอเพนซอร์ส'

    if language and language != '-':
        out += ' (เขียนด้วย %s)' % language
    return out
