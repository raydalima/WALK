# Deploy em produção do WALK em VPS Ubuntu

Este guia prepara o **WALK** para rodar em uma VPS Ubuntu com **PostgreSQL, Gunicorn, Nginx e HTTPS**.

## 1. Pré-requisitos

- VPS Ubuntu 22.04 ou 24.04.
- Domínio já registrado.
- Acesso `sudo` na VPS.
- Repositório do projeto disponível no Git.

## 2. Variáveis de ambiente

Crie um `.env` no servidor com:

```env
SECRET_KEY=gere-uma-chave-secreta-forte
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com

USE_SQLITE=False
DB_NAME=walk_db
DB_USER=walk_user
DB_PASSWORD=senha-forte
DB_HOST=127.0.0.1
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.seuprovedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=usuario-smtp
EMAIL_HOST_PASSWORD=senha-smtp
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=WALK <nao-responda@seu-dominio.com>

SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## 3. Comandos no servidor

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev git nginx postgresql postgresql-contrib build-essential libpq-dev
```

```bash
sudo adduser walk
sudo usermod -aG sudo walk
sudo mkdir -p /var/www/walk
sudo chown -R walk:walk /var/www/walk
```

```bash
cd /var/www/walk
git clone <URL_DO_REPOSITORIO> .
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE walk_db;
CREATE USER walk_user WITH PASSWORD 'senha-forte';
ALTER ROLE walk_user SET client_encoding TO 'utf8';
ALTER ROLE walk_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE walk_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE walk_db TO walk_user;
\q
```

## 5. Migrações e estáticos

```bash
source /var/www/walk/venv/bin/activate
python manage.py migrate --noinput
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## 6. Gunicorn

Teste manual:

```bash
gunicorn walk.wsgi:application --bind 127.0.0.1:8000
```

Serviço systemd:

```bash
sudo cp deploy/systemd/walk-gunicorn.service /etc/systemd/system/walk-gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable walk-gunicorn
sudo systemctl start walk-gunicorn
sudo systemctl status walk-gunicorn
```

## 7. Nginx

```bash
sudo cp deploy/nginx/walk.conf /etc/nginx/sites-available/walk
sudo ln -s /etc/nginx/sites-available/walk /etc/nginx/sites-enabled/walk
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS

Apontar o domínio para o IP da VPS:

- `A` para `seu-dominio.com` -> `IP_DA_VPS`
- `A` para `www.seu-dominio.com` -> `IP_DA_VPS`

Depois instalar o Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

## 9. Checklist final

- `DEBUG=False`
- `ALLOWED_HOSTS` preenchido
- `CSRF_TRUSTED_ORIGINS` com HTTPS
- PostgreSQL funcionando
- `collectstatic` executado
- Gunicorn rodando via systemd
- Nginx proxyando para Gunicorn
- HTTPS ativo
- Interface exibindo **WALK**
