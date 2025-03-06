<div align="center">
  
# 🧠 Neural-Chat

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/genius-harry/neural-chat)

*An AI discussion system enabling collaborative conversations between multiple large language models*

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Models](#-models) • [Configuration](#-configuration) • [Troubleshooting](#-troubleshooting)

</div>

<p align="center">
  <img src="https://via.placeholder.com/800x400?text=Neural-Chat+Conversation+Flow" alt="Neural-Chat System Diagram" width="800"/>
</p>

## ✨ Features

- 🤖 **Multi-model discussions** - Seamlessly integrates GPT-4o, Gemini, Grok, DeepSeek, and Claude
- 🗳️ **Democratic discussion flow** - Models vote on whether to continue the conversation
- 💬 **Structured dialogue** - Models reference and respond to each other's contributions
- 📝 **Automatic summarization** - Generates a concise final summary of the entire discussion
- ⚙️ **Highly configurable** - Customize rounds, prompts, and model behavior

## 📋 Requirements

- Python 3.8+
- API keys for the following services:

| Model | Provider | API Key Registration |
|-------|----------|----------------------|
| GPT-4o | OpenAI | [Get API Key](https://platform.openai.com/api-keys) |
| Gemini | Google | [Get API Key](https://ai.google.dev/) |
| Grok | xAI | [Get API Key](https://x.ai) |
| DeepSeek | DeepSeek AI | [Get API Key](https://platform.deepseek.com/) |
| Claude | Anthropic | [Get API Key](https://console.anthropic.com/keys) |

## 🔧 Installation

<details>
<summary>Expand installation steps</summary>

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Neural-Chat.git
   cd Neural-Chat
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the project root with your API keys:**
   ```
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   XAI_API_KEY=your_xai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

</details>

## 🚀 Quick Start

Run the main script to start a new discussion:

```bash
python main.py
```

You will be prompted to enter a discussion topic. The system will then:

1. Send the topic to each model in sequence
2. Display each model's contribution and vote
3. Tally votes to determine whether to continue the discussion
4. Repeat for multiple rounds (if voted to continue)
5. Generate a final summary of the conversation

## 🛠️ How It Works

1. Each model receives the discussion topic and the full context of previous contributions
2. Models are instructed to:
   - Provide a thoughtful contribution to the topic
   - Reference other models' contributions when appropriate
   - Vote on whether further discussion is needed
3. After all models contribute, votes are tallied
4. If the majority votes to continue, a new round begins
5. After discussion concludes, GPT-4o generates a summary

## ⚙️ Configuration

You can adjust the maximum number of discussion rounds in `config.py`:

```python
MAX_DISCUSSION_ROUNDS = 7  # Change this value as needed
```

The behavior of Neural-Chat can be customized through the `config.py` file:

- `RESPONSE_LENGTH`: Controls the target length of model responses in the discussion (in words). Default is 100 words.

## 🧠 Models

- **GPT-4o**: OpenAI's advanced model
- **Gemini**: Google's generative AI model
- **Grok**: xAI's large language model
- **DeepSeek**: DeepSeek AI's LLM
- **Claude**: Anthropic's AI assistant

Neural-Chat currently supports the following models:

- GPT-4o (OpenAI)
- Gemini 2.0 Flash (Google)
- Grok (xAI)
- DeepSeek
- Claude (Anthropic)

Each model participates in the discussion and provides contributions based on the configured length and other parameters.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## API Keys

To use Neural-Chat, you'll need to provide API keys for the models you want to include in the discussion. These should be configured in `api_keys.py`.
