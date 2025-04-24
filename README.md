anypdf2md/
├── anypdf2md/
│   ├── __init__.py
│   ├── config.py           # Carga/Guarda config, .env, prompts
│   ├── pdf_processor.py    # Lógica de PyMuPDF
│   ├── markitdown_processor.py # Lógica de Markitdown
│   ├── openrouter_client.py # Lógica de API OpenRouter
│   ├── summarizer.py       # Lógica de resumen
│   ├── core.py             # Orquestador principal de conversión
│   └── ui.py               # Definición de la UI Gradio
├── prompts/
│   ├── summary_prompt.md
│   ├── vlm_prompt_base.md
│   ├── vlm_prompt_with_markdown.md
│   ├── vlm_prompt_with_summary.md
│   └── vlm_prompt_full.md
├── main.py                 # Punto de entrada para lanzar la app
├── .env                    # Para la API Key (¡Añadir a .gitignore!)
├── config.json             # Guarda preferencias del usuario
└── requirements.txt        # Dependencias