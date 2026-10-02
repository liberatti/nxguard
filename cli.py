"""CLI entrypoint for managing NXGuard installation, configuration apply, and SecLanguage indexing."""

import sys
import requests

import engine.seclang.seclang_indexer as indexer
from api.tasks import install, update_main_config
import config


def health_check():

    try:
        response = requests.get(f"http://localhost:5000{config.APP_CONTEXT}", timeout=5)
        if response.status_code == 200:
            sys.exit(0)
        else:
            print(f"Health check failed with status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)


def reset_admin():
    """Resets or recreates the administrator account (admin@nxguard.local / admin)."""
    try:
        import getpass
        import bcrypt
        from api.repository.oauth_repository import UserDao

        email = sys.argv[2] if len(sys.argv) >= 3 else input("Email: ").strip()
        password = sys.argv[3] if len(sys.argv) >= 4 else getpass.getpass("Password: ")

        if not email or not password:
            print("Email and password are required.")
            sys.exit(1)

        encrypted_pass = bcrypt.hashpw(
            password.encode("utf8"), bcrypt.gensalt()
        ).decode("utf8")
        with UserDao() as dao:
            dao.create_schema()
            user = dao.get_by_email(email)
            if user and "_id" in user:
                dao.update_by_id(
                    user["_id"],
                    {
                        "name": user.get("name") or "Default Admin",
                        "password": encrypted_pass,
                        "email": email,
                        "role": "superuser",
                    },
                )
                print(f"Password for user '{email}' successfully reset.")
            else:
                dao.persist(
                    {
                        "name": "Default Admin",
                        "password": encrypted_pass,
                        "email": email,
                        "role": "superuser",
                    }
                )
                print(f"Superuser '{email}' created successfully.")
    except Exception as e:
        print(f"Failed to reset admin user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso: python cli.py <apply|install|index|healthcheck|reset_admin> [options]"
        )
        sys.exit(1)

    switch = {
        "apply": update_main_config,
        "install": install,
        "index": indexer.index,
        "healthcheck": health_check,
        "health_check": health_check,
        "reset_admin": reset_admin,
        "reset-admin": reset_admin,
    }

    fn = switch.get(sys.argv[1])
    if fn:
        fn()
    else:
        print(f"Comando desconhecido: {sys.argv[1]}")
        sys.exit(1)
