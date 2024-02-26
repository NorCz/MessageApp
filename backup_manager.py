import datetime
import os
import sys
import apsw
import apsw.ext

MAX_BACKUPS = int(sys.argv[1])
if not os.path.exists('/app/backend/instance/backups'):
    os.mkdir('/app/backend/instance/backups')

if not os.path.isfile('/app/backend/instance/project.db'):
    print('[BACKUP] Database not yet created, exiting.')
    exit()

backups = os.listdir('/app/backend/instance/backups')

if len(backups) >= MAX_BACKUPS:
    ctimes = map(lambda path: os.path.getctime('/app/backend/instance/backups/' + path), backups)
    zipped = list(zip(backups, ctimes))
    res = list(sorted(zipped, key=lambda x: x[1]))
    print(f"[BACKUP] Reached MAX_BACKUPS ({MAX_BACKUPS}), deleting {res[0][0]}")
    os.remove('/app/backend/instance/backups/' + res[0][0])

outname = f"/app/backend/instance/backups/backup_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.db"
connection = apsw.Connection("/app/backend/instance/project.db")
destination = apsw.Connection(outname)


with destination.backup("main", connection, "main") as backup:
    while not backup.done:
        backup.step(7)
        print(f"[BACKUP] Copied backup pages: {backup.page_count-backup.remaining}/{backup.page_count}")

print(f'[BACKUP] Backup created successfully as {outname}, exiting.')
