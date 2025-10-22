# Production Dashboard

This Django-based dashboard provides internal tooling for managing "General Orders" at ww.printoften.co.uk. It offers:

- Authentication protected UI for reviewing and updating orders
- Dedicated purchasing, stock control, and production queues to streamline handoffs
- REST-style JSON API for CRUD operations on orders
- Google Sheets synchronisation utilities to keep data aligned with the "General Orders" sheet
- Audit trail logging whenever order production status changes

## Getting started

```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000. Sign in using the staff credentials you created.

## Google Sheets integration

Provide the `GOOGLE_SHEETS_*` environment variables and a service account JSON file path in `.env`. You can then run the synchronisation command:

```bash
python manage.py sync_sheets
```

To automatically refresh data, schedule the command with cron or a task queue (e.g., Celery or cloud scheduler).

## Deployment

A `Dockerfile` and `deploy/docker-compose.yml` are included to support container-based deployment behind a reverse proxy. Configure DNS for `ww.printoften.co.uk` to point at your hosting environment and ensure TLS termination via your preferred solution (e.g., Traefik, Nginx, or cloud load balancer).

### Deploying on Krystal cPanel

Krystal's cPanel hosting supports Passenger-powered Python applications. The repository ships with a `passenger_wsgi.py` entrypoint so the dashboard can be deployed without Docker. A typical deployment flow is:

1. Log in to cPanel and create a new **Python App** that points to the `dashboard/` directory inside this project. Select Python 3.11 (or the latest available) and note the virtualenv path it creates (e.g. `/home/USERNAME/virtualenv/dashboard/3.11`).
2. Upload the project files (including the `dashboard/` folder) to the application directory using Git, SFTP, or the File Manager.
3. SSH into the server, activate the virtualenv that cPanel created, and install dependencies:

   ```bash
   source /home/USERNAME/virtualenv/dashboard/3.11/bin/activate
   pip install -r ~/path-to-app/dashboard/requirements.txt
   ```

4. Configure environment variables via the **Environment Variables** section of the Python App UI (or by editing `passenger_wsgi.py` to load a `.env` file). At minimum set:

   ```text
   DJANGO_SECRET_KEY=your-secret
   DJANGO_ALLOWED_HOSTS=["ww.printoften.co.uk"]
   DJANGO_DB_ENGINE=django.db.backends.mysql
   DJANGO_DB_NAME=cpanel_database_name
   DJANGO_DB_USER=cpanel_database_user
   DJANGO_DB_PASSWORD=strong-password
   DJANGO_DB_HOST=127.0.0.1
   DJANGO_DB_PORT=3306
   DJANGO_STATIC_ROOT=/home/USERNAME/path-to-app/dashboard/public_static
   DJANGO_STATIC_URL=/static/
   ```

   These credentials should match the database you create in MyPHPAdmin.

5. Run initial setup commands from the application directory:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

6. Ensure the `public_static/` directory is web-accessible either by creating a symlink from `~/public_html/static` or by configuring cPanel's **Static Content** option to serve that path.
7. Restart the Python application from the cPanel interface to pick up the new code and environment variables.

Passenger will load `passenger_wsgi.py`, which exposes the Django WSGI application defined in `dashboard/wsgi.py`.
## Order workflow overview

Orders progress through four statuses inside the dashboard:

1. **Pending** – newly logged work waiting to be actioned.
2. **Awaiting Garments** – purchasing is sourcing garments for the order.
3. **Ready** – garments are in stock and production can begin.
4. **Complete** – work finished and ready for dispatch/collection.

Each order also records its decoration requirement (Embroidery, Print, or Both) and an optional preview image URL that displays on the order detail page. Garments associated with an order can be captured with name, colour, size, quantity, and purchasing status to power the purchasing and stock control views.

