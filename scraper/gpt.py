from openai import OpenAI
import os

def get_gpt_insights(profile_text: str, model: str = "gpt-4o") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = (
        "Você é um especialista em pré-vendas ERP da Benner (Consulte o site benner.com.br para saber mais sobre a vertical)."
        "Seu papel é analisar o perfil de um decisor e sua empresa para gerar insights de prospecção com base em desafios reais do setor, oportunidades estratégicas e o portfólio da Benner.\n\n"
        "Ao gerar os insights, use linguagem consultiva, objetiva e de impacto. Inclua dados contextuais de mercado, regulação (ex: LGPD, e-Social), e dores comuns de empresas como a analisada. "
        "Mencione como os produtos ERP da Benner ajudam a resolver essas dores com argumentos tangíveis (ex: automação de processos, conformidade, redução de riscos, integração de sistemas legados).\n\n"
        "Divida a resposta em seções:\n"
        "1. Pontos de conexão\n"
        "2. Abordagem inicial\n"
        "3. Diagnóstico estratégico\n"
        "4. Tópicos para perguntas (aqui, gere perguntas que esteja relacionada a metodologia SPIN, então use dessa metodologia para gerar perguntas!)\n"
        "5. Tom recomendado para falar com a persona\n\n"
        "Evite generalidades. Seja direto, consultivo, estratégico e focado em valor para o negócio."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Perfil LinkedIn extraído:\n---\n{profile_text}\n---"},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=700,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
