# Assistente de Voz Multi-Idiomas

Este projeto foi criado como parte de um desafio da plataforma de ensino DIO (Digital Innovation One), com orientação do professor Vanilton Falvo.

O objetivo do projeto é construir um assistente de voz multi-idiomas utilizando Whisper para transcrição de áudio e ChatGPT para geração de respostas.



## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/assistente-de-voz-multi-idiomas.git
cd assistente-de-voz-multi-idiomas

2. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv venv
source venv/bin/activate  # No Windows use `venv\Scripts\activate`
pip install -r requirements.txt

3. Configure suas variáveis de ambiente:

```bash
export OPENAI_API_KEY="sua-chave-api-aqui"

4. Execute o assistente:

```bash
python app.py

## Uso

1. O assistente começará a gravar automaticamente após a execução.
2. Fale algo em um dos idiomas suportados.
3. O assistente transcreverá seu áudio, enviará para o ChatGPT e retornará uma resposta em áudio.

## Idiomas Suportados

- Inglês (en)
- Português (pt)
- Espanhol (es)
- Francês (fr)
- Alemão (de)
- Italiano (it)
- Japonês (ja


## Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.
