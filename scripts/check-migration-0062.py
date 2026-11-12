"""Exercise 0061 -> 0062 -> 0061 -> 0062 and preserve module selections."""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='docofhome-0062-') as directory:
    env = {**os.environ, 'JARVIS_DATA_DIR': directory}
    def migrate(target: str, direction: str = 'upgrade') -> None:
        subprocess.run([sys.executable, '-m', 'alembic', direction, target],
                       cwd=ROOT / 'backend', env=env, check=True, capture_output=True)
    migrate('0061')
    database = Path(directory) / 'database/jarvis.sqlite3'
    seed = '''
from sqlmodel import Session
from app.db.session import engine
from app.models.application_setting import ApplicationSetting
with Session(engine) as session:
    session.add(ApplicationSetting(id=1, installation_name="Test", timezone="Europe/Berlin", enabled_modules_json='["assets"]',
                                   main_menu_modules_json='["assets"]'))
    session.commit()
'''
    subprocess.run([sys.executable, '-c', seed], cwd=ROOT/'backend', env=env, check=True)
    migrate('head')
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '0062'
        values = db.execute('SELECT enabled_modules_json, main_menu_modules_json FROM application_settings').fetchone()
        import json
        assert all(json.loads(v) == ['assets', 'time_tracking'] for v in values)
        db.execute("INSERT INTO work_intervals VALUES ('a','123','K','',1,NULL,1,0)")
        try:
            db.execute("INSERT INTO work_intervals VALUES ('b','456','K','',2,NULL,1,0)")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError('Two running intervals were accepted')
    migrate('0061', 'downgrade')
    with sqlite3.connect(database) as db:
        assert json.loads(db.execute('SELECT enabled_modules_json FROM application_settings').fetchone()[0]) == ['assets']
    migrate('head')
print('Migration 0062: upgrade, downgrade, module decisions and single timer verified.')
