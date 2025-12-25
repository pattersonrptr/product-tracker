# Database Initialization Script

## 📋 Propósito

O script `init_dev_db.py` é executado automaticamente durante a inicialização do container Docker e garante que sempre exista um superuser padrão para desenvolvimento.

## 🔑 Credenciais Padrão

```
Username: admin
Password: admin
Email: admin@example.com
```

## ⚙️ Como Funciona

1. **Execução automática**: Roda após as migrations no `start.sh`
2. **Idempotente**: Pode ser executado múltiplas vezes sem problemas
3. **Verificação**: Checa se o usuário `admin` já existe antes de criar
4. **Desenvolvimento only**: Usado apenas em ambiente de desenvolvimento

## 🚀 Quando é Executado

```bash
# Automaticamente ao iniciar os containers
docker compose up --build

# Ou manualmente
docker exec -it web python3 src/scripts/init_dev_db.py
```

## 📊 Fluxo de Inicialização

```
1. Container inicia
2. Aguarda PostgreSQL estar pronto
3. Executa migrations (alembic upgrade head)
4. ✨ Executa init_dev_db.py
   ├─ Verifica se 'admin' existe
   ├─ Se não existe → cria com senha 'admin'
   └─ Se existe → pula (idempotente)
5. Inicia uvicorn (API)
```

## ⚠️ Segurança

**IMPORTANTE**: Este script cria um usuário com credenciais conhecidas (`admin`/`admin`) e deve ser usado **APENAS EM DESENVOLVIMENTO**.

Para produção:
- ❌ NÃO use este script
- ✅ Use o `create_superuser.py` interativo
- ✅ Use senhas fortes e únicas

## 🧪 Benefícios para Testes

1. **Smoke tests funcionam out-of-the-box**:
   ```bash
   ./src/scripts/api_tests/test_auth.sh  # Usa admin/admin automaticamente
   ```

2. **Sem setup manual**: Não precisa rodar `create_superuser.py` após rebuild

3. **Ambiente consistente**: Todos os desenvolvedores têm as mesmas credenciais

## 📝 Exemplo de Saída

```
Initializing development database...
Creating default superuser 'admin'...
✓ Superuser created: admin (ID: 1)
  Username: admin
  Password: admin
  Email: admin@example.com
```

Ou se já existir:

```
Initializing development database...
✓ Superuser 'admin' already exists. Skipping creation.
```

## 🔧 Customização

Se quiser mudar as credenciais padrão, edite:
- `src/scripts/init_dev_db.py` (linhas 35-41)
- `src/scripts/api_tests/test_auth.sh` (linha 13)
