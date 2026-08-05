# 📖 Final Write-Up – Question 3

## 🌍 Architecture Overview

Rather than building two separate hardcoded voice agents, the system follows a **configuration-driven routing architecture**.

A single routing framework dynamically loads market-specific JSON configuration files:

* `ph_config.json` – Philippines
* `id_config.json` – Indonesia

Each configuration controls:

* 🌐 ASR language hints
* 🔊 Native TTS voice selection
* 🌍 Localization rules
* 🚨 Fallback & escalation phrases

This approach makes the solution easily extensible to additional countries without modifying the core application logic.

---

# 🎙️ Language-Specific ASR & Code-Switching Performance

Both markets use **Deepgram Nova-2** because of its strong multilingual speech recognition capabilities and low streaming latency.

## 🇵🇭 Philippines (Taglish)

**Configuration:** Filipino Language Model

### Performance

The ASR successfully handled rapid **Tagalog-English code switching**, accurately recognizing industry terms embedded inside Tagalog sentences such as:

* policy
* premium
* renewal

### Observed Limitation

During very rapid speech transitions, the ASR occasionally produced phonetic substitutions.

| Expected       | Transcribed |
| -------------- | ----------- |
| `ise-escalate` | `iseigisa`  |
| `mag-lapse`    | `maglapsi`  |

These errors occurred primarily because English loanwords were pronounced using native Tagalog phonetics.

---

## 🇮🇩 Indonesia (Bahasa Indonesia)

**Configuration:** Indonesian Language Model

### Performance

The model performed well across both:

* Formal register (e.g., **Bapak**, **Ibu**)
* Informal conversational language (e.g., **nggak**, **suka telat**)

This produced natural conversations that closely resemble real customer support interactions.

### Known Regional Accent Gap

Testing with a strong **Javanese-accented** recording exposed a significant limitation.

The combination of:

* regional pronunciation
* dropped syllables
* accent variation

caused transcription quality to degrade substantially.

### Recommendation

Future production deployments should include:

* Accent-adapted acoustic models
* Region-specific language routing
* Specialized fallback handling for rural Indonesian speakers

---

# 🔊 Native TTS Selection

To improve speech quality, the implementation uses **Azure Neural TTS (Free Tier)** instead of standard ElevenLabs voices.

| Market           | Voice                   |
| ---------------- | ----------------------- |
| 🇵🇭 Philippines | `fil-PH-BlessicaNeural` |
| 🇮🇩 Indonesia   | `id-ID-GadisNeural`     |

### Results

* Natural pronunciation
* Professional voice quality
* Native regional cadence
* Good conversational pacing

### Compromise

Although Azure Neural voices sound highly natural, emotional delivery remains somewhat limited.

During empathy-heavy responses (such as apologies or escalations), the synthesized speech occasionally sounds slightly robotic.

---

# 🚨 Fallback & Human Escalation

To satisfy the requirement of **preventing unexpected English switching**, all escalation responses are localized within the system prompts.

### Example

**Scenario**

Customer:

> "This is so unfair. I want to speak to a manager."

System Response:

> **"Pasensya na po, ise-escalate ko na po ito sa aming specialist..."**

The model correctly suppressed its default English tendencies and produced a fully localized Tagalog escalation.

---

# 🌐 Localization vs Literal Translation

The assistant prioritizes **natural localization** over direct word-for-word translation.

---

## 🇵🇭 Philippines (Life Insurance)

| Direct Translation                        | Localized Taglish                                                                     | Localization Strategy                                                                        |
| ----------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Your policy will cancel if you don't pay. | **Kailangan po nating ma-settle ang premium para hindi mag-lapse ang inyong policy.** | Retains English insurance terminology while using respectful Tagalog phrasing with **"po"**. |
| I will transfer you to a manager.         | **Ise-escalate ko na po ito sa aming specialist...**                                  | Uses the commonly spoken Taglish verb **"Ise-escalate."**                                    |
| Do you want health insurance?             | **Baka gusto niyo rin pong ang health rider para dagdag proteksyon...**               | Conversational wording that sounds natural to Filipino speakers.                             |

---

## 🇮🇩 Indonesia (Multifinance)

| Direct Translation            | Localized Bahasa Indonesia                                  | Localization Strategy                                                                      |
| ----------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Your payment is due tomorrow. | **Besok itu jatuh tempo cicilan motor Bapak.**              | Uses authentic Indonesian finance terminology such as **jatuh tempo** and **cicilan**.     |
| You will get a late fee.      | **Kami bisa catat komitmen Bapak supaya nggak kena denda.** | Combines respectful language (**Bapak**) with natural conversational phrasing (**nggak**). |
| I don't know the answer.      | **Mohon maaf Bapak/Ibu, saya akan eskalasikan hal ini...**  | Switches to a fully formal customer-service register during fallback situations.           |

---

# ✅ Key Highlights

* 🌍 Configuration-driven multi-country architecture
* 🎙️ Deepgram Nova-2 multilingual streaming ASR
* 🔊 Azure Neural TTS with native regional voices
* 🇵🇭 Robust Taglish code-switching support
* 🇮🇩 Natural Bahasa Indonesia conversational support
* 🚨 Localized fallback and human escalation
* 🌐 Context-aware localization instead of literal translation
* 📈 Easily extensible to additional languages and markets
