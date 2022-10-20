from obsrv_plan.general.params import RESULT_DIR
from obsrv_plan.decorators import static_decorator

import datetime
from os.path import join, exists
from os import makedirs
from multiprocessing import Lock

LOGGING_LOCK = Lock()

def printToLog(msg: str):
	with LOGGING_LOCK:
		if not exists(RESULT_DIR):
			makedirs(RESULT_DIR)

		with open(join(RESULT_DIR, ".log"), "a+") as logFile:
			logFile.write(f"[{datetime.datetime.now()}] {msg}\n")