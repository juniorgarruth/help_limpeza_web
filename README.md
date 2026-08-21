# Help! Limpeza Especializada - Versão Web

Sistema de gestão financeira (Receitas e Despesas Aureni, Funcionários,
Relatórios e Cadastros) desenvolvido em Python + Streamlit + SQLite.

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Publicar no Streamlit Community Cloud

1. Crie uma conta no [GitHub](https://github.com) (se ainda não tiver).
2. Crie um repositório **público** (ex.: `help-limpeza-web`).
3. Envie todos os arquivos desta pasta para o repositório
   **exceto** `help_sistema.db` (dados pessoais ficam apenas no seu PC).
4. Acesse [share.streamlit.io](https://share.streamlit.io), entre com a
   conta do GitHub e clique em **Create app** (Deploy a public app from
   GitHub).
5. Preencha: Repository = `seu-usuario/help-limpeza-web`,
   Branch = `main`, Main file path = `streamlit_app.py`.
6. Antes de finalizar, abra **Advanced settings** e cadastre o secret:
   ```
   APP_SENHA = "sua-senha-secreta"
   ```
7. Clique em **Deploy**. Em alguns minutos o app estará no ar em
   `https://seu-usuario-help-limpeza-web.streamlit.app`.

> A senha definida em `APP_SENHA` será solicitada ao abrir o app.
> Sem esse secret (uso local), o acesso é livre.

## Observações sobre os dados

- A versão da nuvem começa com o banco vazio; os dados do PC não são
  enviados (privacidade).
- O armazenamento do Community Cloud é temporário: os dados cadastrados
  na nuvem podem ser perdidos quando o aplicativo reinicia. Para dados
  permanentes na nuvem, conecte um banco externo (ex.: Supabase/Turso).
