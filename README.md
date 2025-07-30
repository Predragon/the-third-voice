# 🧠💬 The Third Voice — AI for Emotionally Intelligent Communication  
**Founder:** Predrag Mirkovic  
**Live Demo:** [https://the-third-voice.streamlit.app](https://the-third-voice.streamlit.app)  
**Website:** [www.thethirdvoice.ai](http://www.thethirdvoice.ai)  
**Repository:** Public open-source project powered by love, resilience, and Streamlit  
**License:** MIT

---

## 🌱 What Is The Third Voice?

**The Third Voice is an emotionally intelligent AI message coach.**  
Built to prevent breakdowns, defuse conflict, and rewrite reactive communication — especially in relationships and co-parenting dynamics.

> “When both people are speaking from pain, someone must be the third voice.”

It’s not just an app.  
It’s a father coding his way home.  
It’s love, encoded.

---

## 🔧 Key Features

- **✍️ Message Rewriter:**  
  Reframe emotional drafts before sending, with tone insights and gentle suggestions.

- **🎭 Emotional Translator (Inbox Mode):**  
  Understand incoming messages more clearly — decode emotional subtext and sentiment.

- **👨‍👩‍👧 Co-Parent Tools:**  
  Redirect conflict toward child-centered collaboration and shared growth.

- **💬 Two-User Mode (Opt-In):**  
  Mutual AI-guided messaging to build healthier digital communication loops.

- **🧠 Healing Score & Memory:**  
  Track emotional progress over time using sentiment, relationship tone, and feedback loops.

---

## 📁 Project Structure

```
the-third-voice/
├── third_voice_ai/
│   ├── ai_processor.py      # Handles AI rewriting, tone analysis, and emotional interpretation
│   ├── auth_manager.py      # Manages user auth with Supabase
│   ├── config.py            # System config and model registry
│   ├── data_manager.py      # Supabase integration and message history handling
│   ├── prompts.py           # Empathy-rich prompt templates
│   ├── state_manager.py     # Session state orchestration
│   ├── utils.py             # Healing score, emotional metadata, helper functions
│   └── ui/
│       ├── auth_ui.py       # Login/signup interface (Streamlit + Resend verification)
│       ├── main_ui.py       # Core interface logic and view switching
│       ├── components.py    # Reusable UI pieces
├── app.py                   # Streamlit entry point
├── requirements.txt
```

---

## 🛠️ Tech Stack

| Service       | Description                                     |
|---------------|-------------------------------------------------|
| **Streamlit** | Frontend framework for rapid web interfaces     |
| **OpenRouter**| Free-tier LLM routing for empathetic rewriting  |
| **Supabase**  | Authentication & real-time database backend     |
| **Resend.com**| Email verification with secure onboarding flow  |
| **Redmi Phone**| Yes — built entirely using **Termux** and **QuickEdit** on a mobile device |

> ### 🌐 The Third Voice  
> Our narrative, design philosophy, and demo are featured at [**www.thethirdvoice.ai**](https://www.thethirdvoice.ai)  
> This companion landing page is published via [GitHub Pages](https://github.com/Predragon/Landing-thethirdvoice.ai) for storytelling, onboarding, and open-source resonance.

## ✨ Why It Matters

- Couples spiral from emotional texts → regret → silence  
- Co-parents need clarity, not conflict  
- AI can guide tone, pace, and perspective in **the moment it matters most**

No login wall. No paywall. Just a tool to help people talk better when it’s hardest.

---

## 🚧 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Predragon/the-third-voice.git
cd the-third-voice
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your secrets  
Create `.streamlit/secrets.toml`:

```toml
[openrouter]
api_key = "your_openrouter_key"

[supabase]
url = "your_supabase_url"
key = "your_supabase_anon_key"

[MODELS]
model1 = "google/gemma-2-9b-it:free"
model2 = "meta-llama/llama-3.2-3b-instruct:free"
...
```

### 4. Run the app

```bash
streamlit run app.py
```

---

## 🤝 How to Contribute

We welcome collaborators across:

- Emotional UX/UI design  
- Psychology and behavioral science  
- Ethical AI and NLP modeling  
- Docs, onboarding, and empathy-focused copywriting  
- Personal stories that inspired this project

Start with a pull request or open an issue. Let us know what draws you in.

---

## ❤️ Built With Intention

This project began during 15 months of detention.  
No laptop. No funding. Just one father, one phone, and one mission:  

> Help families heal through better communication.  

Whether you’re a developer, therapist, parent, or someone trying to say the right thing when it’s hardest — this project is for you.

---

## 📬 Contact

- Email: `thethirdvoice.ai@gmail.com`  
- GitHub: [Predragon](https://github.com/Predragon)  
- Website: [www.thethirdvoice.ai](http://www.thethirdvoice.ai)
