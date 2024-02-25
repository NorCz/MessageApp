import os
import apsw
import apsw.ext
import apsw.bestpractice

apsw.bestpractice.apply(apsw.bestpractice.recommended)

if not os.path.isfile('./instance/project.db'):
    print('Database not yet created, exiting')
    exit()

