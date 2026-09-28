# 🔍 RepoHunter

ค้นหาและรวบรวม repository น่าสนใจบน GitHub

## 🚀 Features

- 🔍 ค้นหา repo ตามชื่อหรือคำอธิบาย
- 🏷️ กรองตามหมวดหมู่ (AI, Automation, Trading, Tools)
- 📊 แสดงสถิติ (จำนวน repo, รวมดาว)
- ⚡ อัปเดตอัตโนมัติผ่าน GitHub Actions
- 🌙 Dark theme สวยงาม

## 📁 Project Structure

```
repohunter/
├── index.html          # หน้าเว็บหลัก
├── style.css           # สไตล์ (Dark Theme)
├── app.js              # Logic ฝั่ง client
├── data/
│   └── repos.json      # ข้อมูล repo (อัปเดตโดย GitHub Actions)
├── .github/
│   └── workflows/
│       └── fetch-repos.yml  # GitHub Actions cron
└── README.md
```

## 🖥️ ใช้งาน

เปิด `index.html` ในเบราว์เซอร์ หรือ Deploy บน GitHub Pages:
- `https://username.github.io/repohunter`

## 🔄 Auto Update

GitHub Actions จะดึงข้อมูล repo ใหม่ทุกวันเวลา 08:00 UTC

## 📊 Data Sources

- GitHub Search API
- GitHub Trending
- Product Hunt
- FirstTimers Only
