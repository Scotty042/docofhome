"""Verify the BCS migration preserves existing intervals and the single-timer index."""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='docofhome-0063-') as directory:
    env = {**os.environ, 'JARVIS_DATA_DIR': directory}
    def migrate(target, direction='upgrade'):
        subprocess.run([sys.executable, '-m', 'alembic', direction, target],
                       cwd=ROOT/'backend', env=env, check=True, capture_output=True)
    migrate('0062')
    database = Path(directory)/'database/jarvis.sqlite3'
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO work_intervals VALUES ('old','T-1','Kunde','Info',100,200,0,1)")
    migrate('head')
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '0063'
        assert db.execute('SELECT * FROM work_intervals').fetchone() == ('old','T-1','Kunde','Info',100,200,0,1,0)
        db.execute('UPDATE work_intervals SET bcs=1')
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT bcs FROM work_intervals').fetchone()[0] == 1
    migrate('0062', 'downgrade')
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT * FROM work_intervals').fetchone() == ('old','T-1','Kunde','Info',100,200,0,1)
    migrate('head')
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT bcs FROM work_intervals').fetchone()[0] == 0
        db.execute("INSERT INTO work_intervals (id,ticket,customer,info,started_at,running,completed) VALUES ('live','T-2','K','',300,1,0)")
        try:
            db.execute("INSERT INTO work_intervals (id,ticket,customer,info,started_at,running,completed) VALUES ('live2','T-3','K','',301,1,0)")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError('Single-timer protection lost')
print('Migration 0063: existing intervals, default false, persistence, downgrade/reupgrade and timer index verified.')
